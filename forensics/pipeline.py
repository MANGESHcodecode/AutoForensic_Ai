"""
AutoForensic AI — Unified Forensic Pipeline & Early Rejection Gate
====================================================================
Orchestrates all five forensic security layers into a single verification
flow. This is the main entry point for the cybersecurity pre-processing
gate that every uploaded vehicle image must pass through before entering
the YOLOv8-Seg Deep Learning damage detection pipeline.

Pipeline Execution Order:
    1. File Validator   → Magic-byte check & re-encoding sanitization
    2. EXIF Analyzer    → Metadata extraction & tampering detection
    3. ELA Engine       → Error Level Analysis & heatmap generation
    4. pHash Detector   → Perceptual hash & duplicate claim screening
    5. AI Detector      → Noise residual, FFT spectral & patch anomaly scanner

Final Decision:
    PASSED_AUTHENTIC   : Image cleared for Deep Learning inference (score ≥ 70)
    SUSPICIOUS_REVIEW  : Needs manual surveyor inspection (40 ≤ score < 70)
    FRAUD_REJECTED     : Pipeline halted immediately (score < 40 or hard reject)

Strict Missing-EXIF Policy:
    If camera hardware metadata is absent (WhatsApp export, web download,
    AI generation), the maximum possible score is capped at 65% and the
    verdict is forced to SUSPICIOUS_REVIEW regardless of other scores.

The pipeline saves forensic artifacts (ELA heatmaps, composite images)
to an output directory for audit trail and report generation.
"""

import json
import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from forensics.file_validator import FileValidator, FileValidationResult
from forensics.exif_analyzer import EXIFAnalyzer, EXIFAnalysisResult
from forensics.ela import ELAAnalyzer, ELAResult
from forensics.phash import PerceptualHasher, PHashResult, DuplicateCheckResult
from forensics.ai_detector import AIDetector, AIDetectionResult

logger = logging.getLogger("autoforensic.forensics.pipeline")


# ══════════════════════════════════════════════════════════════
# DECISION THRESHOLDS
# ══════════════════════════════════════════════════════════════

THRESHOLD_AUTHENTIC = 70.0     # Score ≥ 70 → PASSED_AUTHENTIC
THRESHOLD_SUSPICIOUS = 40.0    # Score ≥ 40 → SUSPICIOUS_REVIEW
                               # Score <  40 → FRAUD_REJECTED

# Component weight distribution for final score
WEIGHTS = {
    "file_validation": 0.15,   # 15% — structural integrity
    "exif_analysis":   0.20,   # 20% — metadata authenticity
    "ela_analysis":    0.25,   # 25% — compression consistency
    "phash_check":     0.15,   # 15% — duplicate detection
    "ai_detection":    0.25,   # 25% — AI generation / inpainting detection
}


class ForensicVerdict:
    """Possible verdicts from the forensic pipeline."""
    PASSED = "PASSED_AUTHENTIC"
    SUSPICIOUS = "SUSPICIOUS_REVIEW"
    REJECTED = "FRAUD_REJECTED"


