"""
AutoForensic AI — Model Evaluation Visualizations
===================================================
Generates presentation-quality charts from YOLOv8-Seg test results.
Run this LOCALLY (it uses the metrics you shared from Colab).
"""

import os
import sys
import io
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

OUTPUT_DIR = r"D:\EDAI 07\visualizations\model_evaluation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════
# MODEL RESULTS (from Colab test evaluation)
# ══════════════════════════════════════════════════════════════

CLASS_NAMES = ['dent', 'scratch', 'crack', 'glass_shatter', 'lamp_broken', 'tire_flat']
CLASS_DISPLAY = ['Dent', 'Scratch', 'Crack', 'Glass\nShatter', 'Lamp\nBroken', 'Tire\nFlat']
INSTANCES = [236, 307, 70, 71, 69, 32]

# Box metrics
BOX_P  = [0.716, 0.690, 0.630, 0.951, 0.899, 0.895]
BOX_R  = [0.530, 0.544, 0.500, 0.972, 0.776, 0.844]
BOX_mAP50 = [0.635, 0.604, 0.588, 0.993, 0.871, 0.893]
BOX_mAP50_95 = [0.375, 0.352, 0.351, 0.955, 0.758, 0.881]

# Mask (Segmentation) metrics
MASK_P  = [0.7099, 0.6816, 0.6123, 0.9507, 0.8992, 0.8953]
MASK_R  = [0.5254, 0.5375, 0.4857, 0.9718, 0.7762, 0.8438]
MASK_mAP50 = [0.6123, 0.5986, 0.5558, 0.9926, 0.8794, 0.8933]
MASK_mAP50_95 = [0.3425, 0.2916, 0.2056, 0.9234, 0.7404, 0.8742]

# Overall metrics
OVERALL_BOX = {'P': 0.797, 'R': 0.694, 'mAP50': 0.764, 'mAP50-95': 0.612}
OVERALL_MASK = {'P': 0.792, 'R': 0.690, 'mAP50': 0.755, 'mAP50-95': 0.563}

# Speed
SPEED = {'preprocess': 1.3, 'inference': 23.9, 'postprocess': 3.5}  # ms per image

# Color scheme
COLORS = ['#4A90D9', '#50C878', '#FF6B6B', '#FFD93D', '#9B59B6', '#FF8C42']
DARK_BG = '#0D1117'
CARD_BG = '#161B22'
TEXT_COLOR = '#E6EDF3'
GRID_COLOR = '#30363D'
ACCENT = '#58A6FF'
GREEN = '#50C878'
RED = '#FF6B6B'
YELLOW = '#FFD93D'

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


def get_performance_color(val):
    """Return color based on performance tier"""
    if val >= 0.85: return '#50C878'   # Excellent - green
    elif val >= 0.65: return '#FFD93D' # Good - yellow
    elif val >= 0.50: return '#FF8C42' # Moderate - orange
    else: return '#FF6B6B'             # Needs improvement - red


print("Generating model evaluation visualizations...\n")


# ══════════════════════════════════════════════════════════════
# VIZ 1: Overall Performance Dashboard
# ══════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(18, 10))
fig.suptitle("AutoForensic AI — YOLOv8m-Seg Model Performance Dashboard",
             fontsize=22, fontweight='bold', color=ACCENT, y=0.98)

gs = GridSpec(2, 4, figure=fig, hspace=0.45, wspace=0.35)

# Row 1: Gauge-style metric cards
metrics_data = [
    ("Box mAP50", OVERALL_BOX['mAP50'], "Detection"),
    ("Box mAP50-95", OVERALL_BOX['mAP50-95'], "Detection"),
    ("Mask mAP50", OVERALL_MASK['mAP50'], "Segmentation"),
    ("Mask mAP50-95", OVERALL_MASK['mAP50-95'], "Segmentation"),
]

