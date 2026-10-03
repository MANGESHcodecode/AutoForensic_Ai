"""
AutoForensic AI — Cybersecurity & Digital Media Forensics Module
=================================================================
Phase 1: Pre-processing security gate that validates every uploaded
vehicle image before it enters the Deep Learning inference pipeline.

Submodules:
    - file_validator : Magic-byte signature verification & image re-encoding
    - exif_analyzer  : EXIF metadata extraction & tampering detection
    - ela            : Error Level Analysis engine & visual heatmap generator
    - phash          : 2D-DCT Perceptual Hashing & duplicate claim detector
    - ai_detector    : AI-generated image & inpainting detection (noise, FFT, patches)
    - pipeline       : Unified forensic orchestrator & early rejection gate
"""

from forensics.file_validator import FileValidator
from forensics.exif_analyzer import EXIFAnalyzer
from forensics.ela import ELAAnalyzer
from forensics.phash import PerceptualHasher
from forensics.ai_detector import AIDetector
from forensics.cost_estimator import RepairCostEstimator
from forensics.pipeline import ForensicPipeline

__all__ = [
    "FileValidator",
    "EXIFAnalyzer",
    "ELAAnalyzer",
    "PerceptualHasher",
    "AIDetector",
    "RepairCostEstimator",
    "ForensicPipeline",
]

