import os
import json
from collections import Counter

names = ['dent', 'scratch', 'crack', 'glass_shatter', 'lamp_broken', 'tire_flat']
base = r'D:\EDAI 07\CarDD_YOLO_Format\labels'

for split in ['train2017', 'val2017', 'test2017']:
    split_dir = os.path.join(base, split)
    files = [f for f in os.listdir(split_dir) if f.endswith('.txt')]
    
    multi = 0
    single = 0
    total_ann = 0
    poly_lengths = []
    
    for f in files:
        fp = os.path.join(split_dir, f)
        lines = open(fp).readlines()
        n = len(lines)
        total_ann += n
        if n > 1:
            multi += 1
        else:
            single += 1
        for line in lines:
            parts = line.strip().split()
            num_coords = (len(parts) - 1) // 2  # polygon vertex count
            poly_lengths.append(num_coords)
    
    print(f"\n=== {split} ===")
    print(f"  Total images: {len(files)}")
    print(f"  Total annotations: {total_ann}")
    print(f"  Avg annotations/image: {total_ann/len(files):.2f}")
    print(f"  Single-annotation images: {single}")
    print(f"  Multi-annotation images: {multi}")
    print(f"  Avg polygon vertices: {sum(poly_lengths)/len(poly_lengths):.1f}")
    print(f"  Min polygon vertices: {min(poly_lengths)}")
    print(f"  Max polygon vertices: {max(poly_lengths)}")

# Check image sizes from COCO annotations
print("\n\n=== IMAGE SIZE ANALYSIS (from COCO) ===")
coco_path = r'D:\EDAI 07\CarDD_release\CarDD_COCO\annotations\instances_train2017.json'
with open(coco_path, 'r') as f:
    coco = json.load(f)

widths = [img['width'] for img in coco['images']]
heights = [img['height'] for img in coco['images']]
sizes = Counter([(w,h) for w,h in zip(widths, heights)])

print(f"  Total images in COCO train: {len(coco['images'])}")
print(f"  Unique image sizes: {len(sizes)}")
print(f"  Most common sizes (top 5):")
for (w,h), cnt in sizes.most_common(5):
    print(f"    {w}x{h}: {cnt} images")
print(f"  Width range: {min(widths)} - {max(widths)}")
print(f"  Height range: {min(heights)} - {max(heights)}")

# COCO category info
print("\n=== COCO CATEGORIES ===")
for cat in coco['categories']:
    print(f"  id={cat['id']}: {cat['name']}")

# Annotations per category in COCO
cat_counts = Counter(ann['category_id'] for ann in coco['annotations'])
print(f"\n  Total COCO annotations: {len(coco['annotations'])}")
for cat in coco['categories']:
    print(f"  {cat['name']}: {cat_counts.get(cat['id'], 0)}")

# Check annotation area distribution
areas = [ann['area'] for ann in coco['annotations']]
print(f"\n=== ANNOTATION AREA STATS ===")
print(f"  Min area: {min(areas):.1f}")
print(f"  Max area: {max(areas):.1f}")
print(f"  Mean area: {sum(areas)/len(areas):.1f}")
areas_sorted = sorted(areas)
print(f"  Median area: {areas_sorted[len(areas_sorted)//2]:.1f}")

# Check co-occurrence of damage types
print("\n=== DAMAGE CO-OCCURRENCE (per image) ===")
from collections import defaultdict
img_classes = defaultdict(set)
for ann in coco['annotations']:
    img_classes[ann['image_id']].add(ann['category_id'])

combo_counts = Counter()
for img_id, classes in img_classes.items():
    cat_names = tuple(sorted([c['name'] for c in coco['categories'] if c['id'] in classes]))
    combo_counts[cat_names] += 1

print(f"  Images with single damage type: {sum(1 for c in img_classes.values() if len(c)==1)}")
print(f"  Images with multiple damage types: {sum(1 for c in img_classes.values() if len(c)>1)}")
print(f"\n  Top 10 damage combinations:")
for combo, cnt in combo_counts.most_common(10):
    print(f"    {' + '.join(combo)}: {cnt}")
