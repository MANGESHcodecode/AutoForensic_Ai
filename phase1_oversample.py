"""
Phase 1 - Step 2: Class Imbalance Mitigation via Minority Oversampling
=======================================================================
Strategy:
  - Identify images dominated by rare classes (tire_flat, glass_shatter, crack)
  - Create symbolic duplicates (copies) of those images + labels into the training set
  - This boosts representation without modifying original data
  - YOLOv8's built-in augmentations (mosaic, copy-paste, HSV) will generate
    unique variants from these duplicates during training

Target: Bring all classes to within 2x of the median class count.
"""

import os
import sys
import io
import shutil
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"D:\EDAI 07\CarDD_YOLO_Format"
TRAIN_IMG = os.path.join(BASE, "images", "train2017")
TRAIN_LBL = os.path.join(BASE, "labels", "train2017")

CLASS_NAMES = ["dent", "scratch", "crack", "glass_shatter", "lamp_broken", "tire_flat"]

# ── Step 1: Analyze current distribution ──
print("=" * 70)
print("  Phase 1.2 — Class Imbalance Mitigation")
print("=" * 70)

# Map each image to its set of classes and per-class annotation count
image_classes = defaultdict(Counter)  # stem -> Counter({class_id: count})

label_files = [f for f in os.listdir(TRAIN_LBL) if f.endswith('.txt')]
for f in label_files:
    stem = os.path.splitext(f)[0]
    for line in open(os.path.join(TRAIN_LBL, f)):
        cls_id = int(line.strip().split()[0])
        image_classes[stem][cls_id] += 1

# Current class totals
class_totals = Counter()
for stem, cls_counter in image_classes.items():
    class_totals += cls_counter

print("\n  Current class distribution:")
for i in range(6):
    print(f"    {CLASS_NAMES[i]:>15}: {class_totals[i]:>5}")

# ── Step 2: Identify images where rare classes are DOMINANT ──
# "Dominant" = the rare class makes up ≥50% of annotations in that image,
# OR the image contains ONLY that class.
# This avoids oversampling images dominated by scratch/dent.

RARE_CLASSES = {2: "crack", 3: "glass_shatter", 4: "lamp_broken", 5: "tire_flat"}

# Target: each rare class should have roughly the count of the median class
median_count = sorted(class_totals.values())[len(class_totals) // 2]
print(f"\n  Median class count: {median_count}")
print(f"  Target: boost rare classes toward {int(median_count * 0.8)} annotations")

# Find candidate images for each rare class
rare_class_images = defaultdict(list)  # class_id -> list of stems

for stem, cls_counter in image_classes.items():
    total_in_img = sum(cls_counter.values())
    for cls_id in RARE_CLASSES:
        if cls_id in cls_counter:
            # Include if: class is dominant OR image only has this class type
            dominance = cls_counter[cls_id] / total_in_img
            if dominance >= 0.4 or len(cls_counter) == 1:
                rare_class_images[cls_id].append(stem)

print("\n  Candidate images per rare class:")
for cls_id, stems in sorted(rare_class_images.items()):
    print(f"    {CLASS_NAMES[cls_id]:>15}: {len(stems)} images")

# ── Step 3: Compute oversampling multipliers ──
target_count = int(median_count * 0.8)  # ~80% of median

oversample_plan = {}
for cls_id in RARE_CLASSES:
    current = class_totals[cls_id]
    if current < target_count:
        needed = target_count - current
        candidates = rare_class_images[cls_id]
        if candidates:
            # How many times do we need to duplicate the candidate set?
            # Each duplication adds sum of cls_id annotations from those images
            cls_in_candidates = sum(image_classes[s][cls_id] for s in candidates)
            repeats = max(1, needed // cls_in_candidates)
            repeats = min(repeats, 4)  # Cap at 4x to avoid extreme oversampling
            oversample_plan[cls_id] = (candidates, repeats)
            print(f"\n  Plan for {CLASS_NAMES[cls_id]}:")
            print(f"    Current: {current}, Target: {target_count}, Deficit: {needed}")
            print(f"    Will duplicate {len(candidates)} images × {repeats} copies")
            print(f"    Expected boost: +{cls_in_candidates * repeats} annotations")

# ── Step 4: Execute oversampling ──
print(f"\n{'='*70}")
print("  Executing oversampling...")
print(f"{'='*70}")

copies_made = 0
new_annotations = Counter()

for cls_id, (candidates, repeats) in oversample_plan.items():
    for rep in range(1, repeats + 1):
        for stem in candidates:
            new_stem = f"{stem}_oversample_c{cls_id}_r{rep}"

            # Find original image file
            orig_img = None
            for ext in ['.jpg', '.jpeg', '.png']:
                candidate_path = os.path.join(TRAIN_IMG, stem + ext)
                if os.path.exists(candidate_path):
                    orig_img = candidate_path
                    orig_ext = ext
                    break

            if orig_img is None:
                continue

            new_img = os.path.join(TRAIN_IMG, new_stem + orig_ext)
            new_lbl = os.path.join(TRAIN_LBL, new_stem + ".txt")

            # Copy image and label
            if not os.path.exists(new_img):
                shutil.copy2(orig_img, new_img)
                shutil.copy2(os.path.join(TRAIN_LBL, stem + ".txt"), new_lbl)
                copies_made += 1

                # Track new annotations
                for line in open(new_lbl):
                    cid = int(line.strip().split()[0])
                    new_annotations[cid] += 1

print(f"\n  ✅ Created {copies_made} oversampled image-label pairs")

# ── Step 5: Report new distribution ──
print(f"\n{'='*70}")
print("  New class distribution after oversampling:")
print(f"{'='*70}")

final_totals = class_totals + new_annotations
for i in range(6):
    change = new_annotations.get(i, 0)
    bar = "█" * (final_totals[i] // 50)
    change_str = f" (+{change})" if change > 0 else ""
    print(f"    {CLASS_NAMES[i]:>15}: {final_totals[i]:>5}{change_str:>10}  {bar}")

total_images_now = len(os.listdir(TRAIN_IMG))
total_labels_now = len([f for f in os.listdir(TRAIN_LBL) if f.endswith('.txt')])
print(f"\n  Total training images: {total_images_now}")
print(f"  Total training labels: {total_labels_now}")

# Imbalance ratio
max_cls = max(final_totals.values())
min_cls = min(final_totals.values())
print(f"  Imbalance ratio: {max_cls/min_cls:.1f}x (was {max(class_totals.values())/min(class_totals.values()):.1f}x)")
print(f"\n{'='*70}\n")
