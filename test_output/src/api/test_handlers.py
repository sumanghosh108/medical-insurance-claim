"""
Unit tests for API handlers
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from api.handlers import (
    health_check_handler,
    submit_claim_handler,
    get_claim_handler,
    update_claim_handler,
    list_claims_handler,
    upload_document_handler,
    get_document_handler,
)
from api.models import ClaimStatus


class TestHealthCheckHandler:
    """Tests for health check endpoint"""
    
    @patch('api.handlers.dynamodb')
    @patch('api.handlers.s3_client')
    def test_health_check_healthy(self, mock_s3, mock_dynamodb):
        """Test health check when all services are healthy"""
        
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.table_status = 'ACTIVE'
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock S3
        mock_s3.head_bucket.return_value = {}
        
        # Call handler
        event = {}
        context = Mock()
        
        response = health_check_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'
        assert body['dependencies']['dynamodb'] == 'healthy'
        assert body['dependencies']['s3'] == 'healthy'
    
    @patch('api.handlers.dynamodb')
    @patch('api.handlers.s3_client')
    def test_health_check_degraded(self, mock_s3, mock_dynamodb):
        """Test health check when service is degraded"""
        
        # Mock DynamoDB failure
        mock_dynamodb.Table.side_effect = Exception("DynamoDB error")
        
        # Mock S3 healthy
        mock_s3.head_bucket.return_value = {}
        
        event = {}
        context = Mock()
        
        response = health_check_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'degraded'
        assert body['dependencies']['dynamodb'] == 'unhealthy'


class TestSubmitClaimHandler:
    """Tests for claim submission endpoint"""
    
    @patch('api.handlers.dynamodb')
    @patch('api.handlers.sqs_client')
    @patch('api.handlers.sns_client')
    def test_submit_claim_success(self, mock_sns, mock_sqs, mock_dynamodb):
        """Test successful claim submission"""
        
        # Mock DynamoDB
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Create valid claim request
        claim_data = {
            "claim_type": "health",
            "personal_info": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1980-01-15T00:00:00Z",
                "email": "john@example.com",
                "phone": "5551234567",
                "address": "123 Main St"
            },
            "policy_info": {
                "policy_number": "AB1234567",
                "policy_holder_name": "John Doe",
                "coverage_type": "Health",
                "effective_date": "2024-01-01T00:00:00Z"
            },
            "incident_info": {
                "incident_date": "2024-03-15T00:00:00Z",
                "incident_location": "Hospital",
                "description": "Medical treatment"
            },
            "amount": {
                "claimed_amount": 5000.00,
                "currency": "USD"
            },
            "medical_info": {
                "provider_name": "Dr. Smith",
                "diagnosis_codes": ["E11.9"],
                "treatment_date": "2024-03-15T00:00:00Z"
            }
        }
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(claim_data),
            'headers': {},
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {
                    'user_id': 'user123',
                    'role': 'user'
                }
            }
        }
        context = Mock()
        
        response = submit_claim_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 202
        body = json.loads(response['body'])
        assert 'metadata' in body
        assert body['metadata']['status'] == 'submitted'
        assert 'claim_number' in body['metadata']
        
        # Verify DynamoDB called
        mock_table.put_item.assert_called_once()
    
    def test_submit_claim_validation_error(self):
        """Test claim submission with invalid data"""
        
        # Missing required fields
        invalid_data = {
            "claim_type": "health"
            # Missing all other required fields
        }
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(invalid_data),
            'headers': {},
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {'user_id': 'user123'}
            }
        }
        context = Mock()
        
        response = submit_claim_handler(event, context)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error_code'] == 'INVALID_INPUT'


class TestGetClaimHandler:
    """Tests for get claim endpoint"""
    
    @patch('api.handlers.dynamodb')
    def test_get_claim_success(self, mock_dynamodb):
        """Test successful claim retrieval"""
        
        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'claim_id': 'claim123',
                'claim_number': 'CLM-1234567890',
                'status': 'processing',
                'priority': 'medium',
                'created_at': '2024-03-15T10:00:00',
                'updated_at': '2024-03-15T10:05:00',
                'created_by': 'user123',
            }
        }
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'claim_id': 'claim123'},
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {
                    'user_id': 'user123',
                    'role': 'user'
                }
            }
        }
        context = Mock()
        
        response = get_claim_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['metadata']['claim_id'] == 'claim123'
        assert body['metadata']['status'] == 'processing'
    
    @patch('api.handlers.dynamodb')
    def test_get_claim_not_found(self, mock_dynamodb):
        """Test claim not found"""
        
        # Mock DynamoDB - no item found
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'claim_id': 'nonexistent'},
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {'user_id': 'user123'}
            }
        }
        context = Mock()
        
        response = get_claim_handler(event, context)
        
        # Should return 404
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error_code'] == 'CLAIM_NOT_FOUND'
    
    @patch('api.handlers.dynamodb')
    def test_get_claim_unauthorized(self, mock_dynamodb):
        """Test unauthorized access to claim"""
        
        # Mock DynamoDB - claim belongs to different user
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'claim_id': 'claim123',
                'claim_number': 'CLM-1234567890',
                'status': 'processing',
                'created_by': 'otheruser',  # Different user
                'created_at': '2024-03-15T10:00:00',
                'updated_at': '2024-03-15T10:05:00',
            }
        }
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'claim_id': 'claim123'},
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {
                    'user_id': 'user123',  # Different user
                    'role': 'user'  # Not admin
                }
            }
        }
        context = Mock()
        
        response = get_claim_handler(event, context)
        
        # Should return 403
        assert response['statusCode'] == 403
        body = json.loads(response['body'])
        assert body['error_code'] == 'UNAUTHORIZED_ACCESS'


class TestUpdateClaimHandler:
    """Tests for update claim endpoint"""
    
    @patch('api.handlers.dynamodb')
    @patch('api.handlers.sns_client')
    def test_update_claim_status(self, mock_sns, mock_dynamodb):
        """Test updating claim status"""
        
        # Mock DynamoDB
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'claim_id': 'claim123',
                'claim_number': 'CLM-1234567890',
                'status': 'submitted',
                'created_by': 'user123',
                'created_at': '2024-03-15T10:00:00',
                'updated_at': '2024-03-15T10:00:00',
            }
        }
        mock_dynamodb.Table.return_value = mock_table
        
        update_data = {
            "status": "processing",
            "additional_notes": "Started processing"
        }
        
        event = {
            'httpMethod': 'PATCH',
            'pathParameters': {'claim_id': 'claim123'},
            'body': json.dumps(update_data),
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {
                    'user_id': 'user123',
                    'role': 'admin'  # Admin can update
                }
            }
        }
        context = Mock()
        
        response = update_claim_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Claim updated successfully'
        
        # Verify DynamoDB update called
        mock_table.update_item.assert_called_once()


class TestListClaimsHandler:
    """Tests for list claims endpoint"""
    
    @patch('api.handlers.dynamodb')
    def test_list_claims(self, mock_dynamodb):
        """Test listing claims"""
        
        # Mock DynamoDB scan
        mock_table = Mock()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'claim_id': 'claim1',
                    'claim_number': 'CLM-001',
                    'status': 'processing',
                    'priority': 'medium',
                    'created_by': 'user123',
                    'created_at': '2024-03-15T10:00:00',
                    'updated_at': '2024-03-15T10:00:00',
                },
                {
                    'claim_id': 'claim2',
                    'claim_number': 'CLM-002',
                    'status': 'approved',
                    'priority': 'high',
                    'created_by': 'user123',
                    'created_at': '2024-03-14T10:00:00',
                    'updated_at': '2024-03-14T10:00:00',
                }
            ]
        }
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'limit': '20',
                'offset': '0'
            },
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {
                    'user_id': 'user123',
                    'role': 'user'
                }
            }
        }
        context = Mock()
        
        response = list_claims_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'claims' in body
        assert len(body['claims']) == 2
        assert body['total_count'] == 2


class TestDocumentHandlers:
    """Tests for document upload and retrieval"""
    
    @patch('api.handlers.dynamodb')
    @patch('api.handlers.s3_client')
    def test_upload_document(self, mock_s3, mock_dynamodb):
        """Test document upload presigned URL generation"""
        
        # Mock DynamoDB - claim exists
        mock_claims_table = Mock()
        mock_claims_table.get_item.return_value = {
            'Item': {'claim_id': 'claim123'}
        }
        
        mock_docs_table = Mock()
        
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_claims_table if 'claims' in name else mock_docs_table
        )
        
        # Mock S3 presigned URL
        mock_s3.generate_presigned_url.return_value = 'https://s3.example.com/upload'
        
        upload_data = {
            "claim_id": "CLM-1234567890",
            "document_type": "medical_record",
            "file_name": "record.pdf",
            "file_size": 1024000,
            "content_type": "application/pdf"
        }
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(upload_data),
            'requestContext': {
                'requestId': 'test-request',
                'authorizer': {'user_id': 'user123'}
            }
        }
        context = Mock()
        
        response = upload_document_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'presigned_url' in body
        assert body['presigned_url'] == 'https://s3.example.com/upload'
        
        # Verify presigned URL generated
        mock_s3.generate_presigned_url.assert_called_once()


def test_create_response_formatting():
    """Test response formatting utility"""
    from api.utils import create_response
    
    response = create_response(200, {'message': 'success'})
    
    assert response['statusCode'] == 200
    assert 'Content-Type' in response['headers']
    assert response['headers']['Content-Type'] == 'application/json'
    
    body = json.loads(response['body'])
    assert body['message'] == 'success'


def test_generate_claim_number():
    """Test claim number generation"""
    from api.utils import generate_claim_number
    
    claim_num = generate_claim_number()
    
    assert claim_num.startswith('CLM-')
    assert len(claim_num) == 19  # CLM-YYYYMMDD-XXXXXX
    
    # Should be unique
    claim_num2 = generate_claim_number()
    assert claim_num != claim_num2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])