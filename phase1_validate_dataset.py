"""
Phase 1 - Step 1: Dataset Validation & Integrity Check
=======================================================
Validates:
  1. Image-Label alignment (every image has a label pair)
  2. Corrupted / unreadable images
  3. Label format correctness (class IDs 0-5, valid polygon coords in [0,1])
  4. Empty label files
  5. Images with no corresponding labels and vice versa
"""

import os
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from PIL import Image
from collections import Counter, defaultdict

BASE = r"D:\EDAI 07\CarDD_YOLO_Format"
SPLITS = ["train2017", "val2017", "test2017"]
NUM_CLASSES = 6
CLASS_NAMES = ["dent", "scratch", "crack", "glass_shatter", "lamp_broken", "tire_flat"]
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

total_issues = 0

def log_issue(msg):
    global total_issues
    total_issues += 1
    print(f"  ❌ {msg}")

def log_ok(msg):
    print(f"  ✅ {msg}")

print("=" * 70)
print("  AutoForensic AI — Dataset Validation Report")
print("=" * 70)

for split in SPLITS:
    print(f"\n{'='*70}")
    print(f"  SPLIT: {split}")
    print(f"{'='*70}")

    img_dir = os.path.join(BASE, "images", split)
    lbl_dir = os.path.join(BASE, "labels", split)

    # --- 1. Collect file stems ---
    img_files = {}
    for f in os.listdir(img_dir):
        ext = os.path.splitext(f)[1].lower()
        if ext in VALID_EXTENSIONS:
            stem = os.path.splitext(f)[0]
            img_files[stem] = f

    lbl_files = {}
    for f in os.listdir(lbl_dir):
        if f.endswith(".txt"):
            stem = os.path.splitext(f)[0]
            lbl_files[stem] = f

    img_stems = set(img_files.keys())
    lbl_stems = set(lbl_files.keys())

    # --- 2. Alignment check ---
    imgs_without_labels = img_stems - lbl_stems
    lbls_without_images = lbl_stems - img_stems

    if imgs_without_labels:
        log_issue(f"{len(imgs_without_labels)} images have NO label file")
        for s in list(imgs_without_labels)[:5]:
            print(f"       → {img_files[s]}")
        if len(imgs_without_labels) > 5:
            print(f"       → ... and {len(imgs_without_labels)-5} more")
    else:
        log_ok(f"All {len(img_stems)} images have matching label files")

    if lbls_without_images:
        log_issue(f"{len(lbls_without_images)} labels have NO image file")
        for s in list(lbls_without_images)[:5]:
            print(f"       → {lbl_files[s]}")
    else:
        log_ok(f"All {len(lbl_stems)} labels have matching image files")

    # --- 3. Image corruption check ---
    corrupted = []
    img_sizes = []
    for stem in sorted(img_stems & lbl_stems):
        fpath = os.path.join(img_dir, img_files[stem])
        try:
            with Image.open(fpath) as img:
                img.verify()  # verify integrity
            # Re-open to get size (verify() leaves file in bad state)
            with Image.open(fpath) as img:
                img_sizes.append((img.width, img.height))
        except Exception as e:
            corrupted.append((img_files[stem], str(e)))

    if corrupted:
        log_issue(f"{len(corrupted)} corrupted images found:")
        for name, err in corrupted[:5]:
            print(f"       → {name}: {err}")
    else:
        log_ok(f"All {len(img_stems & lbl_stems)} images passed integrity check")

    # --- 4. Label format validation ---
    empty_labels = []
    invalid_class_ids = []
    invalid_coords = []
    too_few_vertices = []
    class_counts = Counter()
    annotations_per_image = []

    paired_stems = sorted(img_stems & lbl_stems)
    for stem in paired_stems:
        fpath = os.path.join(lbl_dir, lbl_files[stem])
        lines = open(fpath, "r").readlines()

        if len(lines) == 0:
            empty_labels.append(lbl_files[stem])
            annotations_per_image.append(0)
            continue

        annotations_per_image.append(len(lines))

        for line_idx, line in enumerate(lines):
            parts = line.strip().split()
            if len(parts) < 7:  # class_id + at least 3 vertices (6 coords)
                too_few_vertices.append((lbl_files[stem], line_idx + 1, len(parts)))
                continue

            try:
                class_id = int(parts[0])
            except ValueError:
                invalid_class_ids.append((lbl_files[stem], line_idx + 1, parts[0]))
                continue

            if class_id < 0 or class_id >= NUM_CLASSES:
                invalid_class_ids.append((lbl_files[stem], line_idx + 1, class_id))
                continue

            class_counts[class_id] += 1

            # Validate coordinates are in [0, 1]
            coords = parts[1:]
            if len(coords) % 2 != 0:
                invalid_coords.append((lbl_files[stem], line_idx + 1, "odd number of coordinates"))
                continue

            for i in range(0, len(coords), 2):
                try:
                    x, y = float(coords[i]), float(coords[i + 1])
                    if x < -0.01 or x > 1.01 or y < -0.01 or y > 1.01:
                        invalid_coords.append((lbl_files[stem], line_idx + 1, f"coord out of range: ({x},{y})"))
                        break
                except ValueError:
                    invalid_coords.append((lbl_files[stem], line_idx + 1, f"non-numeric: {coords[i]},{coords[i+1]}"))
                    break

    # Report
    if empty_labels:
        log_issue(f"{len(empty_labels)} empty label files (0 annotations)")
        for name in empty_labels[:3]:
            print(f"       → {name}")
    else:
        log_ok("No empty label files")

    if invalid_class_ids:
        log_issue(f"{len(invalid_class_ids)} lines with invalid class IDs")
        for name, ln, cid in invalid_class_ids[:3]:
            print(f"       → {name}:{ln} class_id={cid}")
    else:
        log_ok("All class IDs valid (0-5)")

    if invalid_coords:
        log_issue(f"{len(invalid_coords)} lines with invalid coordinates")
        for name, ln, reason in invalid_coords[:3]:
            print(f"       → {name}:{ln} — {reason}")
    else:
        log_ok("All polygon coordinates valid and normalized [0,1]")

    if too_few_vertices:
        log_issue(f"{len(too_few_vertices)} annotations with < 3 polygon vertices")
        for name, ln, nparts in too_few_vertices[:3]:
            print(f"       → {name}:{ln} — only {nparts} values")
    else:
        log_ok("All polygons have ≥ 3 vertices")

    # --- 5. Summary stats ---
    print(f"\n  📊 Class distribution ({split}):")
    for i in range(NUM_CLASSES):
        bar = "█" * (class_counts[i] // 50)
        print(f"     {i} ({CLASS_NAMES[i]:>15}): {class_counts[i]:>5}  {bar}")

    total = sum(class_counts.values())
    print(f"     {'':>18}  Total: {total}")

    if annotations_per_image:
        avg = sum(annotations_per_image) / len(annotations_per_image)
        max_ann = max(annotations_per_image)
        print(f"  📊 Annotations/image: avg={avg:.2f}, max={max_ann}")

# --- Final verdict ---
print(f"\n{'='*70}")
if total_issues == 0:
    print("  🎉 DATASET VALIDATION PASSED — 0 issues found!")
    print("  The dataset is clean and ready for training.")
else:
    print(f"  ⚠️  VALIDATION COMPLETE — {total_issues} issues found.")
    print("  Review issues above before training.")
print(f"{'='*70}\n")
