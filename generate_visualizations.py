"""
AutoForensic AI — Dataset Visualization & Preprocessing Insights
================================================================
Generates presentation-quality visualizations for:
  1. Dataset overview & split distribution
  2. Class distribution (per-split & overall)
  3. Before vs After oversampling comparison
  4. Class imbalance ratio improvement
  5. Damage co-occurrence heatmap
  6. Annotation density (annotations per image)
  7. Polygon complexity distribution
  8. Annotation area distribution
  9. Image resolution analysis
  10. Sample annotated images grid
"""

import os
import sys
import io
import json
import numpy as np
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as mticker

# ── Config ──
BASE = r"D:\EDAI 07\CarDD_YOLO_Format"
COCO_TRAIN = r"D:\EDAI 07\CarDD_release\CarDD_COCO\annotations\instances_train2017.json"
OUTPUT_DIR = r"D:\EDAI 07\visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CLASS_NAMES = ["dent", "scratch", "crack", "glass_shatter", "lamp_broken", "tire_flat"]
CLASS_LABELS = ["Dent", "Scratch", "Crack", "Glass\nShatter", "Lamp\nBroken", "Tire\nFlat"]

# Professional color palette
COLORS = ['#4A90D9', '#50C878', '#FF6B6B', '#FFD93D', '#9B59B6', '#FF8C42']
DARK_BG = '#0D1117'
CARD_BG = '#161B22'
TEXT_COLOR = '#E6EDF3'
GRID_COLOR = '#30363D'
ACCENT = '#58A6FF'

# ── Style Setup ──
plt.rcParams.update({
    'figure.facecolor': DARK_BG,
    'axes.facecolor': CARD_BG,
    'axes.edgecolor': GRID_COLOR,
    'axes.labelcolor': TEXT_COLOR,
    'text.color': TEXT_COLOR,
    'xtick.color': TEXT_COLOR,
    'ytick.color': TEXT_COLOR,
    'grid.color': GRID_COLOR,
    'grid.alpha': 0.3,
    'font.family': 'Segoe UI',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'figure.titlesize': 18,
    'figure.titleweight': 'bold',
})


def save_fig(fig, name):
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor(), pad_inches=0.3)
    plt.close(fig)
    print(f"  Saved: {name}.png")
    return path


# ══════════════════════════════════════════════════════════════
# Data Collection
# ══════════════════════════════════════════════════════════════

print("Collecting data...")

# Original (pre-oversample) counts
ORIGINAL_TRAIN = {'dent': 1806, 'scratch': 2560, 'crack': 651, 'glass_shatter': 475, 'lamp_broken': 494, 'tire_flat': 225}
ORIGINAL_IMAGES = 2816

# Current counts (post-oversample) from labels
def get_split_stats(split):
    lbl_dir = os.path.join(BASE, "labels", split)
    files = [f for f in os.listdir(lbl_dir) if f.endswith('.txt')]
    class_counts = Counter()
    ann_per_image = []
    poly_vertices = []
    
    for f in files:
        lines = open(os.path.join(lbl_dir, f)).readlines()
        ann_per_image.append(len(lines))
        for line in lines:
            parts = line.strip().split()
            cls_id = int(parts[0])
            class_counts[cls_id] += 1
            n_vertices = (len(parts) - 1) // 2
            poly_vertices.append(n_vertices)
    
    return {
        'files': len(files),
        'class_counts': class_counts,
        'ann_per_image': ann_per_image,
        'poly_vertices': poly_vertices,
    }

stats = {}
for split in ['train2017', 'val2017', 'test2017']:
    stats[split] = get_split_stats(split)

# COCO data for area analysis and co-occurrence
with open(COCO_TRAIN, 'r') as f:
    coco = json.load(f)

areas = [ann['area'] for ann in coco['annotations']]
cat_map = {c['id']: c['name'] for c in coco['categories']}

# Co-occurrence matrix
img_classes = defaultdict(set)
for ann in coco['annotations']:
    img_classes[ann['image_id']].add(ann['category_id'] - 1)  # 0-indexed

cooccurrence = np.zeros((6, 6), dtype=int)
for classes in img_classes.values():
    classes = list(classes)
    for i in classes:
        for j in classes:
            cooccurrence[i][j] += 1

