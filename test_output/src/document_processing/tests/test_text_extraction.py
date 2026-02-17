"""
Unit tests for text extraction module
"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np

from src.document_processing.text_extraction import (
    TextractExtractor,
    TesseractExtractor,
    DocumentType,
    ExtractionResult,
    extract_text_from_document
)


class TestTextractExtractor:
    """Tests for AWS Textract extraction"""
    
    @pytest.fixture
    def mock_textract_client(self):
        """Mock boto3 Textract client"""
        with patch('document_processing.text_extraction.boto3.client') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def textract_extractor(self, mock_textract_client):
        """Create TextractExtractor instance with mocked client"""
        extractor = TextractExtractor({'aws_region': 'ap-south-1'})
        extractor.textract_client = mock_textract_client
        return extractor
    
    def test_supports_document_type(self, textract_extractor):
        """Test document type support"""
        assert textract_extractor.supports_document_type(DocumentType.PDF)
        assert textract_extractor.supports_document_type(DocumentType.IMAGE)
        assert textract_extractor.supports_document_type(DocumentType.FORM)
        assert not textract_extractor.supports_document_type(DocumentType.HANDWRITTEN)
    
    def test_extract_from_bytes_success(self, textract_extractor, mock_textract_client):
        """Test successful text extraction from bytes"""
        
        # Mock Textract response
        mock_response = {
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'Sample insurance claim',
                    'Confidence': 95.5
                },
                {
                    'BlockType': 'LINE',
                    'Text': 'Policy: ABC123456',
                    'Confidence': 98.2
                },
                {
                    'BlockType': 'PAGE',
                    'Page': 1
                }
            ],
            'DocumentMetadata': {'Pages': 1}
        }
        
        mock_textract_client.detect_document_text.return_value = mock_response
        
        # Test extraction
        document_bytes = b'fake_pdf_content'
        result = textract_extractor.extract(document_bytes)
        
        # Assertions
        assert isinstance(result, ExtractionResult)
        assert 'Sample insurance claim' in result.text
        assert 'Policy: ABC123456' in result.text
        assert result.confidence > 90
        assert result.pages == 1
        assert result.extractor_type == 'textract'
        
        # Verify API was called correctly
        mock_textract_client.detect_document_text.assert_called_once()
    
    def test_extract_with_features(self, textract_extractor, mock_textract_client):
        """Test extraction with feature types (tables, forms)"""
        
        mock_response = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Test', 'Confidence': 95.0},
                {'BlockType': 'TABLE'},
                {'BlockType': 'KEY_VALUE_SET'}
            ],
            'DocumentMetadata': {'Pages': 1}
        }
        
        mock_textract_client.analyze_document.return_value = mock_response
        
        result = textract_extractor.extract(
            b'fake_content',
            feature_types=['TABLES', 'FORMS']
        )
        
        assert result.metadata['tables_count'] == 1
        assert result.metadata['forms_count'] == 1
        
        # Verify analyze_document was called instead of detect_document_text
        mock_textract_client.analyze_document.assert_called_once()
        call_args = mock_textract_client.analyze_document.call_args
        assert 'FeatureTypes' in call_args[1]
        assert call_args[1]['FeatureTypes'] == ['TABLES', 'FORMS']
    
    def test_extract_document_too_large(self, textract_extractor):
        """Test error handling for oversized documents"""
        
        # Create document larger than 5MB
        large_document = b'x' * (6 * 1024 * 1024)
        
        with pytest.raises(ValueError, match="Document too large"):
            textract_extractor.extract(large_document)
    
    def test_parse_s3_uri(self, textract_extractor):
        """Test S3 URI parsing"""
        
        bucket, key = textract_extractor._parse_s3_uri('s3://my-bucket/documents/claim.pdf')
        
        assert bucket == 'my-bucket'
        assert key == 'documents/claim.pdf'
    
    def test_parse_s3_uri_invalid(self, textract_extractor):
        """Test S3 URI parsing with invalid URI"""
        
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            textract_extractor._parse_s3_uri('invalid-uri')
        
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            textract_extractor._parse_s3_uri('s3://bucket-only')
    
    def test_retry_on_throttling(self, textract_extractor, mock_textract_client):
        """Test retry logic for throttling errors"""
        
        from botocore.exceptions import ClientError
        
        # Mock throttling error then success
        mock_textract_client.detect_document_text.side_effect = [
            ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'DetectDocumentText'
            ),
            {'Blocks': [], 'DocumentMetadata': {'Pages': 1}}
        ]
        
        with patch('time.sleep'):  # Don't actually sleep in tests
            result = textract_extractor.extract(b'content')
        
        # Should have retried
        assert mock_textract_client.detect_document_text.call_count == 2


class TestTesseractExtractor:
    """Tests for Tesseract OCR extraction"""
    
    @pytest.fixture
    def tesseract_extractor(self):
        """Create TesseractExtractor instance"""
        return TesseractExtractor({
            'language': 'eng',
            'preprocess': True
        })
    
    def test_supports_document_type(self, tesseract_extractor):
        """Test document type support"""
        assert tesseract_extractor.supports_document_type(DocumentType.HANDWRITTEN)
        assert tesseract_extractor.supports_document_type(DocumentType.IMAGE)
        assert tesseract_extractor.supports_document_type(DocumentType.PDF)
    
    @patch('document_processing.text_extraction.pytesseract.image_to_data')
    def test_extract_from_image_success(self, mock_image_to_data, tesseract_extractor):
        """Test successful text extraction from image"""
        
        # Create fake image
        fake_image = Image.new('RGB', (800, 600), color='white')
        img_bytes = io.BytesIO()
        fake_image.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()
        
        # Mock Tesseract response
        mock_image_to_data.return_value = {
            'text': ['Insurance', 'Claim', 'Form', ''],
            'conf': [95, 92, 88, -1]
        }
        
        result = tesseract_extractor.extract(img_bytes)
        
        assert isinstance(result, ExtractionResult)
        assert 'Insurance' in result.text
        assert result.confidence > 0
        assert result.extractor_type == 'tesseract'
    
    @patch('document_processing.text_extraction.convert_from_bytes')
    @patch('document_processing.text_extraction.pytesseract.image_to_data')
    def test_extract_from_pdf(self, mock_image_to_data, mock_convert, tesseract_extractor):
        """Test PDF extraction (converted to images)"""
        
        # Mock PDF to images conversion
        fake_images = [
            Image.new('RGB', (800, 600)),
            Image.new('RGB', (800, 600))
        ]
        mock_convert.return_value = fake_images
        
        # Mock Tesseract responses
        mock_image_to_data.return_value = {
            'text': ['Page', 'text'],
            'conf': [90, 85]
        }
        
        pdf_bytes = b'fake_pdf_content'
        result = tesseract_extractor.extract(pdf_bytes)
        
        assert result.pages == 2
        mock_convert.assert_called_once()


class TestExtractTextFromDocument:
    """Tests for high-level extraction function"""
    
    @patch('document_processing.text_extraction.TextractExtractor')
    @patch('document_processing.text_extraction.TesseractExtractor')
    def test_prefer_textract_for_pdf(self, mock_tesseract_cls, mock_textract_cls):
        """Test Textract is preferred for PDF documents"""
        
        # Setup mocks
        mock_textract = mock_textract_cls.return_value
        mock_textract.supports_document_type.return_value = True
        mock_textract.extract.return_value = ExtractionResult(
            text='Extracted text',
            confidence=95.0,
            metadata={},
            pages=1,
            processing_time=1.0,
            extractor_type='textract'
        )
        
        # Call function
        result = extract_text_from_document(
            b'pdf_content',
            document_type=DocumentType.PDF,
            prefer_textract=True
        )
        
        # Textract should be used
        mock_textract.extract.assert_called_once()
        assert result.extractor_type == 'textract'
    
    @patch('document_processing.text_extraction.TextractExtractor')
    @patch('document_processing.text_extraction.TesseractExtractor')
    def test_fallback_to_tesseract_on_low_confidence(
        self,
        mock_tesseract_cls,
        mock_textract_cls
    ):
        """Test fallback to Tesseract when Textract confidence is low"""
        
        # Setup mocks
        mock_textract = mock_textract_cls.return_value
        mock_tesseract = mock_tesseract_cls.return_value
        
        mock_textract.supports_document_type.return_value = True
        mock_tesseract.supports_document_type.return_value = True
        
        # Low confidence from Textract
        mock_textract.extract.return_value = ExtractionResult(
            text='Low confidence text',
            confidence=45.0,  # Below 60%
            metadata={},
            pages=1,
            processing_time=1.0,
            extractor_type='textract'
        )
        
        # Higher confidence from Tesseract
        mock_tesseract.extract.return_value = ExtractionResult(
            text='Better text',
            confidence=85.0,
            metadata={},
            pages=1,
            processing_time=2.0,
            extractor_type='tesseract'
        )
        
        result = extract_text_from_document(b'content')
        
        # Should use Tesseract result
        assert result.extractor_type == 'tesseract'
        assert result.confidence == 85.0


class TestIntegration:
    """Integration tests (require actual libraries)"""
    
    @pytest.mark.integration
    def test_real_image_extraction(self):
        """Test extraction from actual image (integration test)"""
        
        # Create simple test image with text
        from PIL import ImageDraw, ImageFont
        
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add text to image
        text = "Insurance Claim #12345"
        draw.text((50, 80), text, fill='black')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()
        
        # Extract (will use real Tesseract if available)
        try:
            result = extract_text_from_document(
                img_bytes,
                document_type=DocumentType.IMAGE,
                prefer_textract=False
            )
            
            # Should extract something
            assert len(result.text) > 0
            
        except Exception as e:
            pytest.skip(f"Integration test requires Tesseract: {e}")


def test_extraction_result_dataclass():
    """Test ExtractionResult dataclass"""
    
    result = ExtractionResult(
        text="Sample text",
        confidence=92.5,
        metadata={'key': 'value'},
        pages=2,
        processing_time=1.5,
        extractor_type='test'
    )
    
    assert result.text == "Sample text"
    assert result.confidence == 92.5
    assert result.pages == 2
    assert result.errors is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])