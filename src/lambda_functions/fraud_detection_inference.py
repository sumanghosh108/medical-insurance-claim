"""Lambda Handler - Fraud Detection Inference.

Runs the trained fraud detection ensemble model against claim data to produce
fraud risk scores. Downloads the model from S3, prepares features, generates
predictions, and publishes alerts for high-risk claims.
"""

import json
import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

MODEL_BUCKET = os.environ.get('MODEL_BUCKET', 'claims-processing-models')
MODEL_KEY = os.environ.get('MODEL_KEY', 'models/fraud_detection/latest/model.joblib')
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', 'claims-processing-results')
CLAIMS_TABLE = os.environ.get('CLAIMS_TABLE', 'claims')
FRAUD_SCORES_TABLE = os.environ.get('FRAUD_SCORES_TABLE', 'fraud_scores')
SNS_TOPIC = os.environ.get('SNS_TOPIC', 'arn:aws:sns:us-east-1:123456789:claim-events')

# Fraud thresholds
FRAUD_THRESHOLD_HIGH = float(os.environ.get('FRAUD_THRESHOLD_HIGH', '0.75'))
FRAUD_THRESHOLD_MEDIUM = float(os.environ.get('FRAUD_THRESHOLD_MEDIUM', '0.5'))

# Cache model in Lambda warm starts
_cached_model = None


