"""
Text Extraction Module

Provides OCR capabilities using AWS Textract (for PDFs) and Tesseract (for handwritten documents).
Implements retry logic, error handling, and confidence scoring.
"""

import io
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract

from .utils import preprocess_image, sanitize_extracted_text, calculate_confidence_score


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DocumentType(Enum):
    """Supported document types for extraction"""
    PDF = "pdf"
    IMAGE = "image"
    HANDWRITTEN = "handwritten"
    FORM = "form"
    INVOICE = "invoice"
    MEDICAL_RECORD = "medical_record"


@dataclass
class ExtractionResult:
    """Result of text extraction operation"""
    text: str
    confidence: float
    metadata: Dict
    pages: int
    processing_time: float
    extractor_type: str
    raw_response: Optional[Dict] = None
    errors: Optional[List[str]] = None


class TextExtractor(ABC):
    """Abstract base class for text extractors"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract(self, document: Union[bytes, str], **kwargs) -> ExtractionResult:
        """Extract text from document"""
        pass
    
    @abstractmethod
    def supports_document_type(self, doc_type: DocumentType) -> bool:
        """Check if extractor supports document type"""
        pass


class TextractExtractor(TextExtractor):
    """
    AWS Textract-based text extractor
    
    Optimized for printed PDFs and forms with high accuracy.
    Supports async processing for large documents.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.textract_client = boto3.client(
            'textract',
            region_name=self.config.get('aws_region', 'us-east-1')
        )
        self.s3_client = boto3.client('s3')
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 2)
    
    def supports_document_type(self, doc_type: DocumentType) -> bool:
        """Textract supports PDFs, images, and forms"""
        return doc_type in [
            DocumentType.PDF,
            DocumentType.IMAGE,
            DocumentType.FORM,
            DocumentType.INVOICE
        ]
    
    def extract(
        self,
        document: Union[bytes, str],
        feature_types: Optional[List[str]] = None,
        use_async: bool = False,
        **kwargs
    ) -> ExtractionResult:
        """
        Extract text using AWS Textract
        
        Args:
            document: Document bytes or S3 URI (s3://bucket/key)
            feature_types: Textract features ['TABLES', 'FORMS', 'QUERIES']
            use_async: Use async API for large documents
            
        Returns:
            ExtractionResult with extracted text and metadata
        """
        start_time = time.time()
        errors = []
        
        try:
            # Determine if document is S3 URI or bytes
            if isinstance(document, str) and document.startswith('s3://'):
                result = self._extract_from_s3(document, feature_types, use_async)
            else:
                result = self._extract_from_bytes(document, feature_types)
            
            processing_time = time.time() - start_time
            
            # Parse Textract response
            text, confidence, metadata = self._parse_textract_response(result)
            
            return ExtractionResult(
                text=sanitize_extracted_text(text),
                confidence=confidence,
                metadata=metadata,
                pages=metadata.get('page_count', 1),
                processing_time=processing_time,
                extractor_type='textract',
                raw_response=result,
                errors=errors if errors else None
            )
            
        except ClientError as e:
            error_msg = f"AWS Textract error: {e.response['Error']['Message']}"
            logger.error(error_msg)
            errors.append(error_msg)
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error in Textract extraction: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            raise
    
    def _extract_from_bytes(
        self,
        document_bytes: bytes,
        feature_types: Optional[List[str]] = None
    ) -> Dict:
        """Extract text from document bytes (synchronous)"""
        
        # Validate document size (max 5MB for sync API)
        if len(document_bytes) > 5 * 1024 * 1024:
            raise ValueError("Document too large for sync API. Use S3 + async processing.")
        
        params = {
            'Document': {'Bytes': document_bytes}
        }
        
        if feature_types:
            params['FeatureTypes'] = feature_types
            response = self._retry_api_call(
                self.textract_client.analyze_document,
                **params
            )
        else:
            response = self._retry_api_call(
                self.textract_client.detect_document_text,
                **params
            )
        
        return response
    
    def _extract_from_s3(
        self,
        s3_uri: str,
        feature_types: Optional[List[str]] = None,
        use_async: bool = False
    ) -> Dict:
        """Extract text from S3 document"""
        
        # Parse S3 URI
        bucket, key = self._parse_s3_uri(s3_uri)
        
        s3_object = {
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
        
        if use_async:
            return self._extract_async(s3_object, feature_types)
        else:
            params = {'Document': s3_object}
            if feature_types:
                params['FeatureTypes'] = feature_types
                return self._retry_api_call(
                    self.textract_client.analyze_document,
                    **params
                )
            else:
                return self._retry_api_call(
                    self.textract_client.detect_document_text,
                    **params
                )
    
    def _extract_async(
        self,
        s3_object: Dict,
        feature_types: Optional[List[str]] = None
    ) -> Dict:
        """Asynchronous extraction for large documents"""
        
        # Start async job
        if feature_types:
            response = self.textract_client.start_document_analysis(
                DocumentLocation=s3_object,
                FeatureTypes=feature_types
            )
        else:
            response = self.textract_client.start_document_text_detection(
                DocumentLocation=s3_object
            )
        
        job_id = response['JobId']
        logger.info(f"Started async Textract job: {job_id}")
        
        # Poll for completion
        max_wait_time = 300  # 5 minutes
        poll_interval = 5
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            if feature_types:
                status_response = self.textract_client.get_document_analysis(JobId=job_id)
            else:
                status_response = self.textract_client.get_document_text_detection(JobId=job_id)
            
            status = status_response['JobStatus']
            
            if status == 'SUCCEEDED':
                logger.info(f"Async job {job_id} completed successfully")
                return status_response
            elif status == 'FAILED':
                raise RuntimeError(f"Textract job {job_id} failed")
            
            time.sleep(poll_interval)
            elapsed_time += poll_interval
        
        raise TimeoutError(f"Textract job {job_id} timed out after {max_wait_time}s")
    
    def _parse_textract_response(self, response: Dict) -> Tuple[str, float, Dict]:
        """Parse Textract response to extract text, confidence, and metadata"""
        
        text_blocks = []
        confidences = []
        page_count = 0
        tables_count = 0
        forms_count = 0
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
                confidences.append(block.get('Confidence', 0))
            elif block['BlockType'] == 'PAGE':
                page_count += 1
            elif block['BlockType'] == 'TABLE':
                tables_count += 1
            elif block['BlockType'] == 'KEY_VALUE_SET':
                forms_count += 1
        
        text = '\n'.join(text_blocks)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        metadata = {
            'page_count': page_count,
            'tables_count': tables_count,
            'forms_count': forms_count,
            'blocks_count': len(response.get('Blocks', [])),
            'document_metadata': response.get('DocumentMetadata', {})
        }
        
        return text, avg_confidence, metadata
    
    def _parse_s3_uri(self, s3_uri: str) -> Tuple[str, str]:
        """Parse S3 URI into bucket and key"""
        if not s3_uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        
        parts = s3_uri[5:].split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")
        
        return parts[0], parts[1]
    
    def _retry_api_call(self, func, **kwargs):
        """Retry AWS API calls with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return func(**kwargs)
            except ClientError as e:
                if attempt == self.max_retries - 1:
                    raise
                
                error_code = e.response['Error']['Code']
                if error_code in ['ThrottlingException', 'ProvisionedThroughputExceededException']:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Throttled, retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    raise


class TesseractExtractor(TextExtractor):
    """
    Tesseract OCR-based text extractor
    
    Optimized for handwritten documents and low-quality scans.
    Includes image preprocessing for better accuracy.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.tesseract_config = self.config.get('tesseract_config', '--psm 3 --oem 3')
        self.preprocess = self.config.get('preprocess', True)
        self.language = self.config.get('language', 'eng')
    
    def supports_document_type(self, doc_type: DocumentType) -> bool:
        """Tesseract best for handwritten and low-quality images"""
        return doc_type in [
            DocumentType.HANDWRITTEN,
            DocumentType.IMAGE,
            DocumentType.PDF
        ]
    
    def extract(
        self,
        document: Union[bytes, str],
        **kwargs
    ) -> ExtractionResult:
        """
        Extract text using Tesseract OCR
        
        Args:
            document: Image bytes or file path
            
        Returns:
            ExtractionResult with extracted text and metadata
        """
        start_time = time.time()
        errors = []
        
        try:
            # Convert document to images
            images = self._prepare_images(document)
            
            # Extract text from each page/image
            all_text = []
            all_confidence = []
            
            for idx, image in enumerate(images):
                if self.preprocess:
                    image = preprocess_image(image)
                
                # Extract with confidence data
                text_data = pytesseract.image_to_data(
                    image,
                    lang=self.language,
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Filter out low-confidence text
                page_text = []
                page_conf = []
                
                for i in range(len(text_data['text'])):
                    text = text_data['text'][i].strip()
                    conf = int(text_data['conf'][i])
                    
                    if text and conf > 0:
                        page_text.append(text)
                        page_conf.append(conf)
                
                all_text.append(' '.join(page_text))
                all_confidence.extend(page_conf)
            
            combined_text = '\n'.join(all_text)
            avg_confidence = sum(all_confidence) / len(all_confidence) if all_confidence else 0.0
            
            processing_time = time.time() - start_time
            
            metadata = {
                'page_count': len(images),
                'language': self.language,
                'preprocessed': self.preprocess,
                'total_words': len(all_confidence)
            }
            
            return ExtractionResult(
                text=sanitize_extracted_text(combined_text),
                confidence=avg_confidence,
                metadata=metadata,
                pages=len(images),
                processing_time=processing_time,
                extractor_type='tesseract',
                errors=errors if errors else None
            )
            
        except Exception as e:
            error_msg = f"Tesseract extraction error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            raise
    
    def _prepare_images(self, document: Union[bytes, str]) -> List[Image.Image]:
        """Convert document to list of PIL Images"""
        
        if isinstance(document, str):
            # File path
            image = Image.open(document)
            return [image]
        
        elif isinstance(document, bytes):
            # Try to open as image first
            try:
                image = Image.open(io.BytesIO(document))
                return [image]
            except:
                # Try PDF conversion
                try:
                    images = convert_from_bytes(document, dpi=300)
                    return images
                except Exception as e:
                    raise ValueError(f"Unable to process document: {str(e)}")
        
        else:
            raise TypeError(f"Unsupported document type: {type(document)}")


def extract_text_from_document(
    document: Union[bytes, str],
    document_type: DocumentType = DocumentType.PDF,
    prefer_textract: bool = True,
    config: Optional[Dict] = None
) -> ExtractionResult:
    """
    High-level function to extract text from documents
    
    Automatically selects best extractor based on document type.
    Falls back to alternative extractor if primary fails.
    
    Args:
        document: Document bytes or S3 URI
        document_type: Type of document being processed
        prefer_textract: Use Textract as primary extractor if available
        config: Configuration dict for extractors
        
    Returns:
        ExtractionResult with extracted text
        
    Example:
        >>> result = extract_text_from_document(
        ...     document=pdf_bytes,
        ...     document_type=DocumentType.PDF
        ... )
        >>> print(result.text)
        >>> print(f"Confidence: {result.confidence}%")
    """
    
    logger.info(f"Extracting text from {document_type.value} document")
    
    # Initialize extractors
    textract = TextractExtractor(config)
    tesseract = TesseractExtractor(config)
    
    # Select primary and fallback extractors
    if prefer_textract and textract.supports_document_type(document_type):
        primary, fallback = textract, tesseract
    else:
        primary, fallback = tesseract, textract
    
    # Try primary extractor
    try:
        result = primary.extract(document)
        
        # If confidence is too low, try fallback
        if result.confidence < 60.0 and fallback.supports_document_type(document_type):
            logger.warning(
                f"Low confidence ({result.confidence}%) from {primary.__class__.__name__}, "
                f"trying {fallback.__class__.__name__}"
            )
            fallback_result = fallback.extract(document)
            
            # Use result with higher confidence
            if fallback_result.confidence > result.confidence:
                logger.info(f"Using {fallback.__class__.__name__} result (better confidence)")
                return fallback_result
        
        return result
        
    except Exception as e:
        logger.error(f"Primary extractor failed: {str(e)}")
        
        # Try fallback
        if fallback.supports_document_type(document_type):
            logger.info(f"Attempting fallback to {fallback.__class__.__name__}")
            return fallback.extract(document)
        else:
            raise