for i, (label, val, category) in enumerate(metrics_data):
    ax = fig.add_subplot(gs[0, i])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Background ring
    theta = np.linspace(0, 2*np.pi, 100)
    ring_r = 0.35
    ax.plot(0.5 + ring_r * np.cos(theta), 0.45 + ring_r * np.sin(theta),
            color=GRID_COLOR, linewidth=12, alpha=0.3)

    # Filled ring (proportional to value)
    n_pts = int(val * 100)
    theta_fill = np.linspace(np.pi/2, np.pi/2 - 2*np.pi*val, n_pts)
    color = get_performance_color(val)
    ax.plot(0.5 + ring_r * np.cos(theta_fill), 0.45 + ring_r * np.sin(theta_fill),
            color=color, linewidth=12, solid_capstyle='round')

    # Value text
    ax.text(0.5, 0.45, f"{val:.1%}", ha='center', va='center',
            fontsize=22, fontweight='bold', color=color)
    ax.text(0.5, 0.88, label, ha='center', va='center',
            fontsize=12, fontweight='bold', color=TEXT_COLOR)
    ax.text(0.5, 0.02, category, ha='center', va='center',
            fontsize=9, color='#8B949E',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#21262D', edgecolor=GRID_COLOR))

# Row 2: Key summary stats
ax2 = fig.add_subplot(gs[1, :2])
ax2.axis('off')
ax2.set_title("Overall Metrics Summary", pad=15, fontsize=14)

metrics_table = [
    ("Metric", "Box", "Mask"),
    ("Precision", f"{OVERALL_BOX['P']:.1%}", f"{OVERALL_MASK['P']:.1%}"),
    ("Recall", f"{OVERALL_BOX['R']:.1%}", f"{OVERALL_MASK['R']:.1%}"),
    ("mAP@50", f"{OVERALL_BOX['mAP50']:.1%}", f"{OVERALL_MASK['mAP50']:.1%}"),
    ("mAP@50-95", f"{OVERALL_BOX['mAP50-95']:.1%}", f"{OVERALL_MASK['mAP50-95']:.1%}"),
    ("F1 Score", f"{2*OVERALL_BOX['P']*OVERALL_BOX['R']/(OVERALL_BOX['P']+OVERALL_BOX['R']):.1%}",
                 f"{2*OVERALL_MASK['P']*OVERALL_MASK['R']/(OVERALL_MASK['P']+OVERALL_MASK['R']):.1%}"),
]

for i, (metric, box_val, mask_val) in enumerate(metrics_table):
    y = 0.88 - i * 0.15
    weight = 'bold' if i == 0 else 'normal'
    color = ACCENT if i == 0 else TEXT_COLOR
    ax2.text(0.15, y, metric, transform=ax2.transAxes, fontsize=12,
             fontweight='bold', color='#8B949E', va='center')
    ax2.text(0.55, y, box_val, transform=ax2.transAxes, fontsize=12,
             fontweight=weight, color=color if i == 0 else '#4A90D9', va='center', ha='center')
    ax2.text(0.82, y, mask_val, transform=ax2.transAxes, fontsize=12,
             fontweight=weight, color=color if i == 0 else '#9B59B6', va='center', ha='center')

# Speed & inference stats
ax3 = fig.add_subplot(gs[1, 2:])
ax3.axis('off')
ax3.set_title("Inference Performance", pad=15, fontsize=14)

total_ms = sum(SPEED.values())
fps = 1000 / total_ms

speed_items = [
    ("Total Latency", f"{total_ms:.1f} ms", ACCENT),
    ("Throughput", f"{fps:.0f} FPS", GREEN),
    ("Preprocess", f"{SPEED['preprocess']:.1f} ms", '#8B949E'),
    ("Inference", f"{SPEED['inference']:.1f} ms", YELLOW),
    ("Postprocess", f"{SPEED['postprocess']:.1f} ms", '#8B949E'),
    ("Test Images", "374", TEXT_COLOR),
    ("Test Instances", "785", TEXT_COLOR),
]

for i, (label, val, color) in enumerate(speed_items):
    y = 0.88 - i * 0.13
    ax3.text(0.1, y, label, transform=ax3.transAxes, fontsize=11,
             fontweight='bold', color='#8B949E', va='center')
    ax3.text(0.75, y, val, transform=ax3.transAxes, fontsize=13,
             fontweight='bold', color=color, va='center', ha='right')

save_fig(fig, "01_performance_dashboard")


# ══════════════════════════════════════════════════════════════
# VIZ 2: Per-Class Segmentation Performance (Grouped Bar)
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Per-Class Segmentation Metrics (Instance Masks)",
             fontsize=18, fontweight='bold', color=ACCENT, y=0.98)

