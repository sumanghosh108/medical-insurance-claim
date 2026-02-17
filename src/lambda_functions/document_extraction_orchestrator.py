"""Lambda Handler - Document Extraction Orchestrator.

Orchestrates text extraction from insurance claim documents stored in S3.
Selects the appropriate extractor (Textract for PDFs, Tesseract for handwritten)
and stores extracted text back to S3 for downstream processing.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

S3_BUCKET = os.environ.get('S3_BUCKET', 'claims-processing-documents')
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', 'claims-processing-results')
CLAIMS_TABLE = os.environ.get('CLAIMS_TABLE', 'claims')
SNS_TOPIC = os.environ.get('SNS_TOPIC', 'arn:aws:sns:ap-south-1:123456789:claim-events')

# Supported document types and their extractors
PDF_EXTENSIONS = {'.pdf'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
HANDWRITTEN_MARKER = '_handwritten'


class DocumentExtractionOrchestrator:
    """Orchestrate document text extraction from S3-stored claim documents."""

    def __init__(self):
        """Initialize with AWS clients and extractors."""
        self.s3 = s3
        self.claims_table = dynamodb.Table(CLAIMS_TABLE)
        self.sns = sns

    def _determine_document_type(self, document_key: str) -> str:
        """Determine document type from the S3 key extension.

        Returns:
            One of 'pdf', 'image', or 'handwritten'.
        """
        key_lower = document_key.lower()

        if HANDWRITTEN_MARKER in key_lower:
            return 'handwritten'

        ext = os.path.splitext(key_lower)[1]
        if ext in PDF_EXTENSIONS:
            return 'pdf'
        if ext in IMAGE_EXTENSIONS:
            return 'image'

        logger.warning(f"Unknown extension '{ext}', defaulting to pdf")
        return 'pdf'

    def _fetch_document(self, document_key: str) -> bytes:
        """Download document bytes from S3."""
        try:
            response = self.s3.get_object(Bucket=S3_BUCKET, Key=document_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to fetch {document_key}: {e}")
            raise

    def _extract_text(self, document_bytes: bytes, doc_type: str) -> Dict[str, Any]:
        """Extract text using the appropriate extractor.

        Uses Textract for PDFs/images and Tesseract for handwritten documents.
        Falls back to Tesseract if Textract fails.
        """
        from src.document_processing import (
            TextractExtractor,
            TesseractExtractor,
        )

        start_time = time.time()

        if doc_type == 'handwritten':
            extractor = TesseractExtractor(config={'preprocess': True})
        else:
            extractor = TextractExtractor(config={
                'feature_types': ['TABLES', 'FORMS'],
            })

        try:
            result = extractor.extract(document_bytes)
            processing_time = time.time() - start_time

            return {
                'text': result.text,
                'confidence': result.confidence,
                'pages': result.pages,
                'extractor_type': result.extractor_type,
                'processing_time': processing_time,
                'metadata': result.metadata,
                'errors': result.errors,
            }
        except Exception as primary_err:
            logger.warning(f"Primary extractor ({doc_type}) failed: {primary_err}")

            # Fallback: try the other extractor
            if doc_type != 'handwritten':
                logger.info("Falling back to Tesseract")
                fallback = TesseractExtractor(config={'preprocess': True})
            else:
                logger.info("Falling back to Textract")
                fallback = TextractExtractor()

            try:
                result = fallback.extract(document_bytes)
                processing_time = time.time() - start_time

                return {
                    'text': result.text,
                    'confidence': result.confidence,
                    'pages': result.pages,
                    'extractor_type': f"{result.extractor_type} (fallback)",
                    'processing_time': processing_time,
                    'metadata': result.metadata,
                    'errors': result.errors,
                }
            except Exception as fallback_err:
                logger.error(f"Fallback extractor also failed: {fallback_err}")
                raise

    def _store_extraction_result(self, claim_id: str, result: Dict) -> str:
        """Store extracted text result to S3 as JSON."""
        output_key = f"extractions/{claim_id}/text_extraction.json"

        payload = {
            'claim_id': claim_id,
            'extracted_at': datetime.utcnow().isoformat(),
            **result,
        }

        self.s3.put_object(
            Bucket=RESULTS_BUCKET,
            Key=output_key,
            Body=json.dumps(payload, default=str),
            ContentType='application/json',
            ServerSideEncryption='aws:kms',
        )
        logger.info(f"Extraction result stored: {output_key}")
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

    def handle(self, event: Dict, context: Any) -> Dict:
        """Main Lambda handler for document extraction.

        Expected event from Step Functions:
            {
                "claim_id": "uuid",
                "document_key": "claims/2025/01/uuid.pdf",
                "timestamp": "ISO-8601"
            }
        """
        try:
            claim_id = event['claim_id']
            document_key = event['document_key']

            logger.info(f"Starting extraction for claim {claim_id}")

            # Update status to indicate extraction in progress
            self._update_claim_status(claim_id, 'EXTRACTING')

            # Determine document type and fetch
            doc_type = self._determine_document_type(document_key)
            document_bytes = self._fetch_document(document_key)

            logger.info(
                f"Document fetched: type={doc_type}, "
                f"size={len(document_bytes)} bytes"
            )

            # Extract text
            extraction_result = self._extract_text(document_bytes, doc_type)

            # Validate extraction quality
            if extraction_result['confidence'] < 0.3:
                logger.warning(
                    f"Low confidence extraction ({extraction_result['confidence']:.2f}) "
                    f"for claim {claim_id}"
                )

            # Store result
            result_key = self._store_extraction_result(claim_id, extraction_result)

            # Update claim status
            self._update_claim_status(
                claim_id,
                'TEXT_EXTRACTED',
                extra={
                    'extraction_confidence': str(extraction_result['confidence']),
                    'extraction_result_key': result_key,
                    'extractor_type': extraction_result['extractor_type'],
                },
            )

            logger.info(f"Extraction complete for claim {claim_id}")

            # Return data for next Step Functions state
            return {
                'claim_id': claim_id,
                'document_key': document_key,
                'extraction_result_key': result_key,
                'extraction_confidence': extraction_result['confidence'],
                'extractor_type': extraction_result['extractor_type'],
                'pages': extraction_result['pages'],
                'processing_time': extraction_result['processing_time'],
                'status': 'TEXT_EXTRACTED',
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
            logger.error(f"Extraction failed for claim {claim_id}: {e}", exc_info=True)

            # Try to update status to ERROR
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
    handler = DocumentExtractionOrchestrator()
    return handler.handle(event, context)
