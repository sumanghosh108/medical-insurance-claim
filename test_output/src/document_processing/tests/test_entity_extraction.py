"""
Unit tests for entity extraction module
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from document_processing.entity_extraction import (
    ClaimEntityExtractor,
    Entity,
    EntityExtractionResult,
    extract_claim_entities
)


class TestClaimEntityExtractor:
    """Tests for claim entity extraction"""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance with mocked dependencies"""
        with patch('document_processing.entity_extraction.spacy.load'):
            extractor = ClaimEntityExtractor({
                'spacy_model': 'en_core_web_sm',
                'use_transformers': False  # Disable for testing
            })
            return extractor
    
    def test_extract_policy_numbers(self, extractor):
        """Test policy number extraction"""
        
        text = "Policy number AB1234567 was filed on 01/15/2024."
        
        result = extractor.extract(text, extract_medical=False, extract_financial=False)
        
        # Check if policy number was extracted
        policy_entities = [e for e in result.entities if e.label == 'POLICY_NUMBER']
        assert len(policy_entities) > 0
        
        # Check structured data
        assert 'policy_info' in result.structured_data
    
    def test_extract_dates(self, extractor):
        """Test date extraction"""
        
        text = """
        Incident occurred on 03/15/2024.
        Claim filed: 2024-03-20
        Service date: March 25, 2024
        """
        
        result = extractor.extract(text, extract_medical=False)
        
        # Should extract multiple dates
        date_entities = [e for e in result.entities if e.label == 'DATE']
        assert len(date_entities) >= 3
        
        # Check structured data
        assert 'dates' in result.structured_data
        assert len(result.structured_data['dates']) > 0
    
    def test_extract_money_amounts(self, extractor):
        """Test monetary amount extraction"""
        
        text = """
        Claim amount: $5,000.00
        Deductible: $500
        Total: $4,500.00
        """
        
        result = extractor.extract(text, extract_medical=False)
        
        # Should extract money entities
        money_entities = [e for e in result.entities if e.label == 'MONEY']
        assert len(money_entities) >= 3
        
        # Check normalized values
        for entity in money_entities:
            assert isinstance(entity.normalized_value, float)
            assert entity.normalized_value > 0
        
        # Check structured data
        assert 'amounts' in result.structured_data
        assert len(result.structured_data['amounts']) >= 3
    
    def test_extract_phone_numbers(self, extractor):
        """Test phone number extraction"""
        
        text = """
        Contact: 555-123-4567
        Office: (555) 987-6543
        Mobile: 555.456.7890
        """
        
        result = extractor.extract(text, extract_medical=False, extract_financial=False)
        
        phone_entities = [e for e in result.entities if e.label == 'PHONE']
        assert len(phone_entities) >= 3
        
        # Check normalization (should remove separators)
        for entity in phone_entities:
            assert entity.normalized_value.isdigit()
            assert len(entity.normalized_value) == 10
    
    def test_extract_email_addresses(self, extractor):
        """Test email extraction"""
        
        text = "Contact us at claims@insurance.com or support@insure.org"
        
        result = extractor.extract(text, extract_medical=False, extract_financial=False)
        
        email_entities = [e for e in result.entities if e.label == 'EMAIL']
        assert len(email_entities) == 2
        
        # Emails should be normalized to lowercase
        for entity in email_entities:
            assert entity.normalized_value == entity.normalized_value.lower()
            assert '@' in entity.normalized_value
    
    def test_extract_ssn(self, extractor):
        """Test SSN extraction"""
        
        text = "Social Security Number: 123-45-6789"
        
        result = extractor.extract(text, extract_medical=False, extract_financial=False)
        
        ssn_entities = [e for e in result.entities if e.label == 'SSN']
        assert len(ssn_entities) >= 1
        
        # SSN should be normalized (no separators)
        ssn_entity = ssn_entities[0]
        assert ssn_entity.normalized_value == '123456789'
    
    def test_extract_icd_codes(self, extractor):
        """Test ICD diagnosis code extraction"""
        
        text = """
        Diagnosis codes: E11.9 (Type 2 diabetes), J44.0 (COPD), M54.5 (Low back pain)
        """
        
        result = extractor.extract(text, extract_medical=True)
        
        icd_entities = [e for e in result.entities if e.label == 'ICD_CODE']
        assert len(icd_entities) >= 3
        
        # Check structured medical data
        assert 'medical_info' in result.structured_data
        assert 'diagnosis_codes' in result.structured_data['medical_info']
        assert len(result.structured_data['medical_info']['diagnosis_codes']) >= 3
    
    def test_extract_cpt_codes(self, extractor):
        """Test CPT procedure code extraction"""
        
        text = """
        Procedures performed:
        99213 - Office visit
        80053 - Comprehensive metabolic panel
        36415 - Venipuncture
        """
        
        result = extractor.extract(text, extract_medical=True)
        
        cpt_entities = [e for e in result.entities if e.label == 'CPT_CODE']
        assert len(cpt_entities) >= 3
        
        # Verify all are 5-digit codes
        for entity in cpt_entities:
            assert len(entity.text) == 5
            assert entity.text.isdigit()
    
    def test_deduplicate_overlapping_entities(self, extractor):
        """Test deduplication of overlapping entities"""
        
        # Create overlapping entities
        entities = [
            Entity(
                text='John Doe',
                label='PERSON',
                confidence=0.9,
                start_char=0,
                end_char=8
            ),
            Entity(
                text='John',
                label='PERSON',
                confidence=0.7,
                start_char=0,
                end_char=4
            ),
            Entity(
                text='Doe',
                label='PERSON',
                confidence=0.8,
                start_char=5,
                end_char=8
            )
        ]
        
        deduplicated = extractor._deduplicate_entities(entities)
        
        # Should keep only highest confidence non-overlapping
        assert len(deduplicated) == 1
        assert deduplicated[0].text == 'John Doe'
        assert deduplicated[0].confidence == 0.9
    
    def test_normalize_dates(self, extractor):
        """Test date normalization"""
        
        date_strings = [
            ('01/15/2024', '%m/%d/%Y'),
            ('2024-01-15', '%Y-%m-%d'),
            ('January 15, 2024', '%B %d, %Y'),
        ]
        
        for date_str, expected_format in date_strings:
            normalized = extractor._parse_date(date_str)
            assert isinstance(normalized, datetime)
            assert normalized.year == 2024
            assert normalized.month == 1
            assert normalized.day == 15
    
    def test_structure_entities(self, extractor):
        """Test entity structuring into categories"""
        
        entities = [
            Entity('John Doe', 'PERSON', 0.9, 0, 8),
            Entity('AB1234567', 'POLICY_NUMBER', 0.95, 20, 29),
            Entity('555-123-4567', 'PHONE', 0.9, 40, 52, '5551234567'),
            Entity('$5000', 'MONEY', 0.9, 60, 65, 5000.0),
            Entity('E11.9', 'ICD_CODE', 0.95, 80, 85),
        ]
        
        structured = extractor._structure_entities(entities)
        
        # Verify structure
        assert structured['personal_info']['name'] == 'John Doe'
        assert structured['personal_info']['phone'] == '5551234567'
        assert structured['policy_info']['policy_number'] == 'AB1234567'
        assert 5000.0 in structured['amounts']
        assert 'E11.9' in structured['medical_info']['diagnosis_codes']
    
    def test_confidence_calculation(self, extractor):
        """Test overall confidence calculation"""
        
        text = "Policy AB123456, Amount: $1,000, Date: 01/15/2024"
        
        result = extractor.extract(text, extract_medical=False, extract_financial=False)
        
        # Should have reasonable confidence
        assert 0 <= result.confidence <= 100
        
        # With multiple high-confidence entities, should be decent
        if len(result.entities) >= 3:
            assert result.confidence > 50