# Image sizes from COCO
widths = [img['width'] for img in coco['images']]
heights = [img['height'] for img in coco['images']]


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 1: Dataset Overview Dashboard
# ══════════════════════════════════════════════════════════════

print("\nGenerating visualizations...")

fig = plt.figure(figsize=(16, 10))
fig.suptitle("AutoForensic AI — CarDD Dataset Overview", fontsize=22, fontweight='bold', color=ACCENT, y=0.98)

gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

# 1a. Split distribution (donut chart)
ax1 = fig.add_subplot(gs[0, 0])
split_sizes = [stats['train2017']['files'], stats['val2017']['files'], stats['test2017']['files']]
split_labels = [f"Train\n{split_sizes[0]}", f"Val\n{split_sizes[1]}", f"Test\n{split_sizes[2]}"]
split_colors = ['#4A90D9', '#50C878', '#FF6B6B']
wedges, texts = ax1.pie(split_sizes, labels=split_labels, colors=split_colors,
                        startangle=90, wedgeprops=dict(width=0.4, edgecolor=DARK_BG, linewidth=2))
for t in texts:
    t.set_fontsize(10)
    t.set_fontweight('bold')
ax1.set_title("Dataset Splits", pad=15)
total_imgs = sum(split_sizes)
ax1.text(0, 0, f"{total_imgs}\nimages", ha='center', va='center', fontsize=14, fontweight='bold', color=ACCENT)

# 1b. Overall class distribution (horizontal bar)
ax2 = fig.add_subplot(gs[0, 1:])
overall_counts = [stats['train2017']['class_counts'][i] + stats['val2017']['class_counts'][i] + stats['test2017']['class_counts'][i] for i in range(6)]
y_pos = np.arange(6)
bars = ax2.barh(y_pos, overall_counts, color=COLORS, height=0.65, edgecolor=DARK_BG, linewidth=1)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(CLASS_LABELS, fontsize=11, fontweight='bold')
ax2.set_xlabel("Number of Annotations", fontsize=11)
ax2.set_title("Overall Class Distribution (All Splits)", pad=15)
ax2.invert_yaxis()
ax2.grid(axis='x', alpha=0.2)
for bar, count in zip(bars, overall_counts):
    ax2.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2, f'{count:,}',
             va='center', fontsize=11, fontweight='bold', color=TEXT_COLOR)

# 1c. Per-split class breakdown (grouped bar)
ax3 = fig.add_subplot(gs[1, :2])
x = np.arange(6)
width = 0.25
for idx, (split, label, color) in enumerate([('train2017', 'Train', '#4A90D9'), ('val2017', 'Val', '#50C878'), ('test2017', 'Test', '#FF6B6B')]):
    counts = [stats[split]['class_counts'][i] for i in range(6)]
    ax3.bar(x + idx * width, counts, width, label=label, color=color, edgecolor=DARK_BG, linewidth=0.5)
ax3.set_xticks(x + width)
ax3.set_xticklabels(CLASS_LABELS, fontsize=10, fontweight='bold')
ax3.set_ylabel("Annotations", fontsize=11)
ax3.set_title("Class Distribution by Split", pad=15)
ax3.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=10)
ax3.grid(axis='y', alpha=0.2)

# 1d. Annotations per image distribution
ax4 = fig.add_subplot(gs[1, 2])
all_ann = stats['train2017']['ann_per_image']
ax4.hist(all_ann, bins=range(1, max(all_ann)+2), color=ACCENT, edgecolor=DARK_BG, alpha=0.85)
ax4.set_xlabel("Annotations per Image", fontsize=10)
ax4.set_ylabel("Number of Images", fontsize=10)
ax4.set_title("Annotation Density\n(Training Set)", pad=15)
ax4.grid(axis='y', alpha=0.2)
avg_ann = np.mean(all_ann)
ax4.axvline(avg_ann, color='#FF6B6B', linestyle='--', linewidth=2, label=f'Mean: {avg_ann:.1f}')
ax4.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=9)

save_fig(fig, "01_dataset_overview")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 2: Before vs After Oversampling
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Class Imbalance Mitigation — Before vs After Oversampling",
             fontsize=18, fontweight='bold', color=ACCENT, y=1.02)

