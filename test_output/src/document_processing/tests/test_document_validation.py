"""
Unit tests for document validation module
"""

import pytest
from datetime import datetime, timedelta

from document_processing.document_validation import (
    DocumentValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    validate_claim_document
)


class TestDocumentValidator:
    """Tests for document validation"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return DocumentValidator({'strict_mode': False})
    
    @pytest.fixture
    def valid_health_claim_data(self):
        """Sample valid health claim data"""
        return {
            'claim_info': {
                'claim_number': 'CLM-1234567890'
            },
            'policy_info': {
                'policy_number': 'AB1234567'
            },
            'personal_info': {
                'name': 'John Doe',
                'ssn': '123456789',
                'phone': '5551234567',
                'email': 'john@example.com'
            },
            'medical_info': {
                'provider': 'Dr. Smith',
                'diagnosis_codes': ['E11.9', 'I10'],
                'procedure_codes': ['99213']
            },
            'dates': [
                datetime(2024, 3, 15),  # Service date
                datetime(2024, 3, 20)   # Filing date
            ],
            'amounts': [5000.0]
        }
    
    def test_validate_valid_health_claim(self, validator, valid_health_claim_data):
        """Test validation of a valid health claim"""
        
        result = validator.validate(
            extracted_data=valid_health_claim_data,
            claim_type='health'
        )
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.errors_count == 0
        assert result.validation_score > 80
    
    def test_required_fields_missing(self, validator):
        """Test validation fails when required fields are missing"""
        
        incomplete_data = {
            'policy_info': {'policy_number': 'AB123456'},
            # Missing claim_number, personal info, etc.
        }
        
        result = validator.validate(
            extracted_data=incomplete_data,
            claim_type='health'
        )
        
        assert result.is_valid is False
        assert result.errors_count > 0
        
        # Check for specific error codes
        error_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert 'REQUIRED_FIELD_MISSING' in error_codes
    
    def test_invalid_policy_number_format(self, validator, valid_health_claim_data):
        """Test validation catches invalid policy number format"""
        
        valid_health_claim_data['policy_info']['policy_number'] = 'INVALID'
        
        result = validator.validate(
            extracted_data=valid_health_claim_data,
            claim_type='health'
        )
        
        # Should have error for invalid format
        error_codes = [issue.code for issue in result.issues]
        assert 'INVALID_POLICY_FORMAT' in error_codes
    
    def test_invalid_email_format(self, validator, valid_health_claim_data):
        """Test validation catches invalid email"""
        
        valid_health_claim_data['personal_info']['email'] = 'not-an-email'
        
        result = validator.validate(
            extracted_data=valid_health_claim_data,
            claim_type='health'
        )
        
        # Should have warning for invalid email
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'INVALID_EMAIL_FORMAT' in warning_codes
    
    def test_invalid_phone_format(self, validator, valid_health_claim_data):
        """Test validation catches invalid phone number"""
        
        valid_health_claim_data['personal_info']['phone'] = '123'  # Too short
        
        result = validator.validate(
            extracted_data=valid_health_claim_data,
            claim_type='health'
        )
        
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'INVALID_PHONE_FORMAT' in warning_codes
    
    def test_invalid_ssn_format(self, validator, valid_health_claim_data):
        """Test validation catches invalid SSN"""
        
        valid_health_claim_data['personal_info']['ssn'] = '12345'  # Too short
        
        result = validator.validate(
            extracted_data=valid_health_claim_data,
            claim_type='health'
        )
        
        error_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert 'INVALID_SSN_FORMAT' in error_codes
    
    def test_missing_diagnosis_codes(self, validator, valid_health_claim_data):
        """Test health claim requires diagnosis codes"""
        
        valid_health_claim_data['medical_info']['diagnosis_codes'] = []
        
        result = validator.validate(
            extracted_data=valid_health_claim_data,
            claim_type='health'
        )
        
        assert result.is_valid is False
        error_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert 'MISSING_DIAGNOSIS' in error_codes
    
    def test_invalid_icd_code_format(self, validator, valid_health_claim_data):
        """Test validation of ICD-10 code format"""
        
        valid_health_claim_data['medical_info']['diagnosis_codes'] = ['INVALID', 'E11.9']
        
        result = validator.validate(
            extracted_data=valid_health_claim_data,
            claim_type='health'
        )
        
        # Should have warning for invalid code
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'INVALID_ICD_CODE' in warning_codes


class TestTemporalValidation:
    """Tests for date and temporal validation"""
    
    @pytest.fixture
    def validator(self):
        return DocumentValidator()
    
    def test_future_dates_flagged(self, validator):
        """Test that future dates are flagged as warnings"""
        
        future_date = datetime.now() + timedelta(days=30)
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [future_date],
            'amounts': [1000.0]
        }
        
        result = validator.validate(data, claim_type='health')
        
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'FUTURE_DATE' in warning_codes
    
    def test_very_old_dates_flagged(self, validator):
        """Test that very old dates (>10 years) are flagged"""
        
        old_date = datetime.now() - timedelta(days=365*11)
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [old_date],
            'amounts': [1000.0]
        }
        
        result = validator.validate(data, claim_type='health')
        
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'VERY_OLD_DATE' in warning_codes
    
    def test_late_filing_flagged(self, validator):
        """Test that late filings (>90 days) are flagged"""
        
        incident_date = datetime.now() - timedelta(days=100)
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [incident_date],
            'amounts': [1000.0]
        }
        
        result = validator.validate(data, claim_type='health')
        
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'LATE_FILING' in warning_codes
    
    def test_timely_filing_passes(self, validator):
        """Test that timely filing (<90 days) passes validation"""
        
        recent_date = datetime.now() - timedelta(days=30)
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [recent_date],
            'amounts': [1000.0]
        }
        
        result = validator.validate(data, claim_type='health')
        
        # Should pass timely filing check
        assert result.validated_fields.get('timely_filing', False) is True
    
    def test_no_dates_found_error(self, validator):
        """Test error when no dates are found"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [],
            'amounts': [1000.0]
        }
        
        result = validator.validate(data, claim_type='health')
        
        assert result.is_valid is False
        error_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert 'NO_DATES_FOUND' in error_codes


