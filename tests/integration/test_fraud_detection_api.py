"""Integration Tests — Fraud Detection API.

Tests the fraud detection model API including prediction,
scoring, and risk classification.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os

from src.ml_models.fraud_detection import FraudDetectionEnsemble
from src.ml_models.feature_engineering import build_feature_engineer, FeatureEngineer


@pytest.mark.integration
class TestFraudDetectionAPI:
    """Tests for the fraud detection scoring API."""

    @pytest.fixture
    def trained_model(self, sample_training_data):
        X, y = sample_training_data
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        model = FraudDetectionEnsemble()
        model.train(X[numeric_cols], y)
        return model, numeric_cols

    def test_single_prediction(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        single = sample_test_data[numeric_cols].iloc[[0]]
        result = model.predict(single)
        assert len(result['fraud_score']) == 1
        assert 0.0 <= result['fraud_score'][0] <= 1.0

    def test_batch_prediction(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        result = model.predict(sample_test_data[numeric_cols])
        assert len(result['fraud_score']) == len(sample_test_data)

    def test_risk_classification(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        result = model.predict(sample_test_data[numeric_cols])
        for score in result['fraud_score']:
            if score >= 0.8:
                risk = 'CRITICAL'
            elif score >= 0.6:
                risk = 'HIGH'
            elif score >= 0.3:
                risk = 'MEDIUM'
            else:
                risk = 'LOW'
            assert risk in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')

    def test_model_persistence(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'model.joblib')
            model.save(path)
            loaded = FraudDetectionEnsemble.load(path)

            orig = model.predict(sample_test_data[numeric_cols])
            loaded_result = loaded.predict(sample_test_data[numeric_cols])

            np.testing.assert_array_almost_equal(
                orig['fraud_score'], loaded_result['fraud_score'], decimal=6
            )

    def test_prediction_reproducibility(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        r1 = model.predict(sample_test_data[numeric_cols])
        r2 = model.predict(sample_test_data[numeric_cols])
        np.testing.assert_array_equal(r1['fraud_score'], r2['fraud_score'])


@pytest.mark.integration
class TestFeatureEngineeringAPI:
    """Tests for the feature engineering pipeline integration."""

    @pytest.fixture
    def sample_df(self):
        np.random.seed(42)
        n = 30
        return pd.DataFrame({
            'claim_amount': np.random.uniform(500, 50000, n),
            'missing_fields': np.random.randint(0, 5, n),
            'duplicate_invoice': np.random.randint(0, 2, n),
            'treatment_type': np.random.choice(['Surgery', 'ER', 'Lab'], n),
            'hospital_id': np.random.choice(['h1', 'h2'], n),
        })

    def test_feature_engineer_round_trip(self, sample_df):
        fe = build_feature_engineer(sample_df)
        transformed = fe.fit_transform(sample_df)
        if hasattr(transformed, 'toarray'):
            transformed = transformed.toarray()
        assert transformed.shape[0] == len(sample_df)
        assert not np.any(np.isnan(transformed))

    def test_feature_engineer_with_model(self, sample_df, sample_training_data):
        """Test that feature engineering output is compatible with model input."""
        X_train, y = sample_training_data
        numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()

        model = FraudDetectionEnsemble()
        model.train(X_train[numeric_cols], y)

        # Predict using test data with matching columns
        test_numeric = sample_df.select_dtypes(include=[np.number])
        # Align columns to model's expected features
        for col in numeric_cols:
            if col not in test_numeric.columns:
                test_numeric[col] = 0.0
        test_aligned = test_numeric[numeric_cols]

        result = model.predict(test_aligned)
        assert len(result['fraud_score']) == len(sample_df)
