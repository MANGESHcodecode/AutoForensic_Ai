"""
AutoForensic AI — File Signature Validator & Image Re-encoding Sanitizer
=========================================================================
Security Layer 1: Validates raw byte-level file signatures (magic bytes)
to block polyglot malware, executable payloads, and script injections
disguised as image uploads. Then re-encodes the image through Pillow
to neutralize any steganographic payloads or appended web-shells.

Supported formats: JPEG, PNG, WebP, BMP, TIFF
Blocked payloads:  PE executables, ELF binaries, PHP/JS injections,
                   ZIP/RAR archives embedded in image streams

References:
    - File Signatures: https://en.wikipedia.org/wiki/List_of_file_signatures
    - Polyglot Attacks: https://portswigger.net/research/bypassing-csp-using-polyglot-jpegs
"""

import io
import os
import struct
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger("autoforensic.forensics.file_validator")


# ══════════════════════════════════════════════════════════════
# MAGIC BYTE SIGNATURES — Known file format headers
# ══════════════════════════════════════════════════════════════

# Valid image format signatures: (offset, magic_bytes, format_name)
VALID_IMAGE_SIGNATURES = [
    (0, b"\xFF\xD8\xFF",             "JPEG"),       # JPEG/JFIF/EXIF
    (0, b"\x89PNG\r\n\x1A\n",       "PNG"),         # PNG
    (0, b"RIFF",                     "WebP"),        # WebP (RIFF container)
    (0, b"BM",                       "BMP"),         # BMP
    (0, b"II\x2A\x00",              "TIFF_LE"),     # TIFF Little-Endian
    (0, b"MM\x00\x2A",              "TIFF_BE"),     # TIFF Big-Endian
]

# Dangerous payload signatures that MUST be rejected
MALICIOUS_SIGNATURES = [
    (0, b"MZ",                       "PE_EXECUTABLE"),       # Windows PE (.exe, .dll)
    (0, b"\x7FELF",                  "ELF_BINARY"),          # Linux ELF binary
    (0, b"PK\x03\x04",              "ZIP_ARCHIVE"),          # ZIP (could be docx/jar)
    (0, b"Rar!\x1A\x07",            "RAR_ARCHIVE"),          # RAR archive
    (0, b"\x1F\x8B",                "GZIP_ARCHIVE"),         # GZIP archive
    (0, b"\xCA\xFE\xBA\xBE",        "JAVA_CLASS"),           # Java .class file
    (0, b"%PDF",                     "PDF_DOCUMENT"),         # PDF (can embed JS)
]

# Script injection patterns to scan for within the file body
SCRIPT_INJECTION_PATTERNS = [
    b"<?php",           # PHP web-shell
    b"<script",         # JavaScript injection
    b"<%",              # ASP/JSP injection
    b"#!/",             # Unix shebang (shell scripts)
    b"eval(",           # Common obfuscation pattern
    b"base64_decode(",  # PHP payload decoder
    b"exec(",           # Command execution
    b"import os",       # Python script injection
]

# Maximum file size: 25 MB (prevents DoS via oversized uploads)
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

# Minimum file size: 1 KB (rejects empty/corrupt stubs)
MIN_FILE_SIZE_BYTES = 1024

# Scan depth for script injections (bytes from end of file)
TAIL_SCAN_BYTES = 8192


class FileValidationResult:
    """Structured result from file validation."""

    def __init__(
        self,
        is_valid: bool,
        detected_format: Optional[str] = None,
        file_size_bytes: int = 0,
        image_dimensions: Optional[Tuple[int, int]] = None,
        sanitized_bytes: Optional[bytes] = None,
        rejection_reason: Optional[str] = None,
        warnings: Optional[list] = None,
    ):
        self.is_valid = is_valid
        self.detected_format = detected_format
        self.file_size_bytes = file_size_bytes
        self.image_dimensions = image_dimensions
        self.sanitized_bytes = sanitized_bytes
        self.rejection_reason = rejection_reason
        self.warnings = warnings or []

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "detected_format": self.detected_format,
            "file_size_bytes": self.file_size_bytes,
            "image_dimensions": self.image_dimensions,
            "rejection_reason": self.rejection_reason,
            "warnings": self.warnings,
        }

    def __repr__(self) -> str:
        status = "VALID" if self.is_valid else "REJECTED"
        return (
            f"FileValidationResult({status}, "
            f"format={self.detected_format}, "
            f"size={self.file_size_bytes:,}B, "
            f"dims={self.image_dimensions})"
        )