metrics_list = [
    ("Precision", MASK_P, axes[0, 0]),
    ("Recall", MASK_R, axes[0, 1]),
    ("mAP@50", MASK_mAP50, axes[1, 0]),
    ("mAP@50-95", MASK_mAP50_95, axes[1, 1]),
]

for title, values, ax in metrics_list:
    x = np.arange(6)
    bar_colors = [get_performance_color(v) for v in values]
    bars = ax.bar(x, values, color=bar_colors, width=0.65, edgecolor=DARK_BG, linewidth=1)

    ax.set_xticks(x)
    ax.set_xticklabels(CLASS_DISPLAY, fontsize=9, fontweight='bold')
    ax.set_ylabel(title, fontsize=11)
    ax.set_title(title, pad=12)
    ax.set_ylim(0, 1.1)
    ax.grid(axis='y', alpha=0.2)

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.1%}', ha='center', fontsize=10, fontweight='bold',
                color=get_performance_color(val))

    # Add threshold lines
    ax.axhline(0.85, color=GREEN, linestyle='--', linewidth=1, alpha=0.4)
    ax.axhline(0.65, color=YELLOW, linestyle='--', linewidth=1, alpha=0.4)
    ax.axhline(0.50, color=RED, linestyle='--', linewidth=1, alpha=0.4)

plt.tight_layout(rect=[0, 0, 1, 0.95])
save_fig(fig, "02_per_class_metrics")


# ══════════════════════════════════════════════════════════════
# VIZ 3: Radar / Spider Chart — Per-Class Performance
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 3, figsize=(16, 11), subplot_kw=dict(polar=True))
fig.suptitle("Per-Class Performance Profiles (Radar Charts)",
             fontsize=18, fontweight='bold', color=ACCENT, y=0.98)

categories = ['Precision', 'Recall', 'mAP50', 'mAP50-95']
N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]

for idx, ax in enumerate(axes.flat):
    ax.set_facecolor(CARD_BG)

    values = [MASK_P[idx], MASK_R[idx], MASK_mAP50[idx], MASK_mAP50_95[idx]]
    values += values[:1]

    ax.plot(angles, values, 'o-', linewidth=2.5, color=COLORS[idx], markersize=6)
    ax.fill(angles, values, alpha=0.2, color=COLORS[idx])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=8, fontweight='bold', color=TEXT_COLOR)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(['0.25', '0.50', '0.75', '1.0'], fontsize=7, color='#8B949E')
    ax.yaxis.grid(True, color=GRID_COLOR, alpha=0.3)
    ax.xaxis.grid(True, color=GRID_COLOR, alpha=0.3)
    ax.spines['polar'].set_color(GRID_COLOR)

    # Title with average score
    avg = np.mean(values[:-1])
    ax.set_title(f"{CLASS_NAMES[idx].replace('_', ' ').title()}\n(avg: {avg:.1%})",
                 pad=18, fontsize=11, fontweight='bold', color=COLORS[idx])

plt.tight_layout(rect=[0, 0, 1, 0.94])
save_fig(fig, "03_radar_profiles")


# ══════════════════════════════════════════════════════════════
# VIZ 4: Box vs Mask Performance Comparison
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle("Detection (Box) vs Segmentation (Mask) Performance",
             fontsize=18, fontweight='bold', color=ACCENT, y=1.02)

# 4a. mAP50 comparison
ax = axes[0]
x = np.arange(6)
width = 0.35
bars1 = ax.bar(x - width/2, BOX_mAP50, width, label='Box mAP50', color='#4A90D9', edgecolor=DARK_BG)
bars2 = ax.bar(x + width/2, MASK_mAP50, width, label='Mask mAP50', color='#9B59B6', edgecolor=DARK_BG)
ax.set_xticks(x)
ax.set_xticklabels(CLASS_DISPLAY, fontsize=9, fontweight='bold')
ax.set_ylabel("mAP@50", fontsize=12)
ax.set_title("mAP@50 — Box vs Mask", pad=12)
ax.set_ylim(0, 1.15)
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=10)
ax.grid(axis='y', alpha=0.2)

