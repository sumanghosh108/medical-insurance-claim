"""Unit Tests — Feature Engineering Module."""

import pytest
import numpy as np
import pandas as pd

from src.ml_models.feature_engineering import (
    FeatureEngineer,
    build_feature_engineer,
    _infer_feature_columns,
)


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for feature engineering tests."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame({
        'claim_amount': np.random.uniform(500, 50000, n),
        'missing_fields': np.random.randint(0, 5, n),
        'duplicate_invoice': np.random.randint(0, 2, n),
        'treatment_type': np.random.choice(['Surgery', 'ER', 'Consultation', 'Lab'], n),
        'hospital_id': np.random.choice(['h1', 'h2', 'h3'], n),
    })


@pytest.fixture
def numeric_only_df():
    """DataFrame with only numeric columns."""
    np.random.seed(42)
    n = 30
    return pd.DataFrame({
        'amount': np.random.uniform(100, 10000, n),
        'count': np.random.randint(1, 10, n),
        'score': np.random.random(n),
    })


# ----------------------------------------------------------------
# _infer_feature_columns
# ----------------------------------------------------------------
class TestInferFeatureColumns:
    """Tests for automatic feature column inference."""

    def test_infers_numeric_columns(self, sample_df):
        numeric, categorical = _infer_feature_columns(sample_df)
        assert 'claim_amount' in numeric
        assert 'missing_fields' in numeric
        assert 'duplicate_invoice' in numeric

    def test_infers_categorical_columns(self, sample_df):
        numeric, categorical = _infer_feature_columns(sample_df)
        assert 'treatment_type' in categorical
        assert 'hospital_id' in categorical

    def test_explicit_numeric_override(self, sample_df):
        numeric, categorical = _infer_feature_columns(
            sample_df, numeric_features=['claim_amount']
        )
        assert numeric == ['claim_amount']
        assert 'missing_fields' in categorical

    def test_explicit_categorical_override(self, sample_df):
        numeric, categorical = _infer_feature_columns(
            sample_df, categorical_features=['hospital_id']
        )
        assert categorical == ['hospital_id']

    def test_all_numeric_df(self, numeric_only_df):
        numeric, categorical = _infer_feature_columns(numeric_only_df)
        assert len(numeric) == 3
        assert len(categorical) == 0

    def test_returns_lists(self, sample_df):
        numeric, categorical = _infer_feature_columns(sample_df)
        assert isinstance(numeric, list)
        assert isinstance(categorical, list)


# ----------------------------------------------------------------
# build_feature_engineer
# ----------------------------------------------------------------
class TestBuildFeatureEngineer:
    """Tests for the feature engineer builder."""

    def test_returns_feature_engineer(self, sample_df):
        fe = build_feature_engineer(sample_df)
        assert isinstance(fe, FeatureEngineer)

    def test_has_preprocessor(self, sample_df):
        fe = build_feature_engineer(sample_df)
        assert fe.preprocessor is not None

    def test_stores_feature_names(self, sample_df):
        fe = build_feature_engineer(sample_df)
        assert len(fe.numeric_features) > 0
        assert len(fe.categorical_features) > 0

    def test_custom_feature_lists(self, sample_df):
        fe = build_feature_engineer(
            sample_df,
            numeric_features=['claim_amount', 'missing_fields'],
            categorical_features=['treatment_type'],
        )
        assert fe.numeric_features == ['claim_amount', 'missing_fields']
        assert fe.categorical_features == ['treatment_type']


# ----------------------------------------------------------------
# FeatureEngineer
# ----------------------------------------------------------------
class TestFeatureEngineer:
    """Tests for the FeatureEngineer class."""

    @pytest.fixture
    def engineer(self, sample_df):
        return build_feature_engineer(sample_df)

    def test_fit_returns_self(self, engineer, sample_df):
        result = engineer.fit(sample_df)
        assert result is engineer

    def test_transform_returns_ndarray(self, engineer, sample_df):
        engineer.fit(sample_df)
        result = engineer.transform(sample_df)
        assert isinstance(result, np.ndarray) or hasattr(result, 'toarray')

    def test_fit_transform_returns_ndarray(self, engineer, sample_df):
        result = engineer.fit_transform(sample_df)
        assert isinstance(result, np.ndarray) or hasattr(result, 'toarray')

    def test_output_rows_match_input(self, engineer, sample_df):
        result = engineer.fit_transform(sample_df)
        if hasattr(result, 'toarray'):
            result = result.toarray()
        assert result.shape[0] == len(sample_df)

    def test_handles_missing_values(self, sample_df):
        # Inject NaN values
        sample_df.loc[0, 'claim_amount'] = np.nan
        sample_df.loc[1, 'treatment_type'] = np.nan
        fe = build_feature_engineer(sample_df)
        result = fe.fit_transform(sample_df)
        if hasattr(result, 'toarray'):
            result = result.toarray()
        assert not np.any(np.isnan(result))

    def test_numeric_only_df(self, numeric_only_df):
        fe = build_feature_engineer(numeric_only_df)
        result = fe.fit_transform(numeric_only_df)
        if hasattr(result, 'toarray'):
            result = result.toarray()
        assert result.shape[0] == len(numeric_only_df)
        assert result.shape[1] >= len(numeric_only_df.columns)
