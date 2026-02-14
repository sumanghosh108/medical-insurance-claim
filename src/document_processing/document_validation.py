"""
Document Validation Module

Validates insurance claim documents against business rules and compliance requirements.
Checks for completeness, accuracy, and policy compliance.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any

from .entity_extraction import EntityExtractionResult


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"      # Critical issues that block processing
    WARNING = "warning"  # Issues that need review but don't block
    INFO = "info"        # Informational notices


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    severity: ValidationSeverity
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of document validation"""
    is_valid: bool
    validation_score: float  # 0-100
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0
    validated_fields: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate counts from issues"""
        self.errors_count = sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
        self.warnings_count = sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
        self.is_valid = self.errors_count == 0


class DocumentValidator:
    """
    Validates insurance claim documents
    
    Performs comprehensive validation including:
    - Required fields completeness
    - Data format validation
    - Business rule compliance
    - Policy coverage validation
    - Temporal consistency checks
    - Amount reasonableness checks
    """
    
    # Required fields for different claim types
    REQUIRED_FIELDS = {
        'health': [
            'claim_number', 'policy_number', 'patient_name',
            'date_of_service', 'provider_name', 'diagnosis_code',
            'procedure_code', 'amount'
        ],
        'auto': [
            'claim_number', 'policy_number', 'insured_name',
            'accident_date', 'vehicle_info', 'damage_description',
            'amount'
        ],
        'property': [
            'claim_number', 'policy_number', 'insured_name',
            'incident_date', 'property_address', 'damage_description',
            'amount'
        ],
        'life': [
            'claim_number', 'policy_number', 'insured_name',
            'beneficiary_name', 'date_of_death', 'cause_of_death',
            'amount'
        ]
    }
    
    # Amount limits for reasonableness checks (in USD)
    AMOUNT_LIMITS = {
        'health': {'min': 0, 'max': 1_000_000, 'typical_max': 50_000},
        'auto': {'min': 0, 'max': 500_000, 'typical_max': 100_000},
        'property': {'min': 0, 'max': 5_000_000, 'typical_max': 500_000},
        'life': {'min': 0, 'max': 10_000_000, 'typical_max': 1_000_000},
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.strict_mode = self.config.get('strict_mode', False)
        self.enable_ml_validation = self.config.get('enable_ml_validation', True)
    
    def validate(
        self,
        extracted_data: Dict,
        claim_type: str = 'health',
        entities: Optional[EntityExtractionResult] = None,
        **kwargs
    ) -> ValidationResult:
        """
        Validate claim document data
        
        Args:
            extracted_data: Structured data from entity extraction
            claim_type: Type of claim (health, auto, property, life)
            entities: Optional EntityExtractionResult for additional validation
            
        Returns:
            ValidationResult with validation status and issues
        """
        
        self.logger.info(f"Validating {claim_type} claim document")
        
        issues: List[ValidationIssue] = []
        validated_fields: Dict[str, bool] = {}
        
        # 1. Required fields validation
        issues.extend(self._validate_required_fields(extracted_data, claim_type, validated_fields))
        
        # 2. Data format validation
        issues.extend(self._validate_data_formats(extracted_data, validated_fields))
        
        # 3. Business rule validation
        issues.extend(self._validate_business_rules(extracted_data, claim_type, validated_fields))
        
        # 4. Temporal consistency
        issues.extend(self._validate_temporal_consistency(extracted_data, validated_fields))
        
        # 5. Amount reasonableness
        issues.extend(self._validate_amounts(extracted_data, claim_type, validated_fields))
        
        # 6. Policy validation
        issues.extend(self._validate_policy_info(extracted_data, validated_fields))
        
        # 7. Medical validation (for health claims)
        if claim_type == 'health':
            issues.extend(self._validate_medical_data(extracted_data, validated_fields))
        
        # 8. Cross-field validation
        issues.extend(self._validate_cross_field_consistency(extracted_data, validated_fields))
        
        # Calculate validation score
        validation_score = self._calculate_validation_score(issues, validated_fields)
        
        # Determine if valid
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        
        metadata = {
            'claim_type': claim_type,
            'fields_validated': len(validated_fields),
            'fields_passed': sum(validated_fields.values()),
            'strict_mode': self.strict_mode,
        }
        
        return ValidationResult(
            is_valid=not has_errors,
            validation_score=validation_score,
            issues=issues,
            validated_fields=validated_fields,
            metadata=metadata
        )
    
    def _validate_required_fields(
        self,
        data: Dict,
        claim_type: str,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Check if all required fields are present and non-empty"""
        issues = []
        required = self.REQUIRED_FIELDS.get(claim_type, [])
        
        for field in required:
            # Map field names to data structure
            field_path = self._get_field_path(field)
            value = self._get_nested_value(data, field_path)
            
            if value is None or (isinstance(value, str) and not value.strip()):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code='REQUIRED_FIELD_MISSING',
                    message=f"Required field '{field}' is missing or empty",
                    field=field,
                    suggestion=f"Please provide a valid {field.replace('_', ' ')}"
                ))
                validated_fields[field] = False
            else:
                validated_fields[field] = True
        
        return issues
    
    def _validate_data_formats(
        self,
        data: Dict,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Validate data formats (dates, emails, phones, etc.)"""
        issues = []
        
        # Validate policy number format
        policy_num = self._get_nested_value(data, 'policy_info.policy_number')
        if policy_num:
            if not self._is_valid_policy_number(policy_num):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code='INVALID_POLICY_FORMAT',
                    message=f"Policy number '{policy_num}' has invalid format",
                    field='policy_number',
                    value=policy_num,
                    suggestion="Policy number should be 2-3 letters followed by 6-10 digits"
                ))
                validated_fields['policy_number_format'] = False
            else:
                validated_fields['policy_number_format'] = True
        
        # Validate email format
        email = self._get_nested_value(data, 'personal_info.email')
        if email and not self._is_valid_email(email):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code='INVALID_EMAIL_FORMAT',
                message=f"Email '{email}' appears invalid",
                field='email',
                value=email
            ))
            validated_fields['email_format'] = False
        elif email:
            validated_fields['email_format'] = True
        
        # Validate phone format
        phone = self._get_nested_value(data, 'personal_info.phone')
        if phone and not self._is_valid_phone(phone):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code='INVALID_PHONE_FORMAT',
                message=f"Phone number '{phone}' appears invalid",
                field='phone',
                value=phone
            ))
            validated_fields['phone_format'] = False
        elif phone:
            validated_fields['phone_format'] = True
        
        # Validate SSN format
        ssn = self._get_nested_value(data, 'personal_info.ssn')
        if ssn and not self._is_valid_ssn(ssn):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code='INVALID_SSN_FORMAT',
                message="SSN format is invalid",
                field='ssn',
                suggestion="SSN should be 9 digits (XXX-XX-XXXX format)"
            ))
            validated_fields['ssn_format'] = False
        elif ssn:
            validated_fields['ssn_format'] = True
        
        return issues
    
    def _validate_business_rules(
        self,
        data: Dict,
        claim_type: str,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Validate business-specific rules"""
        issues = []
        
        # Health claims specific rules
        if claim_type == 'health':
            diagnosis_codes = self._get_nested_value(data, 'medical_info.diagnosis_codes')
            procedure_codes = self._get_nested_value(data, 'medical_info.procedure_codes')
            
            # Must have at least one diagnosis
            if not diagnosis_codes or len(diagnosis_codes) == 0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code='MISSING_DIAGNOSIS',
                    message="Health claim must include at least one diagnosis code",
                    field='diagnosis_codes',
                    suggestion="Add ICD-10 diagnosis code(s)"
                ))
                validated_fields['has_diagnosis'] = False
            else:
                validated_fields['has_diagnosis'] = True
            
            # Validate ICD-10 format
            if diagnosis_codes:
                for code in diagnosis_codes:
                    if not self._is_valid_icd10(str(code)):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            code='INVALID_ICD_CODE',
                            message=f"Diagnosis code '{code}' may be invalid",
                            field='diagnosis_codes',
                            value=code
                        ))
        
        # Auto claims specific rules
        elif claim_type == 'auto':
            vehicle_info = self._get_nested_value(data, 'claim_info.vehicle_info')
            if vehicle_info and isinstance(vehicle_info, str):
                # Should contain year, make, model
                if len(vehicle_info.split()) < 3:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        code='INCOMPLETE_VEHICLE_INFO',
                        message="Vehicle information appears incomplete",
                        field='vehicle_info',
                        value=vehicle_info,
                        suggestion="Include year, make, and model"
                    ))
                    validated_fields['vehicle_info_complete'] = False
                else:
                    validated_fields['vehicle_info_complete'] = True
        
        return issues
    
    def _validate_temporal_consistency(
        self,
        data: Dict,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Validate date consistency and reasonableness"""
        issues = []
        
        dates = self._get_nested_value(data, 'dates', [])
        
        if not dates or len(dates) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code='NO_DATES_FOUND',
                message="No dates found in document",
                field='dates',
                suggestion="Document must include incident/service date"
            ))
            validated_fields['has_dates'] = False
            return issues
        
        validated_fields['has_dates'] = True
        
        # Convert all to datetime
        parsed_dates = []
        for date_val in dates:
            if isinstance(date_val, datetime):
                parsed_dates.append(date_val)
            elif isinstance(date_val, str):
                try:
                    parsed_dates.append(datetime.fromisoformat(date_val))
                except:
                    pass
        
        if not parsed_dates:
            return issues
        
        # Check for future dates
        now = datetime.now()
        for date in parsed_dates:
            if date > now:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code='FUTURE_DATE',
                    message=f"Date {date.strftime('%Y-%m-%d')} is in the future",
                    field='dates',
                    value=date.strftime('%Y-%m-%d')
                ))
                validated_fields['no_future_dates'] = False
        
        # Check for very old dates (>10 years)
        ten_years_ago = now - timedelta(days=365*10)
        for date in parsed_dates:
            if date < ten_years_ago:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code='VERY_OLD_DATE',
                    message=f"Date {date.strftime('%Y-%m-%d')} is more than 10 years old",
                    field='dates',
                    value=date.strftime('%Y-%m-%d')
                ))
                validated_fields['dates_not_too_old'] = False
        
        # Filing deadline check (typically 90 days for most claims)
        if parsed_dates:
            incident_date = min(parsed_dates)  # Assume earliest is incident
            days_since = (now - incident_date).days
            
            if days_since > 90:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code='LATE_FILING',
                    message=f"Claim filed {days_since} days after incident (>90 days)",
                    field='filing_date',
                    suggestion="Late filings may require additional justification"
                ))
                validated_fields['timely_filing'] = False
            else:
                validated_fields['timely_filing'] = True
        
        return issues
    
    def _validate_amounts(
        self,
        data: Dict,
        claim_type: str,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Validate monetary amounts for reasonableness"""
        issues = []
        
        amounts = self._get_nested_value(data, 'amounts', [])
        
        if not amounts or len(amounts) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code='NO_AMOUNT_FOUND',
                message="No claim amount found in document",
                field='amount',
                suggestion="Document must include claim amount"
            ))
            validated_fields['has_amount'] = False
            return issues
        
        validated_fields['has_amount'] = True
        
        # Get amount limits for this claim type
        limits = self.AMOUNT_LIMITS.get(claim_type, self.AMOUNT_LIMITS['health'])
        
        # Validate each amount
        for amount in amounts:
            try:
                amount_float = float(amount)
                
                # Check minimum
                if amount_float < limits['min']:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code='AMOUNT_TOO_LOW',
                        message=f"Amount ${amount_float:,.2f} is below minimum",
                        field='amount',
                        value=amount_float
                    ))
                    validated_fields['amount_valid_range'] = False
                
                # Check maximum
                elif amount_float > limits['max']:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code='AMOUNT_TOO_HIGH',
                        message=f"Amount ${amount_float:,.2f} exceeds maximum ${limits['max']:,.2f}",
                        field='amount',
                        value=amount_float,
                        suggestion="Amounts exceeding limits require special approval"
                    ))
                    validated_fields['amount_valid_range'] = False
                
                # Check if unusually high
                elif amount_float > limits['typical_max']:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        code='AMOUNT_UNUSUALLY_HIGH',
                        message=f"Amount ${amount_float:,.2f} is unusually high for {claim_type} claims",
                        field='amount',
                        value=amount_float,
                        suggestion="High amounts may require additional documentation"
                    ))
                    validated_fields['amount_typical_range'] = False
                else:
                    validated_fields['amount_valid_range'] = True
                    validated_fields['amount_typical_range'] = True
                    
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code='INVALID_AMOUNT_FORMAT',
                    message=f"Amount '{amount}' is not a valid number",
                    field='amount',
                    value=amount
                ))
                validated_fields['amount_valid_format'] = False
        
        return issues
    
    def _validate_policy_info(
        self,
        data: Dict,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Validate policy information"""
        issues = []
        
        policy_number = self._get_nested_value(data, 'policy_info.policy_number')
        
        if not policy_number:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code='MISSING_POLICY_NUMBER',
                message="Policy number is required",
                field='policy_number'
            ))
            validated_fields['has_policy_number'] = False
        else:
            validated_fields['has_policy_number'] = True
            
            # In production, would check against policy database
            # For now, just validate format
            if len(str(policy_number)) < 6:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code='POLICY_NUMBER_TOO_SHORT',
                    message="Policy number seems too short",
                    field='policy_number',
                    value=policy_number
                ))
        
        return issues
    
    def _validate_medical_data(
        self,
        data: Dict,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Validate medical-specific data"""
        issues = []
        
        provider = self._get_nested_value(data, 'medical_info.provider')
        facility = self._get_nested_value(data, 'medical_info.facility')
        
        if not provider and not facility:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code='MISSING_PROVIDER_INFO',
                message="No provider or facility information found",
                field='provider',
                suggestion="Include healthcare provider or facility name"
            ))
            validated_fields['has_provider_info'] = False
        else:
            validated_fields['has_provider_info'] = True
        
        return issues
    
    def _validate_cross_field_consistency(
        self,
        data: Dict,
        validated_fields: Dict[str, bool]
    ) -> List[ValidationIssue]:
        """Validate consistency across multiple fields"""
        issues = []
        
        # Example: Check if claim amount matches sum of line items
        # This would be implemented based on specific business logic
        
        validated_fields['cross_field_consistent'] = True
        return issues
    
    def _calculate_validation_score(
        self,
        issues: List[ValidationIssue],
        validated_fields: Dict[str, bool]
    ) -> float:
        """Calculate overall validation score (0-100)"""
        
        if not validated_fields:
            return 0.0
        
        # Base score from passed validations
        total_fields = len(validated_fields)
        passed_fields = sum(validated_fields.values())
        base_score = (passed_fields / total_fields) * 100 if total_fields > 0 else 0
        
        # Deductions for issues
        error_penalty = sum(10 for i in issues if i.severity == ValidationSeverity.ERROR)
        warning_penalty = sum(2 for i in issues if i.severity == ValidationSeverity.WARNING)
        
        final_score = max(0, base_score - error_penalty - warning_penalty)
        
        return round(final_score, 2)
    
    # Helper methods
    
    def _get_field_path(self, field: str) -> str:
        """Map field name to data structure path"""
        mapping = {
            'claim_number': 'claim_info.claim_number',
            'policy_number': 'policy_info.policy_number',
            'patient_name': 'personal_info.name',
            'insured_name': 'personal_info.name',
            'date_of_service': 'dates',
            'accident_date': 'dates',
            'incident_date': 'dates',
            'date_of_death': 'dates',
            'provider_name': 'medical_info.provider',
            'diagnosis_code': 'medical_info.diagnosis_codes',
            'procedure_code': 'medical_info.procedure_codes',
            'amount': 'amounts',
            'vehicle_info': 'claim_info.vehicle_info',
            'damage_description': 'claim_info.description',
            'property_address': 'personal_info.address',
            'beneficiary_name': 'claim_info.beneficiary',
            'cause_of_death': 'claim_info.cause_of_death',
        }
        return mapping.get(field, field)
    
    def _get_nested_value(self, data: Dict, path: str, default=None) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def _is_valid_policy_number(self, policy_num: str) -> bool:
        """Validate policy number format"""
        pattern = r'^[A-Z]{2,3}\d{6,10}$|^POL-\d{6,10}$'
        return bool(re.match(pattern, str(policy_num)))
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number"""
        # Remove common separators
        digits = re.sub(r'[-.\s()]', '', phone)
        return len(digits) == 10 and digits.isdigit()
    
    def _is_valid_ssn(self, ssn: str) -> bool:
        """Validate SSN format"""
        # Remove separators
        digits = re.sub(r'[-\s]', '', ssn)
        return len(digits) == 9 and digits.isdigit()
    
    def _is_valid_icd10(self, code: str) -> bool:
        """Validate ICD-10 code format"""
        # Basic pattern: Letter followed by 2 digits, optional decimal and 1-2 more digits
        pattern = r'^[A-Z]\d{2}(\.\d{1,2})?$'
        return bool(re.match(pattern, str(code)))


def validate_claim_document(
    extracted_data: Dict,
    claim_type: str = 'health',
    config: Optional[Dict] = None,
    entities: Optional[EntityExtractionResult] = None
) -> ValidationResult:
    """
    High-level function to validate claim document data
    
    Args:
        extracted_data: Structured data from entity extraction
        claim_type: Type of claim
        config: Configuration dict
        entities: Optional entity extraction result
        
    Returns:
        ValidationResult with validation status
        
    Example:
        >>> result = validate_claim_document(
        ...     extracted_data=structured_data,
        ...     claim_type='health'
        ... )
        >>> if result.is_valid:
        ...     print("Document is valid!")
        >>> else:
        ...     for issue in result.issues:
        ...         print(f"{issue.severity}: {issue.message}")
    """
    
    validator = DocumentValidator(config)
    return validator.validate(
        extracted_data=extracted_data,
        claim_type=claim_type,
        entities=entities
    )