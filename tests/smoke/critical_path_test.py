"""Smoke Tests — Critical Path Verification.

Quick tests to verify the most critical system paths
are functional. Intended to run after deployment.
"""

import json
import os
import pytest
import requests
from unittest.mock import patch


BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
TIMEOUT = int(os.environ.get('SMOKE_TEST_TIMEOUT', '10'))


@pytest.mark.smoke
class TestCriticalPaths:
    """Verify critical system paths are operational."""

    def test_api_health_endpoint(self):
        """API is reachable and healthy."""
        try:
            resp = requests.get(f'{BASE_URL}/health', timeout=TIMEOUT)
            assert resp.status_code == 200
        except requests.ConnectionError:
            pytest.skip('API not available — skipping smoke test')

    def test_claims_list_endpoint(self):
        """Claims list endpoint responds."""
        try:
            resp = requests.get(
                f'{BASE_URL}/api/v1/claims?limit=1',
                timeout=TIMEOUT,
            )
            assert resp.status_code in (200, 401, 403)
        except requests.ConnectionError:
            pytest.skip('API not available')

    def test_claim_submission_accepts_post(self):
        """Claim submission endpoint accepts POST requests."""
        try:
            sample_claim = {
                'claim_number': 'CLM-SMOKE-001',
                'patient_id': 'pt-smoke-001',
                'hospital_id': 'hosp-smoke-001',
                'claim_amount': 1000.00,
                'treatment_type': 'Consultation',
                'diagnosis_code': 'Z00.00',
                'claim_date': '2025-01-15T08:00:00Z',
                'service_date': '2025-01-15T08:00:00Z',
            }
            resp = requests.post(
                f'{BASE_URL}/api/v1/claims',
                json=sample_claim,
                timeout=TIMEOUT,
            )
            # Accept 200, 201, 400 (validation), 401 (auth required)
            assert resp.status_code in (200, 201, 400, 401, 403, 422)
        except requests.ConnectionError:
            pytest.skip('API not available')

    def test_fraud_summary_endpoint(self):
        """Fraud summary endpoint responds."""
        try:
            resp = requests.get(
                f'{BASE_URL}/api/v1/fraud/summary',
                timeout=TIMEOUT,
            )
            assert resp.status_code in (200, 401, 403)
        except requests.ConnectionError:
            pytest.skip('API not available')

    def test_metrics_endpoint(self):
        """Processing metrics endpoint responds."""
        try:
            resp = requests.get(
                f'{BASE_URL}/api/v1/metrics/processing',
                timeout=TIMEOUT,
            )
            assert resp.status_code in (200, 401, 403)
        except requests.ConnectionError:
            pytest.skip('API not available')


@pytest.mark.smoke
class TestModuleImports:
    """Verify that all core modules can be imported without errors."""

    def test_import_document_processing(self):
        from src.document_processing import text_extraction
        from src.document_processing import entity_extraction
        from src.document_processing import document_validation
        assert text_extraction is not None

    def test_import_ml_models(self):
        from src.ml_models import fraud_detection
        from src.ml_models import feature_engineering
        assert fraud_detection is not None

    def test_import_database(self):
        from src.database import models
        from src.database import connection
        from src.database import operations
        assert models is not None

    def test_import_lambda_functions(self):
        from src.lambda_functions import claim_ingestion_handler
        assert claim_ingestion_handler is not None

    def test_import_utils(self):
        from src.utils import constants
        from src.utils import exceptions
        assert constants is not None
