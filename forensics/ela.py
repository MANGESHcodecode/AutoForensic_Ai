"""
AutoForensic AI — Error Level Analysis (ELA) Engine
=====================================================
Security Layer 3: Detects image tampering by analyzing compression artifact
inconsistencies. When a JPEG image is re-saved, authentic (untouched) regions
lose quality uniformly, while spliced or digitally altered regions exhibit
different error levels — creating detectable anomalies.

Algorithm:
    1. Load the original image I_orig.
    2. Re-compress at a baseline JPEG quality Q (default 90%).
    3. Compute error matrix: E = |I_orig - I_recompressed|
    4. Scale by enhancement factor for visibility: E_vis = E × scale
    5. Analyze statistical distribution of error values.
    6. Generate color heatmap (JET/INFERNO) for visual inspection.

Interpretation:
    - Uniform ELA across the image = likely authentic (consistent compression)
    - Localized bright hotspots = likely tampered regions (spliced/edited areas)
    - Extremely flat ELA (near zero) = likely re-saved/re-encoded multiple times

References:
    - Krawetz, N. (2007). "A Picture's Worth: Digital Image Analysis & Forensics"
    - FotoForensics: https://fotoforensics.com/tutorial.php
"""

import io
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("autoforensic.forensics.ela")


class ELAResult:
    """Structured result from Error Level Analysis."""

    def __init__(
        self,
        is_suspicious: bool,
        mean_error: float,
        std_error: float,
        max_error: float,
        anomaly_ratio: float,
        uniformity_score: float,
        ela_image: Optional[np.ndarray] = None,
        heatmap_image: Optional[np.ndarray] = None,
        composite_image: Optional[np.ndarray] = None,
        risk_flags: Optional[list] = None,
        authenticity_score: float = 100.0,
    ):
        self.is_suspicious = is_suspicious
        self.mean_error = mean_error
        self.std_error = std_error
        self.max_error = max_error
        self.anomaly_ratio = anomaly_ratio
        self.uniformity_score = uniformity_score
        self.ela_image = ela_image
        self.heatmap_image = heatmap_image
        self.composite_image = composite_image
        self.risk_flags = risk_flags or []
        self.authenticity_score = authenticity_score

    def to_dict(self) -> dict:
        return {
            "is_suspicious": self.is_suspicious,
            "mean_error": round(self.mean_error, 4),
            "std_error": round(self.std_error, 4),
            "max_error": round(self.max_error, 4),
            "anomaly_ratio": round(self.anomaly_ratio, 6),
            "uniformity_score": round(self.uniformity_score, 4),
            "risk_flags": self.risk_flags,
            "authenticity_score": round(self.authenticity_score, 2),
        }

    def __repr__(self) -> str:
        status = "SUSPICIOUS" if self.is_suspicious else "UNIFORM"
        return (
            f"ELAResult({status}, "
            f"mean_err={self.mean_error:.2f}, "
            f"anomaly_ratio={self.anomaly_ratio:.4f}, "
            f"score={self.authenticity_score:.1f}%)"
        )


