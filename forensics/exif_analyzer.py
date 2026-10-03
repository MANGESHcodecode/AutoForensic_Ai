"""
AutoForensic AI — EXIF Metadata Forensic Analyzer
===================================================
Security Layer 2: Extracts and analyzes EXIF (Exchangeable Image File Format)
metadata embedded in uploaded vehicle images to detect signs of digital
manipulation, AI-generated synthetic images, or web-scraped fraud submissions.

Detection Capabilities:
    - Editing software fingerprints (Photoshop, GIMP, Canva, PicsArt, etc.)
    - AI image generator traces (DALL-E, Midjourney, Stable Diffusion metadata)
    - Missing hardware metadata (no camera make/model = suspicious)
    - Timestamp inconsistencies (creation vs modification mismatch)
    - GPS geolocation extraction (for location verification)

Implementation:
    Uses Pillow's built-in EXIF parser — no external dependencies required.
    EXIF tag IDs follow the EXIF 2.32 / TIFF 6.0 specification.

References:
    - EXIF Standard: https://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf
    - EXIF Tag Reference: https://exiv2.org/tags.html
"""

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = logging.getLogger("autoforensic.forensics.exif_analyzer")


# ══════════════════════════════════════════════════════════════
# KNOWN EDITING SOFTWARE SIGNATURES
# ══════════════════════════════════════════════════════════════
# If any of these substrings appear in the EXIF 'Software' or
# 'ProcessingSoftware' tags, the image is flagged as edited.

EDITING_SOFTWARE_SIGNATURES = [
    # Professional editors
    "photoshop", "adobe", "lightroom", "camera raw",
    "capture one", "affinity photo", "darktable",
    # Consumer / mobile editors
    "gimp", "paint.net", "canva", "picsart", "snapseed",
    "pixlr", "fotor", "befunky", "inshot", "vsco",
    "prisma", "facetune", "remini", "photoroom",
    "remove.bg", "inpaint", "luminar",
    # Screenshot / screen capture tools
    "screenshot", "snipping", "greenshot", "sharex",
    "lightshot", "gyazo",
    # AI image generators
    "dall-e", "dalle", "midjourney", "stable diffusion",
    "comfyui", "automatic1111", "invoke ai", "novelai",
    "leonardo.ai", "ideogram", "firefly",
    # Generic indicators
    "edited", "modified", "processed", "enhanced",
]

# Key EXIF tag IDs (decimal) we want to extract
EXIF_TAG_IDS = {
    "Make":                 0x010F,
    "Model":                0x0110,
    "Software":             0x0131,
    "DateTime":             0x0132,
    "DateTimeOriginal":     0x9003,
    "DateTimeDigitized":    0x9004,
    "ExifImageWidth":       0xA002,
    "ExifImageHeight":      0xA003,
    "Orientation":          0x0112,
    "XResolution":          0x011A,
    "YResolution":          0x011B,
    "ExposureTime":         0x829A,
    "FNumber":              0x829D,
    "ISOSpeedRatings":      0x8827,
    "FocalLength":          0x920A,
    "Flash":                0x9209,
    "WhiteBalance":         0xA403,
    "LensModel":            0xA434,
    "ImageDescription":     0x010E,
    "Artist":               0x013B,
    "Copyright":            0x8298,
    "UserComment":          0x9286,
    "ProcessingSoftware":   0x000B,
    "HostComputer":         0x013C,
}


