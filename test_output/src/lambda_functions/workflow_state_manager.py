"""Lambda Handler - Workflow State Manager.

Manages claim processing workflow state transitions and final decisions.
Aggregates results from all previous pipeline steps (extraction, entity extraction,
fraud detection) and determines the final claim disposition.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3

logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
sfn = boto3.client('stepfunctions')
ses = boto3.client('ses')

CLAIMS_TABLE = os.environ.get('CLAIMS_TABLE', 'claims')
AUDIT_TABLE = os.environ.get('AUDIT_TABLE', 'claim_audit_log')
SNS_TOPIC = os.environ.get('SNS_TOPIC', 'arn:aws:sns:ap-south-1:123456789:claim-events')

# Decision thresholds
FRAUD_AUTO_REJECT_THRESHOLD = float(os.environ.get('FRAUD_AUTO_REJECT_THRESHOLD', '0.85'))
FRAUD_MANUAL_REVIEW_THRESHOLD = float(os.environ.get('FRAUD_MANUAL_REVIEW_THRESHOLD', '0.5'))
MIN_VALIDATION_SCORE_FOR_AUTO = float(os.environ.get('MIN_VALIDATION_SCORE_FOR_AUTO', '70.0'))
MAX_RETRY_ATTEMPTS = int(os.environ.get('MAX_RETRY_ATTEMPTS', '3'))


class WorkflowStateManager:
    """Manage claim workflow state transitions and final decisions."""

    def __init__(self):
        """Initialize with AWS clients."""
        self.claims_table = dynamodb.Table(CLAIMS_TABLE)
        self.audit_table = dynamodb.Table(AUDIT_TABLE)
        self.sns = sns

    def _determine_decision(
        self,
        fraud_score: float,
        validation_score: float,
        validation_is_valid: bool,
    ) -> Dict[str, Any]:
        """Determine the final claim decision based on aggregated scores.

        Decision logic:
        - AUTO_REJECTED: fraud_score >= FRAUD_AUTO_REJECT_THRESHOLD
        - MANUAL_REVIEW: fraud_score >= FRAUD_MANUAL_REVIEW_THRESHOLD
                         OR validation_score < MIN_VALIDATION_SCORE_FOR_AUTO
                         OR validation has critical errors
        - APPROVED: all checks pass within acceptable thresholds

        Returns:
            Dictionary with decision, reason, and requires_human_review flag.
        """
        reasons: List[str] = []

        # High fraud score — auto reject
        if fraud_score >= FRAUD_AUTO_REJECT_THRESHOLD:
            reasons.append(
                f"Fraud score ({fraud_score:.3f}) exceeds "
                f"auto-reject threshold ({FRAUD_AUTO_REJECT_THRESHOLD})"
            )
            return {
                'decision': 'REJECTED',
                'reasons': reasons,
                'requires_human_review': False,
                'auto_decided': True,
            }

        # Medium fraud score — manual review
        if fraud_score >= FRAUD_MANUAL_REVIEW_THRESHOLD:
            reasons.append(
                f"Fraud score ({fraud_score:.3f}) exceeds "
                f"review threshold ({FRAUD_MANUAL_REVIEW_THRESHOLD})"
            )

        # Low validation score — manual review
        if validation_score < MIN_VALIDATION_SCORE_FOR_AUTO:
            reasons.append(
                f"Validation score ({validation_score:.1f}) below "
                f"minimum for auto-approval ({MIN_VALIDATION_SCORE_FOR_AUTO})"
            )

        # Validation has critical errors — manual review
        if not validation_is_valid:
            reasons.append("Document validation has critical errors")

        if reasons:
            return {
                'decision': 'MANUAL_REVIEW',
                'reasons': reasons,
                'requires_human_review': True,
                'auto_decided': False,
            }

        # All checks passed
        return {
            'decision': 'APPROVED',
            'reasons': ['All automated checks passed within acceptable thresholds'],
            'requires_human_review': False,
            'auto_decided': True,
        }

    def _update_claim_final_status(
        self,
        claim_id: str,
        decision: Dict,
        fraud_score: float,
        validation_score: float,
    ) -> None:
        """Update the claim with its final decision status."""
        self.claims_table.update_item(
            Key={'claim_id': claim_id},
            UpdateExpression=(
                "SET #s = :status, "
                "updated_at = :ts, "
                "decision = :decision, "
                "decision_reasons = :reasons, "
                "requires_human_review = :review, "
                "auto_decided = :auto, "
                "fraud_score = :fraud, "
                "validation_score = :validation, "
                "decided_at = :decided_at"
            ),
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':status': decision['decision'],
                ':ts': datetime.utcnow().isoformat(),
                ':decision': decision['decision'],
                ':reasons': decision['reasons'],
                ':review': decision['requires_human_review'],
                ':auto': decision['auto_decided'],
                ':fraud': str(fraud_score),
                ':validation': str(validation_score),
                ':decided_at': datetime.utcnow().isoformat(),
            },
        )
        logger.info(f"Claim {claim_id} final status: {decision['decision']}")

    def _record_audit_event(
        self,
        claim_id: str,
        event_type: str,
        details: Dict,
    ) -> None:
        """Record an audit log entry for compliance and traceability."""
        try:
            self.audit_table.put_item(Item={
                'claim_id': claim_id,
                'event_timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'details': json.dumps(details, default=str),
                'source': 'workflow_state_manager',
            })
            logger.info(f"Audit event recorded: {event_type} for {claim_id}")
        except Exception as e:
            logger.warning(f"Failed to record audit event: {e}")

    def _publish_decision_notification(
        self, claim_id: str, decision: Dict, fraud_score: float
    ) -> None:
        """Publish SNS notification with the final claim decision."""
        try:
            event_type = f"CLAIM_{decision['decision']}"

            self.sns.publish(
                TopicArn=SNS_TOPIC,
                Subject=f"Claim {claim_id} — {decision['decision']}",
                Message=json.dumps({
                    'claim_id': claim_id,
                    'decision': decision['decision'],
                    'reasons': decision['reasons'],
                    'fraud_score': fraud_score,
                    'requires_human_review': decision['requires_human_review'],
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                }),
                MessageAttributes={
                    'event_type': {
                        'StringValue': event_type,
                        'DataType': 'String',
                    },
                    'decision': {
                        'StringValue': decision['decision'],
                        'DataType': 'String',
                    },
                },
            )
            logger.info(f"Decision notification published for claim {claim_id}")
        except Exception as e:
            logger.warning(f"Failed to publish decision notification: {e}")

    def _handle_error_state(self, event: Dict) -> Dict:
        """Handle claims that arrived in an error state from a previous step.

        Implements retry logic with a maximum retry count.
        """
        claim_id = event.get('claim_id', 'unknown')
        retry_count = event.get('retry_count', 0)
        error_message = event.get('error', 'Unknown error')
        failed_step = event.get('failed_step', 'unknown')

        logger.warning(
            f"Claim {claim_id} in error state (attempt {retry_count + 1}): "
            f"{error_message}"
        )

        if retry_count < MAX_RETRY_ATTEMPTS:
            # Signal retry to Step Functions
            logger.info(f"Scheduling retry for claim {claim_id}")
            self._record_audit_event(claim_id, 'RETRY_SCHEDULED', {
                'retry_count': retry_count + 1,
                'failed_step': failed_step,
                'error': error_message,
            })

            return {
                'claim_id': claim_id,
                'status': 'RETRY',
                'retry_count': retry_count + 1,
                'retry_from_step': failed_step,
                'original_error': error_message,
            }
        else:
            # Max retries exceeded — send to manual review
            logger.error(
                f"Max retries ({MAX_RETRY_ATTEMPTS}) exceeded for claim {claim_id}"
            )

            self.claims_table.update_item(
                Key={'claim_id': claim_id},
                UpdateExpression=(
                    "SET #s = :status, updated_at = :ts, "
                    "error_message = :err, requires_human_review = :review"
                ),
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':status': 'MANUAL_REVIEW',
                    ':ts': datetime.utcnow().isoformat(),
                    ':err': f"Max retries exceeded: {error_message}",
                    ':review': True,
                },
            )

            self._record_audit_event(claim_id, 'MAX_RETRIES_EXCEEDED', {
                'retry_count': retry_count,
                'failed_step': failed_step,
                'error': error_message,
            })

            self._publish_decision_notification(
                claim_id,
                {
                    'decision': 'MANUAL_REVIEW',
                    'reasons': [f'Max retries exceeded after {retry_count} attempts'],
                    'requires_human_review': True,
                    'auto_decided': False,
                },
                fraud_score=0.0,
            )

            return {
                'claim_id': claim_id,
                'status': 'MANUAL_REVIEW',
                'decision': 'MANUAL_REVIEW',
                'reasons': [
                    f'Processing failed after {retry_count} retries: {error_message}'
                ],
            }

    def handle(self, event: Dict, context: Any) -> Dict:
        """Main Lambda handler for workflow state management.

        Expected event from Step Functions (output of fraud detection):
            {
                "claim_id": "uuid",
                "fraud_score": 0.35,
                "fraud_prediction": 0,
                "fraud_confidence": 0.65,
                "risk_level": "LOW",
                "validation_score": 92.0,
                "validation_is_valid": true,
                "structured_data": { ... },
                ...
            }

        Also handles error states:
            {
                "claim_id": "uuid",
                "status": "ERROR",
                "error": "...",
                "failed_step": "entity_extraction",
                "retry_count": 1
            }
        """
        try:
            claim_id = event.get('claim_id', 'unknown')
            status = event.get('status', '')

            logger.info(
                f"Workflow state manager invoked for claim {claim_id}, "
                f"status: {status}"
            )

            # Handle error/retry states
            if status == 'ERROR':
                return self._handle_error_state(event)

            # Normal flow: aggregate results and make decision
            fraud_score = float(event.get('fraud_score', 0))
            validation_score = float(event.get('validation_score', 0))
            validation_is_valid = event.get('validation_is_valid', False)

            # Determine decision
            decision = self._determine_decision(
                fraud_score=fraud_score,
                validation_score=validation_score,
                validation_is_valid=validation_is_valid,
            )

            logger.info(
                f"Decision for claim {claim_id}: {decision['decision']} "
                f"(fraud={fraud_score:.3f}, validation={validation_score:.1f})"
            )

            # Update claim with final status
            self._update_claim_final_status(
                claim_id, decision, fraud_score, validation_score,
            )

            # Record audit trail
            self._record_audit_event(claim_id, 'DECISION_MADE', {
                'decision': decision['decision'],
                'reasons': decision['reasons'],
                'fraud_score': fraud_score,
                'validation_score': validation_score,
                'auto_decided': decision['auto_decided'],
            })

            # Publish notification
            self._publish_decision_notification(claim_id, decision, fraud_score)

            logger.info(f"Workflow complete for claim {claim_id}")

            return {
                'claim_id': claim_id,
                'status': decision['decision'],
                'decision': decision['decision'],
                'reasons': decision['reasons'],
                'requires_human_review': decision['requires_human_review'],
                'auto_decided': decision['auto_decided'],
                'fraud_score': fraud_score,
                'validation_score': validation_score,
                'decided_at': datetime.utcnow().isoformat(),
            }

        except Exception as e:
            claim_id = event.get('claim_id', 'unknown')
            logger.error(
                f"Workflow state manager failed for claim {claim_id}: {e}",
                exc_info=True,
            )

            try:
                self._record_audit_event(claim_id, 'WORKFLOW_ERROR', {
                    'error': str(e),
                })
            except Exception:
                pass

            return {
                'error': str(e),
                'status': 'ERROR',
                'claim_id': claim_id,
            }


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    handler = WorkflowStateManager()
    return handler.handle(event, context)