class TestExtractClaimEntities:
    """Tests for high-level extraction function"""
    
    @patch('document_processing.entity_extraction.ClaimEntityExtractor')
    def test_extract_claim_entities_function(self, mock_extractor_cls):
        """Test the high-level extract_claim_entities function"""
        
        # Setup mock
        mock_extractor = mock_extractor_cls.return_value
        mock_result = EntityExtractionResult(
            entities=[],
            structured_data={},
            confidence=85.0,
            processing_time=1.0,
            extractor_type='test'
        )
        mock_extractor.extract.return_value = mock_result
        
        # Call function
        text = "Test claim document"
        result = extract_claim_entities(
            text=text,
            extract_medical=True,
            extract_financial=True
        )
        
        # Verify extractor was created and called
        mock_extractor_cls.assert_called_once()
        mock_extractor.extract.assert_called_once_with(
            text=text,
            extract_medical=True,
            extract_financial=True
        )
        
        assert result.confidence == 85.0


class TestEntityNormalization:
    """Tests for entity normalization"""
    
    @pytest.fixture
    def extractor(self):
        with patch('document_processing.entity_extraction.spacy.load'):
            return ClaimEntityExtractor({'use_transformers': False})
    
    def test_normalize_phone(self, extractor):
        """Test phone number normalization"""
        
        test_cases = [
            ('555-123-4567', '5551234567'),
            ('(555) 123-4567', '5551234567'),
            ('555.123.4567', '5551234567'),
            ('555 123 4567', '5551234567'),
        ]
        
        for input_val, expected in test_cases:
            result = extractor._normalize_entity(input_val, 'PHONE')
            assert result == expected
    
    def test_normalize_money(self, extractor):
        """Test money amount normalization"""
        
        test_cases = [
            ('$1,000.00', 1000.0),
            ('$500', 500.0),
            ('$12,345.67', 12345.67),
        ]
        
        for input_val, expected in test_cases:
            result = extractor._normalize_entity(input_val, 'MONEY')
            assert result == expected
    
    def test_normalize_email(self, extractor):
        """Test email normalization"""
        
        test_cases = [
            ('John.Doe@Example.COM', 'john.doe@example.com'),
            ('CLAIMS@INSURE.ORG', 'claims@insure.org'),
        ]
        
        for input_val, expected in test_cases:
            result = extractor._normalize_entity(input_val, 'EMAIL')
            assert result == expected