class FraudDetectionInference:
    """Run fraud detection inference on insurance claims."""

    def __init__(self):
        """Initialize with AWS clients."""
        self.s3 = s3
        self.claims_table = dynamodb.Table(CLAIMS_TABLE)
        self.fraud_scores_table = dynamodb.Table(FRAUD_SCORES_TABLE)
        self.sns = sns
        self.model = None

    def _load_model(self):
        """Load trained fraud detection model from S3.

        Uses module-level caching for Lambda warm starts.
        """
        global _cached_model

        if _cached_model is not None:
            logger.info("Using cached model")
            self.model = _cached_model
            return

        from src.ml_models import FraudDetectionEnsemble

        logger.info(f"Downloading model from s3://{MODEL_BUCKET}/{MODEL_KEY}")

        with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.s3.download_file(MODEL_BUCKET, MODEL_KEY, tmp_path)
            self.model = FraudDetectionEnsemble.load(tmp_path)
            _cached_model = self.model
            logger.info("Model loaded successfully")
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _build_claim_dataframe(
        self, event: Dict, structured_data: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Build a DataFrame from claim event data for model inference.

        Combines the original claim metadata with extracted entity data.
        """
        claim_data = {
            'claim_amount': float(event.get('claim_amount', 0)),
            'hospital_id': event.get('hospital_id', 'unknown'),
            'patient_id': event.get('patient_id', 'unknown'),
            'claim_date': event.get('claim_date', datetime.utcnow().isoformat()),
            'treatment_type': event.get('treatment_type', 'Other'),
            'diagnosis_code': event.get('diagnosis_code', ''),
            'missing_fields': 0,
        }

        # Enrich with structured data from entity extraction
        if structured_data:
            personal_info = structured_data.get('personal_info', {})
            financial_info = structured_data.get('financial_info', {})
            medical_info = structured_data.get('medical_info', {})

            # Count missing critical fields
            critical_fields = [
                personal_info.get('patient_name'),
                personal_info.get('date_of_birth'),
                financial_info.get('claim_amount'),
                medical_info.get('diagnosis_code'),
            ]
            claim_data['missing_fields'] = sum(
                1 for f in critical_fields if not f
            )

            # Override with extracted amount if available
            extracted_amount = financial_info.get('claim_amount')
            if extracted_amount:
                try:
                    claim_data['claim_amount'] = float(extracted_amount)
                except (ValueError, TypeError):
                    pass

        return pd.DataFrame([claim_data])

    def _classify_risk(self, fraud_score: float) -> str:
        """Classify fraud risk level based on score thresholds."""
        if fraud_score >= FRAUD_THRESHOLD_HIGH:
            return 'HIGH'
        elif fraud_score >= FRAUD_THRESHOLD_MEDIUM:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _store_fraud_result(self, claim_id: str, result: Dict) -> str:
        """Store fraud detection results to S3 and DynamoDB."""
        # Store detailed result in S3
        output_key = f"extractions/{claim_id}/fraud_detection.json"
        payload = {
            'claim_id': claim_id,
            'scored_at': datetime.utcnow().isoformat(),
            **result,
        }

        self.s3.put_object(
            Bucket=RESULTS_BUCKET,
            Key=output_key,
            Body=json.dumps(payload, default=str),
            ContentType='application/json',
            ServerSideEncryption='aws:kms',
        )

        # Store score in DynamoDB fraud_scores table
        try:
            self.fraud_scores_table.put_item(Item={
                'claim_id': claim_id,
                'fraud_score': str(result['fraud_score']),
                'risk_level': result['risk_level'],
                'prediction': int(result['prediction']),
                'confidence': str(result['confidence']),
                'scored_at': datetime.utcnow().isoformat(),
                'model_version': result.get('model_version', 'unknown'),
            })
        except Exception as e:
            logger.warning(f"Failed to store fraud score in DynamoDB: {e}")

        logger.info(f"Fraud result stored: {output_key}")
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

    def _publish_fraud_alert(self, claim_id: str, result: Dict) -> None:
        """Publish SNS alert for high-risk fraud detections."""
        if result['risk_level'] in ('HIGH', 'MEDIUM'):
            try:
                self.sns.publish(
                    TopicArn=SNS_TOPIC,
                    Subject=f"Fraud alert: {result['risk_level']} risk - Claim {claim_id}",
                    Message=json.dumps({
                        'claim_id': claim_id,
                        'fraud_score': result['fraud_score'],
                        'risk_level': result['risk_level'],
                        'confidence': result['confidence'],
                        'event_type': 'FRAUD_ALERT',
                    }),
                    MessageAttributes={
                        'event_type': {
                            'StringValue': 'FRAUD_ALERT',
                            'DataType': 'String',
                        },
                        'risk_level': {
                            'StringValue': result['risk_level'],
                            'DataType': 'String',
                        },
                    },
                )
                logger.info(
                    f"Fraud alert published: {result['risk_level']} risk "
                    f"for claim {claim_id}"
                )
            except Exception as e:
                logger.warning(f"Failed to publish fraud alert: {e}")

    def handle(self, event: Dict, context: Any) -> Dict:
        """Main Lambda handler for fraud detection inference.

        Expected event from Step Functions (output of entity extraction):
            {
                "claim_id": "uuid",
                "document_key": "...",
                "structured_data": { ... },
                "validation_score": 85.0,
                ...
            }
        """
        try:
            claim_id = event['claim_id']
            logger.info(f"Starting fraud detection for claim {claim_id}")

            # Update status
            self._update_claim_status(claim_id, 'SCORING_FRAUD')

            start_time = time.time()

            # Load model
            self._load_model()

            # Build features DataFrame
            structured_data = event.get('structured_data')
            claim_df = self._build_claim_dataframe(event, structured_data)

            # Prepare features using the model's feature engineering
            features = self.model.prepare_features(claim_df)

            # Run inference
            predictions = self.model.predict(features)

            processing_time = time.time() - start_time

            # Extract results (single claim)
            fraud_score = float(predictions['fraud_score'][0])
            prediction = int(predictions['prediction'][0])
            confidence = float(predictions['confidence'][0])
            risk_level = self._classify_risk(fraud_score)

            fraud_result = {
                'fraud_score': fraud_score,
                'prediction': prediction,
                'confidence': confidence,
                'risk_level': risk_level,
                'processing_time': processing_time,
                'model_version': os.environ.get('MODEL_VERSION', '1.0.0'),
                'features_used': self.model.feature_names,
            }

            logger.info(
                f"Fraud score: {fraud_score:.3f}, "
                f"risk: {risk_level}, confidence: {confidence:.3f}"
            )

            # Store results
            fraud_result_key = self._store_fraud_result(claim_id, fraud_result)

            # Update claim status
            self._update_claim_status(
                claim_id,
                'FRAUD_SCORED',
                extra={
                    'fraud_score': str(fraud_score),
                    'risk_level': risk_level,
                    'fraud_result_key': fraud_result_key,
                },
            )

            # Publish fraud alert if needed
            self._publish_fraud_alert(claim_id, fraud_result)

            logger.info(f"Fraud detection complete for claim {claim_id}")

            # Return data for next Step Functions state
            return {
                'claim_id': claim_id,
                'document_key': event.get('document_key', ''),
                'fraud_score': fraud_score,
                'fraud_prediction': prediction,
                'fraud_confidence': confidence,
                'risk_level': risk_level,
                'fraud_result_key': fraud_result_key,
                'validation_score': event.get('validation_score', 0),
                'validation_is_valid': event.get('validation_is_valid', False),
                'structured_data': structured_data,
                'status': 'FRAUD_SCORED',
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
                f"Fraud detection failed for claim {claim_id}: {e}",
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
    handler = FraudDetectionInference()
    return handler.handle(event, context)
