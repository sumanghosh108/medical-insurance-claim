"""
Utility Functions for Document Processing

Provides helper functions for image processing, text cleaning,
confidence scoring, and other common operations.
"""

import hashlib
import io
import logging
import re
from typing import List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_bytes, convert_from_path
import cv2


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def convert_pdf_to_images(
    pdf_source: Union[bytes, str],
    dpi: int = 300,
    fmt: str = 'PNG'
) -> List[Image.Image]:
    """
    Convert PDF to list of PIL Images
    
    Args:
        pdf_source: PDF bytes or file path
        dpi: Resolution for conversion (higher = better quality)
        fmt: Output format
        
    Returns:
        List of PIL Image objects, one per page
        
    Example:
        >>> images = convert_pdf_to_images(pdf_bytes, dpi=300)
        >>> print(f"Converted {len(images)} pages")
    """
    
    try:
        if isinstance(pdf_source, bytes):
            images = convert_from_bytes(
                pdf_source,
                dpi=dpi,
                fmt=fmt
            )
        else:
            images = convert_from_path(
                pdf_source,
                dpi=dpi,
                fmt=fmt
            )
        
        logger.info(f"Converted PDF to {len(images)} image(s)")
        return images
        
    except Exception as e:
        logger.error(f"Failed to convert PDF: {str(e)}")
        raise


