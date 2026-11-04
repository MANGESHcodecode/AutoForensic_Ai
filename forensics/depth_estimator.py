"""
AutoForensic AI — Monocular Depth Estimation via MiDaS
======================================================
Uses Intel ISL MiDaS (MiDaS_small via PyTorch Hub) to compute
relative depth maps from single RGB vehicle damage images.

Key capability:
    Given a YOLO segmentation mask of a damage region (e.g. a dent),
    this module computes the **indentation depth** (Δz) by comparing
    the depth inside the damaged mask against the surrounding
    undamaged panel baseline.

    Δz = median(depth_surrounding) − median(depth_damaged)

    The relative MiDaS depth is then scaled to approximate real-world
    centimetres using a configurable calibration factor.

Pipeline flow:
    Image (post-forensic) → MiDaS → relative depth map (H×W float32)
    + YOLO damage masks   → per-damage Δz in cm
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import cv2

logger = logging.getLogger("autoforensic.depth_estimator")


class DepthEstimator:
    """
    Monocular depth estimation engine using MiDaS_small.

    MiDaS produces a relative inverse-depth map from a single RGB image.
    Higher values → closer to camera.  For dent analysis we compute the
    depth delta between the undamaged surrounding panel and the dented
    region within the YOLO mask.

    Usage:
        estimator = DepthEstimator()
        depth_map = estimator.estimate_depth("image.jpg")
        delta_z   = estimator.compute_indentation(depth_map, dent_mask)
    """

    # Calibration: converts MiDaS relative depth units → approximate cm.
    # This is scene-dependent; default tuned for smartphone @ ~50 cm distance.
    DEPTH_SCALE_FACTOR = 0.12  # relative depth unit → cm

    # Dilation kernel size for computing surrounding baseline (pixels)
    SURROUND_DILATION_PX = 40

    def __init__(
        self,
        model_type: str = "MiDaS_small",
        depth_scale: float = DEPTH_SCALE_FACTOR,
        device: Optional[str] = None,
    ):
        """
        Args:
            model_type:   MiDaS variant ('MiDaS_small', 'DPT_Large', etc.)
            depth_scale:  Calibration factor for relative → cm conversion.
            device:       'cpu', 'cuda', or None (auto-detect).
        """
        self.model_type = model_type
        self.depth_scale = depth_scale
        self._device = device
        self._model = None
        self._transform = None

    # ── Lazy loading ──────────────────────────────────────────
    def _load_model(self):
        """Load MiDaS model from PyTorch Hub on first use."""
        if self._model is not None:
            return

        import torch

        device_str = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._torch_device = torch.device(device_str)

        logger.info(
            "Loading MiDaS (%s) from PyTorch Hub on %s ...",
            self.model_type, device_str,
        )

        try:
            # Pre-trust rwightman repo for headless execution
            try:
                if hasattr(torch.hub, "_trust_repo"):
                    torch.hub._trust_repo("rwightman/gen-efficientnet-pytorch")
            except Exception:
                pass

            self._model = torch.hub.load(
                "intel-isl/MiDaS", self.model_type, trust_repo=True
            )
            self._model.to(self._torch_device)
            self._model.eval()

            # Load corresponding transform
            midas_transforms = torch.hub.load(
                "intel-isl/MiDaS", "transforms", trust_repo=True
            )
            if self.model_type in ("DPT_Large", "DPT_Hybrid"):
                self._transform = midas_transforms.dpt_transform
            else:
                self._transform = midas_transforms.small_transform

            logger.info("MiDaS model loaded successfully.")

        except Exception as e:
            logger.error("Failed to load MiDaS model: %s", e)
            raise RuntimeError(
                f"MiDaS model loading failed: {e}. "
                "Ensure PyTorch and internet access are available."
            )

    # ── Core depth estimation ─────────────────────────────────
    def estimate_depth(
        self,
        image_path: str,
        output_dir: Optional[str] = None,
        save_heatmap: bool = True,
    ) -> Dict:
        """
        Compute a relative depth map for the given image.

        Args:
            image_path:   Path to RGB image.
            output_dir:   Where to save depth heatmap visualisation.
            save_heatmap: Whether to save colourised depth map.

        Returns:
            dict with keys:
                depth_map:      np.ndarray (H, W) float32, relative depth
                depth_min:      float
                depth_max:      float
                heatmap_path:   str (path to saved heatmap or None)
                image_shape:    (H, W)
        """
        self._load_model()

        import torch

        image_path = str(image_path)
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"Could not decode image: {image_path}")

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_h, img_w = img_bgr.shape[:2]

        # Transform and predict
        input_batch = self._transform(img_rgb).to(self._torch_device)

        with torch.no_grad():
            prediction = self._model(input_batch)

        # Resize prediction to original resolution
        depth_map = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=(img_h, img_w),
            mode="bicubic",
            align_corners=False,
        ).squeeze().cpu().numpy()

        depth_min = float(depth_map.min())
        depth_max = float(depth_map.max())

        logger.info(
            "Depth map computed: shape=%s, range=[%.2f, %.2f]",
            depth_map.shape, depth_min, depth_max,
        )

        # ── Save depth heatmap visualisation ──────────────────
        heatmap_path = None
        if save_heatmap:
            heatmap_path = self._save_depth_heatmap(
                depth_map, image_path, output_dir
            )

        return {
            "depth_map": depth_map,
            "depth_min": depth_min,
            "depth_max": depth_max,
            "heatmap_path": heatmap_path,
            "image_shape": (img_h, img_w),
        }

    # ── Per-damage indentation depth ──────────────────────────
    def compute_indentation(
        self,
        depth_map: np.ndarray,
        damage_mask: np.ndarray,
        class_name: str = "dent",
        **kwargs,
    ) -> Dict:
        if "damage_class" in kwargs:
            class_name = kwargs["damage_class"]
        """
        Compute the indentation depth Δz for a single damage region.

        The logic:
            1. Extract depth values INSIDE the damage mask (damaged region).
            2. Dilate the mask to create a surrounding ring (undamaged baseline).
            3. Δz = median(surrounding) − median(damaged)
               → positive Δz means the damaged area is pushed inward (dent).
            4. Scale Δz by calibration factor → approximate cm.

        Args:
            depth_map:    (H, W) float32 relative depth array.
            damage_mask:  (H, W) uint8 binary mask (1 = damaged pixel).
            class_name:   Damage class label (for context-aware scaling).

        Returns:
            dict with:
                delta_z_relative:  raw MiDaS depth delta
                delta_z_cm:        calibrated depth in cm
                damaged_median:    median depth inside mask
                baseline_median:   median depth in surrounding ring
                confidence:        quality indicator (0–1)
        """
        # Ensure mask dimensions match depth map
        if damage_mask.shape[:2] != depth_map.shape[:2]:
            damage_mask = cv2.resize(
                damage_mask.astype(np.float32),
                (depth_map.shape[1], depth_map.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            ).astype(np.uint8)

        # 1. Depth inside damaged region
        damaged_pixels = depth_map[damage_mask > 0]
        if len(damaged_pixels) < 10:
            logger.warning("Too few mask pixels (%d) for reliable depth.", len(damaged_pixels))
            return self._empty_indentation()

        damaged_median = float(np.median(damaged_pixels))

        # 2. Create surrounding ring (dilated mask − original mask)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.SURROUND_DILATION_PX, self.SURROUND_DILATION_PX),
        )
        dilated = cv2.dilate(damage_mask, kernel, iterations=1)
        surround_mask = dilated - damage_mask
        surround_pixels = depth_map[surround_mask > 0]

        if len(surround_pixels) < 10:
            logger.warning("Insufficient surrounding pixels for baseline.")
            return self._empty_indentation()

        baseline_median = float(np.median(surround_pixels))

        # 3. Compute delta
        # MiDaS outputs inverse depth: higher = closer to camera
        # For a dent, the damaged area is farther away → lower MiDaS value
        # Δz = baseline − damaged  → positive means indentation
        delta_z_relative = baseline_median - damaged_median

        # Apply class-specific scaling adjustments
        scale = self.depth_scale
        if class_name in ("scratch", "crack"):
            scale *= 0.5  # scratches/cracks are shallower
        elif class_name in ("glass_shatter", "lamp_broken", "tire_flat"):
            scale *= 1.5  # structural damage tends to be deeper

        delta_z_cm = abs(delta_z_relative) * scale

        # Confidence based on sample size and depth contrast
        n_damaged = len(damaged_pixels)
        n_surround = len(surround_pixels)
        sample_confidence = min(1.0, min(n_damaged, n_surround) / 500.0)
        contrast_confidence = min(1.0, abs(delta_z_relative) / (depth_map.max() - depth_map.min() + 1e-6) * 5.0)
        confidence = round((sample_confidence * 0.4 + contrast_confidence * 0.6), 3)

        result = {
            "delta_z_relative": round(float(delta_z_relative), 4),
            "delta_z_cm": round(float(delta_z_cm), 2),
            "damaged_median": round(float(damaged_median), 4),
            "baseline_median": round(float(baseline_median), 4),
            "confidence": round(float(confidence), 3),
            "class_name": str(class_name),
            "num_damaged_pixels": int(n_damaged),
            "num_surround_pixels": int(n_surround),
        }

        logger.info(
            "Indentation [%s]: Δz = %.2f cm (relative=%.4f, conf=%.2f)",
            class_name, delta_z_cm, delta_z_relative, confidence,
        )

        return result

    # ── Batch: process all YOLO detections ────────────────────
    def compute_all_indentations(
        self,
        depth_map: np.ndarray,
        mask_pairs: List[Tuple[str, np.ndarray]],
    ) -> List[Dict]:
        """
        Compute indentation depth for each (class_name, mask) pair
        from the YOLO damage detector output.

        Args:
            depth_map:   (H, W) float32 relative depth map.
            mask_pairs:  List of (class_name, binary_mask) from DamageDetector.

        Returns:
            List of indentation result dicts.
        """
        results = []
        for cls_name, mask in mask_pairs:
            indent = self.compute_indentation(depth_map, mask, cls_name)
            results.append(indent)
        return results

    # ── Depth heatmap visualisation ───────────────────────────
    def _save_depth_heatmap(
        self,
        depth_map: np.ndarray,
        image_path: str,
        output_dir: Optional[str],
    ) -> str:
        """Render and save a colourised depth heatmap."""
        # Normalise to 0–255
        d_min, d_max = depth_map.min(), depth_map.max()
        if d_max - d_min > 1e-6:
            normalised = ((depth_map - d_min) / (d_max - d_min) * 255).astype(np.uint8)
        else:
            normalised = np.zeros_like(depth_map, dtype=np.uint8)

        # Apply INFERNO colourmap (close = warm, far = cool)
        heatmap = cv2.applyColorMap(normalised, cv2.COLORMAP_INFERNO)

        # Blend with original image
        img_bgr = cv2.imread(image_path)
        if img_bgr is not None:
            if heatmap.shape[:2] != img_bgr.shape[:2]:
                heatmap = cv2.resize(heatmap, (img_bgr.shape[1], img_bgr.shape[0]))
            blended = cv2.addWeighted(img_bgr, 0.4, heatmap, 0.6, 0)
        else:
            blended = heatmap

        # Add colour bar legend
        bar_width = 30
        bar_height = blended.shape[0]
        bar = np.zeros((bar_height, bar_width, 3), dtype=np.uint8)
        for y in range(bar_height):
            val = int(255 * (1.0 - y / bar_height))
            bar[y, :] = cv2.applyColorMap(
                np.array([[val]], dtype=np.uint8), cv2.COLORMAP_INFERNO
            )[0, 0]

        # Add labels
        cv2.putText(bar, "Near", (2, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        cv2.putText(bar, "Far", (2, bar_height - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

        blended = np.hstack([blended, bar])

        # Save
        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = Path(image_path).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(image_path).stem
        out_path = out_dir / f"{stem}_depth_heatmap.jpg"
        cv2.imwrite(str(out_path), blended, [cv2.IMWRITE_JPEG_QUALITY, 92])
        logger.info("Depth heatmap saved: %s", out_path)
        return str(out_path)

    # ── Helper ────────────────────────────────────────────────
    @staticmethod
    def _empty_indentation() -> Dict:
        """Return a zeroed-out indentation result when computation fails."""
        return {
            "delta_z_relative": 0.0,
            "delta_z_cm": 0.0,
            "damaged_median": 0.0,
            "baseline_median": 0.0,
            "confidence": 0.0,
            "class_name": "unknown",
            "num_damaged_pixels": 0,
            "num_surround_pixels": 0,
        }
