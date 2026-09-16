"""
AutoForensic AI — YOLOv8-Seg Production Training Script
========================================================
Optimized for: Google Colab Free Tier (T4 GPU, 15GB VRAM)
Dataset: CarDD with minority oversampling applied

Usage (Colab):
  !python train_yolov8_seg.py

The script will:
  1. Load YOLOv8m-seg pretrained weights
  2. Train for 80 epochs with cosine LR, class-aware augmentation
  3. Save best weights for deployment
"""

from ultralytics import YOLO

# ── Model Selection ──
# yolov8m-seg: Medium model — best balance of accuracy & T4 VRAM usage
# yolov8s-seg: Small model — faster, lower accuracy (use if OOM on T4)
# yolov8l-seg: Large model — needs >15GB VRAM (A100 only)
model = YOLO("yolov8m-seg.pt")

# ── Training Configuration ──
# All parameters optimized for CarDD dataset + T4 constraints
results = model.train(
    # ─── Data ───
    data="CarDD_YOLO_Format/data_colab.yaml",
    
    # ─── Training Schedule ───
    epochs=80,                  # 80 epochs is sufficient for ~4200 images
    patience=20,                # Early stopping: stop if no improvement for 20 epochs
    batch=12,                   # 12 fits T4 (15GB) with yolov8m-seg at 640px
                                # Reduce to 8 if you get CUDA OOM errors
    imgsz=640,                  # Standard YOLO input size
    
    # ─── Optimizer ───
    optimizer="SGD",            # SGD with momentum for stable convergence
    lr0=0.01,                   # Initial learning rate
    lrf=0.01,                   # Final LR = lr0 * lrf = 0.0001
    cos_lr=True,                # Cosine annealing for smooth LR decay
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3.0,          # 3 epoch warmup to stabilize early training
    warmup_momentum=0.8,
    warmup_bias_lr=0.1,
    
    # ─── Augmentation (tuned for CarDD) ───
    mosaic=1.0,                 # Mosaic augmentation — combines 4 images
    copy_paste=0.3,             # Copy-paste augmentation — helps rare classes
    mixup=0.1,                  # Light mixup for regularization
    hsv_h=0.015,                # Hue shift
    hsv_s=0.7,                  # Saturation shift
    hsv_v=0.4,                  # Value/brightness shift
    degrees=0.0,                # No rotation (cars have fixed orientation)
    translate=0.1,              # Light translation
    scale=0.5,                  # Scale augmentation
    fliplr=0.5,                 # Horizontal flip (valid for cars)
    flipud=0.0,                 # No vertical flip (cars don't appear upside down)
    erasing=0.4,                # Random erasing for robustness
    close_mosaic=10,            # Disable mosaic for last 10 epochs (fine-tuning)
    
    # ─── Architecture ───
    overlap_mask=True,          # Allow overlapping instance masks
    mask_ratio=4,               # Mask downsampling ratio
    
    # ─── Hardware ───
    device=0,                   # GPU 0 (T4 on Colab)
    workers=2,                  # Colab has limited CPU cores
    amp=True,                   # Mixed precision — critical for T4 VRAM savings
    
    # ─── Saving ───
    save=True,
    save_period=20,             # Checkpoint every 20 epochs
    plots=True,                 # Generate training plots
    val=True,                   # Validate each epoch
    
    # ─── Reproducibility ───
    seed=42,
    deterministic=True,
    
    # ─── Project ───
    project="autoforensic_runs",
    name="cardd_yolov8m_seg",
    exist_ok=True,
)

print("\n" + "=" * 60)
print("  Training Complete!")
print("=" * 60)
print(f"  Best weights: autoforensic_runs/cardd_yolov8m_seg/weights/best.pt")
print(f"  Last weights: autoforensic_runs/cardd_yolov8m_seg/weights/last.pt")
print(f"  Results:      autoforensic_runs/cardd_yolov8m_seg/results.csv")
print("=" * 60)
