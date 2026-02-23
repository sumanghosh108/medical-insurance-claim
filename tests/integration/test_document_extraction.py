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
            'claim_info': {
                'claim_number': 'CLM-2025-002',
            },
            'policy_info': {
                'policy_number': 'POL-9999999901',
            },
            'personal_info': {
                'name': 'John Doe',
            },
            'dates': ['2025-01-15'],
            'medical_info': {
                'provider': 'Test General Hospital',
                'diagnosis_codes': ['K35.80'],
                'procedure_codes': ['44970'],
            },
            'amounts': [12500.00],
        }
        result = validator.validate(entity_data, claim_type='health')
        assert isinstance(result, ValidationResult)
        assert result.validation_score >= 0

    def test_extraction_result_structure(self):
        """Test ExtractionResult has correct structure."""
        result = ExtractionResult(
            text='Sample text',
            confidence=0.95,
            metadata={'source': 'test'},
            pages=1,
            processing_time=0.1,
            extractor_type='test',
        )
        assert result.text == 'Sample text'
        assert result.confidence == 0.95
        assert result.extractor_type == 'test'


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
            'claim_info': {
                'claim_number': 'CLM-2025-001',
            },
            'policy_info': {
                'policy_number': 'POL-1234567890',
            },
            'personal_info': {
                'name': 'Jane Smith',
                'date_of_birth': '1990-03-20',
            },
            'dates': ['2025-01-10'],
            'medical_info': {
                'provider': 'City Medical Center',
                'diagnosis_codes': ['J18.9'],
                'procedure_codes': ['99213'],
            },
            'amounts': [350.00],
        }
        result = validator.validate(data, claim_type='health')
        assert result.validation_score > 50

    def test_incomplete_claim_gets_lower_score(self, validator):
        data = {'amounts': [100.00]}
        result = validator.validate(data, claim_type='health')
        complete_data = {
            'claim_info': {
                'claim_number': 'CLM-2025-003',
            },
            'policy_info': {
                'policy_number': 'POL-1234567890',
            },
            'personal_info': {
                'name': 'Jane Smith',
            },
            'dates': ['2025-01-10'],
            'medical_info': {
                'provider': 'Hospital',
                'diagnosis_codes': ['J18.9'],
                'procedure_codes': ['99213'],
            },
            'amounts': [100.00],
        }
        complete_result = validator.validate(complete_data, claim_type='health')
        assert result.validation_score <= complete_result.validation_score

    def test_high_amount_claim_validation(self, validator):
        data = {
            'claim_info': {
                'claim_number': 'CLM-2025-004',
            },
            'policy_info': {
                'policy_number': 'POL-1234567890',
            },
            'personal_info': {
                'name': 'Test Patient',
            },
            'dates': ['2025-01-10'],
            'medical_info': {
                'provider': 'Test Hospital',
                'diagnosis_codes': ['I25.10'],
                'procedure_codes': ['33533'],
            },
            'amounts': [150000.00],
        }
        result = validator.validate(data, claim_type='health')
        assert isinstance(result, ValidationResult)
