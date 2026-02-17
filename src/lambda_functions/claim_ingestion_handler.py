"""Lambda Handler - Claim Ingestion and Orchestration."""

import json
import uuid
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import boto3

logger = logging.getLogger(__name__)

s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

STATE_MACHINE_ARN = "arn:aws:states:ap-south-1:123456789:stateMachine:ClaimProcessor"
S3_BUCKET = "claims-processing-documents"
CLAIMS_TABLE = "claims"
SNS_TOPIC = "arn:aws:sns:ap-south-1:123456789:claim-events"


class ClaimIngestionHandler:
    """Handle claim submissions and orchestration."""
    
    def __init__(self):
        """Initialize with AWS clients."""
        self.s3 = s3
        self.sfn = sfn
        self.claims_table = dynamodb.Table(CLAIMS_TABLE)
        self.sns = sns
    
    def validate_claim(self, data: Dict[str, Any]) -> Tuple[bool, list]:
        """Validate claim payload."""
        required = [
            'patient_id', 'hospital_id', 'claim_amount',
            'treatment_type', 'diagnosis_code', 'claim_date'
        ]
        errors = []
        
        for field in required:
            if field not in data or not data[field]:
                errors.append(f"Missing: {field}")
        
        try:
            amt = float(data.get('claim_amount', 0))
            if amt <= 0 or amt > 1000000:
                errors.append("Invalid amount")
        except (ValueError, TypeError):
            errors.append("Amount must be number")
        
        try:
            date_str = data.get('claim_date')
            if date_str:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            errors.append("Invalid date format")
        
        return (len(errors) == 0, errors)
    
    def save_to_s3(self, claim_id: str, doc_b64: str, doc_type: str) -> str:
        """Save document to S3 with encryption."""
        try:
            doc_bytes = base64.b64decode(doc_b64)
            now = datetime.utcnow()
            s3_key = f"claims/{now.year}/{now.month:02d}/{claim_id}.{doc_type}"
            
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=doc_bytes,
                ServerSideEncryption='aws:kms',
                Metadata={'claim-id': claim_id},
            )
            logger.info(f"Saved: {s3_key}")
            return s3_key
        except Exception as e:
            logger.error(f"S3 error: {e}", exc_info=True)
            raise
    
    def save_metadata(self, claim_id: str, data: Dict, s3_key: str) -> None:
        """Save claim metadata to DynamoDB."""
        self.claims_table.put_item(Item={
            'claim_id': claim_id,
            'patient_id': data['patient_id'],
            'hospital_id': data['hospital_id'],
            'claim_amount': float(data['claim_amount']),
            'treatment_type': data['treatment_type'],
            'diagnosis_code': data['diagnosis_code'],
            'claim_date': data['claim_date'],
            'document_key': s3_key,
            'submission_time': datetime.utcnow().isoformat(),
            'status': 'PROCESSING',
        })
        logger.info(f"Metadata saved: {claim_id}")
    
    def trigger_workflow(self, claim_id: str, s3_key: str) -> str:
        """Trigger Step Functions workflow."""
        try:
            response = self.sfn.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=f"claim-{claim_id}",
                input=json.dumps({
                    'claim_id': claim_id,
                    'document_key': s3_key,
                    'timestamp': datetime.utcnow().isoformat(),
                }),
            )
            logger.info(f"Workflow: {response['executionArn']}")
            return response['executionArn']
        except Exception as e:
            logger.error(f"Workflow error: {e}", exc_info=True)
            raise
    
    def publish_notification(self, claim_id: str, message: str) -> None:
        """Publish SNS notification."""
        try:
            self.sns.publish(
                TopicArn=SNS_TOPIC,
                Subject=f"Claim {claim_id}",
                Message=message,
                MessageAttributes={
                    'claim_id': {'StringValue': claim_id, 'DataType': 'String'},
                },
            )
            logger.info(f"Notification: {claim_id}")
        except Exception as e:
            logger.warning(f"SNS error: {e}")
    
    def handle(self, event: Dict, context: Any) -> Dict:
        """Main Lambda handler."""
        try:
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', {})
            
            logger.info("Claim received")
            
            # Validate
            valid, errors = self.validate_claim(body)
            if not valid:
                logger.warning(f"Validation failed: {errors}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid claim', 'details': errors}),
                    'headers': {'Content-Type': 'application/json'},
                }
            
            # Process
            claim_id = str(uuid.uuid4())
            doc_b64 = body.pop('document', '')
            doc_type = body.get('document_type', 'pdf')
            
            if not doc_b64:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Document required'}),
                    'headers': {'Content-Type': 'application/json'},
                }
            
            s3_key = self.save_to_s3(claim_id, doc_b64, doc_type)
            self.save_metadata(claim_id, body, s3_key)
            arn = self.trigger_workflow(claim_id, s3_key)
            self.publish_notification(claim_id, f"Claim {claim_id} processing started")
            
            logger.info(f"Success: {claim_id}")
            return {
                'statusCode': 202,
                'body': json.dumps({
                    'claim_id': claim_id,
                    'status': 'processing',
                    'execution_arn': arn,
                    'message': 'Claim processing started',
                }),
                'headers': {'Content-Type': 'application/json'},
            }
        
        except Exception as e:
            logger.error(f"Handler error: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Server error', 'message': str(e)}),
                'headers': {'Content-Type': 'application/json'},
            }


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    handler = ClaimIngestionHandler()
    return handler.handle(event, context)