# 2a. Before
ax = axes[0]
before_counts = [ORIGINAL_TRAIN[n] for n in CLASS_NAMES]
bars = ax.bar(range(6), before_counts, color=COLORS, edgecolor=DARK_BG, linewidth=1, alpha=0.7)
ax.set_xticks(range(6))
ax.set_xticklabels(CLASS_LABELS, fontsize=9, fontweight='bold')
ax.set_ylabel("Annotations", fontsize=11)
ax.set_title(f"BEFORE Oversampling\n({ORIGINAL_IMAGES} images)", pad=15, color='#FF6B6B')
ax.grid(axis='y', alpha=0.2)
for bar, c in zip(bars, before_counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30, str(c),
            ha='center', fontsize=10, fontweight='bold')
# Add imbalance ratio
max_b, min_b = max(before_counts), min(before_counts)
ax.text(0.95, 0.95, f"Imbalance\nRatio: {max_b/min_b:.1f}×", transform=ax.transAxes,
        ha='right', va='top', fontsize=12, fontweight='bold', color='#FF6B6B',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FF6B6B22', edgecolor='#FF6B6B'))

# 2b. After
ax = axes[1]
after_counts = [stats['train2017']['class_counts'][i] for i in range(6)]
bars = ax.bar(range(6), after_counts, color=COLORS, edgecolor=DARK_BG, linewidth=1)
ax.set_xticks(range(6))
ax.set_xticklabels(CLASS_LABELS, fontsize=9, fontweight='bold')
ax.set_ylabel("Annotations", fontsize=11)
ax.set_title(f"AFTER Oversampling\n({stats['train2017']['files']} images)", pad=15, color='#50C878')
ax.grid(axis='y', alpha=0.2)
for bar, c in zip(bars, after_counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30, str(c),
            ha='center', fontsize=10, fontweight='bold')
max_a, min_a = max(after_counts), min(after_counts)
ax.text(0.95, 0.95, f"Imbalance\nRatio: {max_a/min_a:.1f}×", transform=ax.transAxes,
        ha='right', va='top', fontsize=12, fontweight='bold', color='#50C878',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#50C87822', edgecolor='#50C878'))

# 2c. Change (delta)
ax = axes[2]
deltas = [after_counts[i] - before_counts[i] for i in range(6)]
bar_colors = ['#50C878' if d > 0 else '#888' for d in deltas]
bars = ax.bar(range(6), deltas, color=bar_colors, edgecolor=DARK_BG, linewidth=1)
ax.set_xticks(range(6))
ax.set_xticklabels(CLASS_LABELS, fontsize=9, fontweight='bold')
ax.set_ylabel("Annotations Added", fontsize=11)
ax.set_title("Annotations Added\nPer Class", pad=15, color='#FFD93D')
ax.grid(axis='y', alpha=0.2)
for bar, d in zip(bars, deltas):
    label = f"+{d}" if d > 0 else str(d)
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, label,
            ha='center', fontsize=11, fontweight='bold',
            color='#50C878' if d > 0 else '#888')
ax.axhline(0, color=GRID_COLOR, linewidth=1)

plt.tight_layout()
save_fig(fig, "02_before_vs_after_oversampling")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 3: Imbalance Ratio Improvement
# ══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle("Class Imbalance Ratio — Improvement Achieved", fontsize=16, fontweight='bold', color=ACCENT)

# Compute per-class ratio relative to the smallest class
before_ratios = [c / min(before_counts) for c in before_counts]
after_ratios = [c / min(after_counts) for c in after_counts]

x = np.arange(6)
width = 0.35
bars1 = ax.bar(x - width/2, before_ratios, width, label='Before (11.4× max)', color='#FF6B6B', alpha=0.7, edgecolor=DARK_BG)
bars2 = ax.bar(x + width/2, after_ratios, width, label='After (4.4× max)', color='#50C878', edgecolor=DARK_BG)

ax.set_xticks(x)
ax.set_xticklabels(CLASS_LABELS, fontsize=10, fontweight='bold')
ax.set_ylabel("Ratio vs. Smallest Class", fontsize=12)
ax.axhline(1.0, color='#FFD93D', linestyle='--', linewidth=1.5, alpha=0.6, label='Ideal (1.0×)')
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=10)
ax.grid(axis='y', alpha=0.2)

# Annotate ratios
for bar, ratio in zip(bars1, before_ratios):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, f'{ratio:.1f}×',
            ha='center', fontsize=9, fontweight='bold', color='#FF6B6B')