for bar, val in zip(bars1, BOX_mAP50):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.1%}', ha='center', fontsize=8, fontweight='bold', color='#4A90D9')
for bar, val in zip(bars2, MASK_mAP50):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.1%}', ha='center', fontsize=8, fontweight='bold', color='#9B59B6')

# 4b. mAP50-95 comparison
ax = axes[1]
bars1 = ax.bar(x - width/2, BOX_mAP50_95, width, label='Box mAP50-95', color='#4A90D9', edgecolor=DARK_BG)
bars2 = ax.bar(x + width/2, MASK_mAP50_95, width, label='Mask mAP50-95', color='#9B59B6', edgecolor=DARK_BG)
ax.set_xticks(x)
ax.set_xticklabels(CLASS_DISPLAY, fontsize=9, fontweight='bold')
ax.set_ylabel("mAP@50-95", fontsize=12)
ax.set_title("mAP@50-95 — Box vs Mask (Strict)", pad=12)
ax.set_ylim(0, 1.15)
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=10)
ax.grid(axis='y', alpha=0.2)

for bar, val in zip(bars1, BOX_mAP50_95):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.1%}', ha='center', fontsize=8, fontweight='bold', color='#4A90D9')
for bar, val in zip(bars2, MASK_mAP50_95):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.1%}', ha='center', fontsize=8, fontweight='bold', color='#9B59B6')

plt.tight_layout()
save_fig(fig, "04_box_vs_mask_comparison")


# ══════════════════════════════════════════════════════════════
# VIZ 5: F1 Score & Performance Tiers
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle("Model Performance Analysis — F1 Scores & Performance Tiers",
             fontsize=18, fontweight='bold', color=ACCENT, y=1.02)

# 5a. F1 scores (Box & Mask)
ax = axes[0]
box_f1 = [2*p*r/(p+r) if (p+r) > 0 else 0 for p, r in zip(BOX_P, BOX_R)]
mask_f1 = [2*p*r/(p+r) if (p+r) > 0 else 0 for p, r in zip(MASK_P, MASK_R)]

x = np.arange(6)
width = 0.35
bars1 = ax.bar(x - width/2, box_f1, width, label='Box F1', color='#4A90D9', edgecolor=DARK_BG)
bars2 = ax.bar(x + width/2, mask_f1, width, label='Mask F1', color='#9B59B6', edgecolor=DARK_BG)
ax.set_xticks(x)
ax.set_xticklabels(CLASS_DISPLAY, fontsize=9, fontweight='bold')
ax.set_ylabel("F1 Score", fontsize=12)
ax.set_title("F1 Score by Class", pad=12)
ax.set_ylim(0, 1.15)
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=10)
ax.grid(axis='y', alpha=0.2)
ax.axhline(0.7, color=GREEN, linestyle='--', linewidth=1, alpha=0.4, label='Good threshold')

for bar, val in zip(bars1, box_f1):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.2f}', ha='center', fontsize=9, fontweight='bold', color='#4A90D9')
for bar, val in zip(bars2, mask_f1):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.2f}', ha='center', fontsize=9, fontweight='bold', color='#9B59B6')

# 5b. Performance tiers
ax = axes[1]
ax.axis('off')
ax.set_title("Performance Classification", pad=20)

tiers = [
    ("EXCELLENT", "mAP50 > 85%", ['glass_shatter', 'tire_flat', 'lamp_broken'], GREEN),
    ("GOOD", "mAP50 65-85%", [], YELLOW),
    ("MODERATE", "mAP50 50-65%", ['dent', 'scratch', 'crack'], '#FF8C42'),
    ("NEEDS WORK", "mAP50 < 50%", [], RED),
]

