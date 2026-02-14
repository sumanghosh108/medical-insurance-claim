"""
Entity Extraction Module

Extracts structured entities from insurance claim documents using spaCy and HuggingFace.
Identifies key information: names, dates, amounts, medical codes, policy numbers, etc.
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any

import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import numpy as np

from .utils import sanitize_extracted_text


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Entity:
    """Extracted entity with metadata"""
    text: str
    label: str
    confidence: float
    start_char: int
    end_char: int
    normalized_value: Optional[Any] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class EntityExtractionResult:
    """Result of entity extraction operation"""
    entities: List[Entity]
    structured_data: Dict
    confidence: float
    processing_time: float
    extractor_type: str
    errors: Optional[List[str]] = None


class EntityExtractor(ABC):
    """Abstract base class for entity extractors"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self, text: str, **kwargs) -> EntityExtractionResult:
        """Extract entities from text"""
        pass


class ClaimEntityExtractor(EntityExtractor):
    """
    Insurance claim-specific entity extractor
    
    Extracts:
    - Personal information (names, DOB, SSN, contact)
    - Policy information (numbers, dates, coverage)
    - Claim details (incident date, amounts, descriptions)
    - Medical information (codes, procedures, diagnoses)
    - Financial information (amounts, account numbers)
    """
    
    # Entity types for insurance claims
    ENTITY_TYPES = {
        'PERSON': 'Person name',
        'DATE': 'Date (incident, filing, etc.)',
        'MONEY': 'Monetary amount',
        'POLICY_NUMBER': 'Insurance policy number',
        'CLAIM_NUMBER': 'Claim number',
        'SSN': 'Social Security Number',
        'PHONE': 'Phone number',
        'EMAIL': 'Email address',
        'ADDRESS': 'Physical address',
        'ICD_CODE': 'ICD diagnosis code',
        'CPT_CODE': 'CPT procedure code',
        'PROVIDER': 'Healthcare provider name',
        'FACILITY': 'Medical facility',
        'VEHICLE': 'Vehicle information',
        'INJURY': 'Injury description',
        'ORG': 'Organization',
        'PERCENT': 'Percentage',
    }
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        
        # Load spaCy model
        model_name = self.config.get('spacy_model', 'en_core_web_lg')
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"Model {model_name} not found, downloading...")
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', model_name])
            self.nlp = spacy.load(model_name)
        
        # Initialize pattern matcher
        self.matcher = Matcher(self.nlp.vocab)
        self._add_custom_patterns()
        
        # Load HuggingFace NER model for medical entities
        self.use_transformers = self.config.get('use_transformers', True)
        if self.use_transformers:
            self._init_transformer_model()
    
    def _init_transformer_model(self):
        """Initialize HuggingFace transformer for NER"""
        try:
            model_name = self.config.get(
                'transformer_model',
                'allenai/scibert_scivocab_uncased'  # Good for medical text
            )
            self.ner_pipeline = pipeline(
                'ner',
                model=model_name,
                aggregation_strategy='simple'
            )
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}")
            self.use_transformers = False
    
    def _add_custom_patterns(self):
        """Add custom regex patterns for insurance-specific entities"""
        
        # Policy number patterns (various formats)
        policy_patterns = [
            [{"TEXT": {"REGEX": r"^[A-Z]{2,3}\d{6,10}$"}}],  # AB1234567
            [{"TEXT": {"REGEX": r"^POL-\d{6,10}$"}}],         # POL-123456
        ]
        self.matcher.add("POLICY_NUMBER", policy_patterns)
        
        # Claim number patterns
        claim_patterns = [
            [{"TEXT": {"REGEX": r"^CLM-\d{8,12}$"}}],
            [{"TEXT": {"REGEX": r"^[A-Z]\d{10}$"}}],
        ]
        self.matcher.add("CLAIM_NUMBER", claim_patterns)
        
        # SSN patterns (XXX-XX-XXXX)
        ssn_patterns = [
            [{"TEXT": {"REGEX": r"^\d{3}-\d{2}-\d{4}$"}}],
        ]
        self.matcher.add("SSN", ssn_patterns)
        
        # ICD codes
        icd_patterns = [
            [{"TEXT": {"REGEX": r"^[A-Z]\d{2}(\.\d{1,2})?$"}}],  # ICD-10
        ]
        self.matcher.add("ICD_CODE", icd_patterns)
        
        # CPT codes
        cpt_patterns = [
            [{"TEXT": {"REGEX": r"^\d{5}$"}}],
        ]
        self.matcher.add("CPT_CODE", cpt_patterns)
    
    def extract(
        self,
        text: str,
        extract_medical: bool = True,
        extract_financial: bool = True,
        **kwargs
    ) -> EntityExtractionResult:
        """
        Extract entities from claim document text
        
        Args:
            text: Input text from claim document
            extract_medical: Extract medical codes and terms
            extract_financial: Extract financial information
            
        Returns:
            EntityExtractionResult with extracted entities
        """
        import time
        start_time = time.time()
        errors = []
        
        try:
            # Clean text
            text = sanitize_extracted_text(text)
            
            # Process with spaCy
            doc = self.nlp(text)
            
            # Extract entities
            entities = []
            
            # Standard NER entities
            entities.extend(self._extract_spacy_entities(doc))
            
            # Pattern-based entities
            entities.extend(self._extract_pattern_entities(doc))
            
            # Regex-based entities
            entities.extend(self._extract_regex_entities(text))
            
            # Medical entities (if enabled and transformer available)
            if extract_medical and self.use_transformers:
                entities.extend(self._extract_medical_entities(text))
            
            # Financial entities
            if extract_financial:
                entities.extend(self._extract_financial_entities(text))
            
            # Remove duplicates and merge overlapping entities
            entities = self._deduplicate_entities(entities)
            
            # Structure the extracted data
            structured_data = self._structure_entities(entities)
            
            # Calculate overall confidence
            avg_confidence = np.mean([e.confidence for e in entities]) if entities else 0.0
            
            processing_time = time.time() - start_time
            
            return EntityExtractionResult(
                entities=entities,
                structured_data=structured_data,
                confidence=avg_confidence,
                processing_time=processing_time,
                extractor_type='claim_entity_extractor',
                errors=errors if errors else None
            )
            
        except Exception as e:
            error_msg = f"Entity extraction error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            raise
    
    def _extract_spacy_entities(self, doc: Doc) -> List[Entity]:
        """Extract entities using spaCy NER"""
        entities = []
        
        for ent in doc.ents:
            # Map spaCy labels to our entity types
            label = self._map_spacy_label(ent.label_)
            
            if label:
                entity = Entity(
                    text=ent.text,
                    label=label,
                    confidence=0.85,  # Default spaCy confidence
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    normalized_value=self._normalize_entity(ent.text, label)
                )
                entities.append(entity)
        
        return entities
    
    def _extract_pattern_entities(self, doc: Doc) -> List[Entity]:
        """Extract entities using pattern matching"""
        entities = []
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            entity = Entity(
                text=span.text,
                label=label,
                confidence=0.95,  # High confidence for pattern matches
                start_char=span.start_char,
                end_char=span.end_char,
                normalized_value=self._normalize_entity(span.text, label)
            )
            entities.append(entity)
        
        return entities
    
    def _extract_regex_entities(self, text: str) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []
        
        # Phone numbers
        phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label='PHONE',
                confidence=0.90,
                start_char=match.start(),
                end_char=match.end(),
                normalized_value=re.sub(r'[-.\s]', '', match.group())
            ))
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label='EMAIL',
                confidence=0.95,
                start_char=match.start(),
                end_char=match.end(),
                normalized_value=match.group().lower()
            ))
        
        # Money amounts
        money_pattern = r'\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        for match in re.finditer(money_pattern, text):
            amount_str = match.group().replace('$', '').replace(',', '').strip()
            entities.append(Entity(
                text=match.group(),
                label='MONEY',
                confidence=0.90,
                start_char=match.start(),
                end_char=match.end(),
                normalized_value=float(amount_str)
            ))
        
        # Dates (various formats)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',         # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(Entity(
                    text=match.group(),
                    label='DATE',
                    confidence=0.85,
                    start_char=match.start(),
                    end_char=match.end(),
                    normalized_value=self._parse_date(match.group())
                ))
        
        return entities
    
    def _extract_medical_entities(self, text: str) -> List[Entity]:
        """Extract medical entities using transformer model"""
        entities = []
        
        try:
            # Chunk text if too long (transformer limit)
            max_length = 512
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            
            offset = 0
            for chunk in chunks:
                ner_results = self.ner_pipeline(chunk)
                
                for result in ner_results:
                    entity = Entity(
                        text=result['word'],
                        label=self._map_bio_label(result['entity_group']),
                        confidence=result['score'],
                        start_char=result['start'] + offset,
                        end_char=result['end'] + offset
                    )
                    entities.append(entity)
                
                offset += len(chunk)
                
        except Exception as e:
            logger.warning(f"Medical entity extraction failed: {e}")
        
        return entities
    
    def _extract_financial_entities(self, text: str) -> List[Entity]:
        """Extract financial entities (account numbers, routing numbers, etc.)"""
        entities = []
        
        # Account numbers (8-17 digits)
        account_pattern = r'\b\d{8,17}\b'
        for match in re.finditer(account_pattern, text):
            # Avoid matching dates or phone numbers
            if not re.match(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', match.group()):
                entities.append(Entity(
                    text=match.group(),
                    label='ACCOUNT_NUMBER',
                    confidence=0.70,
                    start_char=match.start(),
                    end_char=match.end()
                ))
        
        return entities
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate and overlapping entities, keeping highest confidence"""
        if not entities:
            return []
        
        # Sort by start position
        sorted_entities = sorted(entities, key=lambda e: (e.start_char, -e.confidence))
        
        # Remove overlaps
        unique_entities = []
        last_end = -1
        
        for entity in sorted_entities:
            # If this entity doesn't overlap with previous, add it
            if entity.start_char >= last_end:
                unique_entities.append(entity)
                last_end = entity.end_char
            # If it overlaps but has higher confidence, replace
            elif entity.confidence > unique_entities[-1].confidence:
                unique_entities[-1] = entity
                last_end = entity.end_char
        
        return unique_entities
    
    def _structure_entities(self, entities: List[Entity]) -> Dict:
        """Structure entities into claim-relevant categories"""
        structured = {
            'personal_info': {},
            'policy_info': {},
            'claim_info': {},
            'medical_info': {},
            'financial_info': {},
            'dates': [],
            'amounts': [],
        }
        
        for entity in entities:
            label = entity.label
            value = entity.normalized_value or entity.text
            
            # Personal information
            if label == 'PERSON':
                structured['personal_info']['name'] = value
            elif label == 'SSN':
                structured['personal_info']['ssn'] = value
            elif label == 'PHONE':
                structured['personal_info']['phone'] = value
            elif label == 'EMAIL':
                structured['personal_info']['email'] = value
            elif label == 'ADDRESS':
                structured['personal_info']['address'] = value
            
            # Policy information
            elif label == 'POLICY_NUMBER':
                structured['policy_info']['policy_number'] = value
            elif label == 'CLAIM_NUMBER':
                structured['claim_info']['claim_number'] = value
            
            # Medical information
            elif label == 'ICD_CODE':
                if 'diagnosis_codes' not in structured['medical_info']:
                    structured['medical_info']['diagnosis_codes'] = []
                structured['medical_info']['diagnosis_codes'].append(value)
            elif label == 'CPT_CODE':
                if 'procedure_codes' not in structured['medical_info']:
                    structured['medical_info']['procedure_codes'] = []
                structured['medical_info']['procedure_codes'].append(value)
            elif label == 'PROVIDER':
                structured['medical_info']['provider'] = value
            elif label == 'FACILITY':
                structured['medical_info']['facility'] = value
            
            # Financial information
            elif label == 'MONEY':
                structured['amounts'].append(value)
            elif label == 'ACCOUNT_NUMBER':
                structured['financial_info']['account_number'] = value
            
            # Dates
            elif label == 'DATE':
                structured['dates'].append(value)
        
        return structured
    
    def _map_spacy_label(self, label: str) -> Optional[str]:
        """Map spaCy entity labels to our schema"""
        mapping = {
            'PERSON': 'PERSON',
            'ORG': 'ORG',
            'DATE': 'DATE',
            'MONEY': 'MONEY',
            'PERCENT': 'PERCENT',
            'GPE': 'ADDRESS',  # Geopolitical entity
            'LOC': 'ADDRESS',
        }
        return mapping.get(label)
    
    def _map_bio_label(self, label: str) -> str:
        """Map BIO scheme labels to our schema"""
        # Remove B-, I- prefixes
        clean_label = label.replace('B-', '').replace('I-', '')
        
        mapping = {
            'DISEASE': 'INJURY',
            'CHEMICAL': 'MEDICATION',
            'TREATMENT': 'PROCEDURE',
        }
        
        return mapping.get(clean_label, clean_label)
    
    def _normalize_entity(self, text: str, label: str) -> Any:
        """Normalize entity values to standard formats"""
        
        if label == 'DATE':
            return self._parse_date(text)
        elif label == 'MONEY':
            try:
                return float(text.replace('$', '').replace(',', '').strip())
            except:
                return text
        elif label == 'PHONE':
            return re.sub(r'[-.\s]', '', text)
        elif label == 'EMAIL':
            return text.lower().strip()
        elif label == 'SSN':
            return re.sub(r'[-\s]', '', text)
        else:
            return text.strip()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        formats = [
            '%m/%d/%Y',
            '%m/%d/%y',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None


def extract_claim_entities(
    text: str,
    config: Optional[Dict] = None,
    extract_medical: bool = True,
    extract_financial: bool = True
) -> EntityExtractionResult:
    """
    High-level function to extract entities from insurance claim text
    
    Args:
        text: Input text from claim document
        config: Configuration dict
        extract_medical: Extract medical entities
        extract_financial: Extract financial entities
        
    Returns:
        EntityExtractionResult with extracted entities
        
    Example:
        >>> result = extract_claim_entities(
        ...     text="Policy ABC123456. John Doe filed claim on 01/15/2024. Amount: $5,000."
        ... )
        >>> print(result.structured_data['policy_info'])
        >>> print(result.structured_data['personal_info'])
    """
    
    logger.info("Extracting entities from claim document")
    
    extractor = ClaimEntityExtractor(config)
    return extractor.extract(
        text=text,
        extract_medical=extract_medical,
        extract_financial=extract_financial
    )