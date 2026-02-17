"""Lambda Handler - Entity Extraction Processor.

Extracts structured entities (names, dates, amounts, medical codes, policy numbers)
from previously extracted document text. Validates extracted data against
business rules and stores structured results for downstream fraud analysis.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', 'claims-processing-results')
CLAIMS_TABLE = os.environ.get('CLAIMS_TABLE', 'claims')
SNS_TOPIC = os.environ.get('SNS_TOPIC', 'arn:aws:sns:ap-south-1:123456789:claim-events')

# Minimum acceptable validation score to proceed automatically
MIN_VALIDATION_SCORE = float(os.environ.get('MIN_VALIDATION_SCORE', '60.0'))


class EntityExtractionProcessor:
    """Extract structured entities from claim document text and validate them."""

    def __init__(self):
        """Initialize with AWS clients."""
        self.s3 = s3
        self.claims_table = dynamodb.Table(CLAIMS_TABLE)
        self.sns = sns

    def _load_extracted_text(self, extraction_result_key: str) -> Dict:
        """Load the previously extracted text from S3."""
        try:
            response = self.s3.get_object(
                Bucket=RESULTS_BUCKET,
                Key=extraction_result_key,
            )
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            logger.error(f"Failed to load extraction result: {e}")
            raise

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Run entity extraction on the document text.

        Returns:
            Dictionary with entities, structured_data, confidence, etc.
        """
        from src.document_processing import extract_claim_entities

        result = extract_claim_entities(
            text=text,
            extract_medical=True,
            extract_financial=True,
        )

        return {
            'entities': [
                {
                    'text': e.text,
                    'label': e.label,
                    'confidence': e.confidence,
                    'normalized_value': e.normalized_value,
                }
                for e in result.entities
            ],
            'structured_data': result.structured_data,
            'entity_confidence': result.confidence,
            'extractor_type': result.extractor_type,
            'processing_time': result.processing_time,
            'entity_count': len(result.entities),
            'errors': result.errors,
        }

    def _validate_entities(
        self, structured_data: Dict, claim_type: str = 'health'
    ) -> Dict[str, Any]:
        """Validate extracted entities against business rules.

        Returns:
            Dictionary with validation result details.
        """
        from src.document_processing import DocumentValidator

        validator = DocumentValidator()
        result = validator.validate(
            extracted_data=structured_data,
            claim_type=claim_type,
        )

        return {
            'is_valid': result.is_valid,
            'validation_score': result.validation_score,
            'errors_count': result.errors_count,
            'warnings_count': result.warnings_count,
            'validated_fields': result.validated_fields,
            'issues': [
                {
                    'severity': issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                    'code': issue.code,
                    'message': issue.message,
                    'field': issue.field,
                    'suggestion': issue.suggestion,
                }
                for issue in result.issues
            ],
        }

    def _store_entity_result(self, claim_id: str, result: Dict) -> str:
        """Store entity extraction and validation results to S3."""
        output_key = f"extractions/{claim_id}/entity_extraction.json"

        payload = {
            'claim_id': claim_id,
            'processed_at': datetime.utcnow().isoformat(),
            **result,
        }

        self.s3.put_object(
            Bucket=RESULTS_BUCKET,
            Key=output_key,
            Body=json.dumps(payload, default=str),
            ContentType='application/json',
            ServerSideEncryption='aws:kms',
        )
        logger.info(f"Entity result stored: {output_key}")
        return output_key

    def _update_claim_status(
        self, claim_id: str, status: str, extra: Optional[Dict] = None
    ) -> None:
        """Update claim status in DynamoDB."""
        update_expr = "SET #s = :status, updated_at = :ts"
        expr_values = {
            ':status': status,
            ':ts': datetime.utcnow().isoformat(),
        }
        expr_names = {'#s': 'status'}

        if extra:
            for key, value in extra.items():
                update_expr += f", {key} = :{key}"
                expr_values[f":{key}"] = value

        self.claims_table.update_item(
            Key={'claim_id': claim_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
        logger.info(f"Claim {claim_id} status updated to {status}")

    def _publish_validation_alert(
        self, claim_id: str, validation_result: Dict
    ) -> None:
        """Publish SNS alert if validation score is below threshold."""
        if validation_result['validation_score'] < MIN_VALIDATION_SCORE:
            try:
                self.sns.publish(
                    TopicArn=SNS_TOPIC,
                    Subject=f"Low validation score for claim {claim_id}",
                    Message=json.dumps({
                        'claim_id': claim_id,
                        'validation_score': validation_result['validation_score'],
                        'errors_count': validation_result['errors_count'],
                        'warnings_count': validation_result['warnings_count'],
                        'event_type': 'VALIDATION_ALERT',
                    }),
                    MessageAttributes={
                        'event_type': {
                            'StringValue': 'VALIDATION_ALERT',
                            'DataType': 'String',
                        },
                    },
                )
                logger.info(f"Validation alert published for claim {claim_id}")
            except Exception as e:
                logger.warning(f"Failed to publish validation alert: {e}")

    def handle(self, event: Dict, context: Any) -> Dict:
        """Main Lambda handler for entity extraction.

        Expected event from Step Functions (output of document extraction):
            {
                "claim_id": "uuid",
                "document_key": "claims/2025/01/uuid.pdf",
                "extraction_result_key": "extractions/uuid/text_extraction.json",
                "extraction_confidence": 0.95,
                ...
            }
        """
        try:
            claim_id = event['claim_id']
            extraction_result_key = event['extraction_result_key']

            logger.info(f"Starting entity extraction for claim {claim_id}")

            # Update status
            self._update_claim_status(claim_id, 'EXTRACTING_ENTITIES')

            # Load extracted text
            extraction_data = self._load_extracted_text(extraction_result_key)
            text = extraction_data.get('text', '')

            if not text or not text.strip():
                logger.warning(f"No text content for claim {claim_id}")
                self._update_claim_status(
                    claim_id, 'ERROR',
                    extra={'error_message': 'No text content extracted from document'},
                )
                return {
                    'claim_id': claim_id,
                    'status': 'ERROR',
                    'error': 'No text content extracted from document',
                }

            # Extract entities
            entity_result = self._extract_entities(text)
            logger.info(
                f"Extracted {entity_result['entity_count']} entities "
                f"(confidence: {entity_result['entity_confidence']:.2f})"
            )

            # Validate extracted data
            claim_type = extraction_data.get('claim_type', 'health')
            validation_result = self._validate_entities(
                entity_result['structured_data'],
                claim_type=claim_type,
            )
            logger.info(
                f"Validation score: {validation_result['validation_score']:.1f}, "
                f"errors: {validation_result['errors_count']}, "
                f"warnings: {validation_result['warnings_count']}"
            )

            # Combine results
            combined_result = {
                'entity_extraction': entity_result,
                'validation': validation_result,
            }

            # Store results
            entity_result_key = self._store_entity_result(claim_id, combined_result)

            # Update claim status
            self._update_claim_status(
                claim_id,
                'ENTITIES_EXTRACTED',
                extra={
                    'entity_result_key': entity_result_key,
                    'entity_count': str(entity_result['entity_count']),
                    'validation_score': str(validation_result['validation_score']),
                },
            )

            # Alert on low validation scores
            self._publish_validation_alert(claim_id, validation_result)

            logger.info(f"Entity extraction complete for claim {claim_id}")

            # Return data for next Step Functions state
            return {
                'claim_id': claim_id,
                'document_key': event.get('document_key', ''),
                'extraction_result_key': extraction_result_key,
                'entity_result_key': entity_result_key,
                'entity_count': entity_result['entity_count'],
                'entity_confidence': entity_result['entity_confidence'],
                'validation_score': validation_result['validation_score'],
                'validation_is_valid': validation_result['is_valid'],
                'structured_data': entity_result['structured_data'],
                'status': 'ENTITIES_EXTRACTED',
            }

        except KeyError as e:
            logger.error(f"Missing required field: {e}")
            return {
                'error': f'Missing required field: {e}',
                'status': 'ERROR',
                'claim_id': event.get('claim_id', 'unknown'),
            }
        except Exception as e:
            claim_id = event.get('claim_id', 'unknown')
            logger.error(
                f"Entity extraction failed for claim {claim_id}: {e}",
                exc_info=True,
            )

            try:
                self._update_claim_status(
                    claim_id, 'ERROR',
                    extra={'error_message': str(e)[:500]},
                )
            except Exception:
                logger.error("Failed to update error status", exc_info=True)

            return {
                'error': str(e),
                'status': 'ERROR',
                'claim_id': claim_id,
            }


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    handler = EntityExtractionProcessor()
    return handler.handle(event, context)