for i, (tier, criteria, classes, color) in enumerate(tiers):
    y = 0.85 - i * 0.22

    # Tier badge
    ax.text(0.05, y, tier, transform=ax.transAxes, fontsize=13, fontweight='bold',
            color=color, va='center',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=f'{color}22', edgecolor=color, linewidth=1.5))

    # Criteria
    ax.text(0.38, y, criteria, transform=ax.transAxes, fontsize=10,
            color='#8B949E', va='center')

    # Classes
    if classes:
        class_str = ', '.join([c.replace('_', ' ').title() for c in classes])
        ax.text(0.65, y, class_str, transform=ax.transAxes, fontsize=11,
                fontweight='bold', color=TEXT_COLOR, va='center')
    else:
        ax.text(0.65, y, "—", transform=ax.transAxes, fontsize=11,
                color='#555', va='center')

plt.tight_layout()
save_fig(fig, "05_f1_and_tiers")


# ══════════════════════════════════════════════════════════════
# VIZ 6: Precision vs Recall Scatter
# ══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(10, 8))
fig.suptitle("Precision vs Recall — Per-Class Trade-off",
             fontsize=16, fontweight='bold', color=ACCENT)

# Plot each class as a bubble (size = number of instances)
for i in range(6):
    size = INSTANCES[i] / max(INSTANCES) * 800 + 100
    ax.scatter(MASK_R[i], MASK_P[i], s=size, c=COLORS[i], alpha=0.7,
               edgecolors='white', linewidth=2, zorder=5)
    # Label
    offset_x = 0.02 if MASK_R[i] < 0.8 else -0.05
    offset_y = 0.02
    ax.annotate(f"{CLASS_NAMES[i].replace('_', ' ').title()}\n({INSTANCES[i]} inst.)",
                (MASK_R[i], MASK_P[i]), fontsize=9, fontweight='bold',
                xytext=(MASK_R[i] + offset_x, MASK_P[i] + offset_y),
                color=COLORS[i])

# F1 iso-curves
for f1 in [0.3, 0.5, 0.7, 0.8, 0.9]:
    r_range = np.linspace(0.01, 1.0, 100)
    p_range = f1 * r_range / (2 * r_range - f1)
    valid = (p_range >= 0) & (p_range <= 1) & (r_range >= 0)
    ax.plot(r_range[valid], p_range[valid], '--', color=GRID_COLOR, alpha=0.5, linewidth=1)
    # Label the curve
    idx_label = np.argmin(np.abs(r_range - 0.95))
    if valid[idx_label] and p_range[idx_label] <= 1:
        ax.text(0.95, p_range[idx_label], f'F1={f1}', fontsize=7, color='#555', va='center')

ax.set_xlabel("Recall", fontsize=13, fontweight='bold')
ax.set_ylabel("Precision", fontsize=13, fontweight='bold')
ax.set_xlim(0.35, 1.05)
ax.set_ylim(0.5, 1.05)
ax.grid(alpha=0.2)

# Add overall marker
overall_r = OVERALL_MASK['R']
overall_p = OVERALL_MASK['P']
ax.scatter(overall_r, overall_p, s=300, c=ACCENT, marker='*', zorder=10,
           edgecolors='white', linewidth=1.5)
ax.annotate(f"Overall\n(P={overall_p:.1%}, R={overall_r:.1%})",
            (overall_r, overall_p), fontsize=10, fontweight='bold',
            xytext=(overall_r - 0.12, overall_p - 0.06), color=ACCENT,
            arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.5))