for bar, ratio in zip(bars2, after_ratios):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, f'{ratio:.1f}×',
            ha='center', fontsize=9, fontweight='bold', color='#50C878')

# Arrow showing improvement
ax.annotate('', xy=(0.75, 0.4), xytext=(0.75, 0.8),
            xycoords='axes fraction', textcoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color='#FFD93D', lw=2.5))
ax.text(0.78, 0.6, "61%\nimproved", transform=ax.transAxes, fontsize=12,
        fontweight='bold', color='#FFD93D', va='center')

plt.tight_layout()
save_fig(fig, "03_imbalance_ratio_improvement")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 4: Damage Co-Occurrence Heatmap
# ══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(9, 8))
fig.suptitle("Damage Type Co-Occurrence Matrix", fontsize=16, fontweight='bold', color=ACCENT)

# Normalize diagonal to show conditional probability
cooc_display = cooccurrence.copy().astype(float)
for i in range(6):
    if cooc_display[i][i] > 0:
        cooc_display[i] = cooc_display[i] / cooc_display[i][i] * 100

im = ax.imshow(cooc_display, cmap='YlOrRd', aspect='auto')
ax.set_xticks(range(6))
ax.set_yticks(range(6))
short_labels = ["Dent", "Scratch", "Crack", "Glass\nShatter", "Lamp\nBroken", "Tire\nFlat"]
ax.set_xticklabels(short_labels, fontsize=10, fontweight='bold')
ax.set_yticklabels(short_labels, fontsize=10, fontweight='bold')

# Annotate cells
for i in range(6):
    for j in range(6):
        val = cooccurrence[i][j]
        pct = cooc_display[i][j]
        color = 'white' if pct > 50 else TEXT_COLOR
        ax.text(j, i, f'{val}\n({pct:.0f}%)', ha='center', va='center',
                fontsize=9, fontweight='bold', color=color)

ax.set_xlabel("Co-occurs With →", fontsize=12, labelpad=10)
ax.set_ylabel("Damage Type →", fontsize=12, labelpad=10)

cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Co-occurrence %", fontsize=10, color=TEXT_COLOR)
cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=TEXT_COLOR)

plt.tight_layout()
save_fig(fig, "04_damage_cooccurrence_heatmap")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 5: Annotation Area Distribution
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Damage Region Size Analysis", fontsize=16, fontweight='bold', color=ACCENT, y=1.02)

# 5a. Area distribution (log scale)
ax = axes[0]
areas_np = np.array(areas)
ax.hist(np.log10(areas_np + 1), bins=50, color=ACCENT, edgecolor=DARK_BG, alpha=0.85)
ax.set_xlabel("Damage Area (log₁₀ pixels²)", fontsize=11)
ax.set_ylabel("Count", fontsize=11)
ax.set_title("Damage Area Distribution", pad=15)
ax.grid(axis='y', alpha=0.2)

# Add size markers
median_area = np.median(areas_np)
ax.axvline(np.log10(median_area), color='#FFD93D', linestyle='--', linewidth=2, label=f'Median: {median_area:,.0f} px²')
ax.axvline(np.log10(np.mean(areas_np)), color='#FF6B6B', linestyle='--', linewidth=2, label=f'Mean: {np.mean(areas_np):,.0f} px²')
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=9)

# 5b. Area by damage class
ax = axes[1]
class_areas = defaultdict(list)
for ann in coco['annotations']:
    cls_idx = ann['category_id'] - 1
    class_areas[cls_idx].append(ann['area'])

bp_data = [class_areas[i] for i in range(6)]
bp = ax.boxplot(bp_data, patch_artist=True, tick_labels=short_labels,
                boxprops=dict(linewidth=1.5),
                medianprops=dict(color='white', linewidth=2),
                whiskerprops=dict(color=TEXT_COLOR),
                capprops=dict(color=TEXT_COLOR),
                flierprops=dict(marker='o', markersize=2, alpha=0.3, markerfacecolor=TEXT_COLOR))
for patch, color in zip(bp['boxes'], COLORS):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax.set_yscale('log')
ax.set_ylabel("Area (pixels², log scale)", fontsize=11)
ax.set_title("Damage Area by Class", pad=15)
ax.grid(axis='y', alpha=0.2)