def preprocess_image(
    image: Image.Image,
    enhance_contrast: bool = True,
    denoise: bool = True,
    sharpen: bool = True,
    binarize: bool = False,
    target_size: Optional[Tuple[int, int]] = None
) -> Image.Image:
    """
    Preprocess image for better OCR accuracy
    
    Applies various image enhancement techniques to improve
    text extraction quality.
    
    Args:
        image: PIL Image object
        enhance_contrast: Apply contrast enhancement
        denoise: Apply noise reduction
        sharpen: Apply sharpening filter
        binarize: Convert to black and white (good for clean scans)
        target_size: Resize to (width, height)
        
    Returns:
        Preprocessed PIL Image
        
    Example:
        >>> processed = preprocess_image(
        ...     image,
        ...     enhance_contrast=True,
        ...     denoise=True
        ... )
    """
    
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if specified
        if target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to grayscale for processing
        gray_image = image.convert('L')
        
        # Enhance contrast
        if enhance_contrast:
            enhancer = ImageEnhance.Contrast(gray_image)
            gray_image = enhancer.enhance(1.5)
        
        # Denoise
        if denoise:
            # Convert to numpy for OpenCV processing
            img_array = np.array(gray_image)
            denoised = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
            gray_image = Image.fromarray(denoised)
        
        # Sharpen
        if sharpen:
            gray_image = gray_image.filter(ImageFilter.SHARPEN)
        
        # Binarize (threshold to black and white)
        if binarize:
            img_array = np.array(gray_image)
            _, binary = cv2.threshold(
                img_array,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            gray_image = Image.fromarray(binary)
        
        logger.debug("Image preprocessing completed")
        return gray_image
        
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {str(e)}, returning original")
        return image


def sanitize_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text
    
    Removes extra whitespace, fixes common OCR errors,
    normalizes line breaks, etc.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
        
    Example:
        >>> clean = sanitize_extracted_text(raw_text)
    """
    
    if not text:
        return ""
    
    # Remove null bytes and control characters
    text = text.replace('\x00', '')
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Fix common OCR errors
    replacements = {
        '|': 'I',  # Common misread
        '0': 'O',  # In words (context dependent, simplified here)
        '§': 'S',
        '©': 'C',
        '®': 'R',
    }
    
    # Apply replacements carefully (only when surrounded by letters)
    for old, new in replacements.items():
        text = re.sub(f'(?<=[a-zA-Z]){re.escape(old)}(?=[a-zA-Z])', new, text)
    
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
    text = re.sub(r' *\n *', '\n', text)  # Remove spaces around newlines
    
    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Final trim
    text = text.strip()
    
    return text


def calculate_confidence_score(
    extracted_text: str,
    word_confidences: Optional[List[float]] = None,
    metadata: Optional[dict] = None
) -> float:
    """
    Calculate overall confidence score for extracted text
    
    Considers multiple factors:
    - Individual word confidences
    - Text length and completeness
    - Presence of expected patterns
    - Metadata quality indicators
    
    Args:
        extracted_text: The extracted text
        word_confidences: List of confidence scores per word (0-100)
        metadata: Additional metadata from extraction
        
    Returns:
        Overall confidence score (0-100)
        
    Example:
        >>> score = calculate_confidence_score(
        ...     text="Sample text",
        ...     word_confidences=[95.0, 87.3, 92.1]
        ... )
    """
    
    if not extracted_text:
        return 0.0
    
    # Base score from word confidences
    if word_confidences and len(word_confidences) > 0:
        avg_word_confidence = np.mean(word_confidences)
    else:
        avg_word_confidence = 70.0  # Default assumption
    
    # Text quality factors
    text_length = len(extracted_text)
    word_count = len(extracted_text.split())
    
    # Penalty for very short text
    length_factor = min(1.0, text_length / 100)
    
    # Penalty for lots of special characters (indicates poor OCR)
    special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,!?-]', extracted_text)) / max(text_length, 1)
    special_char_penalty = min(20, special_char_ratio * 100)
    
    # Bonus for well-formed sentences
    sentence_count = len(re.findall(r'[.!?]+', extracted_text))
    sentence_bonus = min(5, sentence_count) if word_count > 10 else 0
    
    # Metadata factors
    metadata_bonus = 0
    if metadata:
        # Bonus for high page count (indicates successful processing)
        page_count = metadata.get('page_count', 1)
        metadata_bonus += min(5, page_count - 1)
        
        # Bonus for detected tables/forms
        if metadata.get('tables_count', 0) > 0:
            metadata_bonus += 3
        if metadata.get('forms_count', 0) > 0:
            metadata_bonus += 3
    
    # Calculate final score
    confidence = (
        avg_word_confidence * length_factor
        - special_char_penalty
        + sentence_bonus
        + metadata_bonus
    )
    
    # Clamp to 0-100 range
    confidence = max(0.0, min(100.0, confidence))
    
    return round(confidence, 2)


def extract_tables_from_image(image: Image.Image) -> List[List[List[str]]]:
    """
    Extract tables from image using simple grid detection
    
    Args:
        image: PIL Image containing tables
        
    Returns:
        List of tables, where each table is a 2D list of cells
        
    Note:
        This is a basic implementation. For production, consider
        using specialized table detection models or AWS Textract's
        table extraction features.
    """
    
    tables = []
    
    try:
        # Convert to OpenCV format
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Detect horizontal and vertical lines
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter for rectangular contours (potential table cells)
        cell_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Minimum cell size
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                if len(approx) == 4:  # Rectangular
                    cell_contours.append(contour)
        
        # Group cells into tables (simplified logic)
        # In production, use more sophisticated clustering
        if len(cell_contours) >= 4:  # At least 2x2 table
            logger.info(f"Detected {len(cell_contours)} potential table cells")
            # Table extraction logic would go here
            # For now, return empty as this is complex to implement generically
        
    except Exception as e:
        logger.warning(f"Table extraction failed: {str(e)}")
    
    return tables


def compute_document_hash(content: bytes) -> str:
    """
    Compute SHA-256 hash of document content
    
    Useful for:
    - Duplicate detection
    - Document integrity verification
    - Change detection
    
    Args:
        content: Document bytes
        
    Returns:
        Hexadecimal hash string
        
    Example:
        >>> hash_val = compute_document_hash(pdf_bytes)
        >>> print(f"Document hash: {hash_val}")
    """
    
    return hashlib.sha256(content).hexdigest()


def split_document_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[str]:
    """
    Split long document into overlapping chunks
    
    Useful for processing with models that have token limits.
    
    Args:
        text: Input text
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
        
    Example:
        >>> chunks = split_document_into_chunks(long_text, chunk_size=500)
    """
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end within last 100 chars
            search_start = max(start, end - 100)
            sentence_end = max(
                text.rfind('. ', search_start, end),
                text.rfind('! ', search_start, end),
                text.rfind('? ', search_start, end)
            )
            
            if sentence_end > start:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def detect_document_language(text: str) -> str:
    """
    Detect language of document text
    
    Args:
        text: Input text
        
    Returns:
        ISO 639-1 language code (e.g., 'en', 'es', 'fr')
        
    Note:
        This is a simplified implementation. For production,
        use a dedicated language detection library like langdetect
        or fasttext.
    """
    
    # Simplified language detection based on common words
    # In production, use proper language detection library
    
    text_lower = text.lower()
    
    # English indicators
    en_words = ['the', 'and', 'is', 'to', 'in', 'of', 'a', 'for', 'on', 'with']
    en_count = sum(f' {word} ' in f' {text_lower} ' for word in en_words)
    
    # Spanish indicators
    es_words = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'por', 'con', 'para']
    es_count = sum(f' {word} ' in f' {text_lower} ' for word in es_words)
    
    # French indicators
    fr_words = ['le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'pour']
    fr_count = sum(f' {word} ' in f' {text_lower} ' for word in fr_words)
    
    # Simple majority vote
    counts = {'en': en_count, 'es': es_count, 'fr': fr_count}
    detected_lang = max(counts, key=counts.get)
    
    logger.debug(f"Detected language: {detected_lang} (confidence: {counts[detected_lang]})")
    
    return detected_lang if counts[detected_lang] > 2 else 'en'  # Default to English


def extract_key_value_pairs(text: str) -> dict:
    """
    Extract key-value pairs from text
    
    Useful for forms and structured documents.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary of key-value pairs
        
    Example:
        >>> pairs = extract_key_value_pairs("Name: John Doe\nPolicy: ABC123")
        >>> print(pairs)  # {'Name': 'John Doe', 'Policy': 'ABC123'}
    """
    
    pairs = {}
    
    # Pattern: "Key: Value" or "Key = Value"
    pattern = r'([A-Z][A-Za-z\s]+?)[:=]\s*(.+?)(?:\n|$)'
    
    matches = re.finditer(pattern, text, re.MULTILINE)
    
    for match in matches:
        key = match.group(1).strip()
        value = match.group(2).strip()
        
        # Clean up key
        key = re.sub(r'\s+', '_', key).lower()
        
        pairs[key] = value
    
    return pairs


def validate_image_quality(
    image: Image.Image,
    min_width: int = 200,
    min_height: int = 200,
    min_dpi: int = 150
) -> Tuple[bool, str]:
    """
    Validate if image quality is sufficient for OCR
    
    Args:
        image: PIL Image
        min_width: Minimum width in pixels
        min_height: Minimum height in pixels
        min_dpi: Minimum DPI (if available in metadata)
        
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        >>> valid, msg = validate_image_quality(image)
        >>> if not valid:
        ...     print(f"Quality issue: {msg}")
    """
    
    width, height = image.size
    
    # Check dimensions
    if width < min_width or height < min_height:
        return False, f"Image too small: {width}x{height} (min: {min_width}x{min_height})"
    
    # Check DPI if available
    dpi = image.info.get('dpi')
    if dpi:
        dpi_value = dpi[0] if isinstance(dpi, tuple) else dpi
        if dpi_value < min_dpi:
            return False, f"DPI too low: {dpi_value} (min: {min_dpi})"
    
    # Check if image is too dark or too light
    img_array = np.array(image.convert('L'))
    mean_brightness = np.mean(img_array)
    
    if mean_brightness < 30:
        return False, "Image too dark for reliable OCR"
    elif mean_brightness > 225:
        return False, "Image too bright/washed out for reliable OCR"
    
    return True, "Image quality acceptable"


def merge_text_blocks(blocks: List[str], separator: str = '\n') -> str:
    """
    Intelligently merge text blocks preserving structure
    
    Args:
        blocks: List of text blocks
        separator: Separator to use between blocks
        
    Returns:
        Merged text
    """
    
    if not blocks:
        return ""
    
    # Remove empty blocks
    blocks = [b.strip() for b in blocks if b and b.strip()]
    
    # Merge with separator
    merged = separator.join(blocks)
    
    # Clean up excessive separators
    merged = re.sub(f'{re.escape(separator)}{{3,}}', separator * 2, merged)
    
    return merged.strip()


# Export commonly used functions
__all__ = [
    'convert_pdf_to_images',
    'preprocess_image',
    'sanitize_extracted_text',
    'calculate_confidence_score',
    'extract_tables_from_image',
    'compute_document_hash',
    'split_document_into_chunks',
    'detect_document_language',
    'extract_key_value_pairs',
    'validate_image_quality',
    'merge_text_blocks',
]