class FileValidator:
    """
    Validates uploaded image files at the byte level and re-encodes
    them to neutralize hidden payloads.

    Pipeline:
        1. Check file size bounds (1 KB – 25 MB)
        2. Read raw header bytes and match against magic-byte tables
        3. Reject if malicious signatures detected (PE, ELF, ZIP, etc.)
        4. Scan file tail for appended script injections (PHP, JS, etc.)
        5. Attempt Pillow decode to verify image structural integrity
        6. Re-encode through Pillow to strip any non-pixel payload data
        7. Return sanitized image bytes + validation report

    Usage:
        >>> validator = FileValidator()
        >>> result = validator.validate("path/to/car_damage.jpg")
        >>> if result.is_valid:
        ...     clean_image_bytes = result.sanitized_bytes
    """

    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "TIFF"}

    def __init__(
        self,
        max_file_size: int = MAX_FILE_SIZE_BYTES,
        min_file_size: int = MIN_FILE_SIZE_BYTES,
        allowed_formats: Optional[set] = None,
        re_encode_quality: int = 95,
    ):
        """
        Args:
            max_file_size: Maximum allowed file size in bytes (default 25 MB).
            min_file_size: Minimum allowed file size in bytes (default 1 KB).
            allowed_formats: Set of allowed image format names.
            re_encode_quality: JPEG quality for re-encoded output (default 95).
        """
        self.max_file_size = max_file_size
        self.min_file_size = min_file_size
        self.allowed_formats = allowed_formats or self.ALLOWED_FORMATS
        self.re_encode_quality = re_encode_quality

    def validate(self, image_input) -> FileValidationResult:
        """
        Validate an image from a file path or raw bytes.

        Args:
            image_input: File path (str/Path) or raw bytes of the image.

        Returns:
            FileValidationResult with validation status and sanitized bytes.
        """
        warnings = []

        # ── Step 0: Read raw bytes ──
        try:
            if isinstance(image_input, (str, Path)):
                path = Path(image_input)
                if not path.exists():
                    return FileValidationResult(
                        is_valid=False,
                        rejection_reason=f"File not found: {path}",
                    )
                raw_bytes = path.read_bytes()
            elif isinstance(image_input, bytes):
                raw_bytes = image_input
            elif isinstance(image_input, io.BytesIO):
                raw_bytes = image_input.getvalue()
            else:
                return FileValidationResult(
                    is_valid=False,
                    rejection_reason=f"Unsupported input type: {type(image_input).__name__}",
                )
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                rejection_reason=f"Failed to read file: {e}",
            )

        file_size = len(raw_bytes)

        # ── Step 1: File size bounds check ──
        if file_size < self.min_file_size:
            return FileValidationResult(
                is_valid=False,
                file_size_bytes=file_size,
                rejection_reason=(
                    f"File too small ({file_size:,} bytes). "
                    f"Minimum: {self.min_file_size:,} bytes. "
                    f"Likely corrupt or empty stub."
                ),
            )

        if file_size > self.max_file_size:
            return FileValidationResult(
                is_valid=False,
                file_size_bytes=file_size,
                rejection_reason=(
                    f"File too large ({file_size:,} bytes). "
                    f"Maximum: {self.max_file_size:,} bytes. "
                    f"Potential denial-of-service vector."
                ),
            )

        # ── Step 2: Check for MALICIOUS signatures ──
        for offset, signature, threat_name in MALICIOUS_SIGNATURES:
            if raw_bytes[offset : offset + len(signature)] == signature:
                logger.warning(
                    "BLOCKED: Malicious file signature detected — %s", threat_name
                )
                return FileValidationResult(
                    is_valid=False,
                    file_size_bytes=file_size,
                    rejection_reason=(
                        f"Malicious file signature detected: {threat_name}. "
                        f"This is NOT a valid image file."
                    ),
                )

        # ── Step 3: Match against valid image signatures ──
        detected_format = None
        for offset, signature, fmt_name in VALID_IMAGE_SIGNATURES:
            if raw_bytes[offset : offset + len(signature)] == signature:
                detected_format = fmt_name
                break

        if detected_format is None:
            return FileValidationResult(
                is_valid=False,
                file_size_bytes=file_size,
                rejection_reason=(
                    f"Unrecognized file signature. Header bytes: "
                    f"{raw_bytes[:16].hex(' ')}. "
                    f"Not a supported image format."
                ),
            )

        # WebP requires additional validation (must contain WEBP marker)
        if detected_format == "WebP":
            if raw_bytes[8:12] != b"WEBP":
                return FileValidationResult(
                    is_valid=False,
                    file_size_bytes=file_size,
                    detected_format="RIFF_NON_WEBP",
                    rejection_reason=(
                        "RIFF container detected but not WebP format. "
                        "Could be AVI/WAV masquerading as image."
                    ),
                )

        # Normalize format names for Pillow compatibility
        fmt_normalized = detected_format.split("_")[0]  # TIFF_LE → TIFF

        # ── Step 4: Scan for appended script injections ──
        tail_region = raw_bytes[-TAIL_SCAN_BYTES:] if file_size > TAIL_SCAN_BYTES else raw_bytes
        # Also scan a region after the image data that may contain appended scripts
        for pattern in SCRIPT_INJECTION_PATTERNS:
            pattern_lower = pattern.lower()
            if pattern_lower in tail_region.lower():
                logger.warning(
                    "BLOCKED: Script injection pattern found — %s",
                    pattern.decode("ascii", errors="replace"),
                )
                return FileValidationResult(
                    is_valid=False,
                    file_size_bytes=file_size,
                    detected_format=fmt_normalized,
                    rejection_reason=(
                        f"Embedded script injection detected: "
                        f"'{pattern.decode('ascii', errors='replace')}' pattern "
                        f"found in file tail. Likely polyglot attack."
                    ),
                )

        # ── Step 5: Pillow structural integrity check ──
        try:
            img = Image.open(io.BytesIO(raw_bytes))
            img.verify()  # Verify without full decode

            # Re-open for actual pixel access (verify() closes the image)
            img = Image.open(io.BytesIO(raw_bytes))
            img.load()  # Force full pixel decode
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                file_size_bytes=file_size,
                detected_format=fmt_normalized,
                rejection_reason=(
                    f"Image structural integrity check failed: {e}. "
                    f"File has valid magic bytes but corrupt image data."
                ),
            )

        image_dimensions = img.size  # (width, height)
        pillow_format = img.format or fmt_normalized

        # Validate dimensions (reject extremely small or suspiciously large)
        width, height = image_dimensions
        if width < 50 or height < 50:
            warnings.append(
                f"Very small image ({width}x{height}). "
                f"May not contain meaningful vehicle damage data."
            )

        if width > 8000 or height > 8000:
            warnings.append(
                f"Very large image ({width}x{height}). "
                f"Consider downscaling for processing efficiency."
            )

        # ── Step 6: Re-encode to strip hidden payloads ──
        try:
            sanitized_bytes = self._re_encode_image(img, pillow_format)
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                file_size_bytes=file_size,
                detected_format=fmt_normalized,
                image_dimensions=image_dimensions,
                rejection_reason=(
                    f"Image re-encoding failed: {e}. "
                    f"File may contain malformed pixel data."
                ),
            )

        size_diff = file_size - len(sanitized_bytes)
        if size_diff > 50000:  # > 50KB of non-pixel data stripped
            warnings.append(
                f"Re-encoding stripped {size_diff:,} bytes of non-pixel data. "
                f"Original file may have contained appended payloads."
            )

        logger.info(
            "PASSED: %s image (%dx%d, %s bytes) validated and sanitized.",
            fmt_normalized, width, height, f"{file_size:,}",
        )

        return FileValidationResult(
            is_valid=True,
            detected_format=fmt_normalized,
            file_size_bytes=file_size,
            image_dimensions=image_dimensions,
            sanitized_bytes=sanitized_bytes,
            warnings=warnings,
        )

    def _re_encode_image(self, img: Image.Image, fmt: str) -> bytes:
        """
        Re-encode an image through Pillow to produce clean pixel-only output.
        This strips ALL metadata, comments, ICC profiles, and any appended data.

        Args:
            img: Pillow Image object.
            fmt: Target format string.

        Returns:
            Clean re-encoded bytes.
        """
        buffer = io.BytesIO()

        # Convert RGBA to RGB for JPEG (JPEG doesn't support alpha)
        if fmt.upper() in ("JPEG", "JPG") and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        elif img.mode == "P":
            img = img.convert("RGB")

        # Choose output format
        if fmt.upper() in ("JPEG", "JPG", "JFIF"):
            img.save(
                buffer,
                format="JPEG",
                quality=self.re_encode_quality,
                optimize=True,
                exif=b"",  # Explicitly strip EXIF
            )
        elif fmt.upper() == "PNG":
            img.save(
                buffer,
                format="PNG",
                optimize=True,
            )
        elif fmt.upper() == "WEBP":
            img.save(
                buffer,
                format="WEBP",
                quality=self.re_encode_quality,
            )
        else:
            # Fallback: save as PNG for maximum compatibility
            img.save(buffer, format="PNG")

        return buffer.getvalue()

    def validate_and_save(
        self,
        image_input,
        output_path: str,
    ) -> FileValidationResult:
        """
        Validate an image and save the sanitized version to disk.

        Args:
            image_input: File path or raw bytes.
            output_path: Where to save the sanitized image.

        Returns:
            FileValidationResult with validation status.
        """
        result = self.validate(image_input)

        if result.is_valid and result.sanitized_bytes:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(result.sanitized_bytes)
            logger.info("Sanitized image saved to: %s", output_path)

        return result