class EXIFAnalysisResult:
    """Structured result from EXIF metadata analysis."""

    def __init__(
        self,
        has_exif: bool,
        metadata: Dict[str, Any],
        gps_data: Optional[Dict[str, Any]],
        camera_info: Dict[str, Optional[str]],
        software_detected: Optional[str],
        is_edited: bool,
        editing_software_match: Optional[str],
        is_ai_generated: bool,
        ai_generator_match: Optional[str],
        has_camera_hardware: bool,
        timestamp_coherent: bool,
        risk_flags: List[str],
        authenticity_score: float,
    ):
        self.has_exif = has_exif
        self.metadata = metadata
        self.gps_data = gps_data
        self.camera_info = camera_info
        self.software_detected = software_detected
        self.is_edited = is_edited
        self.editing_software_match = editing_software_match
        self.is_ai_generated = is_ai_generated
        self.ai_generator_match = ai_generator_match
        self.has_camera_hardware = has_camera_hardware
        self.timestamp_coherent = timestamp_coherent
        self.risk_flags = risk_flags
        self.authenticity_score = authenticity_score

    def to_dict(self) -> dict:
        return {
            "has_exif": self.has_exif,
            "metadata": self.metadata,
            "gps_data": self.gps_data,
            "camera_info": self.camera_info,
            "software_detected": self.software_detected,
            "is_edited": self.is_edited,
            "editing_software_match": self.editing_software_match,
            "is_ai_generated": self.is_ai_generated,
            "ai_generator_match": self.ai_generator_match,
            "has_camera_hardware": self.has_camera_hardware,
            "timestamp_coherent": self.timestamp_coherent,
            "risk_flags": self.risk_flags,
            "authenticity_score": round(self.authenticity_score, 2),
        }

    def __repr__(self) -> str:
        status = "AUTHENTIC" if self.authenticity_score >= 60 else "SUSPICIOUS"
        return (
            f"EXIFAnalysisResult({status}, "
            f"score={self.authenticity_score:.1f}%, "
            f"camera={self.camera_info.get('make', 'Unknown')}, "
            f"edited={self.is_edited}, "
            f"flags={len(self.risk_flags)})"
        )


