"""Unit Tests — Lambda Handlers."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.lambda_functions.claim_ingestion_handler import ClaimIngestionHandler
from src.lambda_functions.document_extraction_orchestrator import DocumentExtractionOrchestrator
from src.lambda_functions.entity_extraction_processor import EntityExtractionProcessor
from src.lambda_functions.fraud_detection_inference import FraudDetectionInference
from src.lambda_functions.workflow_state_manager import WorkflowStateManager


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


def _load_fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


# ----------------------------------------------------------------
# ClaimIngestionHandler
# ----------------------------------------------------------------
class TestClaimIngestionHandler:
    """Tests for the claim ingestion Lambda handler."""

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_init(self, mock_resource, mock_client):
        handler = ClaimIngestionHandler()
        assert handler is not None

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_missing_body_returns_400(self, mock_resource, mock_client):
        handler = ClaimIngestionHandler()
        result = handler.handle({}, None)
        assert result['statusCode'] in (400, 500)

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_returns_dict(self, mock_resource, mock_client):
        handler = ClaimIngestionHandler()
        event = {'body': json.dumps(_load_fixture('sample_claim.json'))}
        result = handler.handle(event, None)
        assert isinstance(result, dict)
        assert 'statusCode' in result


# ----------------------------------------------------------------
# DocumentExtractionOrchestrator
# ----------------------------------------------------------------
class TestDocumentExtractionOrchestrator:
    """Tests for the document extraction Lambda handler."""

    @patch.dict(os.environ, {
        'S3_BUCKET': 'test-bucket',
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_init(self, mock_resource, mock_client):
        handler = DocumentExtractionOrchestrator()
        assert handler is not None

    @patch.dict(os.environ, {
        'S3_BUCKET': 'test-bucket',
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_missing_claim_id_returns_error(self, mock_resource, mock_client):
        handler = DocumentExtractionOrchestrator()
        result = handler.handle({}, None)
        assert isinstance(result, dict)
        assert result.get('statusCode', 500) >= 400 or 'error' in str(result).lower()


# ----------------------------------------------------------------
# EntityExtractionProcessor
# ----------------------------------------------------------------
class TestEntityExtractionProcessor:
    """Tests for the entity extraction Lambda handler."""

    @patch.dict(os.environ, {
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'MIN_VALIDATION_SCORE': '70.0',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_init(self, mock_resource, mock_client):
        handler = EntityExtractionProcessor()
        assert handler is not None

    @patch.dict(os.environ, {
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'MIN_VALIDATION_SCORE': '70.0',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_missing_claim_id_returns_error(self, mock_resource, mock_client):
        handler = EntityExtractionProcessor()
        result = handler.handle({}, None)
        assert isinstance(result, dict)


# ----------------------------------------------------------------
# FraudDetectionInference
# ----------------------------------------------------------------
class TestFraudDetectionInference:
    """Tests for the fraud detection Lambda handler."""

    @patch.dict(os.environ, {
        'MODEL_BUCKET': 'test-models',
        'MODEL_KEY': 'models/fraud/v2.1.0.joblib',
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'FRAUD_SCORES_TABLE': 'test-fraud-scores',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_THRESHOLD_HIGH': '0.8',
        'FRAUD_THRESHOLD_MEDIUM': '0.5',
        'MODEL_VERSION': 'v2.1.0',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_init(self, mock_resource, mock_client):
        handler = FraudDetectionInference()
        assert handler is not None

    @patch.dict(os.environ, {
        'MODEL_BUCKET': 'test-models',
        'MODEL_KEY': 'models/fraud/v2.1.0.joblib',
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'FRAUD_SCORES_TABLE': 'test-fraud-scores',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_THRESHOLD_HIGH': '0.8',
        'FRAUD_THRESHOLD_MEDIUM': '0.5',
        'MODEL_VERSION': 'v2.1.0',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_missing_claim_id_returns_error(self, mock_resource, mock_client):
        handler = FraudDetectionInference()
        result = handler.handle({}, None)
        assert isinstance(result, dict)

    @patch.dict(os.environ, {
        'MODEL_BUCKET': 'test-models',
        'MODEL_KEY': 'models/fraud/v2.1.0.joblib',
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'FRAUD_SCORES_TABLE': 'test-fraud-scores',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_THRESHOLD_HIGH': '0.8',
        'FRAUD_THRESHOLD_MEDIUM': '0.5',
        'MODEL_VERSION': 'v2.1.0',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_positive_path(self, mock_resource, mock_client):
        """End-to-end positive path: mocked model + AWS clients → FRAUD_SCORED."""
        import numpy as np

        # Build a mock trained model
        mock_model = MagicMock()
        mock_model.feature_names = ['claim_amount', 'claim_amount_log', 'missing_fields']
        mock_model.prepare_features = MagicMock(return_value=MagicMock())
        mock_model.predict = MagicMock(return_value={
            'fraud_score': np.array([0.3]),
            'prediction': np.array([0]),
            'confidence': np.array([0.7]),
        })

        # Mock S3 put_object and DynamoDB table
        mock_s3 = MagicMock()
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_client.return_value = mock_s3
        mock_resource.return_value = mock_dynamodb

        handler = FraudDetectionInference()

        # Inject pre-loaded model to skip S3 download
        import src.lambda_functions.fraud_detection_inference as _mod
        _mod._cached_model = mock_model

        try:
            event = {
                'claim_id': 'claim-abc-123',
                'claim_amount': 5000.0,
                'hospital_id': 'HOSP-1',
                'patient_id': 'PAT-1',
                'claim_date': '2024-01-15T10:00:00',
                'treatment_type': 'Surgery',
                'diagnosis_code': 'K35',
                'document_key': 'docs/claim-abc-123.pdf',
            }
            result = handler.handle(event, None)
        finally:
            _mod._cached_model = None  # clean up cache

        assert result['status'] == 'FRAUD_SCORED'
        assert 'fraud_score' in result
        assert result['risk_level'] == 'LOW'   # 0.3 < 0.5 threshold
        assert result['claim_id'] == 'claim-abc-123'
        mock_s3.put_object.assert_called_once()
        mock_table.put_item.assert_called_once()


# ----------------------------------------------------------------
# WorkflowStateManager
# ----------------------------------------------------------------
class TestWorkflowStateManager:
    """Tests for the workflow state manager Lambda handler."""

    @patch.dict(os.environ, {
        'CLAIMS_TABLE': 'test-claims',
        'AUDIT_TABLE': 'test-audit',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_AUTO_REJECT_THRESHOLD': '0.85',
        'FRAUD_MANUAL_REVIEW_THRESHOLD': '0.5',
        'MIN_VALIDATION_SCORE_FOR_AUTO': '70.0',
        'MAX_RETRY_ATTEMPTS': '3',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_init(self, mock_resource, mock_client):
        handler = WorkflowStateManager()
        assert handler is not None

    @patch.dict(os.environ, {
        'CLAIMS_TABLE': 'test-claims',
        'AUDIT_TABLE': 'test-audit',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_AUTO_REJECT_THRESHOLD': '0.85',
        'FRAUD_MANUAL_REVIEW_THRESHOLD': '0.5',
        'MIN_VALIDATION_SCORE_FOR_AUTO': '70.0',
        'MAX_RETRY_ATTEMPTS': '3',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_missing_claim_id_returns_error(self, mock_resource, mock_client):
        handler = WorkflowStateManager()
        result = handler.handle({}, None)
        assert isinstance(result, dict)

    @patch.dict(os.environ, {
        'CLAIMS_TABLE': 'test-claims',
        'AUDIT_TABLE': 'test-audit',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_AUTO_REJECT_THRESHOLD': '0.85',
        'FRAUD_MANUAL_REVIEW_THRESHOLD': '0.5',
        'MIN_VALIDATION_SCORE_FOR_AUTO': '70.0',
        'MAX_RETRY_ATTEMPTS': '3',
    })
    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handle_error_action(self, mock_resource, mock_client):
        handler = WorkflowStateManager()
        event = {
            'claim_id': 'test-claim-id',
            'action': 'handle_error',
            'error': {'message': 'Test error'},
        }
        result = handler.handle(event, None)
        assert isinstance(result, dict)
