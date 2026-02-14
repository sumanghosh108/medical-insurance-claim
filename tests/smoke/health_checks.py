"""Smoke Tests — Health Checks.

Lightweight checks for infrastructure dependencies:
database, S3, SNS, and core Python packages.
"""

import os
import sys
import pytest


@pytest.mark.smoke
class TestPythonEnvironment:
    """Verify the Python environment is correctly configured."""

    def test_python_version(self):
        assert sys.version_info >= (3, 9), f'Python 3.9+ required, got {sys.version}'

    def test_core_packages_installed(self):
        import boto3
        import sqlalchemy
        import pandas
        import numpy
        import sklearn
        assert boto3 is not None
        assert sqlalchemy is not None

    def test_ml_packages_installed(self):
        import joblib
        assert joblib is not None

    def test_web_packages_installed(self):
        try:
            import flask  # noqa: F401
        except ImportError:
            try:
                import fastapi  # noqa: F401
            except ImportError:
                pytest.skip('No web framework installed')


@pytest.mark.smoke
class TestDatabaseHealth:
    """Verify database connectivity."""

    def test_database_url_configured(self):
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            pytest.skip('DATABASE_URL not set — skipping DB health check')
        assert len(db_url) > 0

    def test_database_connection(self):
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            pytest.skip('DATABASE_URL not set')

        from src.database.connection import DatabaseConnection
        conn = DatabaseConnection(db_url)
        try:
            conn.connect()
            assert conn.health_check() is True
        except Exception as e:
            pytest.fail(f'Database connection failed: {e}')
        finally:
            conn.disconnect()


@pytest.mark.smoke
class TestAWSHealth:
    """Verify AWS service connectivity."""

    def test_aws_credentials_present(self):
        has_creds = (
            os.environ.get('AWS_ACCESS_KEY_ID')
            or os.environ.get('AWS_PROFILE')
            or os.environ.get('AWS_ROLE_ARN')
        )
        if not has_creds:
            pytest.skip('No AWS credentials configured — skipping')
        assert has_creds

    def test_s3_access(self):
        bucket = os.environ.get('S3_BUCKET')
        if not bucket:
            pytest.skip('S3_BUCKET not set')

        import boto3
        try:
            s3 = boto3.client('s3')
            s3.head_bucket(Bucket=bucket)
        except Exception as e:
            pytest.fail(f'S3 access failed: {e}')

    def test_dynamodb_access(self):
        table = os.environ.get('CLAIMS_TABLE')
        if not table:
            pytest.skip('CLAIMS_TABLE not set')

        import boto3
        try:
            dynamo = boto3.resource('dynamodb')
            tbl = dynamo.Table(table)
            tbl.table_status  # Triggers a DescribeTable call
        except Exception as e:
            pytest.fail(f'DynamoDB access failed: {e}')


@pytest.mark.smoke
class TestFileSystem:
    """Verify required directories and files exist."""

    def test_project_structure(self):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        required_dirs = [
            'src',
            'src/database',
            'src/document_processing',
            'src/lambda_functions',
            'src/ml_models',
            'src/utils',
            'tests',
            'database',
        ]
        for d in required_dirs:
            path = os.path.join(project_root, d)
            assert os.path.isdir(path), f'Missing directory: {d}'

    def test_key_config_files(self):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_files = ['requirements.txt']
        for f in config_files:
            path = os.path.join(project_root, f)
            if os.path.exists(path):
                assert os.path.getsize(path) > 0, f'Config file is empty: {f}'
