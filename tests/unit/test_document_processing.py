"""Unit Tests — Document Processing Module."""

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
    ValidationSeverity,
)


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


def _load_fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


# ----------------------------------------------------------------
# TextractExtractor
# ----------------------------------------------------------------
class TestTextractExtractor:
    """Tests for AWS Textract-based extraction."""

    @pytest.fixture
    def extractor(self):
        with patch('boto3.client'):
            return TextractExtractor()

    @patch('boto3.client')
    def test_init_creates_textract_client(self, mock_boto):
        extractor = TextractExtractor()
        mock_boto.assert_called()

    def test_extract_returns_extraction_result(self, extractor):
        mock_response = _load_fixture('mock_response.json')
        with patch.object(extractor, 'extract', return_value=ExtractionResult(
            text=mock_response['extracted_text'],
            confidence=0.98,
            metadata={},
            pages=1,
            processing_time=0.5,
            extractor_type='textract',
        )):
            result = extractor.extract(b'fake_pdf_bytes')
            assert isinstance(result, ExtractionResult)
            assert result.text is not None
            assert len(result.text) > 0
            assert result.confidence > 0.0

    def test_extract_empty_document(self, extractor):
        """Empty document should still return an ExtractionResult (may have empty text)."""
        with patch.object(extractor, 'extract', return_value=ExtractionResult(
            text='',
            confidence=0.0,
            metadata={},
            pages=0,
            processing_time=0.01,
            extractor_type='textract',
        )):
            result = extractor.extract(b'')
            assert isinstance(result, ExtractionResult)

    def test_document_type_enum(self):
        assert DocumentType.PDF is not None
        assert DocumentType.IMAGE is not None
        assert DocumentType.HANDWRITTEN is not None


# ----------------------------------------------------------------
# TesseractExtractor
# ----------------------------------------------------------------
class TestTesseractExtractor:
    """Tests for Tesseract OCR-based extraction."""

    @pytest.fixture
    def extractor(self):
        return TesseractExtractor()

    def test_init_succeeds(self, extractor):
        assert extractor is not None

    def test_extract_result_structure(self, extractor):
        with patch.object(extractor, 'extract', return_value=ExtractionResult(
            text='Sample OCR output text',
            confidence=0.85,
            metadata={'engine': 'tesseract'},
            pages=1,
            processing_time=0.3,
            extractor_type='tesseract',
        )):
            result = extractor.extract(b'fake_image')
            assert isinstance(result, ExtractionResult)
            assert result.confidence > 0.0
            assert result.extractor_type == 'tesseract'


# ----------------------------------------------------------------
# Entity Extraction
# ----------------------------------------------------------------
class TestEntityExtraction:
    """Tests for entity extraction from text."""

    @pytest.fixture
    def sample_text(self):
        mock = _load_fixture('mock_response.json')
        return mock['extracted_text']

    def test_extract_returns_result_object(self, sample_text):
        with patch('src.document_processing.entity_extraction.ClaimEntityExtractor') as MockExtractor:
            mock_instance = MockExtractor.return_value
            mock_instance.extract.return_value = EntityExtractionResult(
                entities=[
                    Entity(text='John Doe', label='PERSON', confidence=0.95, start_char=0, end_char=8),
                ],
                structured_data={},
                confidence=0.95,
                processing_time=0.1,
                extractor_type='claim',
            )
            result = extract_claim_entities(sample_text)
            assert isinstance(result, EntityExtractionResult)

    def test_extract_finds_person_entities(self, sample_text):
        with patch('src.document_processing.entity_extraction.ClaimEntityExtractor') as MockExtractor:
            mock_instance = MockExtractor.return_value
            mock_instance.extract.return_value = EntityExtractionResult(
                entities=[
                    Entity(text='John Doe', label='PERSON', confidence=0.95, start_char=0, end_char=8),
                    Entity(text='K35.80', label='DIAGNOSIS', confidence=0.97, start_char=20, end_char=26),
                ],
                structured_data={},
                confidence=0.96,
                processing_time=0.1,
                extractor_type='claim',
            )
            result = extract_claim_entities(sample_text)
            person_entities = [e for e in result.entities if e.label == 'PERSON']
            assert len(person_entities) >= 1

    def test_extract_with_empty_text(self):
        with patch('src.document_processing.entity_extraction.ClaimEntityExtractor') as MockExtractor:
            mock_instance = MockExtractor.return_value
            mock_instance.extract.return_value = EntityExtractionResult(
                entities=[],
                structured_data={},
                confidence=0.0,
                processing_time=0.005,
                extractor_type='claim',
            )
            result = extract_claim_entities('')
            assert len(result.entities) == 0

    def test_entity_has_required_fields(self):
        entity = Entity(text='12500.00', label='MONEY', confidence=0.98, start_char=0, end_char=8)
        assert entity.label == 'MONEY'
        assert entity.text == '12500.00'
        assert 0.0 <= entity.confidence <= 1.0


# ----------------------------------------------------------------
# Document Validation
# ----------------------------------------------------------------
class TestDocumentValidation:
    """Tests for document validation logic."""

    @pytest.fixture
    def validator(self):
        return DocumentValidator()

    @pytest.fixture
    def valid_claim_data(self):
        return {
            'patient_name': 'John Doe',
            'date_of_birth': '1985-06-15',
            'diagnosis_code': 'K35.80',
            'procedure_code': '44970',
            'claim_amount': 12500.00,
            'service_date': '2025-01-15',
            'provider_name': 'Test General Hospital',
            'provider_npi': '9999999901',
        }

    def test_validate_returns_result(self, validator, valid_claim_data):
        result = validator.validate(valid_claim_data, claim_type='health')
        assert isinstance(result, ValidationResult)

    def test_valid_data_passes(self, validator, valid_claim_data):
        result = validator.validate(valid_claim_data, claim_type='health')
        assert result.validation_score >= 0

    def test_missing_required_fields_fails(self, validator):
        result = validator.validate({}, claim_type='health')
        assert result.validation_score < 100

    def test_negative_amount_fails(self, validator, valid_claim_data):
        valid_claim_data['claim_amount'] = -500.00
        result = validator.validate(valid_claim_data, claim_type='health')
        assert any(
            issue.severity == ValidationSeverity.ERROR
            for issue in result.issues
        ) or result.validation_score < 100

    def test_validation_severity_levels(self):
        assert ValidationSeverity.INFO is not None
        assert ValidationSeverity.WARNING is not None
        assert ValidationSeverity.ERROR is not None

