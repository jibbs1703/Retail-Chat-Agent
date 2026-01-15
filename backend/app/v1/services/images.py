"""Image processing utilities."""

import io
from typing import BinaryIO

from PIL import Image

from backend.app.v1.core.configurations import get_settings

settings = get_settings()


class ImageValidationError(Exception):
    """Exception raised for image validation errors.

    Attributes:
        message (str): Human-readable error message.
        error_type (str): Category of the error (format, size, decode, etc).
        details (dict): Additional error details for logging/debugging.
    """

    def __init__(
        self,
        message: str,
        error_type: str = "validation",
        details: dict = None,
    ):
        """Initialize ImageValidationError.

        Args:
            message: Human-readable error message.
            error_type: Category of error. Defaults to "validation".
            details: Additional context about the error.
        """
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses.

        Returns:
            dict: Error information in dictionary format.
        """
        return {
            "error": self.message,
            "error_type": self.error_type,
            "details": self.details,
        }

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return f"ImageValidationError(type={self.error_type}, message={self.message})"


def decode_image(data: bytes | BinaryIO) -> Image.Image:
    """Decode image data into a PIL Image.

    Args:
        data: Image data as bytes or file-like object.

    Returns:
        Image.Image: Decoded PIL Image in RGB mode.

    Raises:
        ImageValidationError: If image cannot be decoded.
    """
    try:
        if isinstance(data, bytes):
            data = io.BytesIO(data)

        image = Image.open(data)
        if image.format and image.format.upper() not in settings.supported_image_formats:
            raise ImageValidationError(
                f"Unsupported image format: {image.format}. "
                f"Supported: {', '.join(settings.supported_image_formats)}",
                error_type="unsupported_format",
                details={
                    "format": image.format,
                    "supported": list(settings.supported_image_formats),
                },
            )
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image
    except ImageValidationError:
        raise
    except Exception as e:
        raise ImageValidationError(
            f"Failed to decode image: {str(e)}",
            error_type="decode_error",
            details={"exception": type(e).__name__},
        ) from e


def validate_image(image: Image.Image, max_size: int = None) -> None:
    """Validate an image for processing.

    Args:
        image: PIL Image to validate.
        max_size: Maximum allowed dimension size. Defaults to settings.max_image_size.

    Raises:
        ImageValidationError: If image fails validation.
    """
    if max_size is None:
        max_size = settings.max_image_size

    if not isinstance(image, Image.Image):
        raise ImageValidationError(
            "Input must be a PIL Image object",
            error_type="invalid_type",
            details={"received_type": type(image).__name__},
        )

    width, height = image.size

    if width < 1 or height < 1:
        raise ImageValidationError(
            f"Invalid image size: {width}x{height}",
            error_type="invalid_size",
            details={"width": width, "height": height},
        )

    if width > max_size or height > max_size:
        raise ImageValidationError(
            f"Image too large: {width}x{height}. Max size: {max_size}x{max_size}",
            error_type="size_exceeded",
            details={
                "width": width,
                "height": height,
                "max_size": max_size,
            },
        )


def resize_image(image: Image.Image, max_size: int = None) -> Image.Image:
    """Resize image if it exceeds max size while maintaining aspect ratio.

    Args:
        image: PIL Image to resize.
        max_size: Maximum dimension size. Defaults to settings.max_image_size.

    Returns:
        Image.Image: Resized image (or original if within size).
    """
    if max_size is None:
        max_size = settings.max_image_size

    width, height = image.size

    if width <= max_size and height <= max_size:
        return image

    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized


def process_image(data: bytes | BinaryIO, max_size: int = None) -> Image.Image:
    """Complete image processing pipeline: decode, validate, and resize.

    This is the main entry point for image processing throughout the application.
    It handles all image preparation steps for embedding generation.

    Args:
        data: Image data as bytes or file-like object.
        max_size: Maximum dimension size for resizing. Defaults to settings.max_image_size.

    Returns:
        Image.Image: Processed PIL Image ready for embedding.

    Raises:
        ImageValidationError: If image processing fails at any step.
    """
    if max_size is None:
        max_size = settings.max_image_size

    try:
        image = decode_image(data)
        validate_image(image, max_size)
        resized = resize_image(image, max_size)
        return resized
    except ImageValidationError:
        raise
    except Exception as e:
        raise ImageValidationError(
            f"Image processing failed: {str(e)}",
            error_type="processing_error",
            details={"exception": type(e).__name__},
        ) from e


def get_image_info(image: Image.Image) -> dict:
    """Get detailed information about an image.

    Useful for debugging, logging, and understanding image properties.

    Args:
        image: PIL Image to inspect.

    Returns:
        dict: Image information including dimensions, mode, format, and aspect ratio.
    """
    width, height = image.size
    aspect_ratio = width / height if height > 0 else 0
    return {
        "width": width,
        "height": height,
        "aspect_ratio": round(aspect_ratio, 2),
        "size": (width, height),
        "mode": image.mode,
        "format": image.format,
    }
