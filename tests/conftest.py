"""Pytest Configuration and Shared Fixtures."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_training_data():
    """Create sample training data for testing."""
    np.random.seed(42)
    n_samples = 200
    
    X = pd.DataFrame({
        'claim_amount': np.random.uniform(1000, 50000, n_samples),
        'hospital_id': np.random.choice(['h1', 'h2', 'h3', 'h4'], n_samples),
        'patient_id': np.random.choice([f'p{i}' for i in range(20)], n_samples),
        'claim_date': pd.date_range('2025-01-01', periods=n_samples, freq='H'),
        'treatment_type': np.random.choice(['Surgery', 'Consultation', 'ER', 'Lab'], n_samples),
        'diagnosis_code': [f'ICD{i:03d}' for i in range(n_samples)],
        'missing_fields': np.random.randint(0, 3, n_samples),
        'bill_treatment_mismatch': np.random.randint(0, 2, n_samples),
        'duplicate_invoice': np.random.randint(0, 2, n_samples),
    })
    
    y = pd.Series(np.random.binomial(1, 0.05, n_samples))
    return X, y


@pytest.fixture
def sample_test_data(sample_training_data):
    """Create sample test data."""
    np.random.seed(43)
    n_test = 50
    
    X_test = pd.DataFrame({
        'claim_amount': np.random.uniform(1000, 50000, n_test),
        'hospital_id': np.random.choice(['h1', 'h2', 'h3', 'h4'], n_test),
        'patient_id': np.random.choice([f'p{i}' for i in range(20)], n_test),
        'claim_date': pd.date_range('2025-02-01', periods=n_test, freq='H'),
        'treatment_type': np.random.choice(['Surgery', 'Consultation', 'ER', 'Lab'], n_test),
        'diagnosis_code': [f'ICD{i:03d}' for i in range(n_test)],
        'missing_fields': np.random.randint(0, 3, n_test),
        'bill_treatment_mismatch': np.random.randint(0, 2, n_test),
        'duplicate_invoice': np.random.randint(0, 2, n_test),
    })
    
    return X_test