class TestAmountValidation:
    """Tests for monetary amount validation"""
    
    @pytest.fixture
    def validator(self):
        return DocumentValidator()
    
    def test_amount_within_valid_range(self, validator):
        """Test amount within valid range passes"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [25000.0]  # Within typical health claim range
        }
        
        result = validator.validate(data, claim_type='health')
        
        # Should pass amount validation
        assert result.validated_fields.get('amount_valid_range', False) is True
        assert result.validated_fields.get('amount_typical_range', False) is True
    
    def test_amount_too_high(self, validator):
        """Test amount exceeding maximum is flagged"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [2000000.0]  # Exceeds health claim max
        }
        
        result = validator.validate(data, claim_type='health')
        
        assert result.is_valid is False
        error_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert 'AMOUNT_TOO_HIGH' in error_codes
    
    def test_amount_too_low(self, validator):
        """Test negative amount is flagged"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [-100.0]
        }
        
        result = validator.validate(data, claim_type='health')
        
        assert result.is_valid is False
        error_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert 'AMOUNT_TOO_LOW' in error_codes
    
    def test_unusually_high_amount_warning(self, validator):
        """Test unusually high (but valid) amount gets warning"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [75000.0]  # Higher than typical but within max
        }
        
        result = validator.validate(data, claim_type='health')
        
        # Should be valid but have warning
        assert result.is_valid is True
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'AMOUNT_UNUSUALLY_HIGH' in warning_codes
    
    def test_no_amount_found_error(self, validator):
        """Test error when no amount is found"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': []
        }
        
        result = validator.validate(data, claim_type='health')
        
        assert result.is_valid is False
        error_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert 'NO_AMOUNT_FOUND' in error_codes
    
    def test_different_claim_type_limits(self, validator):
        """Test different amount limits for different claim types"""
        
        # Auto claim with high amount
        auto_data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [200000.0]
        }
        
        auto_result = validator.validate(auto_data, claim_type='auto')
        
        # Should be valid for auto (typical max 100k, max 500k)
        assert auto_result.is_valid is True
        
        # Life claim with high amount
        life_data = {
            'policy_info': {'policy_number': 'AB123456'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [2000000.0]
        }
        
        life_result = validator.validate(life_data, claim_type='life')
        
        # Should be valid for life insurance (typical max 1M, max 10M)
        assert life_result.is_valid is True


class TestBusinessRuleValidation:
    """Tests for business-specific validation rules"""
    
    @pytest.fixture
    def validator(self):
        return DocumentValidator()
    
    def test_auto_claim_vehicle_info(self, validator):
        """Test auto claim vehicle information validation"""
        
        # Incomplete vehicle info
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'claim_info': {'vehicle_info': 'Toyota'},  # Missing year and model
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [5000.0]
        }
        
        result = validator.validate(data, claim_type='auto')
        
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'INCOMPLETE_VEHICLE_INFO' in warning_codes
    
    def test_auto_claim_complete_vehicle_info(self, validator):
        """Test auto claim with complete vehicle information"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'claim_info': {'vehicle_info': '2020 Toyota Camry'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [5000.0]
        }
        
        result = validator.validate(data, claim_type='auto')
        
        # Should pass vehicle info validation
        assert result.validated_fields.get('vehicle_info_complete', False) is True
    
    def test_health_claim_missing_provider(self, validator):
        """Test health claim without provider information"""
        
        data = {
            'policy_info': {'policy_number': 'AB123456'},
            'medical_info': {
                'diagnosis_codes': ['E11.9']
                # No provider or facility
            },
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [1000.0]
        }
        
        result = validator.validate(data, claim_type='health')
        
        warning_codes = [issue.code for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert 'MISSING_PROVIDER_INFO' in warning_codes


class TestValidationScoring:
    """Tests for validation score calculation"""
    
    @pytest.fixture
    def validator(self):
        return DocumentValidator()
    
    def test_perfect_score(self, validator):
        """Test validation score for perfect document"""
        
        perfect_data = {
            'claim_info': {'claim_number': 'CLM-1234567890'},
            'policy_info': {'policy_number': 'AB1234567'},
            'personal_info': {
                'name': 'John Doe',
                'ssn': '123456789',
                'phone': '5551234567',
                'email': 'john@example.com'
            },
            'medical_info': {
                'provider': 'Dr. Smith',
                'diagnosis_codes': ['E11.9'],
                'procedure_codes': ['99213']
            },
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [5000.0]
        }
        
        result = validator.validate(perfect_data, claim_type='health')
        
        # Should have high score
        assert result.validation_score >= 90
        assert result.is_valid is True
    
    def test_score_with_errors(self, validator):
        """Test validation score decreases with errors"""
        
        data_with_errors = {
            'policy_info': {'policy_number': 'INVALID'},  # Invalid format
            'personal_info': {'ssn': '123'},  # Invalid SSN
            'dates': [],  # Missing dates
            'amounts': []  # Missing amount
        }
        
        result = validator.validate(data_with_errors, claim_type='health')
        
        # Should have low score
        assert result.validation_score < 50
        assert result.is_valid is False
        assert result.errors_count > 0
    
    def test_score_with_warnings(self, validator):
        """Test validation score with warnings but no errors"""
        
        data_with_warnings = {
            'policy_info': {'policy_number': 'AB1234567'},
            'personal_info': {'email': 'not-valid-email'},  # Warning
            'dates': [datetime.now() - timedelta(days=95)],  # Late filing warning
            'amounts': [75000.0]  # Unusually high warning
        }
        
        result = validator.validate(data_with_warnings, claim_type='health')
        
        # Should be valid but with reduced score
        assert result.is_valid is True
        assert 70 <= result.validation_score < 95
        assert result.warnings_count > 0


class TestHighLevelFunction:
    """Tests for high-level validate_claim_document function"""
    
    def test_validate_claim_document_function(self):
        """Test the high-level validation function"""
        
        data = {
            'policy_info': {'policy_number': 'AB1234567'},
            'dates': [datetime.now() - timedelta(days=10)],
            'amounts': [5000.0]
        }
        
        result = validate_claim_document(
            extracted_data=data,
            claim_type='health'
        )
        
        assert isinstance(result, ValidationResult)
        assert result.metadata['claim_type'] == 'health'


class TestHelperMethods:
    """Tests for validator helper methods"""
    
    @pytest.fixture
    def validator(self):
        return DocumentValidator()
    
    def test_get_nested_value(self, validator):
        """Test nested dictionary value retrieval"""
        
        data = {
            'level1': {
                'level2': {
                    'value': 'found'
                }
            }
        }
        
        # Test successful retrieval
        result = validator._get_nested_value(data, 'level1.level2.value')
        assert result == 'found'
        
        # Test default value for missing key
        result = validator._get_nested_value(data, 'missing.path', 'default')
        assert result == 'default'
    
    def test_is_valid_policy_number(self, validator):
        """Test policy number format validation"""
        
        assert validator._is_valid_policy_number('AB1234567')
        assert validator._is_valid_policy_number('POL-123456')
        assert validator._is_valid_policy_number('ABC1234567890')
        
        assert not validator._is_valid_policy_number('123456')
        assert not validator._is_valid_policy_number('INVALID')
    
    def test_is_valid_email(self, validator):
        """Test email format validation"""
        
        assert validator._is_valid_email('john@example.com')
        assert validator._is_valid_email('user.name@company.org')
        
        assert not validator._is_valid_email('not-an-email')
        assert not validator._is_valid_email('@example.com')
        assert not validator._is_valid_email('user@')
    
    def test_is_valid_phone(self, validator):
        """Test phone number validation"""
        
        assert validator._is_valid_phone('5551234567')
        assert validator._is_valid_phone('555-123-4567')
        assert validator._is_valid_phone('(555) 123-4567')
        
        assert not validator._is_valid_phone('123')
        assert not validator._is_valid_phone('12345678901')
    
    def test_is_valid_ssn(self, validator):
        """Test SSN validation"""
        
        assert validator._is_valid_ssn('123456789')
        assert validator._is_valid_ssn('123-45-6789')
        
        assert not validator._is_valid_ssn('12345')
        assert not validator._is_valid_ssn('abc123456')
    
    def test_is_valid_icd10(self, validator):
        """Test ICD-10 code format validation"""
        
        assert validator._is_valid_icd10('E11.9')
        assert validator._is_valid_icd10('I10')
        assert validator._is_valid_icd10('M79.3')
        assert validator._is_valid_icd10('A01.05')
        
        assert not validator._is_valid_icd10('123')
        assert not validator._is_valid_icd10('ABC')
        assert not validator._is_valid_icd10('E11.999')


def test_validation_issue_dataclass():
    """Test ValidationIssue dataclass"""
    
    issue = ValidationIssue(
        severity=ValidationSeverity.ERROR,
        code='TEST_ERROR',
        message='This is a test error',
        field='test_field',
        value='invalid',
        suggestion='Use a valid value'
    )
    
    assert issue.severity == ValidationSeverity.ERROR
    assert issue.code == 'TEST_ERROR'
    assert issue.field == 'test_field'


def test_validation_result_dataclass():
    """Test ValidationResult dataclass and post_init"""
    
    issues = [
        ValidationIssue(ValidationSeverity.ERROR, 'ERR1', 'Error 1'),
        ValidationIssue(ValidationSeverity.WARNING, 'WARN1', 'Warning 1'),
        ValidationIssue(ValidationSeverity.WARNING, 'WARN2', 'Warning 2'),
    ]
    
    result = ValidationResult(
        is_valid=True,  # Will be overridden in post_init
        validation_score=75.0,
        issues=issues
    )
    
    # post_init should set is_valid=False due to error
    assert result.is_valid is False
    assert result.errors_count == 1
    assert result.warnings_count == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])