plt.tight_layout()
save_fig(fig, "05_annotation_area_analysis")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 6: Polygon Complexity
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Annotation Quality — Polygon Mask Complexity", fontsize=16, fontweight='bold', color=ACCENT, y=1.02)

# 6a. Vertex count histogram
ax = axes[0]
all_vertices = stats['train2017']['poly_vertices']
ax.hist(all_vertices, bins=50, color='#9B59B6', edgecolor=DARK_BG, alpha=0.85)
ax.set_xlabel("Number of Polygon Vertices", fontsize=11)
ax.set_ylabel("Count", fontsize=11)
ax.set_title("Polygon Vertex Distribution", pad=15)
ax.grid(axis='y', alpha=0.2)
avg_v = np.mean(all_vertices)
ax.axvline(avg_v, color='#FFD93D', linestyle='--', linewidth=2, label=f'Mean: {avg_v:.0f} vertices')
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=10)

# 6b. Quality interpretation
ax = axes[1]
quality_bins = {'Simple\n(3-10)': 0, 'Moderate\n(11-30)': 0, 'Detailed\n(31-80)': 0, 'Highly Detailed\n(80+)': 0}
for v in all_vertices:
    if v <= 10: quality_bins['Simple\n(3-10)'] += 1
    elif v <= 30: quality_bins['Moderate\n(11-30)'] += 1
    elif v <= 80: quality_bins['Detailed\n(31-80)'] += 1
    else: quality_bins['Highly Detailed\n(80+)'] += 1

qcolors = ['#FF6B6B', '#FFD93D', '#50C878', '#4A90D9']
wedges, texts, autotexts = ax.pie(quality_bins.values(), labels=quality_bins.keys(),
                                    colors=qcolors, autopct='%1.1f%%',
                                    startangle=90, wedgeprops=dict(edgecolor=DARK_BG, linewidth=2))
for t in texts:
    t.set_fontsize(10)
    t.set_fontweight('bold')
for t in autotexts:
    t.set_fontsize(9)
    t.set_fontweight('bold')
    t.set_color('white')
ax.set_title("Annotation Quality Breakdown", pad=15)

plt.tight_layout()
save_fig(fig, "06_polygon_complexity")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 7: Image Resolution Analysis
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Image Resolution Analysis", fontsize=16, fontweight='bold', color=ACCENT, y=1.02)

# 7a. Scatter of width vs height
ax = axes[0]
ax.scatter(widths, heights, s=5, alpha=0.15, color=ACCENT, edgecolors='none')
ax.set_xlabel("Width (pixels)", fontsize=11)
ax.set_ylabel("Height (pixels)", fontsize=11)
ax.set_title("Image Size Distribution", pad=15)
ax.grid(alpha=0.2)

# Highlight most common size
from collections import Counter as C2
size_counts = C2(zip(widths, heights))
top_size, top_count = size_counts.most_common(1)[0]
ax.scatter([top_size[0]], [top_size[1]], s=200, color='#FF6B6B', zorder=5, marker='*',
           label=f'Most common: {top_size[0]}×{top_size[1]} ({top_count} imgs)')
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=9, loc='lower right')

# 7b. Aspect ratio histogram
ax = axes[1]
aspect_ratios = [w/h for w, h in zip(widths, heights)]
ax.hist(aspect_ratios, bins=40, color='#FF8C42', edgecolor=DARK_BG, alpha=0.85)
ax.set_xlabel("Aspect Ratio (Width / Height)", fontsize=11)
ax.set_ylabel("Count", fontsize=11)
ax.set_title("Aspect Ratio Distribution", pad=15)
ax.grid(axis='y', alpha=0.2)
ax.axvline(1.0, color='#FF6B6B', linestyle='--', linewidth=2, alpha=0.7, label='Square (1:1)')
ax.axvline(np.median(aspect_ratios), color='#FFD93D', linestyle='--', linewidth=2,
           label=f'Median: {np.median(aspect_ratios):.2f}')
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=9)

plt.tight_layout()
save_fig(fig, "07_image_resolution_analysis")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 8: Pipeline Summary Infographic
# ══════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(16, 8))
fig.suptitle("AutoForensic AI — Data Preprocessing Pipeline Summary",
             fontsize=20, fontweight='bold', color=ACCENT, y=0.97)

ax = fig.add_subplot(111)
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

