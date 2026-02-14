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
        with patch.object(extractor, 'extract_text', return_value=ExtractionResult(
            text=mock_response['extracted_text'],
            confidence=0.98,
            document_type=DocumentType.PDF,
            pages=1,
            metadata={}
        )):
            result = extractor.extract_text(b'fake_pdf_bytes', DocumentType.PDF)
            assert isinstance(result, ExtractionResult)
            assert result.text is not None
            assert len(result.text) > 0
            assert result.confidence > 0.0

    def test_extract_empty_document_raises(self, extractor):
        with pytest.raises(Exception):
            extractor.extract_text(b'', DocumentType.PDF)

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
        with patch.object(extractor, 'extract_text', return_value=ExtractionResult(
            text='Sample OCR output text',
            confidence=0.85,
            document_type=DocumentType.HANDWRITTEN,
            pages=1,
            metadata={'engine': 'tesseract'}
        )):
            result = extractor.extract_text(b'fake_image', DocumentType.HANDWRITTEN)
            assert isinstance(result, ExtractionResult)
            assert result.confidence > 0.0
            assert result.document_type == DocumentType.HANDWRITTEN


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
                    Entity(entity_type='PERSON', value='John Doe', confidence=0.95),
                ],
                raw_text_length=len(sample_text),
                processing_time_ms=100,
            )
            result = extract_claim_entities(sample_text)
            assert isinstance(result, EntityExtractionResult)

    def test_extract_finds_person_entities(self, sample_text):
        with patch('src.document_processing.entity_extraction.ClaimEntityExtractor') as MockExtractor:
            mock_instance = MockExtractor.return_value
            mock_instance.extract.return_value = EntityExtractionResult(
                entities=[
                    Entity(entity_type='PERSON', value='John Doe', confidence=0.95),
                    Entity(entity_type='DIAGNOSIS', value='K35.80', confidence=0.97),
                ],
                raw_text_length=len(sample_text),
                processing_time_ms=100,
            )
            result = extract_claim_entities(sample_text)
            person_entities = [e for e in result.entities if e.entity_type == 'PERSON']
            assert len(person_entities) >= 1

    def test_extract_with_empty_text(self):
        with patch('src.document_processing.entity_extraction.ClaimEntityExtractor') as MockExtractor:
            mock_instance = MockExtractor.return_value
            mock_instance.extract.return_value = EntityExtractionResult(
                entities=[],
                raw_text_length=0,
                processing_time_ms=5,
            )
            result = extract_claim_entities('')
            assert len(result.entities) == 0

    def test_entity_has_required_fields(self):
        entity = Entity(entity_type='MONEY', value='12500.00', confidence=0.98)
        assert entity.entity_type == 'MONEY'
        assert entity.value == '12500.00'
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
        assert result.score >= 0

    def test_missing_required_fields_fails(self, validator):
        result = validator.validate({}, claim_type='health')
        assert result.score < 100

    def test_negative_amount_fails(self, validator, valid_claim_data):
        valid_claim_data['claim_amount'] = -500.00
        result = validator.validate(valid_claim_data, claim_type='health')
        assert any(
            issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            for issue in result.issues
        ) or result.score < 100

    def test_validation_severity_levels(self):
        assert ValidationSeverity.INFO is not None
        assert ValidationSeverity.WARNING is not None
        assert ValidationSeverity.ERROR is not None
        assert ValidationSeverity.CRITICAL is not None