# Size legend
ax.text(0.02, 0.02, "Bubble size = number of instances in test set",
        transform=ax.transAxes, fontsize=8, color='#8B949E',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#21262D', edgecolor=GRID_COLOR))

save_fig(fig, "06_precision_vs_recall")


# ══════════════════════════════════════════════════════════════
# VIZ 7: Instance Distribution vs Performance
# ══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 7))
fig.suptitle("Training Data vs Model Performance — Does More Data Help?",
             fontsize=16, fontweight='bold', color=ACCENT)

x = np.arange(6)
width = 0.35

# Normalize instances for visual comparison
max_inst = max(INSTANCES)
norm_instances = [i / max_inst for i in INSTANCES]

ax2 = ax.twinx()

bars1 = ax.bar(x - width/2, INSTANCES, width, color=COLORS, alpha=0.6,
               edgecolor=DARK_BG, linewidth=1, label='Test Instances')
line = ax2.plot(x, MASK_mAP50, 'o-', color=ACCENT, linewidth=3, markersize=10,
                label='Mask mAP50', zorder=5)
line2 = ax2.plot(x, MASK_mAP50_95, 's--', color='#FF8C42', linewidth=2.5, markersize=8,
                 label='Mask mAP50-95', zorder=5)

ax.set_xticks(x)
ax.set_xticklabels(CLASS_DISPLAY, fontsize=10, fontweight='bold')
ax.set_ylabel("Test Instances", fontsize=12, color='#8B949E')
ax2.set_ylabel("mAP Score", fontsize=12, color=ACCENT)
ax2.set_ylim(0, 1.1)
ax.grid(axis='y', alpha=0.15)

# Combine legends
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, facecolor=CARD_BG,
          edgecolor=GRID_COLOR, fontsize=10, loc='upper left')

# Annotate instance counts
for bar, inst in zip(bars1, INSTANCES):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            str(inst), ha='center', fontsize=10, fontweight='bold', color='#8B949E')

# Annotate mAP values
for i, (m50, m95) in enumerate(zip(MASK_mAP50, MASK_mAP50_95)):
    ax2.text(i, m50 + 0.03, f'{m50:.1%}', ha='center', fontsize=9,
             fontweight='bold', color=ACCENT)

plt.tight_layout()
save_fig(fig, "07_data_vs_performance")


# ══════════════════════════════════════════════════════════════
# VIZ 8: Comprehensive Heatmap
# ══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(12, 7))
fig.suptitle("Complete Metrics Heatmap — All Classes × All Metrics",
             fontsize=16, fontweight='bold', color=ACCENT)

# Build the matrix
metric_names = ['Box P', 'Box R', 'Box mAP50', 'Box mAP50-95',
                'Mask P', 'Mask R', 'Mask mAP50', 'Mask mAP50-95']
matrix = np.array([
    BOX_P, BOX_R, BOX_mAP50, BOX_mAP50_95,
    MASK_P, MASK_R, MASK_mAP50, MASK_mAP50_95
])

im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0.15, vmax=1.0)
ax.set_xticks(np.arange(6))
ax.set_yticks(np.arange(8))
ax.set_xticklabels([c.replace('\n', ' ') for c in CLASS_DISPLAY], fontsize=10, fontweight='bold')
ax.set_yticklabels(metric_names, fontsize=10, fontweight='bold')

# Annotate values
for i in range(8):
    for j in range(6):
        val = matrix[i, j]
        color = 'white' if val < 0.5 or val > 0.85 else 'black'
        ax.text(j, i, f'{val:.1%}', ha='center', va='center',
                fontsize=10, fontweight='bold', color=color)

# Add divider between Box and Mask metrics
ax.axhline(3.5, color=ACCENT, linewidth=2, linestyle='-')
ax.text(-0.7, 1.5, 'BOX', rotation=90, va='center', ha='center',
        fontsize=10, fontweight='bold', color='#4A90D9')
ax.text(-0.7, 5.5, 'MASK', rotation=90, va='center', ha='center',
        fontsize=10, fontweight='bold', color='#9B59B6')

cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
cbar.set_label("Score", fontsize=10, color=TEXT_COLOR)
cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=TEXT_COLOR)

plt.tight_layout()
save_fig(fig, "08_metrics_heatmap")


# ══════════════════════════════════════════════════════════════
# VIZ 9: Model Summary Infographic
# ══════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(18, 9))
fig.suptitle("AutoForensic AI — Trained Model Summary Card",
             fontsize=22, fontweight='bold', color=ACCENT, y=0.97)

ax = fig.add_subplot(111)
ax.set_xlim(0, 12)
ax.set_ylim(0, 7)
ax.axis('off')

# ── Model Info Card ──
rect = FancyBboxPatch((0.3, 4.2), 3.5, 2.3, boxstyle="round,pad=0.15",
                       facecolor='#1a1a2e', edgecolor='#4A90D9', linewidth=2)
