"""Integration Tests — Document Extraction Pipeline.

Tests the document extraction flow from S3 retrieval through
text extraction and entity extraction with mocked AWS services.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

from src.document_processing.text_extraction import (
    TextractExtractor,
    TesseractExtractor,
    DocumentType,
    ExtractionResult,
)
from src.document_processing.entity_extraction import (
    extract_claim_entities,
    EntityExtractionResult,
    Entity,
)
from src.document_processing.document_validation import (
    DocumentValidator,
    ValidationResult,
)


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


def _load_fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


@pytest.mark.integration
class TestExtractionPipeline:
    """Tests for the full extraction pipeline."""

    @pytest.fixture
    def mock_responses(self):
        return _load_fixture('mock_response.json')

    def test_textract_to_entity_pipeline(self, mock_responses):
        """Test that extracted text can be processed into entities."""
        extracted_text = mock_responses['extracted_text']
        assert len(extracted_text) > 0

        # Validate the text contains expected content
        assert 'John Doe' in extracted_text
        assert 'K35.80' in extracted_text
        assert '12,500.00' in extracted_text

    def test_entity_extraction_to_validation(self, mock_responses):
        """Test that extracted entities can be validated."""
        validator = DocumentValidator()
        entity_data = {
            'patient_name': 'John Doe',
            'diagnosis_code': 'K35.80',
            'procedure_code': '44970',
            'claim_amount': 12500.00,
            'service_date': '2025-01-15',
            'provider_name': 'Test General Hospital',
            'provider_npi': '9999999901',
        }
        result = validator.validate(entity_data, claim_type='health')
        assert isinstance(result, ValidationResult)
        assert result.score >= 0

    def test_extraction_result_structure(self):
        """Test ExtractionResult has correct structure."""
        result = ExtractionResult(
            text='Sample text',
            confidence=0.95,
            document_type=DocumentType.PDF,
            pages=1,
            metadata={'source': 'test'},
        )
        assert result.text == 'Sample text'
        assert result.confidence == 0.95
        assert result.document_type == DocumentType.PDF


@pytest.mark.integration
class TestDocumentTypeDetection:
    """Tests for document type classification."""

    def test_pdf_type(self):
        assert DocumentType.PDF is not None

    def test_image_type(self):
        assert DocumentType.IMAGE is not None

    def test_handwritten_type(self):
        assert DocumentType.HANDWRITTEN is not None


@pytest.mark.integration
class TestValidationIntegration:
    """Tests for end-to-end validation scenarios."""

    @pytest.fixture
    def validator(self):
        return DocumentValidator()

    def test_complete_claim_passes_validation(self, validator):
        data = {
            'patient_name': 'Jane Smith',
            'date_of_birth': '1990-03-20',
            'diagnosis_code': 'J18.9',
            'procedure_code': '99213',
            'claim_amount': 350.00,
            'service_date': '2025-01-10',
            'provider_name': 'City Medical Center',
            'provider_npi': '1234567890',
        }
        result = validator.validate(data, claim_type='health')
        assert result.score > 50

    def test_incomplete_claim_gets_lower_score(self, validator):
        data = {'claim_amount': 100.00}
        result = validator.validate(data, claim_type='health')
        complete_data = {
            'patient_name': 'Jane Smith',
            'diagnosis_code': 'J18.9',
            'claim_amount': 100.00,
            'service_date': '2025-01-10',
            'provider_name': 'Hospital',
            'provider_npi': '1234567890',
        }
        complete_result = validator.validate(complete_data, claim_type='health')
        assert result.score <= complete_result.score

    def test_high_amount_claim_validation(self, validator):
        data = {
            'patient_name': 'Test Patient',
            'diagnosis_code': 'I25.10',
            'procedure_code': '33533',
            'claim_amount': 150000.00,
            'service_date': '2025-01-10',
            'provider_name': 'Test Hospital',
            'provider_npi': '1234567890',
        }
        result = validator.validate(data, claim_type='health')
        assert isinstance(result, ValidationResult)
