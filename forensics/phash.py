"""
AutoForensic AI — 2D-DCT Perceptual Hashing (pHash) & Duplicate Detector
==========================================================================
Security Layer 4: Generates robust perceptual fingerprints of vehicle images
using 2D Discrete Cosine Transform (DCT). Unlike cryptographic hashes (SHA-256)
that change completely with even 1-bit modification, perceptual hashes remain
stable under minor transformations (resize, compression, brightness shifts)
while still changing for semantically different images.

This enables detection of:
    - Duplicate insurance claims (same vehicle damage submitted under different
      policy numbers or by different claimants)
    - Near-duplicate fraud (same image with minor cropping, rotation, or
      color adjustments to bypass simple file-hash checks)
    - Re-submitted claims from web-scraped vehicle damage photos

Algorithm (DCT-based pHash):
    1. Convert to grayscale
    2. Resize to 32×32 pixels (removes high-frequency spatial noise)
    3. Apply 2D Discrete Cosine Transform via cv2.dct()
    4. Extract top-left 8×8 low-frequency coefficients (skip DC at [0,0])
    5. Compute median of the 63 AC coefficients
    6. Generate 64-bit binary hash: 1 if coeff > median, else 0
    7. Format as 16-character hexadecimal string

Hamming Distance Interpretation:
    - Distance ≤  5 : DUPLICATE (near-identical image — flag for fraud review)
    - Distance ≤ 10 : SUSPECTED VARIANT (resized/cropped version)
    - Distance ≤ 15 : POSSIBLY RELATED (same scene, different angle)
    - Distance >  15 : UNIQUE (different image)

References:
    - Zauner, C. (2010). "Implementation and Benchmarking of Perceptual Image
      Hash Functions" (Master's Thesis, Upper Austria University)
    - OpenCV cv2.dct: hardware-accelerated Discrete Cosine Transform
"""

import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("autoforensic.forensics.phash")


# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════

# Resize target for DCT input
DCT_SIZE = 32

# Block size for low-frequency extraction
HASH_SIZE = 8

# Hamming distance thresholds
THRESHOLD_DUPLICATE = 5       # Identical / near-identical
THRESHOLD_VARIANT = 10        # Resized / cropped / compressed version
THRESHOLD_RELATED = 15        # Same scene, different framing


class PHashResult:
    """Structured result from perceptual hash computation."""

    def __init__(
        self,
        hash_hex: str,
        hash_binary: str,
        hash_bits: np.ndarray,
    ):
        self.hash_hex = hash_hex
        self.hash_binary = hash_binary
        self.hash_bits = hash_bits

    def to_dict(self) -> dict:
        return {
            "hash_hex": self.hash_hex,
            "hash_binary": self.hash_binary,
        }

    def __repr__(self) -> str:
        return f"PHashResult(hex={self.hash_hex})"

    def __eq__(self, other) -> bool:
        if isinstance(other, PHashResult):
            return self.hash_hex == other.hash_hex
        return False


class DuplicateCheckResult:
    """Structured result from duplicate/similarity comparison."""

    def __init__(
        self,
        query_hash: str,
        match_hash: str,
        hamming_distance: int,
        similarity_pct: float,
        verdict: str,
        is_duplicate: bool,
        match_source: Optional[str] = None,
    ):
        self.query_hash = query_hash
        self.match_hash = match_hash
        self.hamming_distance = hamming_distance
        self.similarity_pct = similarity_pct
        self.verdict = verdict
        self.is_duplicate = is_duplicate
        self.match_source = match_source

    def to_dict(self) -> dict:
        return {
            "query_hash": self.query_hash,
            "match_hash": self.match_hash,
            "hamming_distance": self.hamming_distance,
            "similarity_pct": round(self.similarity_pct, 2),
            "verdict": self.verdict,
            "is_duplicate": self.is_duplicate,
            "match_source": self.match_source,
        }

    def __repr__(self) -> str:
        return (
            f"DuplicateCheckResult(distance={self.hamming_distance}, "
            f"similarity={self.similarity_pct:.1f}%, "
            f"verdict={self.verdict})"
        )