class EXIFAnalyzer:
    """
    Extracts and forensically analyzes EXIF metadata from uploaded vehicle
    images to detect manipulation, AI generation, or missing provenance.

    Forensic Checks:
        1. EXIF Presence — Does the file contain any metadata?
        2. Camera Hardware — Are Make/Model tags present and valid?
        3. Software Detection — Is there an editing/AI software fingerprint?
        4. Timestamp Coherence — Do creation and modification dates align?
        5. GPS Extraction — Location data for cross-referencing claims.
        6. Risk Scoring — Weighted authenticity score (0-100%).

    Usage:
        >>> analyzer = EXIFAnalyzer()
        >>> result = analyzer.analyze("path/to/car_damage.jpg")
        >>> print(result.authenticity_score)
        85.0
        >>> print(result.is_edited)
        False
    """

    # AI generator keywords (subset of editing signatures, higher severity)
    AI_GENERATOR_KEYWORDS = [
        "dall-e", "dalle", "midjourney", "stable diffusion",
        "comfyui", "automatic1111", "invoke ai", "novelai",
        "leonardo.ai", "ideogram", "firefly",
    ]

    def __init__(self):
        pass

    def analyze(self, image_input) -> EXIFAnalysisResult:
        """
        Perform full EXIF forensic analysis on an image.

        Args:
            image_input: File path (str/Path), raw bytes, or Pillow Image.

        Returns:
            EXIFAnalysisResult with metadata, flags, and authenticity score.
        """
        # Load image
        img = self._load_image(image_input)
        if img is None:
            return self._no_exif_result("Failed to open image file.")

        # Extract raw EXIF data
        exif_data = self._extract_exif(img)
        if not exif_data:
            return self._no_exif_result(
                "No EXIF metadata found. Image may be a screenshot, "
                "web download, or AI-generated synthetic image."
            )

        # Parse into structured fields
        metadata = self._parse_metadata(exif_data)
        gps_data = self._extract_gps(exif_data)
        camera_info = self._extract_camera_info(metadata)
        software_detected = metadata.get("Software") or metadata.get("ProcessingSoftware")

        # Run forensic checks
        is_edited, editing_match = self._check_editing_software(software_detected)
        is_ai_gen, ai_match = self._check_ai_generated(software_detected, metadata)
        has_hardware = self._check_camera_hardware(camera_info)
        timestamp_ok = self._check_timestamp_coherence(metadata)

        # Compile risk flags
        risk_flags = []
        if is_ai_gen:
            risk_flags.append(f"AI-GENERATED: Detected '{ai_match}' in metadata")
        if is_edited:
            risk_flags.append(f"EDITING_SOFTWARE: '{editing_match}' detected in Software tag")
        if not has_hardware:
            risk_flags.append("NO_CAMERA_HARDWARE: Missing Make/Model — not from a physical camera")
        if not timestamp_ok:
            risk_flags.append("TIMESTAMP_MISMATCH: Creation and modification dates are inconsistent")
        if software_detected and not is_edited:
            # Unknown software — not in our blocklist but still present
            risk_flags.append(f"UNKNOWN_SOFTWARE: '{software_detected}' — verify manually")

        # Calculate weighted authenticity score
        authenticity_score = self._calculate_score(
            has_exif=True,
            has_hardware=has_hardware,
            is_edited=is_edited,
            is_ai_gen=is_ai_gen,
            timestamp_ok=timestamp_ok,
            has_gps=gps_data is not None and len(gps_data) > 0,
        )

        return EXIFAnalysisResult(
            has_exif=True,
            metadata=metadata,
            gps_data=gps_data,
            camera_info=camera_info,
            software_detected=software_detected,
            is_edited=is_edited,
            editing_software_match=editing_match,
            is_ai_generated=is_ai_gen,
            ai_generator_match=ai_match,
            has_camera_hardware=has_hardware,
            timestamp_coherent=timestamp_ok,
            risk_flags=risk_flags,
            authenticity_score=authenticity_score,
        )

    # ── Internal Methods ──

    def _load_image(self, image_input) -> Optional[Image.Image]:
        """Load image from path, bytes, or existing PIL Image."""
        try:
            if isinstance(image_input, Image.Image):
                return image_input
            if isinstance(image_input, (str, Path)):
                return Image.open(str(image_input))
            if isinstance(image_input, bytes):
                return Image.open(io.BytesIO(image_input))
            if isinstance(image_input, io.BytesIO):
                return Image.open(image_input)
            return None
        except Exception as e:
            logger.error("Failed to load image for EXIF analysis: %s", e)
            return None

    def _extract_exif(self, img: Image.Image) -> Optional[dict]:
        """Extract raw EXIF data from a Pillow Image."""
        try:
            exif = img._getexif()
            if exif is None:
                return None
            return exif
        except (AttributeError, Exception):
            return None

    def _parse_metadata(self, exif_data: dict) -> Dict[str, Any]:
        """Convert raw EXIF tag IDs to human-readable key-value pairs."""
        parsed = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, f"Unknown_0x{tag_id:04X}")

            # Skip binary/large data fields
            if isinstance(value, bytes) and len(value) > 256:
                parsed[tag_name] = f"<binary data, {len(value)} bytes>"
                continue

            # Clean up string values
            if isinstance(value, str):
                value = value.strip().rstrip("\x00")

            # Handle IFD pointers (nested EXIF data)
            if tag_name == "GPSInfo":
                continue  # Handled separately

            parsed[tag_name] = value

        return parsed

    def _extract_gps(self, exif_data: dict) -> Optional[Dict[str, Any]]:
        """Extract GPS coordinates from EXIF GPS IFD."""
        gps_info = exif_data.get(0x8825)  # GPSInfo tag
        if not gps_info or not isinstance(gps_info, dict):
            return None

        gps_data = {}
        for tag_id, value in gps_info.items():
            tag_name = GPSTAGS.get(tag_id, f"GPSTag_{tag_id}")
            gps_data[tag_name] = value

        # Try to compute decimal coordinates
        try:
            lat = self._gps_to_decimal(
                gps_data.get("GPSLatitude"),
                gps_data.get("GPSLatitudeRef", "N"),
            )
            lon = self._gps_to_decimal(
                gps_data.get("GPSLongitude"),
                gps_data.get("GPSLongitudeRef", "E"),
            )
            if lat is not None and lon is not None:
                gps_data["decimal_latitude"] = round(lat, 6)
                gps_data["decimal_longitude"] = round(lon, 6)
        except Exception:
            pass

        return gps_data if gps_data else None

    @staticmethod
    def _gps_to_decimal(
        dms_tuple: Optional[tuple], ref: str
    ) -> Optional[float]:
        """Convert GPS DMS (degrees, minutes, seconds) to decimal degrees."""
        if dms_tuple is None or len(dms_tuple) != 3:
            return None

        degrees = float(dms_tuple[0])
        minutes = float(dms_tuple[1])
        seconds = float(dms_tuple[2])

        decimal = degrees + minutes / 60.0 + seconds / 3600.0

        if ref in ("S", "W"):
            decimal = -decimal

        return decimal

    def _extract_camera_info(self, metadata: dict) -> Dict[str, Optional[str]]:
        """Extract camera hardware information."""
        return {
            "make": metadata.get("Make"),
            "model": metadata.get("Model"),
            "lens": metadata.get("LensModel"),
            "software": metadata.get("Software"),
            "exposure": str(metadata.get("ExposureTime", "")),
            "f_number": str(metadata.get("FNumber", "")),
            "iso": str(metadata.get("ISOSpeedRatings", "")),
            "focal_length": str(metadata.get("FocalLength", "")),
            "flash": str(metadata.get("Flash", "")),
            "orientation": str(metadata.get("Orientation", "")),
        }

    def _check_editing_software(
        self, software: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Check if the Software tag matches known editing applications."""
        if not software:
            return False, None

        software_lower = software.lower()
        for sig in EDITING_SOFTWARE_SIGNATURES:
            if sig in software_lower:
                logger.warning("Editing software detected in EXIF: %s", software)
                return True, sig

        return False, None

    def _check_ai_generated(
        self, software: Optional[str], metadata: dict
    ) -> Tuple[bool, Optional[str]]:
        """Check if image appears to be AI-generated."""
        # Check Software tag
        if software:
            sw_lower = software.lower()
            for keyword in self.AI_GENERATOR_KEYWORDS:
                if keyword in sw_lower:
                    return True, keyword

        # Check ImageDescription and UserComment for AI traces
        for field in ("ImageDescription", "UserComment", "Artist", "Copyright"):
            value = metadata.get(field)
            if value and isinstance(value, str):
                val_lower = value.lower()
                for keyword in self.AI_GENERATOR_KEYWORDS:
                    if keyword in val_lower:
                        return True, keyword

        return False, None

    def _check_camera_hardware(self, camera_info: dict) -> bool:
        """
        Check if camera hardware metadata is present.
        Genuine camera photos always have Make and Model.
        Screenshots, web downloads, and AI images typically lack these.
        """
        make = camera_info.get("make")
        model = camera_info.get("model")

        return bool(make and model and len(make) > 1 and len(model) > 1)

    def _check_timestamp_coherence(self, metadata: dict) -> bool:
        """
        Check if DateTime and DateTimeOriginal are coherent.
        A large gap between creation and modification can indicate editing.
        """
        dt_original = metadata.get("DateTimeOriginal")
        dt_modified = metadata.get("DateTime")

        if not dt_original or not dt_modified:
            # Can't verify if timestamps are missing
            return True  # No flag (absence handled by other checks)

        try:
            fmt = "%Y:%m:%d %H:%M:%S"
            t_orig = datetime.strptime(str(dt_original), fmt)
            t_mod = datetime.strptime(str(dt_modified), fmt)

            delta = abs((t_mod - t_orig).total_seconds())

            # Allow up to 60 seconds difference (camera processing delay)
            if delta > 60:
                logger.warning(
                    "Timestamp mismatch: Original=%s, Modified=%s (delta=%ds)",
                    dt_original, dt_modified, delta,
                )
                return False
        except (ValueError, TypeError):
            # Can't parse timestamps — no flag
            return True

        return True

    def _calculate_score(
        self,
        has_exif: bool,
        has_hardware: bool,
        is_edited: bool,
        is_ai_gen: bool,
        timestamp_ok: bool,
        has_gps: bool,
    ) -> float:
        """
        Calculate weighted EXIF authenticity score (0-100%).

        Scoring weights:
            - Has EXIF data at all:       15 points
            - Camera hardware present:    30 points
            - No editing software:        25 points
            - Not AI-generated:           15 points
            - Timestamps coherent:        10 points
            - GPS data present:            5 points (bonus)
        """
        score = 0.0

        if has_exif:
            score += 15.0
        if has_hardware:
            score += 30.0
        if not is_edited:
            score += 25.0
        if not is_ai_gen:
            score += 15.0
        if timestamp_ok:
            score += 10.0
        if has_gps:
            score += 5.0

        return min(score, 100.0)

    def _no_exif_result(self, reason: str) -> EXIFAnalysisResult:
        """Return a result for images with no EXIF data."""
        return EXIFAnalysisResult(
            has_exif=False,
            metadata={},
            gps_data=None,
            camera_info={"make": None, "model": None, "lens": None,
                         "software": None, "exposure": "", "f_number": "",
                         "iso": "", "focal_length": "", "flash": "",
                         "orientation": ""},
            software_detected=None,
            is_edited=False,
            editing_software_match=None,
            is_ai_generated=False,
            ai_generator_match=None,
            has_camera_hardware=False,
            timestamp_coherent=True,
            risk_flags=[reason],
            authenticity_score=25.0,  # Low score for no EXIF
        )