ax.add_patch(rect)
ax.text(2.05, 6.15, "MODEL", ha='center', fontsize=10, fontweight='bold', color='#4A90D9')
items = [
    ("Architecture", "YOLOv8m-seg"),
    ("Task", "Instance Segmentation"),
    ("Classes", "6 damage types"),
    ("Training", "80 epochs, T4 GPU"),
    ("Dataset", "4,204 train images"),
]
for i, (k, v) in enumerate(items):
    ax.text(0.6, 5.85 - i*0.38, k, fontsize=9, color='#8B949E', fontweight='bold')
    ax.text(2.3, 5.85 - i*0.38, v, fontsize=10, color=TEXT_COLOR, fontweight='bold')

# ── Performance Card ──
rect = FancyBboxPatch((4.2, 4.2), 3.5, 2.3, boxstyle="round,pad=0.15",
                       facecolor='#1a1a2e', edgecolor=GREEN, linewidth=2)
ax.add_patch(rect)
ax.text(5.95, 6.15, "PERFORMANCE", ha='center', fontsize=10, fontweight='bold', color=GREEN)
perf_items = [
    ("Mask mAP@50", f"{OVERALL_MASK['mAP50']:.1%}", ACCENT),
    ("Mask mAP@50-95", f"{OVERALL_MASK['mAP50-95']:.1%}", ACCENT),
    ("Precision", f"{OVERALL_MASK['P']:.1%}", GREEN),
    ("Recall", f"{OVERALL_MASK['R']:.1%}", YELLOW),
    ("Inference Speed", f"{SPEED['inference']:.0f}ms ({1000/sum(SPEED.values()):.0f} FPS)", TEXT_COLOR),
]
for i, (k, v, c) in enumerate(perf_items):
    ax.text(4.5, 5.85 - i*0.38, k, fontsize=9, color='#8B949E', fontweight='bold')
    ax.text(6.3, 5.85 - i*0.38, v, fontsize=10, color=c, fontweight='bold')

# ── Best/Worst Card ──
rect = FancyBboxPatch((8.1, 4.2), 3.5, 2.3, boxstyle="round,pad=0.15",
                       facecolor='#1a1a2e', edgecolor=YELLOW, linewidth=2)
ax.add_patch(rect)
ax.text(9.85, 6.15, "CLASS INSIGHTS", ha='center', fontsize=10, fontweight='bold', color=YELLOW)
insight_items = [
    ("Best Class", "Glass Shatter (99.3%)", GREEN),
    ("Runner Up", "Tire Flat (89.3%)", GREEN),
    ("Hardest", "Crack (55.6%)", RED),
    ("Most Common", f"Scratch ({INSTANCES[1]} inst.)", '#8B949E'),
    ("Rarest", f"Tire Flat ({INSTANCES[5]} inst.)", '#8B949E'),
]
for i, (k, v, c) in enumerate(insight_items):
    ax.text(8.4, 5.85 - i*0.38, k, fontsize=9, color='#8B949E', fontweight='bold')
    ax.text(9.8, 5.85 - i*0.38, v, fontsize=10, color=c, fontweight='bold')

# ── Bottom: Per-class horizontal bar chart ──
class_short = ['Dent', 'Scratch', 'Crack', 'Glass Shat.', 'Lamp Broken', 'Tire Flat']
for i in range(6):
    y = 3.2 - i * 0.55
    # Class name
    ax.text(0.5, y + 0.1, class_short[i], fontsize=10, fontweight='bold', color=COLORS[i], va='center')
    # Background bar
    rect_bg = FancyBboxPatch((2.5, y - 0.1), 8.5, 0.35, boxstyle="round,pad=0.05",
                               facecolor='#21262D', edgecolor='none')
    ax.add_patch(rect_bg)
    # Filled bar (proportional to mAP50)
    bar_width = MASK_mAP50[i] * 8.5
    bar_color = get_performance_color(MASK_mAP50[i])
    rect_fill = FancyBboxPatch((2.5, y - 0.1), bar_width, 0.35, boxstyle="round,pad=0.05",
                                 facecolor=bar_color, edgecolor='none', alpha=0.8)
    ax.add_patch(rect_fill)
    # Value label
    ax.text(2.5 + bar_width + 0.15, y + 0.08, f'{MASK_mAP50[i]:.1%}',
            fontsize=10, fontweight='bold', color=bar_color, va='center')