class ELAAnalyzer:
    """
    Performs Error Level Analysis on uploaded vehicle damage images
    to detect digitally manipulated regions (spliced fake damage,
    cloned artifacts, AI-inpainted areas).

    The analyzer compresses the image at a controlled quality level
    and measures the pixel-level error between the original and the
    recompressed version. Genuine images show uniform error distribution;
    tampered images show localized anomalies.

    Usage:
        >>> analyzer = ELAAnalyzer()
        >>> result = analyzer.analyze("path/to/car_damage.jpg")
        >>> print(result.is_suspicious)
        False
        >>> print(result.authenticity_score)
        82.5
        >>> # Save the visual heatmap
        >>> analyzer.save_heatmap(result, "output/ela_heatmap.jpg")
    """

    def __init__(
        self,
        quality: int = 90,
        scale_factor: int = 20,
        anomaly_threshold: float = 0.02,
        colormap: int = cv2.COLORMAP_JET,
    ):
        """
        Args:
            quality: JPEG recompression quality level (default 90).
                     Lower quality amplifies error differences.
            scale_factor: Multiplier for error visualization (default 20).
                          Higher values make subtle differences more visible.
            anomaly_threshold: Fraction of high-error pixels that triggers
                               a suspicion flag (default 0.02 = 2%).
            colormap: OpenCV colormap for heatmap visualization.
                      cv2.COLORMAP_JET (default) or cv2.COLORMAP_INFERNO.
        """
        self.quality = quality
        self.scale_factor = scale_factor
        self.anomaly_threshold = anomaly_threshold
        self.colormap = colormap

    def analyze(self, image_input) -> ELAResult:
        """
        Perform Error Level Analysis on an image.

        Args:
            image_input: File path (str/Path), raw bytes, or numpy array (BGR).

        Returns:
            ELAResult with statistical metrics, heatmap, and authenticity score.
        """
        # ── Step 1: Load original image ──
        original = self._load_image(image_input)
        if original is None:
            return ELAResult(
                is_suspicious=False,
                mean_error=0.0,
                std_error=0.0,
                max_error=0.0,
                anomaly_ratio=0.0,
                uniformity_score=0.0,
                risk_flags=["ELA_LOAD_FAILED: Could not load image"],
                authenticity_score=50.0,
            )

        # ── Step 2: Recompress at baseline quality ──
        recompressed = self._recompress(original, self.quality)

        # ── Step 3: Compute absolute error matrix ──
        # Both images must be float64 for precise difference calculation
        orig_float = original.astype(np.float64)
        recomp_float = recompressed.astype(np.float64)
        error_matrix = np.abs(orig_float - recomp_float)

        # ── Step 4: Compute per-pixel error magnitude (grayscale) ──
        # Use L2 norm across color channels for each pixel
        if len(error_matrix.shape) == 3:
            error_gray = np.sqrt(np.sum(error_matrix ** 2, axis=2))
        else:
            error_gray = error_matrix

        # ── Step 5: Statistical analysis ──
        mean_error = float(np.mean(error_gray))
        std_error = float(np.std(error_gray))
        max_error = float(np.max(error_gray))

        # Dynamic threshold: pixels with error > mean + 3*std are anomalous
        if std_error > 0:
            anomaly_mask = error_gray > (mean_error + 3.0 * std_error)
        else:
            anomaly_mask = np.zeros_like(error_gray, dtype=bool)

        total_pixels = error_gray.size
        anomaly_pixels = int(np.sum(anomaly_mask))
        anomaly_ratio = anomaly_pixels / total_pixels if total_pixels > 0 else 0.0

        # Uniformity score: coefficient of variation (lower = more uniform = more authentic)
        cv = std_error / (mean_error + 1e-8)  # Avoid division by zero
        # Map CV to 0-100 score: CV < 0.5 = very uniform (100), CV > 2.0 = very non-uniform (0)
        uniformity_score = max(0.0, min(100.0, 100.0 * (1.0 - cv / 2.0)))

        # ── Step 6: Generate visual outputs ──
        # ELA visualization (scaled error)
        ela_scaled = np.clip(error_matrix * self.scale_factor, 0, 255).astype(np.uint8)

        # Grayscale ELA for heatmap
        ela_gray_scaled = np.clip(error_gray * self.scale_factor, 0, 255).astype(np.uint8)

        # Color heatmap
        heatmap = cv2.applyColorMap(ela_gray_scaled, self.colormap)

        # Composite: original | ELA | heatmap side-by-side
        composite = self._create_composite(original, ela_scaled, heatmap)

        # ── Step 7: Risk assessment ──
        risk_flags = []
        is_suspicious = False

        if anomaly_ratio > self.anomaly_threshold:
            is_suspicious = True
            risk_flags.append(
                f"HIGH_ANOMALY_RATIO: {anomaly_ratio:.4f} ({anomaly_pixels:,} anomalous pixels) "
                f"exceeds threshold {self.anomaly_threshold}"
            )

        if std_error > 15.0:
            is_suspicious = True
            risk_flags.append(
                f"HIGH_ERROR_VARIANCE: std_error={std_error:.2f} indicates "
                f"non-uniform compression (potential splicing)"
            )

        if max_error > 100.0 and anomaly_ratio > 0.005:
            risk_flags.append(
                f"LOCALIZED_HOTSPOT: max_error={max_error:.1f} with clustered anomalies"
            )

        if mean_error < 1.0 and max_error < 5.0:
            risk_flags.append(
                "EXTREMELY_FLAT_ELA: Image may have been re-compressed multiple times "
                "(information loss or laundering)"
            )

        # ── Step 8: Authenticity score ──
        authenticity_score = self._calculate_score(
            mean_error, std_error, anomaly_ratio, uniformity_score, is_suspicious
        )

        return ELAResult(
            is_suspicious=is_suspicious,
            mean_error=mean_error,
            std_error=std_error,
            max_error=max_error,
            anomaly_ratio=anomaly_ratio,
            uniformity_score=uniformity_score,
            ela_image=ela_scaled,
            heatmap_image=heatmap,
            composite_image=composite,
            risk_flags=risk_flags,
            authenticity_score=authenticity_score,
        )

    def save_heatmap(
        self,
        result: ELAResult,
        output_path: str,
        save_composite: bool = True,
    ) -> None:
        """
        Save ELA visualization outputs to disk.

        Args:
            result: ELAResult from analyze().
            output_path: Base output path (e.g., "output/ela_heatmap.jpg").
            save_composite: If True, also save the composite side-by-side image.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if result.heatmap_image is not None:
            cv2.imwrite(str(output), result.heatmap_image)
            logger.info("ELA heatmap saved: %s", output)

        if save_composite and result.composite_image is not None:
            composite_path = output.parent / f"{output.stem}_composite{output.suffix}"
            cv2.imwrite(str(composite_path), result.composite_image)
            logger.info("ELA composite saved: %s", composite_path)

        if result.ela_image is not None:
            ela_path = output.parent / f"{output.stem}_raw{output.suffix}"
            cv2.imwrite(str(ela_path), result.ela_image)
            logger.info("ELA raw saved: %s", ela_path)

    # ── Internal Methods ──

    def _load_image(self, image_input) -> Optional[np.ndarray]:
        """Load image as BGR numpy array."""
        try:
            if isinstance(image_input, np.ndarray):
                return image_input

            if isinstance(image_input, (str, Path)):
                # Use cv2.imread for file paths
                img = cv2.imread(str(image_input), cv2.IMREAD_COLOR)
                if img is None:
                    # Try with unicode path support
                    raw = Path(image_input).read_bytes()
                    arr = np.frombuffer(raw, dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                return img

            if isinstance(image_input, bytes):
                arr = np.frombuffer(image_input, dtype=np.uint8)
                return cv2.imdecode(arr, cv2.IMREAD_COLOR)

            if isinstance(image_input, io.BytesIO):
                arr = np.frombuffer(image_input.getvalue(), dtype=np.uint8)
                return cv2.imdecode(arr, cv2.IMREAD_COLOR)

            if isinstance(image_input, Image.Image):
                # Convert PIL Image to OpenCV BGR
                rgb = np.array(image_input.convert("RGB"))
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            return None
        except Exception as e:
            logger.error("Failed to load image for ELA: %s", e)
            return None

    def _recompress(self, image: np.ndarray, quality: int) -> np.ndarray:
        """
        Recompress an image at the specified JPEG quality level.
        This creates the reference image for error comparison.
        """
        # Encode to JPEG in memory
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        _, buffer = cv2.imencode(".jpg", image, encode_params)

        # Decode back to get the recompressed version
        recompressed = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

        return recompressed

    def _create_composite(
        self,
        original: np.ndarray,
        ela: np.ndarray,
        heatmap: np.ndarray,
    ) -> np.ndarray:
        """
        Create a side-by-side composite: [Original | ELA | Heatmap]
        with labeled headers.
        """
        h, w = original.shape[:2]

        # Ensure all images have the same dimensions
        ela_resized = cv2.resize(ela, (w, h)) if ela.shape[:2] != (h, w) else ela
        heatmap_resized = cv2.resize(heatmap, (w, h)) if heatmap.shape[:2] != (h, w) else heatmap

        # Ensure all images are 3-channel
        if len(ela_resized.shape) == 2:
            ela_resized = cv2.cvtColor(ela_resized, cv2.COLOR_GRAY2BGR)

        # Create header bar
        header_height = 40
        panel_w = w
        total_w = panel_w * 3

        # Create composite canvas
        composite = np.zeros((h + header_height, total_w, 3), dtype=np.uint8)

        # Add header background
        header = np.full((header_height, total_w, 3), (30, 30, 30), dtype=np.uint8)

        labels = ["ORIGINAL", "ERROR LEVEL ANALYSIS", "TAMPER HEATMAP"]
        for i, label in enumerate(labels):
            x_offset = i * panel_w + panel_w // 2 - len(label) * 5
            cv2.putText(
                header, label, (max(x_offset, i * panel_w + 10), 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA,
            )

        composite[:header_height, :, :] = header

        # Place images
        composite[header_height:, 0:panel_w, :] = original
        composite[header_height:, panel_w:2*panel_w, :] = ela_resized
        composite[header_height:, 2*panel_w:3*panel_w, :] = heatmap_resized

        # Add separator lines
        cv2.line(composite, (panel_w, 0), (panel_w, h + header_height), (100, 100, 100), 2)
        cv2.line(composite, (2*panel_w, 0), (2*panel_w, h + header_height), (100, 100, 100), 2)

        return composite

    def _calculate_score(
        self,
        mean_error: float,
        std_error: float,
        anomaly_ratio: float,
        uniformity_score: float,
        is_suspicious: bool,
    ) -> float:
        """
        Calculate ELA-based authenticity score (0-100%).

        Scoring logic:
            - Start at 100 (fully authentic assumption)
            - Deduct based on anomaly indicators
            - High uniformity (low variance) is good
            - Low anomaly ratio is good
        """
        score = 100.0

        # Penalize high anomaly ratio (0-40 points)
        if anomaly_ratio > 0.05:
            score -= 40.0
        elif anomaly_ratio > 0.02:
            score -= 25.0
        elif anomaly_ratio > 0.01:
            score -= 15.0
        elif anomaly_ratio > 0.005:
            score -= 8.0

        # Penalize high standard deviation (0-30 points)
        if std_error > 25.0:
            score -= 30.0
        elif std_error > 15.0:
            score -= 20.0
        elif std_error > 10.0:
            score -= 10.0

        # Penalize extremely flat ELA (possible laundering)
        if mean_error < 0.5:
            score -= 10.0

        # Bonus for high uniformity
        if uniformity_score > 80:
            score += 5.0

        # Additional penalty if flagged as suspicious
        if is_suspicious:
            score -= 10.0

        return max(0.0, min(100.0, score))
