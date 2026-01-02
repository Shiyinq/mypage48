"""
Image validation utilities for base64 encoded images.
Validates MIME types and magic bytes to ensure uploaded content is a valid image.
"""
import base64
import imghdr
from typing import Optional, Tuple

# Maximum file size in bytes (3 MB)
MAX_IMAGE_SIZE_BYTES = 3 * 1024 * 1024

# Allowed MIME types and their corresponding magic bytes identifiers
ALLOWED_MIME_TYPES = frozenset([
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
])

# Valid data URL prefixes
VALID_DATA_URL_PREFIXES = (
    "data:image/jpeg;base64,",
    "data:image/jpg;base64,",
    "data:image/png;base64,",
    "data:image/gif;base64,",
    "data:image/webp;base64,",
)


class ImageValidationError(Exception):
    """Raised when image validation fails."""
    pass


class ImageTooLargeError(ImageValidationError):
    """Raised when image exceeds maximum size."""
    def __init__(self, size_bytes: int):
        self.size_bytes = size_bytes
        super().__init__(f"Image size {size_bytes} bytes exceeds maximum allowed {MAX_IMAGE_SIZE_BYTES} bytes")


class InvalidImageTypeError(ImageValidationError):
    """Raised when image type is not allowed."""
    def __init__(self, detected_type: Optional[str] = None):
        self.detected_type = detected_type
        msg = f"Invalid image type: {detected_type}" if detected_type else "Invalid image type"
        super().__init__(msg)


class InvalidBase64Error(ImageValidationError):
    """Raised when base64 string is malformed."""
    pass


def _extract_base64_data(data_url: str) -> Tuple[str, str]:
    """
    Extract the base64 data and MIME type from a data URL.
    
    Args:
        data_url: A data URL string (e.g., "data:image/png;base64,...")
        
    Returns:
        Tuple of (base64_data, mime_type)
        
    Raises:
        InvalidBase64Error: If the data URL format is invalid
    """
    if not data_url:
        raise InvalidBase64Error("Empty data URL")
    
    # Check if it's a valid data URL
    if not data_url.startswith("data:"):
        raise InvalidBase64Error("Invalid data URL: must start with 'data:'")
    
    # Find the comma separator
    comma_index = data_url.find(",")
    if comma_index == -1:
        raise InvalidBase64Error("Invalid data URL: missing base64 data separator")
    
    # Extract header and data
    header = data_url[:comma_index]
    base64_data = data_url[comma_index + 1:]
    
    if not base64_data:
        raise InvalidBase64Error("Empty base64 data")
    
    # Parse MIME type from header (e.g., "data:image/png;base64")
    # Remove "data:" prefix
    header_content = header[5:]
    
    # Split by semicolon to get MIME type
    parts = header_content.split(";")
    if not parts:
        raise InvalidBase64Error("Invalid data URL: missing MIME type")
    
    mime_type = parts[0].lower()
    
    # Normalize jpg to jpeg
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
    
    return base64_data, mime_type


def _decode_base64(base64_data: str) -> bytes:
    """
    Decode base64 string to bytes.
    
    Raises:
        InvalidBase64Error: If decoding fails
    """
    try:
        return base64.b64decode(base64_data)
    except Exception as e:
        raise InvalidBase64Error(f"Failed to decode base64 data: {str(e)}")


def _detect_image_type(image_bytes: bytes) -> Optional[str]:
    """
    Detect the image type from magic bytes.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Image type string (e.g., 'jpeg', 'png') or None if not recognized
    """
    # Use imghdr to detect image type from magic bytes
    img_type = imghdr.what(None, h=image_bytes)
    
    # Additional check for WebP (imghdr doesn't detect it)
    if img_type is None and len(image_bytes) >= 12:
        # WebP files start with "RIFF" followed by file size, then "WEBP"
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "webp"
    
    return img_type


def validate_base64_image(data_url: str) -> bytes:
    """
    Validate a base64-encoded image and return the decoded bytes.
    
    This function performs the following validations:
    1. Validates the data URL format
    2. Checks that the MIME type is allowed
    3. Decodes the base64 data
    4. Checks the file size against the maximum allowed
    5. Validates the actual image content using magic bytes
    
    Args:
        data_url: A data URL string (e.g., "data:image/png;base64,...")
        
    Returns:
        The decoded image bytes if validation passes
        
    Raises:
        InvalidBase64Error: If the data URL or base64 encoding is invalid
        InvalidImageTypeError: If the image type is not allowed
        ImageTooLargeError: If the image exceeds the maximum size
    """
    # Extract base64 data and MIME type
    base64_data, declared_mime = _extract_base64_data(data_url)
    
    # Check declared MIME type
    if declared_mime not in ALLOWED_MIME_TYPES:
        raise InvalidImageTypeError(declared_mime)
    
    # Decode base64
    image_bytes = _decode_base64(base64_data)
    
    # Check size
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ImageTooLargeError(len(image_bytes))
    
    # Validate actual content using magic bytes
    detected_type = _detect_image_type(image_bytes)
    
    if detected_type is None:
        raise InvalidImageTypeError(None)
    
    # Map detected type to MIME type for comparison
    detected_mime = f"image/{detected_type}"
    
    # Normalize jpg to jpeg
    if detected_mime == "image/jpg":
        detected_mime = "image/jpeg"
    
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise InvalidImageTypeError(detected_mime)
    
    return image_bytes


def is_valid_base64_image(data_url: str) -> bool:
    """
    Check if a data URL contains a valid image.
    
    Args:
        data_url: A data URL string
        
    Returns:
        True if the image is valid, False otherwise
    """
    try:
        validate_base64_image(data_url)
        return True
    except ImageValidationError:
        return False
