"""
API Handlers

Lambda function handlers for API Gateway integration.
Each handler processes HTTP requests, validates input, executes business logic,
and returns properly formatted responses.
"""

import json
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from pydantic import ValidationError

from .models import (
    ClaimSubmissionRequest,
    ClaimUpdateRequest,
    ClaimQueryParams,
    DocumentUploadRequest,
    ClaimResponse,
    ClaimListResponse,
    DocumentResponse,
    ErrorResponse,
    HealthCheckResponse,
    ClaimStatus,
    ClaimMetadata,
)
from .middleware import authenticate_request, check_rate_limit, cors_handler
from .utils import (
    create_response,
    parse_request_body,
    extract_user_info,
    generate_claim_number,
)


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sqs_client = boto3.client('sqs')
sns_client = boto3.client('sns')


# Configuration from environment variables
import os
CLAIMS_TABLE = os.getenv('CLAIMS_TABLE', 'insurance-claims')
DOCUMENTS_TABLE = os.getenv('DOCUMENTS_TABLE', 'claim-documents')
DOCUMENTS_BUCKET = os.getenv('DOCUMENTS_BUCKET', 'insurance-claims-documents')
PROCESSING_QUEUE = os.getenv('PROCESSING_QUEUE_URL', '')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')


def health_check_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Health check endpoint
    
    GET /health
    
    Returns service health status and dependency checks.
    """
    logger.info("Health check requested")
    
    try:
        # Check dependencies
        dependencies = {}
        
        # Check DynamoDB
        try:
            table = dynamodb.Table(CLAIMS_TABLE)
            table.table_status
            dependencies['dynamodb'] = 'healthy'
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {e}")
            dependencies['dynamodb'] = 'unhealthy'
        
        # Check S3
        try:
            s3_client.head_bucket(Bucket=DOCUMENTS_BUCKET)
            dependencies['s3'] = 'healthy'
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            dependencies['s3'] = 'unhealthy'
        
        # Overall status
        overall_status = 'healthy'
        if 'unhealthy' in dependencies.values():
            overall_status = 'degraded'
        
        response_body = HealthCheckResponse(
            status=overall_status,
            version="1.0.0",
            timestamp=datetime.utcnow(),
            dependencies=dependencies
        )
        
        return create_response(200, response_body.dict())
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return create_response(500, {
            "status": "unhealthy",
            "error": str(e)
        })


@cors_handler
@authenticate_request
@check_rate_limit
def submit_claim_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Submit new insurance claim
    
    POST /claims
    
    Validates claim data, creates claim record, and initiates processing workflow.
    """
    request_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    logger.info(f"[{request_id}] Claim submission requested")
    
    try:
        # Parse and validate request body
        try:
            claim_data = parse_request_body(event, ClaimSubmissionRequest)
        except ValidationError as e:
            logger.warning(f"[{request_id}] Validation error: {e}")
            return create_response(400, ErrorResponse(
                error="ValidationError",
                error_code="INVALID_INPUT",
                message="Request validation failed",
                details={"errors": e.errors()},
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        # Extract user info from auth context
        user_info = extract_user_info(event)
        user_id = user_info.get('user_id', 'unknown')
        
        # Generate claim ID and number
        claim_id = f"claim_{uuid.uuid4().hex}"
        claim_number = generate_claim_number()
        
        # Create claim record
        now = datetime.utcnow()
        claim_record = {
            'claim_id': claim_id,
            'claim_number': claim_number,
            'status': ClaimStatus.SUBMITTED.value,
            'priority': claim_data.priority.value,
            'claim_type': claim_data.claim_type.value,
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'created_by': user_id,
            
            # Claim data
            'personal_info': claim_data.personal_info.dict(),
            'policy_info': claim_data.policy_info.dict(),
            'incident_info': claim_data.incident_info.dict(),
            'amount': claim_data.amount.dict(),
            'medical_info': claim_data.medical_info.dict() if claim_data.medical_info else None,
            'additional_notes': claim_data.additional_notes,
            'attachments': claim_data.attachments or [],
            
            # Processing metadata
            'processing_started_at': None,
            'processing_completed_at': None,
            'assigned_to': None,
            'validation_results': None,
            'fraud_score': None,
        }
        
        # Save to DynamoDB
        table = dynamodb.Table(CLAIMS_TABLE)
        table.put_item(Item=claim_record)
        logger.info(f"[{request_id}] Claim {claim_number} created successfully")
        
        # Send to processing queue
        if PROCESSING_QUEUE:
            try:
                sqs_client.send_message(
                    QueueUrl=PROCESSING_QUEUE,
                    MessageBody=json.dumps({
                        'claim_id': claim_id,
                        'claim_number': claim_number,
                        'claim_type': claim_data.claim_type.value,
                        'priority': claim_data.priority.value,
                        'timestamp': now.isoformat()
                    }),
                    MessageAttributes={
                        'claim_type': {'StringValue': claim_data.claim_type.value, 'DataType': 'String'},
                        'priority': {'StringValue': claim_data.priority.value, 'DataType': 'String'}
                    }
                )
                logger.info(f"[{request_id}] Claim {claim_number} queued for processing")
            except Exception as e:
                logger.error(f"[{request_id}] Failed to queue claim: {e}")
                # Don't fail the request, but log the error
        
        # Send notification
        if SNS_TOPIC_ARN:
            try:
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=f"New Claim Submitted: {claim_number}",
                    Message=json.dumps({
                        'claim_id': claim_id,
                        'claim_number': claim_number,
                        'status': ClaimStatus.SUBMITTED.value,
                        'claim_type': claim_data.claim_type.value,
                        'amount': claim_data.amount.claimed_amount,
                        'created_at': now.isoformat()
                    })
                )
            except Exception as e:
                logger.error(f"[{request_id}] Failed to send notification: {e}")
        
        # Prepare response
        response_data = ClaimResponse(
            metadata=ClaimMetadata(
                claim_id=claim_id,
                claim_number=claim_number,
                status=ClaimStatus.SUBMITTED,
                priority=claim_data.priority,
                created_at=now,
                updated_at=now,
                created_by=user_id
            ),
            claim_data=claim_data,
            next_steps=[
                "Claim submitted successfully",
                "Documents are being processed",
                "You will receive updates via email",
                "Expected processing time: 24-48 hours"
            ]
        )
        
        return create_response(202, response_data.dict())  # 202 Accepted
        
    except Exception as e:
        logger.error(f"[{request_id}] Claim submission error: {e}", exc_info=True)
        return create_response(500, ErrorResponse(
            error="InternalServerError",
            error_code="CLAIM_SUBMISSION_FAILED",
            message="Failed to process claim submission",
            details={"error": str(e)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        ).dict())


@cors_handler
@authenticate_request
def get_claim_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Retrieve claim by ID
    
    GET /claims/{claim_id}
    
    Returns detailed claim information including processing status.
    """
    request_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    
    try:
        # Extract claim ID from path
        claim_id = event.get('pathParameters', {}).get('claim_id')
        if not claim_id:
            return create_response(400, ErrorResponse(
                error="BadRequest",
                error_code="MISSING_CLAIM_ID",
                message="Claim ID is required",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        logger.info(f"[{request_id}] Retrieving claim: {claim_id}")
        
        # Get user info for authorization check
        user_info = extract_user_info(event)
        user_id = user_info.get('user_id', 'unknown')
        
        # Retrieve from DynamoDB
        table = dynamodb.Table(CLAIMS_TABLE)
        response = table.get_item(Key={'claim_id': claim_id})
        
        if 'Item' not in response:
            logger.warning(f"[{request_id}] Claim not found: {claim_id}")
            return create_response(404, ErrorResponse(
                error="NotFound",
                error_code="CLAIM_NOT_FOUND",
                message=f"Claim {claim_id} not found",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        claim_record = response['Item']
        
        # Authorization check - user can only access their own claims (unless admin)
        is_admin = user_info.get('role') == 'admin'
        if not is_admin and claim_record.get('created_by') != user_id:
            logger.warning(f"[{request_id}] Unauthorized access attempt by {user_id} to claim {claim_id}")
            return create_response(403, ErrorResponse(
                error="Forbidden",
                error_code="UNAUTHORIZED_ACCESS",
                message="You don't have permission to access this claim",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        # Build response
        from .models import ValidationResult, FraudScore, ProcessingResult
        
        metadata = ClaimMetadata(
            claim_id=claim_record['claim_id'],
            claim_number=claim_record['claim_number'],
            status=ClaimStatus(claim_record['status']),
            priority=claim_record.get('priority', 'medium'),
            created_at=datetime.fromisoformat(claim_record['created_at']),
            updated_at=datetime.fromisoformat(claim_record['updated_at']),
            created_by=claim_record['created_by'],
            assigned_to=claim_record.get('assigned_to')
        )
        
        response_data = ClaimResponse(
            metadata=metadata,
            validation=ValidationResult(**claim_record['validation_results']) if claim_record.get('validation_results') else None,
            fraud_score=FraudScore(**claim_record['fraud_score']) if claim_record.get('fraud_score') else None,
            processing=ProcessingResult(
                documents_processed=len(claim_record.get('attachments', [])),
                text_extraction_confidence=claim_record.get('extraction_confidence'),
                entities_extracted=claim_record.get('entities_count')
            ) if claim_record.get('attachments') else None
        )
        
        return create_response(200, response_data.dict())
        
    except Exception as e:
        logger.error(f"[{request_id}] Get claim error: {e}", exc_info=True)
        return create_response(500, ErrorResponse(
            error="InternalServerError",
            error_code="GET_CLAIM_FAILED",
            message="Failed to retrieve claim",
            details={"error": str(e)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        ).dict())


@cors_handler
@authenticate_request
def update_claim_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update existing claim
    
    PATCH /claims/{claim_id}
    
    Updates claim status, notes, or assignments.
    """
    request_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    
    try:
        # Extract claim ID
        claim_id = event.get('pathParameters', {}).get('claim_id')
        if not claim_id:
            return create_response(400, ErrorResponse(
                error="BadRequest",
                error_code="MISSING_CLAIM_ID",
                message="Claim ID is required",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        # Parse update request
        try:
            update_data = parse_request_body(event, ClaimUpdateRequest)
        except ValidationError as e:
            return create_response(400, ErrorResponse(
                error="ValidationError",
                error_code="INVALID_INPUT",
                message="Request validation failed",
                details={"errors": e.errors()},
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        logger.info(f"[{request_id}] Updating claim: {claim_id}")
        
        # Get user info
        user_info = extract_user_info(event)
        user_id = user_info.get('user_id', 'unknown')
        is_admin = user_info.get('role') == 'admin'
        
        # Check if claim exists and user has permission
        table = dynamodb.Table(CLAIMS_TABLE)
        response = table.get_item(Key={'claim_id': claim_id})
        
        if 'Item' not in response:
            return create_response(404, ErrorResponse(
                error="NotFound",
                error_code="CLAIM_NOT_FOUND",
                message=f"Claim {claim_id} not found",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        claim_record = response['Item']
        
        # Authorization - only admins or claim creator can update
        if not is_admin and claim_record.get('created_by') != user_id:
            return create_response(403, ErrorResponse(
                error="Forbidden",
                error_code="UNAUTHORIZED_UPDATE",
                message="You don't have permission to update this claim",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        # Build update expression
        update_expr_parts = []
        expr_attr_values = {}
        expr_attr_names = {}
        
        if update_data.status:
            update_expr_parts.append('#status = :status')
            expr_attr_names['#status'] = 'status'
            expr_attr_values[':status'] = update_data.status.value
        
        if update_data.additional_notes:
            update_expr_parts.append('additional_notes = :notes')
            expr_attr_values[':notes'] = update_data.additional_notes
        
        if update_data.attachments:
            update_expr_parts.append('attachments = :attachments')
            expr_attr_values[':attachments'] = update_data.attachments
        
        if update_data.assigned_to:
            update_expr_parts.append('assigned_to = :assigned_to')
            expr_attr_values[':assigned_to'] = update_data.assigned_to
        
        # Always update timestamp
        update_expr_parts.append('updated_at = :updated_at')
        expr_attr_values[':updated_at'] = datetime.utcnow().isoformat()
        
        if not update_expr_parts:
            return create_response(400, ErrorResponse(
                error="BadRequest",
                error_code="NO_UPDATES",
                message="No updates provided",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        # Perform update
        update_expr = 'SET ' + ', '.join(update_expr_parts)
        
        table.update_item(
            Key={'claim_id': claim_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names if expr_attr_names else None
        )
        
        logger.info(f"[{request_id}] Claim {claim_id} updated successfully")
        
        # Send notification if status changed
        if update_data.status and SNS_TOPIC_ARN:
            try:
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=f"Claim Status Updated: {claim_record['claim_number']}",
                    Message=json.dumps({
                        'claim_id': claim_id,
                        'claim_number': claim_record['claim_number'],
                        'old_status': claim_record['status'],
                        'new_status': update_data.status.value,
                        'updated_by': user_id,
                        'updated_at': datetime.utcnow().isoformat()
                    })
                )
            except Exception as e:
                logger.error(f"[{request_id}] Failed to send notification: {e}")
        
        return create_response(200, {
            "message": "Claim updated successfully",
            "claim_id": claim_id,
            "updated_fields": list(update_expr_parts)
        })
        
    except Exception as e:
        logger.error(f"[{request_id}] Update claim error: {e}", exc_info=True)
        return create_response(500, ErrorResponse(
            error="InternalServerError",
            error_code="UPDATE_CLAIM_FAILED",
            message="Failed to update claim",
            details={"error": str(e)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        ).dict())


@cors_handler
@authenticate_request
def list_claims_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List claims with filtering and pagination
    
    GET /claims?status=processing&limit=20&offset=0
    
    Returns paginated list of claims based on query parameters.
    """
    request_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        
        try:
            filters = ClaimQueryParams(**query_params)
        except ValidationError as e:
            return create_response(400, ErrorResponse(
                error="ValidationError",
                error_code="INVALID_QUERY_PARAMS",
                message="Invalid query parameters",
                details={"errors": e.errors()},
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        logger.info(f"[{request_id}] Listing claims with filters: {filters.dict()}")
        
        # Get user info
        user_info = extract_user_info(event)
        user_id = user_info.get('user_id', 'unknown')
        is_admin = user_info.get('role') == 'admin'
        
        # Build DynamoDB query
        table = dynamodb.Table(CLAIMS_TABLE)
        
        # In production, use proper indexes and query instead of scan
        # This is simplified for demonstration
        scan_kwargs = {
            'Limit': min(filters.limit, 100)
        }
        
        # Add filter expressions
        filter_expressions = []
        expr_attr_values = {}
        expr_attr_names = {}
        
        if filters.status:
            filter_expressions.append('#status = :status')
            expr_attr_names['#status'] = 'status'
            expr_attr_values[':status'] = filters.status.value
        
        if filters.claim_type:
            filter_expressions.append('claim_type = :claim_type')
            expr_attr_values[':claim_type'] = filters.claim_type.value
        
        if filters.policy_number:
            filter_expressions.append('policy_info.policy_number = :policy_number')
            expr_attr_values[':policy_number'] = filters.policy_number
        
        # Non-admin users can only see their own claims
        if not is_admin:
            filter_expressions.append('created_by = :user_id')
            expr_attr_values[':user_id'] = user_id
        
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expr_attr_values
            if expr_attr_names:
                scan_kwargs['ExpressionAttributeNames'] = expr_attr_names
        
        # Execute scan
        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        # Build claim responses
        claims = []
        for item in items:
            metadata = ClaimMetadata(
                claim_id=item['claim_id'],
                claim_number=item['claim_number'],
                status=ClaimStatus(item['status']),
                priority=item.get('priority', 'medium'),
                created_at=datetime.fromisoformat(item['created_at']),
                updated_at=datetime.fromisoformat(item['updated_at']),
                created_by=item['created_by'],
                assigned_to=item.get('assigned_to')
            )
            
            claims.append(ClaimResponse(metadata=metadata))
        
        # Apply offset (in production, use proper pagination with LastEvaluatedKey)
        if filters.offset > 0:
            claims = claims[filters.offset:]
        
        # Apply limit
        claims = claims[:filters.limit]
        
        # Determine if there are more results
        has_more = 'LastEvaluatedKey' in response
        
        response_data = ClaimListResponse(
            claims=claims,
            total_count=len(items),  # In production, get actual count
            limit=filters.limit,
            offset=filters.offset,
            has_more=has_more
        )
        
        return create_response(200, response_data.dict())
        
    except Exception as e:
        logger.error(f"[{request_id}] List claims error: {e}", exc_info=True)
        return create_response(500, ErrorResponse(
            error="InternalServerError",
            error_code="LIST_CLAIMS_FAILED",
            message="Failed to list claims",
            details={"error": str(e)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        ).dict())


@cors_handler
@authenticate_request
def upload_document_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate presigned URL for document upload
    
    POST /documents/upload
    
    Returns presigned URL for direct S3 upload.
    """
    request_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    
    try:
        # Parse upload request
        try:
            upload_request = parse_request_body(event, DocumentUploadRequest)
        except ValidationError as e:
            return create_response(400, ErrorResponse(
                error="ValidationError",
                error_code="INVALID_INPUT",
                message="Request validation failed",
                details={"errors": e.errors()},
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        logger.info(f"[{request_id}] Document upload requested for claim: {upload_request.claim_id}")
        
        # Get user info
        user_info = extract_user_info(event)
        user_id = user_info.get('user_id', 'unknown')
        
        # Verify claim exists
        table = dynamodb.Table(CLAIMS_TABLE)
        response = table.get_item(Key={'claim_id': upload_request.claim_id})
        
        if 'Item' not in response:
            return create_response(404, ErrorResponse(
                error="NotFound",
                error_code="CLAIM_NOT_FOUND",
                message=f"Claim {upload_request.claim_id} not found",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex}"
        s3_key = f"{upload_request.claim_id}/{document_id}/{upload_request.file_name}"
        
        # Generate presigned URL for upload
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': DOCUMENTS_BUCKET,
                'Key': s3_key,
                'ContentType': upload_request.content_type,
                'ContentLength': upload_request.file_size,
            },
            ExpiresIn=3600,  # 1 hour
            HttpMethod='PUT'
        )
        
        # Create document metadata record
        doc_table = dynamodb.Table(DOCUMENTS_TABLE)
        now = datetime.utcnow()
        
        doc_record = {
            'document_id': document_id,
            'claim_id': upload_request.claim_id,
            'document_type': upload_request.document_type.value,
            'file_name': upload_request.file_name,
            'file_size': upload_request.file_size,
            'content_type': upload_request.content_type,
            's3_uri': f"s3://{DOCUMENTS_BUCKET}/{s3_key}",
            's3_bucket': DOCUMENTS_BUCKET,
            's3_key': s3_key,
            'uploaded_at': now.isoformat(),
            'uploaded_by': user_id,
            'processing_status': 'pending',
            'extraction_results': None
        }
        
        doc_table.put_item(Item=doc_record)
        
        logger.info(f"[{request_id}] Presigned URL generated for document: {document_id}")
        
        from .models import DocumentMetadata
        
        response_data = DocumentResponse(
            metadata=DocumentMetadata(
                document_id=document_id,
                claim_id=upload_request.claim_id,
                document_type=upload_request.document_type,
                file_name=upload_request.file_name,
                file_size=upload_request.file_size,
                content_type=upload_request.content_type,
                s3_uri=doc_record['s3_uri'],
                uploaded_at=now,
                uploaded_by=user_id,
                processing_status='pending'
            ),
            presigned_url=presigned_url
        )
        
        return create_response(200, response_data.dict())
        
    except Exception as e:
        logger.error(f"[{request_id}] Upload document error: {e}", exc_info=True)
        return create_response(500, ErrorResponse(
            error="InternalServerError",
            error_code="UPLOAD_DOCUMENT_FAILED",
            message="Failed to generate upload URL",
            details={"error": str(e)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        ).dict())


@cors_handler
@authenticate_request
def get_document_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Retrieve document metadata and download URL
    
    GET /documents/{document_id}
    
    Returns document metadata and presigned download URL.
    """
    request_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    
    try:
        # Extract document ID
        document_id = event.get('pathParameters', {}).get('document_id')
        if not document_id:
            return create_response(400, ErrorResponse(
                error="BadRequest",
                error_code="MISSING_DOCUMENT_ID",
                message="Document ID is required",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        logger.info(f"[{request_id}] Retrieving document: {document_id}")
        
        # Get document metadata
        doc_table = dynamodb.Table(DOCUMENTS_TABLE)
        response = doc_table.get_item(Key={'document_id': document_id})
        
        if 'Item' not in response:
            return create_response(404, ErrorResponse(
                error="NotFound",
                error_code="DOCUMENT_NOT_FOUND",
                message=f"Document {document_id} not found",
                request_id=request_id,
                timestamp=datetime.utcnow()
            ).dict())
        
        doc_record = response['Item']
        
        # Generate presigned download URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': doc_record['s3_bucket'],
                'Key': doc_record['s3_key']
            },
            ExpiresIn=3600  # 1 hour
        )
        
        from .models import DocumentMetadata
        
        response_data = DocumentResponse(
            metadata=DocumentMetadata(
                document_id=doc_record['document_id'],
                claim_id=doc_record['claim_id'],
                document_type=doc_record['document_type'],
                file_name=doc_record['file_name'],
                file_size=doc_record['file_size'],
                content_type=doc_record['content_type'],
                s3_uri=doc_record['s3_uri'],
                uploaded_at=datetime.fromisoformat(doc_record['uploaded_at']),
                uploaded_by=doc_record['uploaded_by'],
                processing_status=doc_record['processing_status']
            ),
            presigned_url=presigned_url,
            extraction_results=doc_record.get('extraction_results')
        )
        
        return create_response(200, response_data.dict())
        
    except Exception as e:
        logger.error(f"[{request_id}] Get document error: {e}", exc_info=True)
        return create_response(500, ErrorResponse(
            error="InternalServerError",
            error_code="GET_DOCUMENT_FAILED",
            message="Failed to retrieve document",
            details={"error": str(e)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        ).dict())


# Export all handlers
__all__ = [
    "health_check_handler",
    "submit_claim_handler",
    "get_claim_handler",
    "update_claim_handler",
    "list_claims_handler",
    "upload_document_handler",
    "get_document_handler",
]