class TestComplexDocument:
    """Test extraction from complex, realistic documents"""
    
    @pytest.fixture
    def extractor(self):
        with patch('document_processing.entity_extraction.spacy.load'):
            return ClaimEntityExtractor({'use_transformers': False})
    
    def test_extract_from_full_claim_document(self, extractor):
        """Test extraction from a complete claim document"""
        
        document_text = """
        INSURANCE CLAIM FORM
        
        Policy Number: AB1234567
        Claim Number: CLM-9876543210
        
        Insured Information:
        Name: John Michael Doe
        SSN: 123-45-6789
        Phone: (555) 123-4567
        Email: john.doe@email.com
        Address: 123 Main Street, Anytown, ST 12345
        
        Incident Information:
        Date of Incident: 03/15/2024
        Date of Filing: 03/20/2024
        
        Medical Information:
        Provider: Dr. Sarah Johnson, MD
        Facility: City General Hospital
        Diagnosis Codes: E11.9, I10, M79.3
        Procedure Codes: 99213, 36415, 80053
        
        Financial Information:
        Total Claim Amount: $8,500.00
        Deductible: $1,000.00
        Patient Responsibility: $1,500.00
        """
        
        result = extractor.extract(
            document_text,
            extract_medical=True,
            extract_financial=True
        )
        
        # Verify comprehensive extraction
        assert result.entities is not None
        assert len(result.entities) > 10  # Should extract many entities
        
        # Verify structured data
        data = result.structured_data
        
        # Personal info
        assert 'personal_info' in data
        assert data['personal_info'].get('name') is not None
        assert data['personal_info'].get('ssn') == '123456789'
        assert data['personal_info'].get('phone') == '5551234567'
        assert data['personal_info'].get('email') == 'john.doe@email.com'
        
        # Policy info
        assert 'policy_info' in data
        assert data['policy_info'].get('policy_number') == 'AB1234567'
        
        # Claim info
        assert 'claim_info' in data
        assert data['claim_info'].get('claim_number') == 'CLM-9876543210'
        
        # Medical info
        assert 'medical_info' in data
        assert len(data['medical_info'].get('diagnosis_codes', [])) >= 3
        assert len(data['medical_info'].get('procedure_codes', [])) >= 3
        
        # Financial info
        assert 'amounts' in data
        assert len(data['amounts']) >= 3
        
        # Dates
        assert 'dates' in data
        assert len(data['dates']) >= 2


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def extractor(self):
        with patch('document_processing.entity_extraction.spacy.load'):
            return ClaimEntityExtractor({'use_transformers': False})
    
    def test_empty_text(self, extractor):
        """Test extraction from empty text"""
        
        result = extractor.extract("")
        
        assert result.entities == []
        assert result.confidence == 0.0
    
    def test_text_with_no_entities(self, extractor):
        """Test extraction from text with no recognizable entities"""
        
        text = "This is just random text with no useful information."
        
        result = extractor.extract(text, extract_medical=False, extract_financial=False)
        
        # May extract some entities but should handle gracefully
        assert isinstance(result, EntityExtractionResult)
        assert result.confidence >= 0
    
    def test_malformed_dates(self, extractor):
        """Test handling of malformed dates"""
        
        text = "Date: 99/99/9999"  # Invalid date
        
        result = extractor.extract(text, extract_medical=False, extract_financial=False)
        
        # Should not crash
        assert isinstance(result, EntityExtractionResult)
    
    def test_very_long_text(self, extractor):
        """Test handling of very long documents"""
        
        # Create long text
        long_text = "Policy AB123456. " * 1000  # Repeat many times
        
        result = extractor.extract(long_text, extract_medical=False)
        
        # Should handle without error
        assert isinstance(result, EntityExtractionResult)
        # Should still extract the policy number
        assert len([e for e in result.entities if e.label == 'POLICY_NUMBER']) > 0


def test_entity_dataclass():
    """Test Entity dataclass"""
    
    entity = Entity(
        text="John Doe",
        label="PERSON",
        confidence=0.95,
        start_char=0,
        end_char=8,
        normalized_value="John Doe"
    )
    
    assert entity.text == "John Doe"
    assert entity.label == "PERSON"
    assert entity.confidence == 0.95
    assert entity.metadata == {}


def test_extraction_result_dataclass():
    """Test EntityExtractionResult dataclass"""
    
    result = EntityExtractionResult(
        entities=[],
        structured_data={},
        confidence=85.0,
        processing_time=2.5,
        extractor_type='test'
    )
    
    assert result.confidence == 85.0
    assert result.processing_time == 2.5
    assert result.errors is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])