save_fig(fig, "09_model_summary_card")


# ══════════════════════════════════════════════════════════════
# VIZ 10: Strengths & Weaknesses Analysis
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.suptitle("Model Strengths & Areas for Improvement",
             fontsize=18, fontweight='bold', color=ACCENT, y=1.02)

# 10a. Waterfall chart showing contribution to overall mAP
ax = axes[0]
weighted_map = [MASK_mAP50[i] * INSTANCES[i] / sum(INSTANCES) for i in range(6)]
sorted_idx = np.argsort(weighted_map)[::-1]

y_pos = np.arange(6)
sorted_values = [weighted_map[i] for i in sorted_idx]
sorted_names = [CLASS_NAMES[i].replace('_', ' ').title() for i in sorted_idx]
sorted_colors = [COLORS[i] for i in sorted_idx]

bars = ax.barh(y_pos, sorted_values, color=sorted_colors, height=0.6, edgecolor=DARK_BG)
ax.set_yticks(y_pos)
ax.set_yticklabels(sorted_names, fontsize=11, fontweight='bold')
ax.set_xlabel("Weighted Contribution to Overall mAP50", fontsize=11)
ax.set_title("Contribution to Overall mAP50\n(weighted by instances)", pad=15)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.2)

for bar, val in zip(bars, sorted_values):
    ax.text(bar.get_width() + 0.003, bar.get_y() + bar.get_height()/2,
            f'{val:.3f}', va='center', fontsize=10, fontweight='bold')

# 10b. Gap analysis — room for improvement
ax = axes[1]
perfect = [1.0] * 6
gaps = [1.0 - MASK_mAP50[i] for i in range(6)]
sorted_gap_idx = np.argsort(gaps)[::-1]

y_pos = np.arange(6)
sorted_gaps = [gaps[i] for i in sorted_gap_idx]
sorted_achieved = [MASK_mAP50[i] for i in sorted_gap_idx]
sorted_names2 = [CLASS_NAMES[i].replace('_', ' ').title() for i in sorted_gap_idx]
sorted_colors2 = [COLORS[i] for i in sorted_gap_idx]

# Achieved (filled)
bars_achieved = ax.barh(y_pos, sorted_achieved, color=sorted_colors2, height=0.6,
                         edgecolor=DARK_BG, alpha=0.8, label='Achieved')
# Gap (lighter)
bars_gap = ax.barh(y_pos, sorted_gaps, left=sorted_achieved, color='#21262D',
                    height=0.6, edgecolor=GRID_COLOR, linewidth=0.5, label='Room for improvement')

ax.set_yticks(y_pos)
ax.set_yticklabels(sorted_names2, fontsize=11, fontweight='bold')
ax.set_xlabel("mAP50 Score", fontsize=11)
ax.set_title("Gap to Perfect Score (100%)\n— Room for Improvement", pad=15)
ax.invert_yaxis()
ax.set_xlim(0, 1.1)
ax.grid(axis='x', alpha=0.2)
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, fontsize=9)

for i, (achieved, gap) in enumerate(zip(sorted_achieved, sorted_gaps)):
    ax.text(achieved/2, i, f'{achieved:.1%}', ha='center', va='center',
            fontsize=10, fontweight='bold', color='white')
    if gap > 0.05:
        ax.text(achieved + gap/2, i, f'-{gap:.1%}', ha='center', va='center',
                fontsize=9, color='#FF6B6B', fontweight='bold')

plt.tight_layout()
save_fig(fig, "10_strengths_weaknesses")


print(f"\n{'='*70}")
print(f"  All 10 evaluation visualizations saved to:")
print(f"  {OUTPUT_DIR}")
print(f"{'='*70}")
print(f"\n  Files generated:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    if f.endswith('.png'):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f)) / 1024
        print(f"    {f:45s} ({size:.0f} KB)")
