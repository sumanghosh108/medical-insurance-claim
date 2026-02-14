"""Load Test — Locust Configuration.

Simulates concurrent claim submissions, fraud checks,
and status queries against the claims processing API.

Usage:
    locust -f tests/load/locustfile.py --config tests/load/load_test_config.yaml
"""

import json
import random
import uuid
from datetime import datetime, timedelta

from locust import HttpUser, task, between, tag


class ClaimSubmissionUser(HttpUser):
    """Simulates users submitting new claims."""

    wait_time = between(1, 5)

    def _generate_claim(self) -> dict:
        """Generate a random claim payload."""
        treatments = [
            ('Emergency Room Visit', 'R10.9', '99285'),
            ('Consultation', 'Z00.00', '99213'),
            ('Surgery', 'K35.80', '44970'),
            ('Lab Work', 'R79.89', '80053'),
            ('Cardiac Evaluation', 'I25.10', '93000'),
        ]
        treatment, diag, proc = random.choice(treatments)
        service_date = datetime.now() - timedelta(days=random.randint(0, 30))

        return {
            'claim_number': f'CLM-LOAD-{uuid.uuid4().hex[:8].upper()}',
            'patient_id': f'pt-load-{random.randint(1, 100):04d}',
            'hospital_id': f'hosp-load-{random.randint(1, 10):04d}',
            'claim_amount': round(random.uniform(200, 75000), 2),
            'treatment_type': treatment,
            'diagnosis_code': diag,
            'procedure_code': proc,
            'claim_date': datetime.now().isoformat(),
            'service_date': service_date.isoformat(),
        }

    @tag('submit')
    @task(3)
    def submit_claim(self):
        """Submit a new claim."""
        claim = self._generate_claim()
        self.client.post(
            '/api/v1/claims',
            json=claim,
            name='/api/v1/claims [POST]',
        )

    @tag('query')
    @task(5)
    def get_claims_list(self):
        """Query paginated claims list."""
        page = random.randint(1, 10)
        self.client.get(
            f'/api/v1/claims?page={page}&limit=20',
            name='/api/v1/claims [GET]',
        )

    @tag('query')
    @task(2)
    def get_claim_detail(self):
        """Get a specific claim detail."""
        claim_id = f'clm-load-{random.randint(1, 1000):04d}'
        self.client.get(
            f'/api/v1/claims/{claim_id}',
            name='/api/v1/claims/:id [GET]',
        )

    @tag('fraud')
    @task(1)
    def get_fraud_scores(self):
        """Query fraud scores summary."""
        self.client.get(
            '/api/v1/fraud/summary',
            name='/api/v1/fraud/summary [GET]',
        )


class AdminUser(HttpUser):
    """Simulates admin users checking dashboards."""

    wait_time = between(5, 15)

    @tag('admin')
    @task(3)
    def get_processing_metrics(self):
        """Check processing metrics dashboard."""
        self.client.get(
            '/api/v1/metrics/processing',
            name='/api/v1/metrics/processing [GET]',
        )

    @tag('admin')
    @task(2)
    def get_fraud_statistics(self):
        """Check fraud statistics dashboard."""
        self.client.get(
            '/api/v1/metrics/fraud',
            name='/api/v1/metrics/fraud [GET]',
        )

    @tag('admin')
    @task(1)
    def get_sla_compliance(self):
        """Check SLA compliance."""
        self.client.get(
            '/api/v1/metrics/sla',
            name='/api/v1/metrics/sla [GET]',
        )

    @tag('admin')
    @task(1)
    def update_claim_status(self):
        """Approve or reject a claim."""
        claim_id = f'clm-load-{random.randint(1, 1000):04d}'
        action = random.choice(['APPROVED', 'REJECTED', 'MANUAL_REVIEW'])
        self.client.patch(
            f'/api/v1/claims/{claim_id}/status',
            json={'status': action, 'notes': 'Load test action'},
            name='/api/v1/claims/:id/status [PATCH]',
        )