# Pipeline boxes
def draw_box(ax, x, y, w, h, title, lines, color, border_color):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                     facecolor=color, edgecolor=border_color, linewidth=2)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.25, title, ha='center', va='top',
            fontsize=12, fontweight='bold', color='white')
    for i, line in enumerate(lines):
        ax.text(x + w/2, y + h - 0.6 - i*0.3, line, ha='center', va='top',
                fontsize=9, color='#B0B0B0')

# Step 1: Raw Dataset
draw_box(ax, 0.2, 3.2, 2.2, 2.5, "1. RAW DATASET",
         ["CarDD (COCO Format)", "4,000 images", "8,740 annotations", "6 damage classes", "237 unique sizes"],
         '#1a1a2e', '#4A90D9')

# Arrow
ax.annotate('', xy=(2.8, 4.45), xytext=(2.4, 4.45),
            arrowprops=dict(arrowstyle='->', color='#FFD93D', lw=2.5))

# Step 2: Format Conversion
draw_box(ax, 2.9, 3.2, 2.2, 2.5, "2. YOLO CONVERSION",
         ["COCO → YOLOv8-Seg", "Normalized polygons", "train/val/test split", "70%/20%/10%", "data.yaml created"],
         '#1a1a2e', '#50C878')

# Arrow
ax.annotate('', xy=(5.5, 4.45), xytext=(5.1, 4.45),
            arrowprops=dict(arrowstyle='->', color='#FFD93D', lw=2.5))

# Step 3: Validation
draw_box(ax, 5.6, 3.2, 2.2, 2.5, "3. VALIDATION",
         ["0 corrupted images", "0 missing labels", "All coords [0,1]", "All class IDs valid", "0 empty files"],
         '#1a1a2e', '#FFD93D')

# Arrow
ax.annotate('', xy=(8.2, 4.45), xytext=(7.8, 4.45),
            arrowprops=dict(arrowstyle='->', color='#FFD93D', lw=2.5))

# Step 4: Oversampling
draw_box(ax, 8.3, 3.2, 1.5, 2.5, "4. OVERSAMPLE",
         ["Minority boost", "11.4× → 4.4×", "2816 → 4204 imgs", "+1388 copies"],
         '#1a1a2e', '#FF6B6B')

# Bottom stats bar
stats_text = [
    ("Total Images", f"{total_imgs:,}"),
    ("Total Annotations", f"{sum(overall_counts):,}"),
    ("Avg Vertices/Mask", f"{np.mean(all_vertices):.0f}"),
    ("Imbalance (Before)", "11.4×"),
    ("Imbalance (After)", "4.4×"),
]

for i, (label, val) in enumerate(stats_text):
    x_pos = 0.5 + i * 2.0
    rect = mpatches.FancyBboxPatch((x_pos, 0.3), 1.6, 1.8, boxstyle="round,pad=0.1",
                                     facecolor='#21262D', edgecolor=GRID_COLOR, linewidth=1)
    ax.add_patch(rect)
    ax.text(x_pos + 0.8, 1.6, val, ha='center', va='center',
            fontsize=16, fontweight='bold', color=ACCENT)
    ax.text(x_pos + 0.8, 0.9, label, ha='center', va='center',
            fontsize=9, color='#8B949E')

save_fig(fig, "08_pipeline_summary")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 9: Training Strategy Overview
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(14, 7))
fig.suptitle("YOLOv8m-Seg Training Strategy for Colab T4",
             fontsize=16, fontweight='bold', color=ACCENT, y=1.02)

# 9a. Training hyperparameters as a stylized table
ax = axes[0]
ax.axis('off')
params = [
    ("Model", "YOLOv8m-seg"),
    ("Pretrained", "COCO weights"),
    ("Epochs", "80 (patience: 20)"),
    ("Batch Size", "12"),
    ("Image Size", "640 × 640"),
    ("Optimizer", "SGD + Cosine LR"),
    ("LR", "0.01 → 0.0001"),
    ("AMP", "Enabled (FP16)"),
    ("GPU", "T4 (15GB VRAM)"),
    ("Est. Time", "~2-3 hours"),
]
for i, (key, val) in enumerate(params):
    y_pos = 0.95 - i * 0.09
    bg_color = '#21262D' if i % 2 == 0 else CARD_BG
    ax.text(0.05, y_pos, key, transform=ax.transAxes, fontsize=11, fontweight='bold',
            color='#8B949E', va='center')
    ax.text(0.55, y_pos, val, transform=ax.transAxes, fontsize=11, fontweight='bold',
            color=ACCENT, va='center')