class ForensicReport:
    """Complete forensic analysis report for a single image submission."""

    def __init__(
        self,
        image_source: str,
        verdict: str,
        overall_score: float,
        file_validation: dict,
        exif_analysis: dict,
        ela_analysis: dict,
        phash_result: dict,
        duplicate_check: Optional[dict],
        ai_detection: Optional[dict] = None,
        risk_flags: list = None,
        processing_time_ms: float = 0.0,
        timestamp: str = "",
        image_sha256: str = "",
        ela_heatmap_path: Optional[str] = None,
        ela_composite_path: Optional[str] = None,
        ai_heatmap_path: Optional[str] = None,
    ):
        self.image_source = image_source
        self.verdict = verdict
        self.overall_score = overall_score
        self.file_validation = file_validation
        self.exif_analysis = exif_analysis
        self.ela_analysis = ela_analysis
        self.phash_result = phash_result
        self.duplicate_check = duplicate_check
        self.ai_detection = ai_detection
        self.risk_flags = risk_flags or []
        self.processing_time_ms = processing_time_ms
        self.timestamp = timestamp
        self.image_sha256 = image_sha256
        self.ela_heatmap_path = ela_heatmap_path
        self.ela_composite_path = ela_composite_path
        self.ai_heatmap_path = ai_heatmap_path

    def to_dict(self) -> dict:
        return {
            "image_source": self.image_source,
            "verdict": self.verdict,
            "overall_score": round(self.overall_score, 2),
            "component_scores": {
                "file_validation": self.file_validation,
                "exif_analysis": self.exif_analysis,
                "ela_analysis": self.ela_analysis,
                "phash_result": self.phash_result,
                "duplicate_check": self.duplicate_check,
                "ai_detection": self.ai_detection,
            },
            "risk_flags": self.risk_flags,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "timestamp": self.timestamp,
            "image_sha256": self.image_sha256,
            "artifacts": {
                "ela_heatmap": self.ela_heatmap_path,
                "ela_composite": self.ela_composite_path,
                "ai_heatmap": self.ai_heatmap_path,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def __repr__(self) -> str:
        return (
            f"ForensicReport(verdict={self.verdict}, "
            f"score={self.overall_score:.1f}%, "
            f"flags={len(self.risk_flags)}, "
            f"time={self.processing_time_ms:.0f}ms)"
        )


class ForensicPipeline:
    """
    Unified forensic verification pipeline for AutoForensic AI.

    Runs all four security layers sequentially and produces a
    comprehensive forensic report with an overall authenticity
    score and a pass/review/reject decision.

    Usage:
        >>> pipeline = ForensicPipeline(output_dir="forensic_output")
        >>> report = pipeline.verify("path/to/car_damage.jpg")
        >>> print(report.verdict)         # "PASSED_AUTHENTIC"
        >>> print(report.overall_score)   # 85.0
        >>> print(report.to_json())       # Full JSON report
    """

    def __init__(
        self,
        output_dir: str = "forensic_output",
        save_artifacts: bool = True,
        ela_quality: int = 90,
        ela_scale: int = 20,
        phash_duplicate_threshold: int = 5,
        ai_patch_size: int = 64,
        ai_noise_threshold: float = 3.0,
    ):
        """
        Args:
            output_dir: Directory to save forensic artifacts (heatmaps, reports).
            save_artifacts: Whether to save ELA heatmaps and composites.
            ela_quality: JPEG quality for ELA recompression.
            ela_scale: Error visualization scaling factor.
            phash_duplicate_threshold: Hamming distance for duplicate detection.
            ai_patch_size: Patch size for AI local anomaly scanner.
            ai_noise_threshold: Noise disparity threshold for AI inpainting detection.
        """
        self.output_dir = Path(output_dir)
        self.save_artifacts = save_artifacts

        # Initialize component analyzers
        self.file_validator = FileValidator()
        self.exif_analyzer = EXIFAnalyzer()
        self.ela_analyzer = ELAAnalyzer(
            quality=ela_quality,
            scale_factor=ela_scale,
        )
        self.phash_hasher = PerceptualHasher(
            duplicate_threshold=phash_duplicate_threshold,
        )
        self.ai_detector = AIDetector(
            patch_size=ai_patch_size,
            noise_disparity_threshold=ai_noise_threshold,
        )

        # Create output directory
        if save_artifacts:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def verify(
        self,
        image_input,
        source_label: Optional[str] = None,
        check_duplicates: bool = True,
        register_hash: bool = True,
    ) -> ForensicReport:
        """
        Run the complete forensic verification pipeline on an image.

        Args:
            image_input: File path (str/Path) or raw bytes.
            source_label: Identifier for this submission (e.g., claim ID).
            check_duplicates: Whether to check against registered hashes.
            register_hash: Whether to register this hash after verification.

        Returns:
            ForensicReport with verdict, scores, flags, and artifact paths.
        """
        start_time = time.perf_counter()
        all_risk_flags = []
        component_scores = {}

        # Determine source label
        if source_label is None:
            if isinstance(image_input, (str, Path)):
                source_label = Path(image_input).name
            else:
                source_label = f"upload_{int(time.time())}"

        # Compute SHA-256 of raw input for audit trail
        image_sha256 = self._compute_sha256(image_input)

        # ════════════════════════════════════════════════════════
        # LAYER 1: File Signature Validation & Sanitization
        # ════════════════════════════════════════════════════════
        logger.info("━━━ Layer 1: File Validation ━━━")
        file_result = self.file_validator.validate(image_input)

        if not file_result.is_valid:
            # HARD REJECT — don't proceed further
            elapsed = (time.perf_counter() - start_time) * 1000
            all_risk_flags.append(f"FILE_REJECTED: {file_result.rejection_reason}")
            return ForensicReport(
                image_source=source_label,
                verdict=ForensicVerdict.REJECTED,
                overall_score=0.0,
                file_validation=file_result.to_dict(),
                exif_analysis={"skipped": "File validation failed"},
                ela_analysis={"skipped": "File validation failed"},
                phash_result={"skipped": "File validation failed"},
                duplicate_check=None,
                risk_flags=all_risk_flags,
                processing_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
                image_sha256=image_sha256,
            )

        # Use sanitized bytes for subsequent analysis
        clean_bytes = file_result.sanitized_bytes
        all_risk_flags.extend(
            [f"FILE_WARNING: {w}" for w in file_result.warnings]
        )
        component_scores["file_validation"] = 100.0  # Passed = full score

        # ════════════════════════════════════════════════════════
        # LAYER 2: EXIF Metadata Forensic Analysis
        # ════════════════════════════════════════════════════════
        logger.info("━━━ Layer 2: EXIF Analysis ━━━")
        exif_result = self.exif_analyzer.analyze(
            image_input if isinstance(image_input, (str, Path)) else clean_bytes
        )

        component_scores["exif_analysis"] = exif_result.authenticity_score
        all_risk_flags.extend(
            [f"EXIF: {flag}" for flag in exif_result.risk_flags]
        )

        # ════════════════════════════════════════════════════════
        # LAYER 3: Error Level Analysis
        # ════════════════════════════════════════════════════════
        logger.info("━━━ Layer 3: Error Level Analysis ━━━")
        ela_result = self.ela_analyzer.analyze(
            image_input if isinstance(image_input, (str, Path)) else clean_bytes
        )

        component_scores["ela_analysis"] = ela_result.authenticity_score
        all_risk_flags.extend(
            [f"ELA: {flag}" for flag in ela_result.risk_flags]
        )

        # Save ELA artifacts
        ela_heatmap_path = None
        ela_composite_path = None
        if self.save_artifacts and ela_result.heatmap_image is not None:
            safe_name = "".join(
                c if c.isalnum() or c in "._-" else "_"
                for c in source_label
            )
            heatmap_file = self.output_dir / f"{safe_name}_ela_heatmap.jpg"
            composite_file = self.output_dir / f"{safe_name}_ela_composite.jpg"

            self.ela_analyzer.save_heatmap(ela_result, str(heatmap_file))

            ela_heatmap_path = str(heatmap_file)
            ela_composite_path = str(composite_file)

        # ════════════════════════════════════════════════════════
        # LAYER 4: Perceptual Hash & Duplicate Detection
        # ════════════════════════════════════════════════════════
        logger.info("━━━ Layer 4: Perceptual Hashing ━━━")
        try:
            phash_result = self.phash_hasher.compute_hash(
                image_input if isinstance(image_input, (str, Path)) else clean_bytes
            )
            phash_dict = phash_result.to_dict()

            # Check for duplicates in registry
            duplicate_result = None
            if check_duplicates:
                dup_check = self.phash_hasher.check_duplicate(phash_result)
                if dup_check is not None:
                    duplicate_result = dup_check.to_dict()
                    if dup_check.is_duplicate:
                        all_risk_flags.append(
                            f"DUPLICATE_CLAIM: Image matches '{dup_check.match_source}' "
                            f"(distance={dup_check.hamming_distance}, "
                            f"similarity={dup_check.similarity_pct:.1f}%)"
                        )
                        component_scores["phash_check"] = 0.0  # Duplicate = zero
                    else:
                        component_scores["phash_check"] = 100.0
                else:
                    component_scores["phash_check"] = 100.0
            else:
                component_scores["phash_check"] = 100.0

            # Register hash for future comparisons
            if register_hash:
                self.phash_hasher.register_hash(phash_result, source=source_label)

        except Exception as e:
            logger.error("pHash computation failed: %s", e)
            phash_dict = {"error": str(e)}
            duplicate_result = None
            component_scores["phash_check"] = 50.0  # Neutral on failure

        # ════════════════════════════════════════════════════════
        # LAYER 5: AI-Generated Image & Inpainting Detection
        # ════════════════════════════════════════════════════════
        logger.info("━━━ Layer 5: AI Detection ━━━")
        ai_detection_dict = None
        ai_heatmap_path = None
        try:
            ai_result = self.ai_detector.analyze(
                image_input if isinstance(image_input, (str, Path)) else clean_bytes
            )
            ai_detection_dict = ai_result.to_dict()
            component_scores["ai_detection"] = ai_result.authenticity_score
            all_risk_flags.extend(
                [f"AI_DETECT: {flag}" for flag in ai_result.risk_flags]
            )

            # Save AI inpainting anomaly heatmap artifact
            if self.save_artifacts and hasattr(ai_result, "save_heatmap") and ai_result.heatmap is not None:
                safe_name = Path(str(source_label)).stem.replace(" ", "_")
                ai_heatmap_path = str(self.output_dir / f"{safe_name}_ai_heatmap.jpg")
                ai_result.save_heatmap(ai_heatmap_path)
                logger.info("AI inpainting heatmap saved to %s", ai_heatmap_path)
        except Exception as e:
            logger.error("AI detection failed: %s", e)
            ai_detection_dict = {"error": str(e)}
            component_scores["ai_detection"] = 50.0  # Neutral on failure

        # ════════════════════════════════════════════════════════
        # FINAL SCORE & VERDICT
        # ════════════════════════════════════════════════════════
        overall_score = sum(
            component_scores.get(component, 0.0) * weight
            for component, weight in WEIGHTS.items()
        )

        # ── Strict Missing-EXIF Downgrade Policy ──
        # In insurance claims, every legitimate photo must come from a
        # physical camera. If camera hardware EXIF is completely absent
        # (WhatsApp export, web download, AI generation), cap the score
        # and force SUSPICIOUS_REVIEW. This prevents "compression
        # laundering" where AI-edited images are sent through WhatsApp
        # to strip all forensic metadata.
        has_camera_exif = exif_result.has_exif and exif_result.has_camera_hardware
        missing_exif_downgrade = False

        if not has_camera_exif:
            missing_exif_downgrade = True
            # Cap at 65% maximum — cannot auto-pass without camera metadata
            if overall_score > 65.0:
                overall_score = 65.0
                logger.info(
                    "Score capped at 65%% due to missing camera EXIF metadata"
                )

        # Determine verdict
        if any("DUPLICATE_CLAIM" in f for f in all_risk_flags):
            verdict = ForensicVerdict.REJECTED
            overall_score = min(overall_score, 15.0)  # Cap score for duplicates
        elif ai_detection_dict and ai_detection_dict.get("is_ai_suspected", False) and (
            ai_detection_dict.get("overall_ai_score", 100.0) < 50.0
            or (
                ai_detection_dict.get("noise_score", 100.0) <= 50.0
                and ai_detection_dict.get("patch_score", 100.0) <= 60.0
            )
            or (
                ai_detection_dict.get("patch_metrics", {}).get("max_noise_disparity", 0.0) > 12.0
                and ai_detection_dict.get("noise_score", 100.0) < 60.0
            )
        ):
            # High-confidence AI damage inpainting / generation detected
            verdict = ForensicVerdict.REJECTED
            overall_score = min(overall_score, 25.0)
            all_risk_flags.insert(
                0,
                f"FRAUD_AI_INPAINTING: Claim image rejected due to confirmed synthetic AI "
                f"damage inpainting (AI score: {ai_detection_dict.get('overall_ai_score', 0):.1f}%). "
                f"Damage features were artificially synthesized."
            )
        elif missing_exif_downgrade and overall_score >= THRESHOLD_SUSPICIOUS:
            # Force SUSPICIOUS_REVIEW when camera metadata is missing
            verdict = ForensicVerdict.SUSPICIOUS
            if not any("MISSING_CAMERA_EXIF" in f for f in all_risk_flags):
                all_risk_flags.append(
                    "MISSING_CAMERA_EXIF: No camera hardware metadata detected. "
                    "Image may be from WhatsApp, web download, or AI generation. "
                    "Score capped at 65%% — manual surveyor review required."
                )
        elif ai_detection_dict and ai_detection_dict.get("is_ai_suspected", False):
            # Moderate AI anomaly: force SUSPICIOUS_REVIEW and cap score
            verdict = ForensicVerdict.SUSPICIOUS
            overall_score = min(overall_score, 45.0)
            all_risk_flags.append(
                f"AI_MANIPULATION_SUSPECTED: Statistical markers suggest synthetic AI "
                f"generation or inpainting (AI score: {ai_detection_dict.get('overall_ai_score', 0):.1f}%). "
                f"Forensic expert review required."
            )
        elif overall_score >= THRESHOLD_AUTHENTIC:
            verdict = ForensicVerdict.PASSED
        elif overall_score >= THRESHOLD_SUSPICIOUS:
            verdict = ForensicVerdict.SUSPICIOUS
        else:
            verdict = ForensicVerdict.REJECTED

        elapsed = (time.perf_counter() - start_time) * 1000

        logger.info(
            "━━━ Forensic Verdict: %s (Score: %.1f%%, Flags: %d, Time: %.0fms) ━━━",
            verdict, overall_score, len(all_risk_flags), elapsed,
        )

        report = ForensicReport(
            image_source=source_label,
            verdict=verdict,
            overall_score=overall_score,
            file_validation=file_result.to_dict(),
            exif_analysis=exif_result.to_dict(),
            ela_analysis=ela_result.to_dict(),
            phash_result=phash_dict,
            duplicate_check=duplicate_result,
            ai_detection=ai_detection_dict,
            risk_flags=all_risk_flags,
            processing_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc).isoformat(),
            image_sha256=image_sha256,
            ela_heatmap_path=ela_heatmap_path,
            ela_composite_path=ela_composite_path,
            ai_heatmap_path=ai_heatmap_path,
        )

        # Save JSON report
        if self.save_artifacts:
            self._save_report(report, source_label)

        return report

    def _compute_sha256(self, image_input) -> str:
        """Compute SHA-256 hash of the raw image input."""
        try:
            if isinstance(image_input, (str, Path)):
                data = Path(image_input).read_bytes()
            elif isinstance(image_input, bytes):
                data = image_input
            else:
                data = b""
            return hashlib.sha256(data).hexdigest()
        except Exception:
            return "sha256_computation_failed"

    def _save_report(self, report: ForensicReport, source_label: str) -> None:
        """Save the forensic report as JSON."""
        safe_name = "".join(
            c if c.isalnum() or c in "._-" else "_"
            for c in source_label
        )
        report_path = self.output_dir / f"{safe_name}_forensic_report.json"
        try:
            report_path.write_text(report.to_json(), encoding="utf-8")
            logger.info("Forensic report saved: %s", report_path)
        except Exception as e:
            logger.error("Failed to save forensic report: %s", e)

    def get_stats(self) -> dict:
        """Get pipeline statistics."""
        return {
            "registered_hashes": self.phash_hasher.get_registry_size(),
            "output_directory": str(self.output_dir),
        }
