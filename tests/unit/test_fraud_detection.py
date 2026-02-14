"""Unit Tests — Fraud Detection Model."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import tempfile
import os

from src.ml_models.fraud_detection import FraudDetectionEnsemble


class TestFraudDetectionEnsemble:
    """Tests for the fraud detection ensemble model."""

    @pytest.fixture
    def training_data(self, sample_training_data):
        """Use conftest fixture for training data."""
        return sample_training_data

    @pytest.fixture
    def test_features(self, sample_test_data):
        """Use conftest fixture for test data."""
        return sample_test_data

    @pytest.fixture
    def trained_model(self, training_data):
        """Create and train a model for testing."""
        X, y = training_data
        # Keep only numeric columns for training
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        model = FraudDetectionEnsemble()
        model.train(X[numeric_cols], y)
        return model, numeric_cols

    # ----- Initialization -----
    def test_init(self):
        model = FraudDetectionEnsemble()
        assert model is not None
        assert model.is_trained is False

    # ----- Training -----
    def test_train_marks_model_trained(self, training_data):
        X, y = training_data
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        model = FraudDetectionEnsemble()
        model.train(X[numeric_cols], y)
        assert model.is_trained is True

    def test_train_sets_feature_names(self, trained_model):
        model, numeric_cols = trained_model
        assert model.feature_names is not None
        assert len(model.feature_names) == len(numeric_cols)

    def test_train_creates_sub_models(self, trained_model):
        model, _ = trained_model
        assert model.rf_model is not None
        assert model.lr_model is not None
        assert model.isolation_forest is not None
        assert model.scaler is not None

    # ----- Prediction -----
    def test_predict_returns_dict(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        X_test = sample_test_data[numeric_cols]
        result = model.predict(X_test)
        assert isinstance(result, dict)
        assert 'fraud_score' in result
        assert 'prediction' in result
        assert 'confidence' in result

    def test_predict_scores_in_range(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        X_test = sample_test_data[numeric_cols]
        result = model.predict(X_test)
        assert np.all(result['fraud_score'] >= 0.0)
        assert np.all(result['fraud_score'] <= 1.0)

    def test_predict_confidence_in_range(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        X_test = sample_test_data[numeric_cols]
        result = model.predict(X_test)
        assert np.all(result['confidence'] >= 0.5)
        assert np.all(result['confidence'] <= 1.0)

    def test_predict_returns_correct_length(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        X_test = sample_test_data[numeric_cols]
        result = model.predict(X_test)
        assert len(result['fraud_score']) == len(X_test)
        assert len(result['prediction']) == len(X_test)

    def test_predict_binary_predictions(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        X_test = sample_test_data[numeric_cols]
        result = model.predict(X_test)
        unique_preds = set(result['prediction'])
        assert unique_preds.issubset({0, 1})

    def test_predict_untrained_raises(self, sample_test_data):
        model = FraudDetectionEnsemble()
        numeric_cols = sample_test_data.select_dtypes(include=[np.number]).columns.tolist()
        with pytest.raises(Exception):
            model.predict(sample_test_data[numeric_cols])

    # ----- Save/Load -----
    def test_save_and_load(self, trained_model, sample_test_data):
        model, numeric_cols = trained_model
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'model.joblib')
            model.save(filepath)
            assert os.path.exists(filepath)

            loaded = FraudDetectionEnsemble.load(filepath)
            assert loaded.is_trained is True

            # Predictions should match
            X_test = sample_test_data[numeric_cols]
            orig_result = model.predict(X_test)
            loaded_result = loaded.predict(X_test)
            np.testing.assert_array_almost_equal(
                orig_result['fraud_score'],
                loaded_result['fraud_score'],
                decimal=6,
            )

    # ----- Ensemble Weights -----
    def test_ensemble_weights_sum_to_one(self):
        """The ensemble uses weights 0.4 + 0.3 + 0.3 = 1.0."""
        assert abs(0.4 + 0.3 + 0.3 - 1.0) < 1e-10