class PerceptualHasher:
    """
    Computes 2D-DCT Perceptual Hashes (pHash) for vehicle images and
    performs similarity comparisons to detect duplicate insurance claims.

    The hasher maintains an in-memory registry of previously seen hashes
    (for session-level duplicate detection) and supports comparison against
    any externally stored hash database.

    Usage:
        >>> hasher = PerceptualHasher()
        >>> hash1 = hasher.compute_hash("car_damage_1.jpg")
        >>> hash2 = hasher.compute_hash("car_damage_2.jpg")
        >>> distance = hasher.hamming_distance(hash1, hash2)
        >>> print(f"Distance: {distance}, Duplicate: {distance <= 5}")

        # Session-level duplicate detection
        >>> hasher.register_hash(hash1, source="claim_001")
        >>> check = hasher.check_duplicate(hash2)
        >>> if check.is_duplicate:
        ...     print(f"FRAUD: Matches {check.match_source}")
    """

    def __init__(
        self,
        dct_size: int = DCT_SIZE,
        hash_size: int = HASH_SIZE,
        duplicate_threshold: int = THRESHOLD_DUPLICATE,
        variant_threshold: int = THRESHOLD_VARIANT,
    ):
        """
        Args:
            dct_size: Image resize target for DCT (default 32×32).
            hash_size: Low-frequency block to extract (default 8×8 = 64 bits).
            duplicate_threshold: Hamming distance for duplicate flag (default 5).
            variant_threshold: Hamming distance for variant flag (default 10).
        """
        self.dct_size = dct_size
        self.hash_size = hash_size
        self.duplicate_threshold = duplicate_threshold
        self.variant_threshold = variant_threshold

        # In-memory hash registry: {hash_hex: source_label}
        self._registry: dict = {}

    def compute_hash(self, image_input) -> PHashResult:
        """
        Compute the 64-bit perceptual hash of an image.

        Algorithm:
            1. Grayscale conversion
            2. Resize to 32×32
            3. 2D Discrete Cosine Transform (cv2.dct)
            4. Extract 8×8 low-frequency block (skip DC)
            5. Median threshold → 64-bit binary hash
            6. Convert to 16-char hex string

        Args:
            image_input: File path, raw bytes, numpy array, or PIL Image.

        Returns:
            PHashResult with hex hash, binary hash, and raw bit array.
        """
        # Load and preprocess
        gray = self._load_grayscale(image_input)
        if gray is None:
            raise ValueError("Failed to load image for perceptual hashing.")

        # Resize to DCT target size
        resized = cv2.resize(gray, (self.dct_size, self.dct_size), interpolation=cv2.INTER_AREA)

        # Convert to float32 for DCT
        float_img = resized.astype(np.float32)

        # Apply 2D Discrete Cosine Transform
        dct_result = cv2.dct(float_img)

        # Extract low-frequency block (top-left 8×8, excluding DC at [0,0])
        low_freq = dct_result[:self.hash_size, :self.hash_size].copy()
        low_freq[0, 0] = 0.0  # Zero out DC component

        # Flatten the 8×8 block to 64 values
        flat = low_freq.flatten()

        # Compute median threshold
        median_val = float(np.median(flat))

        # Generate binary hash: 1 if above median, 0 otherwise
        hash_bits = (flat > median_val).astype(np.uint8)

        # Convert to binary string (64 chars of 0/1)
        hash_binary = "".join(str(b) for b in hash_bits)

        # Convert to hexadecimal string (16 chars)
        hash_int = int(hash_binary, 2)
        hash_hex = f"{hash_int:016x}"

        return PHashResult(
            hash_hex=hash_hex,
            hash_binary=hash_binary,
            hash_bits=hash_bits,
        )

    def hamming_distance(
        self,
        hash_a: Union[PHashResult, str],
        hash_b: Union[PHashResult, str],
    ) -> int:
        """
        Compute the Hamming distance between two perceptual hashes.
        This counts the number of differing bits between the two hashes.

        Args:
            hash_a: PHashResult or hex string.
            hash_b: PHashResult or hex string.

        Returns:
            Integer Hamming distance (0 = identical, 64 = completely different).
        """
        hex_a = hash_a.hash_hex if isinstance(hash_a, PHashResult) else hash_a
        hex_b = hash_b.hash_hex if isinstance(hash_b, PHashResult) else hash_b

        # Convert hex to integer
        int_a = int(hex_a, 16)
        int_b = int(hex_b, 16)

        # XOR and count set bits
        xor = int_a ^ int_b
        distance = bin(xor).count("1")

        return distance

    def similarity_percentage(
        self,
        hash_a: Union[PHashResult, str],
        hash_b: Union[PHashResult, str],
    ) -> float:
        """
        Compute similarity percentage between two hashes.

        Args:
            hash_a: PHashResult or hex string.
            hash_b: PHashResult or hex string.

        Returns:
            Similarity percentage (100% = identical, 0% = completely different).
        """
        distance = self.hamming_distance(hash_a, hash_b)
        return (1.0 - distance / 64.0) * 100.0

    def classify_similarity(self, distance: int) -> str:
        """
        Classify the relationship between two images based on Hamming distance.

        Returns:
            One of: "DUPLICATE", "VARIANT", "RELATED", "UNIQUE"
        """
        if distance <= self.duplicate_threshold:
            return "DUPLICATE"
        elif distance <= self.variant_threshold:
            return "VARIANT"
        elif distance <= THRESHOLD_RELATED:
            return "RELATED"
        else:
            return "UNIQUE"

    def register_hash(
        self,
        hash_result: Union[PHashResult, str],
        source: str = "unknown",
    ) -> None:
        """
        Register a hash in the in-memory registry for session-level
        duplicate detection.

        Args:
            hash_result: PHashResult or hex string.
            source: Label identifying the source (e.g., claim ID, filename).
        """
        hex_val = hash_result.hash_hex if isinstance(hash_result, PHashResult) else hash_result
        self._registry[hex_val] = source
        logger.info("Registered pHash %s from source: %s", hex_val, source)

    def check_duplicate(
        self,
        hash_result: Union[PHashResult, str],
        threshold: Optional[int] = None,
    ) -> Optional[DuplicateCheckResult]:
        """
        Check if an image hash matches any previously registered hash.

        Args:
            hash_result: PHashResult or hex string to check.
            threshold: Override duplicate threshold (default uses self.duplicate_threshold).

        Returns:
            DuplicateCheckResult if a match is found, None if no duplicates.
        """
        if not self._registry:
            return None

        threshold = threshold or self.duplicate_threshold
        query_hex = hash_result.hash_hex if isinstance(hash_result, PHashResult) else hash_result

        best_match = None
        best_distance = 65  # Impossible distance (max is 64)

        for registered_hex, source in self._registry.items():
            if registered_hex == query_hex:
                # Skip self-comparison
                if source == "self":
                    continue

            distance = self.hamming_distance(query_hex, registered_hex)

            if distance < best_distance:
                best_distance = distance
                best_match = (registered_hex, source)

        if best_match is None:
            return None

        match_hex, match_source = best_match
        similarity = self.similarity_percentage(query_hex, match_hex)
        verdict = self.classify_similarity(best_distance)
        is_duplicate = best_distance <= threshold

        if is_duplicate:
            logger.warning(
                "DUPLICATE DETECTED: query=%s matches %s (source=%s, distance=%d)",
                query_hex, match_hex, match_source, best_distance,
            )

        return DuplicateCheckResult(
            query_hash=query_hex,
            match_hash=match_hex,
            hamming_distance=best_distance,
            similarity_pct=similarity,
            verdict=verdict,
            is_duplicate=is_duplicate,
            match_source=match_source,
        )

    def compare_images(
        self, image_a, image_b
    ) -> DuplicateCheckResult:
        """
        Directly compare two images for similarity.

        Args:
            image_a: First image (path, bytes, or array).
            image_b: Second image (path, bytes, or array).

        Returns:
            DuplicateCheckResult with comparison metrics.
        """
        hash_a = self.compute_hash(image_a)
        hash_b = self.compute_hash(image_b)

        distance = self.hamming_distance(hash_a, hash_b)
        similarity = self.similarity_percentage(hash_a, hash_b)
        verdict = self.classify_similarity(distance)

        return DuplicateCheckResult(
            query_hash=hash_a.hash_hex,
            match_hash=hash_b.hash_hex,
            hamming_distance=distance,
            similarity_pct=similarity,
            verdict=verdict,
            is_duplicate=distance <= self.duplicate_threshold,
        )

    def get_registry_size(self) -> int:
        """Return the number of hashes in the registry."""
        return len(self._registry)

    def clear_registry(self) -> None:
        """Clear the in-memory hash registry."""
        self._registry.clear()
        logger.info("pHash registry cleared.")

    # ── Internal Methods ──

    def _load_grayscale(self, image_input) -> Optional[np.ndarray]:
        """Load an image and convert to grayscale."""
        try:
            if isinstance(image_input, np.ndarray):
                if len(image_input.shape) == 3:
                    return cv2.cvtColor(image_input, cv2.COLOR_BGR2GRAY)
                return image_input

            if isinstance(image_input, (str, Path)):
                img = cv2.imread(str(image_input), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    # Try with unicode path support
                    raw = Path(image_input).read_bytes()
                    arr = np.frombuffer(raw, dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
                return img

            if isinstance(image_input, bytes):
                arr = np.frombuffer(image_input, dtype=np.uint8)
                return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

            if isinstance(image_input, io.BytesIO):
                arr = np.frombuffer(image_input.getvalue(), dtype=np.uint8)
                return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

            if isinstance(image_input, Image.Image):
                return np.array(image_input.convert("L"))

            return None
        except Exception as e:
            logger.error("Failed to load image for pHash: %s", e)
            return None
