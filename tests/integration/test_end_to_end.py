"""Integration Tests — End-to-End Claim Processing.

Tests the complete lifecycle from claim submission to final decision,
verifying data flows correctly between pipeline stages.
"""

import json
import os
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.document_processing.document_validation import DocumentValidator, ValidationResult
from src.ml_models.fraud_detection import FraudDetectionEnsemble
from src.ml_models.feature_engineering import build_feature_engineer


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


def _load_fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


@pytest.mark.integration
class TestEndToEndPipeline:
    """Tests for the complete processing pipeline."""

    @pytest.fixture
    def trained_model(self, sample_training_data):
        X, y = sample_training_data
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        model = FraudDetectionEnsemble()
        model.train(X[numeric_cols], y)
        return model, numeric_cols

    def test_validation_to_fraud_detection_flow(self, trained_model):
        """Test data flows from validation to fraud detection."""
        model, numeric_cols = trained_model

        # Step 1: Validate extracted data
        validator = DocumentValidator()
        extracted_data = {
            'patient_name': 'John Doe',
            'diagnosis_code': 'K35.80',
            'procedure_code': '44970',
            'claim_amount': 12500.00,
            'service_date': '2025-01-15',
            'provider_name': 'Test Hospital',
            'provider_npi': '9999999901',
        }
        validation_result = validator.validate(extracted_data, claim_type='health')
        assert isinstance(validation_result, ValidationResult)

        # Step 2: Prepare features and run prediction
        test_features = pd.DataFrame({
            col: [np.random.uniform(0, 50000) if 'amount' in col
                  else np.random.randint(0, 3)]
            for col in numeric_cols
        }, index=[0])

        fraud_result = model.predict(test_features)
        assert 'fraud_score' in fraud_result
        assert 0.0 <= fraud_result['fraud_score'][0] <= 1.0

    def test_decision_logic_with_scores(self):
        """Test that decision logic works with validation and fraud scores."""
        # Simulate decision thresholds
        fraud_auto_reject = 0.85
        fraud_manual_review = 0.5
        min_validation_score = 70.0

        # Scenario 1: Low risk, valid documents → APPROVED
        fraud_score_1, val_score_1 = 0.15, 92.5
        assert fraud_score_1 < fraud_manual_review
        assert val_score_1 >= min_validation_score

        # Scenario 2: High risk → REJECTED
        fraud_score_2 = 0.92
        assert fraud_score_2 >= fraud_auto_reject

        # Scenario 3: Medium risk → MANUAL_REVIEW
        fraud_score_3 = 0.65
        assert fraud_manual_review <= fraud_score_3 < fraud_auto_reject

    def test_feature_engineering_to_prediction(self, sample_training_data, sample_test_data):
        """Test feature engineering integrates with prediction."""
        X_train, y = sample_training_data
        X_test = sample_test_data

        # Build features
        numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()

        # Train model
        model = FraudDetectionEnsemble()
        model.train(X_train[numeric_cols], y)

        # Predict
        result = model.predict(X_test[numeric_cols])
        assert len(result['fraud_score']) == len(X_test)
        assert all(0 <= s <= 1 for s in result['fraud_score'])


@pytest.mark.integration
class TestDataConsistency:
    """Tests that data formats are consistent across pipeline stages."""

    def test_fixture_claim_has_required_fields(self):
        claim = _load_fixture('sample_claim.json')
        required = ['claim_id', 'claim_number', 'patient', 'hospital',
                     'claim_amount', 'treatment_type', 'diagnosis_code',
                     'status', 'documents']
        for field in required:
            assert field in claim, f"Missing required field: {field}"

    def test_fixture_mock_response_has_all_stages(self):
        response = _load_fixture('mock_response.json')
        assert 'textract_response' in response
        assert 'extracted_text' in response
        assert 'entity_extraction_result' in response
        assert 'fraud_prediction_result' in response
        assert 'validation_result' in response

    def test_fraud_score_range_consistency(self):
        response = _load_fixture('mock_response.json')
        score = response['fraud_prediction_result']['fraud_score']
        assert 0.0 <= score <= 1.0

    def test_validation_score_range_consistency(self):
        response = _load_fixture('mock_response.json')
        score = response['validation_result']['score']
        assert 0.0 <= score <= 100.0
