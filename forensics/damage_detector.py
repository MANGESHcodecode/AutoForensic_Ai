"""
AutoForensic AI — YOLOv8 Instance Segmentation Damage Detector
===============================================================
Loads the project-trained YOLOv8-Seg model (Model/best.pt) and runs
per-instance segmentation inference on forensically verified vehicle
images.

Output per detection:
    • Bounding box (xyxy, normalised & pixel)
    • Binary segmentation mask (H×W numpy bool array)
    • Class label (one of 6 CarDD damage categories)
    • Confidence score
    • Approximate surface area in cm² (mask pixel count → camera model)
    • Annotated overlay image saved to output_dir

Classes:
    0: dent
    1: scratch
    2: crack
    3: glass_shatter
    4: lamp_broken
    5: tire_flat
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import numpy as np
import cv2

logger = logging.getLogger("autoforensic.damage_detector")

# ── Default model path relative to project root ───────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_MODEL_PATH = _PROJECT_ROOT / "Model" / "best.pt"

# ── CarDD class mapping (index → label) ───────────────────────
CLASS_NAMES: Dict[int, str] = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "lamp_broken",
    5: "tire_flat",
}

# ── Approximate camera calibration constants ──────────────────
# These defaults assume a typical smartphone at ~50 cm distance.
# For production use, calibrate from actual camera intrinsics.
PIXELS_PER_CM_DEFAULT = 18.0  # ~18 px per real-world cm at 50 cm distance


class DamageDetector:
    """
    Wraps the YOLOv8-Seg model for automotive damage detection.

    Usage:
        detector = DamageDetector()
        results = detector.detect("path/to/image.jpg")
        # results → list of DamageDetection dicts
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        pixels_per_cm: float = PIXELS_PER_CM_DEFAULT,
        device: Optional[str] = None,
    ):
        """
        Args:
            model_path:             Path to YOLOv8-Seg .pt weights.
            confidence_threshold:   Minimum detection confidence.
            iou_threshold:          NMS IoU threshold.
            pixels_per_cm:          Calibration constant for px → cm conversion.
            device:                 'cpu', 'cuda', or None (auto-detect).
        """
        self.model_path = Path(model_path) if model_path else _DEFAULT_MODEL_PATH
        self.conf_thresh = confidence_threshold
        self.iou_thresh = iou_threshold
        self.pixels_per_cm = pixels_per_cm
        self.device = device
        self._model = None

        if not self.model_path.exists():
            logger.warning(
                "YOLOv8-Seg model not found at %s. "
                "Detection will return empty results until model is placed.",
                self.model_path,
            )

    # ── Lazy model loading ────────────────────────────────────
    def _load_model(self):
        """Load the YOLO model on first inference call (lazy init)."""
        if self._model is not None:
            return

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"YOLOv8-Seg model weights not found: {self.model_path}"
            )

        try:
            from ultralytics import YOLO

            logger.info("Loading YOLOv8-Seg model from %s ...", self.model_path)
            self._model = YOLO(str(self.model_path))

            # Override class names if the model doesn't have them
            if hasattr(self._model, "names") and self._model.names:
                logger.info("Model class names: %s", self._model.names)
            else:
                logger.info("Using project-defined class names: %s", CLASS_NAMES)

            logger.info("YOLOv8-Seg model loaded successfully.")

        except ImportError:
            raise ImportError(
                "ultralytics package not installed. "
                "Run: pip install ultralytics"
            )

    # ── Core detection method ─────────────────────────────────
    def detect(
        self,
        image_path: str,
        output_dir: Optional[str] = None,
        save_overlay: bool = True,
    ) -> Dict:
        """
        Run YOLOv8-Seg inference on a single image.

        Args:
            image_path:   Path to the input image (post-forensic verification).
            output_dir:   Directory to save annotated overlay. Defaults to
                          same directory as image_path.
            save_overlay: Whether to save the annotated result image.

        Returns:
            dict with keys:
                detections:      list of per-instance dicts
                annotated_path:  path to overlay image (or None)
                total_detected:  int count of detections
                image_shape:     (H, W) of original image
        """
        self._load_model()

        image_path = str(image_path)
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Read original for dimensions
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"Could not decode image: {image_path}")

        img_h, img_w = img_bgr.shape[:2]

        # Run inference
        results = self._model.predict(
            source=image_path,
            conf=self.conf_thresh,
            iou=self.iou_thresh,
            device=self.device or "",
            verbose=False,
        )

        detections: List[Dict] = []

        if results and len(results) > 0:
            result = results[0]  # single image → single result

            # Extract class names from model
            model_names = (
                result.names if hasattr(result, "names") and result.names
                else CLASS_NAMES
            )

            boxes = result.boxes  # Boxes object
            masks = result.masks  # Masks object (may be None if no segments)

            if boxes is not None and len(boxes) > 0:
                for idx in range(len(boxes)):
                    # Bounding box
                    xyxy = boxes.xyxy[idx].cpu().numpy().tolist()
                    conf = float(boxes.conf[idx].cpu().numpy())
                    cls_id = int(boxes.cls[idx].cpu().numpy())
                    cls_name = model_names.get(cls_id, f"class_{cls_id}")

                    # Segmentation mask
                    mask_binary = None
                    mask_area_px = 0.0
                    area_cm2 = 0.0

                    if masks is not None and idx < len(masks):
                        # masks.data is (N, H_mask, W_mask) tensor
                        mask_tensor = masks.data[idx].cpu().numpy()
                        # Resize to original image dimensions
                        mask_resized = cv2.resize(
                            mask_tensor.astype(np.float32),
                            (img_w, img_h),
                            interpolation=cv2.INTER_LINEAR,
                        )
                        mask_binary = (mask_resized > 0.5).astype(np.uint8)
                        mask_area_px = float(mask_binary.sum())
                        area_cm2 = mask_area_px / (self.pixels_per_cm ** 2)
                    else:
                        # Fallback: estimate area from bounding box
                        x1, y1, x2, y2 = xyxy
                        bbox_area_px = (x2 - x1) * (y2 - y1)
                        mask_area_px = bbox_area_px * 0.65  # ~65% fill ratio
                        area_cm2 = mask_area_px / (self.pixels_per_cm ** 2)

                    detection = {
                        "detection_id": idx + 1,
                        "class_id": cls_id,
                        "class": cls_name,
                        "confidence": round(conf, 4),
                        "bbox_xyxy": [round(v, 1) for v in xyxy],
                        "mask_area_px": round(mask_area_px, 1),
                        "area_cm2": round(area_cm2, 1),
                        "mask": mask_binary,  # numpy array, not serialised
                    }
                    detections.append(detection)

                    logger.info(
                        "  [%d] %s  conf=%.2f  area=%.1f cm²",
                        idx + 1, cls_name, conf, area_cm2,
                    )

        # ── Save annotated overlay ────────────────────────────
        annotated_path = None
        if save_overlay and detections:
            annotated_path = self._save_annotated(
                img_bgr, detections, image_path, output_dir
            )

        logger.info(
            "Damage detection complete: %d instance(s) found in %s",
            len(detections), Path(image_path).name,
        )

        # Strip non-serialisable mask arrays for the return dict
        serialisable_detections = []
        for d in detections:
            d_copy = {k: v for k, v in d.items() if k != "mask"}
            serialisable_detections.append(d_copy)

        return {
            "detections": serialisable_detections,
            "raw_detections": detections,  # includes numpy masks
            "annotated_path": annotated_path,
            "total_detected": len(detections),
            "image_shape": (img_h, img_w),
        }

    # ── Annotated overlay rendering ───────────────────────────
    def _save_annotated(
        self,
        img_bgr: np.ndarray,
        detections: List[Dict],
        image_path: str,
        output_dir: Optional[str],
    ) -> str:
        """Draw bounding boxes, masks, and labels on the image and save."""
        overlay = img_bgr.copy()

        # Color palette for each class (BGR)
        COLORS = {
            "dent":          (0, 165, 255),    # Orange
            "scratch":       (0, 255, 255),    # Yellow
            "crack":         (0, 0, 255),      # Red
            "glass_shatter": (255, 0, 0),      # Blue
            "lamp_broken":   (255, 0, 255),    # Magenta
            "tire_flat":     (128, 128, 0),    # Teal
        }
        DEFAULT_COLOR = (0, 255, 0)  # Green fallback

        for det in detections:
            cls_name = det["class"]
            conf = det["confidence"]
            color = COLORS.get(cls_name, DEFAULT_COLOR)

            # Draw mask overlay (semi-transparent)
            mask = det.get("mask")
            if mask is not None:
                mask_colored = np.zeros_like(overlay)
                mask_colored[mask > 0] = color
                overlay = cv2.addWeighted(overlay, 1.0, mask_colored, 0.35, 0)

            # Draw bounding box
            x1, y1, x2, y2 = [int(v) for v in det["bbox_xyxy"]]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)

            # Label
            label = f"{cls_name} {conf:.0%} ({det['area_cm2']:.0f}cm²)"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(
                overlay,
                (x1, y1 - label_size[1] - 8),
                (x1 + label_size[0] + 4, y1),
                color,
                -1,
            )
            cv2.putText(
                overlay, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2,
            )

        # Determine output path
        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = Path(image_path).parent

        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(image_path).stem
        out_path = out_dir / f"{stem}_damage_overlay.jpg"
        cv2.imwrite(str(out_path), overlay, [cv2.IMWRITE_JPEG_QUALITY, 92])
        logger.info("Annotated overlay saved: %s", out_path)
        return str(out_path)

    # ── Utility: get raw masks for depth analysis ─────────────
    def get_masks_for_depth(
        self, detection_result: Dict
    ) -> List[Tuple[str, np.ndarray]]:
        """
        Extract (class_name, binary_mask) tuples from a detection result.
        Used by DepthEstimator to compute per-damage indentation depth.
        """
        pairs = []
        for det in detection_result.get("raw_detections", []):
            mask = det.get("mask")
            if mask is not None:
                pairs.append((det["class"], mask))
        return pairs