ax.set_title("Hyperparameters", pad=20)

# 9b. Augmentation pipeline visualization
ax = axes[1]
ax.axis('off')
augmentations = [
    ("Mosaic", "1.0", "Combines 4 images", '#4A90D9'),
    ("Copy-Paste", "0.3", "Boosts rare classes", '#50C878'),
    ("MixUp", "0.1", "Blends 2 images", '#FF8C42'),
    ("HSV Augment", "H:0.015 S:0.7 V:0.4", "Color variation", '#FFD93D'),
    ("Horizontal Flip", "0.5", "Mirror augment", '#9B59B6'),
    ("Scale", "0.5", "Multi-scale training", '#FF6B6B'),
    ("Random Erasing", "0.4", "Occlusion robustness", '#4ECDC4'),
    ("Close Mosaic", "Epoch 70+", "Fine-tune last 10", '#E8815E'),
]
for i, (name, val, desc, color) in enumerate(augmentations):
    y_pos = 0.95 - i * 0.115
    # Color dot
    ax.plot(0.02, y_pos, 'o', markersize=10, color=color, transform=ax.transAxes)
    ax.text(0.08, y_pos, name, transform=ax.transAxes, fontsize=11, fontweight='bold',
            color=TEXT_COLOR, va='center')
    ax.text(0.42, y_pos, val, transform=ax.transAxes, fontsize=10,
            color=ACCENT, va='center', fontweight='bold')
    ax.text(0.72, y_pos, desc, transform=ax.transAxes, fontsize=9,
            color='#8B949E', va='center')
ax.set_title("Augmentation Pipeline", pad=20)

plt.tight_layout()
save_fig(fig, "09_training_strategy")


# ══════════════════════════════════════════════════════════════
# VISUALIZATION 10: Multi-damage vs Single-damage
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Multi-Damage Analysis — Real-World Complexity",
             fontsize=16, fontweight='bold', color=ACCENT, y=1.02)

# 10a. Single vs multi-damage pie
ax = axes[0]
single = sum(1 for c in img_classes.values() if len(c) == 1)
multi = sum(1 for c in img_classes.values() if len(c) > 1)
wedges, texts, autotexts = ax.pie([single, multi],
    labels=[f'Single Damage\n({single})', f'Multiple Damages\n({multi})'],
    colors=['#4A90D9', '#FF6B6B'],
    autopct='%1.1f%%', startangle=90,
    wedgeprops=dict(edgecolor=DARK_BG, linewidth=2))
for t in texts: t.set_fontsize(11); t.set_fontweight('bold')
for t in autotexts: t.set_fontsize(11); t.set_fontweight('bold'); t.set_color('white')
ax.set_title("Single vs Multi-Damage Images", pad=15)

# 10b. Top damage combinations
ax = axes[1]
combo_counts = Counter()
for classes in img_classes.values():
    cat_names = tuple(sorted([CLASS_NAMES[c] for c in classes]))
    combo_counts[cat_names] += 1

top_combos = combo_counts.most_common(8)
combo_labels = [' + '.join(c) for c, _ in top_combos]
combo_vals = [v for _, v in top_combos]

y_pos = np.arange(len(combo_labels))
bar_colors = [ACCENT if len(c) == 1 else '#FF6B6B' for c, _ in top_combos]
bars = ax.barh(y_pos, combo_vals, color=bar_colors, height=0.6, edgecolor=DARK_BG)
ax.set_yticks(y_pos)
ax.set_yticklabels(combo_labels, fontsize=9, fontweight='bold')
ax.set_xlabel("Number of Images", fontsize=11)
ax.set_title("Top Damage Combinations", pad=15)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.2)

for bar, val in zip(bars, combo_vals):
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2, str(val),
            va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
save_fig(fig, "10_multi_damage_analysis")


print(f"\n{'='*70}")
print(f"  All 10 visualizations saved to: {OUTPUT_DIR}")
print(f"{'='*70}")
print(f"\n  Files generated:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    size = os.path.getsize(os.path.join(OUTPUT_DIR, f)) / 1024
    print(f"    {f:45s} ({size:.0f} KB)")
