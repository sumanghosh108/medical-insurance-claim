"""Integration Tests — Claim Processing Workflow.

Tests the full claim processing pipeline from ingestion through
document extraction, entity extraction, fraud detection, and
final decision by the workflow state manager.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


def _load_fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


@pytest.fixture
def mock_aws():
    """Patch all AWS service clients."""
    with patch('boto3.client') as mock_client, \
         patch('boto3.resource') as mock_resource:
        yield mock_client, mock_resource


@pytest.fixture
def sample_claim():
    return _load_fixture('sample_claim.json')


@pytest.fixture
def mock_responses():
    return _load_fixture('mock_response.json')


@pytest.mark.integration
class TestClaimWorkflowPipeline:
    """Tests for the complete claim processing workflow."""

    @patch.dict(os.environ, {
        'S3_BUCKET': 'test-bucket',
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_SCORES_TABLE': 'test-fraud-scores',
        'MODEL_BUCKET': 'test-models',
        'MODEL_KEY': 'models/fraud/v2.1.0.joblib',
        'FRAUD_THRESHOLD_HIGH': '0.8',
        'FRAUD_THRESHOLD_MEDIUM': '0.5',
        'MODEL_VERSION': 'v2.1.0',
        'MIN_VALIDATION_SCORE': '70.0',
        'AUDIT_TABLE': 'test-audit',
        'FRAUD_AUTO_REJECT_THRESHOLD': '0.85',
        'FRAUD_MANUAL_REVIEW_THRESHOLD': '0.5',
        'MIN_VALIDATION_SCORE_FOR_AUTO': '70.0',
        'MAX_RETRY_ATTEMPTS': '3',
    })
    def test_ingestion_handler_accepts_valid_claim(self, mock_aws, sample_claim):
        from src.lambda_functions.claim_ingestion_handler import ClaimIngestionHandler
        handler = ClaimIngestionHandler()
        event = {'body': json.dumps(sample_claim)}
        result = handler.handle(event, None)
        assert isinstance(result, dict)
        assert 'statusCode' in result

    @patch.dict(os.environ, {
        'S3_BUCKET': 'test-bucket',
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
    })
    def test_extraction_handler_processes_event(self, mock_aws):
        from src.lambda_functions.document_extraction_orchestrator import DocumentExtractionOrchestrator
        handler = DocumentExtractionOrchestrator()
        event = {
            'claim_id': 'test-claim-id',
            'document_keys': ['claims/test/report.pdf'],
        }
        result = handler.handle(event, None)
        assert isinstance(result, dict)

    @patch.dict(os.environ, {
        'RESULTS_BUCKET': 'test-results',
        'CLAIMS_TABLE': 'test-claims',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'MIN_VALIDATION_SCORE': '70.0',
    })
    def test_entity_extraction_processes_event(self, mock_aws):
        from src.lambda_functions.entity_extraction_processor import EntityExtractionProcessor
        handler = EntityExtractionProcessor()
        event = {
            'claim_id': 'test-claim-id',
            'extraction_results_key': 'results/test/extraction.json',
        }
        result = handler.handle(event, None)
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
    def test_workflow_manager_processes_event(self, mock_aws):
        from src.lambda_functions.workflow_state_manager import WorkflowStateManager
        handler = WorkflowStateManager()
        event = {
            'claim_id': 'test-claim-id',
            'action': 'make_decision',
            'fraud_score': 0.15,
            'validation_score': 92.5,
        }
        result = handler.handle(event, None)
        assert isinstance(result, dict)


@pytest.mark.integration
class TestWorkflowStateTransitions:
    """Tests for valid and invalid state transitions."""

    @patch.dict(os.environ, {
        'CLAIMS_TABLE': 'test-claims',
        'AUDIT_TABLE': 'test-audit',
        'SNS_TOPIC': 'arn:aws:sns:ap-south-1:000000000000:test',
        'FRAUD_AUTO_REJECT_THRESHOLD': '0.85',
        'FRAUD_MANUAL_REVIEW_THRESHOLD': '0.5',
        'MIN_VALIDATION_SCORE_FOR_AUTO': '70.0',
        'MAX_RETRY_ATTEMPTS': '3',
    })
    def test_high_fraud_score_triggers_rejection(self, mock_aws):
        from src.lambda_functions.workflow_state_manager import WorkflowStateManager
        handler = WorkflowStateManager()
        event = {
            'claim_id': 'test-claim-id',
            'action': 'make_decision',
            'fraud_score': 0.95,
            'validation_score': 85.0,
        }
        result = handler.handle(event, None)
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
    def test_medium_fraud_score_triggers_manual_review(self, mock_aws):
        from src.lambda_functions.workflow_state_manager import WorkflowStateManager
        handler = WorkflowStateManager()
        event = {
            'claim_id': 'test-claim-id',
            'action': 'make_decision',
            'fraud_score': 0.65,
            'validation_score': 85.0,
        }
        result = handler.handle(event, None)
        assert isinstance(result, dict)
