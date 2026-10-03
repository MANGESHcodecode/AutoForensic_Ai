"""
AutoForensic AI — Forensic Analysis CLI Demo
================================================
Standalone command-line tool to run the complete forensic verification
pipeline on any vehicle damage image.

Usage:
    python run_forensics_demo.py                          # Run on built-in test samples
    python run_forensics_demo.py path/to/car_image.jpg    # Analyze a specific image
    python run_forensics_demo.py image1.jpg image2.jpg    # Compare two images

Output:
    - Console report with verdict, scores, and risk flags
    - ELA heatmap and composite saved to forensic_output/
    - JSON forensic report saved to forensic_output/
"""

import sys
import os
import json
import logging
from pathlib import Path

# Configure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from forensics.pipeline import ForensicPipeline, ForensicVerdict
from forensics.phash import PerceptualHasher


# ══════════════════════════════════════════════════════════════
# CONSOLE FORMATTING
# ══════════════════════════════════════════════════════════════

VERDICT_ICONS = {
    ForensicVerdict.PASSED: "✅",
    ForensicVerdict.SUSPICIOUS: "⚠️",
    ForensicVerdict.REJECTED: "🚫",
}

VERDICT_COLORS = {
    ForensicVerdict.PASSED: "\033[92m",     # Green
    ForensicVerdict.SUSPICIOUS: "\033[93m",  # Yellow
    ForensicVerdict.REJECTED: "\033[91m",    # Red
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
WHITE = "\033[97m"


def print_header():
    """Print the AutoForensic AI banner."""
    print(f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   {WHITE}{BOLD}AutoForensic AI — Cybersecurity & Media Forensics{RESET}{CYAN}         ║
║   {DIM}Digital Media Forensic Analysis Engine{RESET}{CYAN}                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")


def print_report(report):
    """Pretty-print a forensic report to console."""
    icon = VERDICT_ICONS.get(report.verdict, "❓")
    color = VERDICT_COLORS.get(report.verdict, "")

    print(f"\n{'━' * 60}")
    print(f"  {BOLD}📄 Image: {WHITE}{report.image_source}{RESET}")
    print(f"{'━' * 60}")

    # Verdict
    print(f"\n  {BOLD}Verdict:{RESET}  {color}{icon} {report.verdict}{RESET}")
    print(f"  {BOLD}Score:{RESET}    {color}{report.overall_score:.1f}%{RESET}")
    print(f"  {BOLD}Time:{RESET}     {report.processing_time_ms:.0f}ms")

    # Component scores
    print(f"\n  {BOLD}Component Analysis:{RESET}")
    components = report.to_dict().get("component_scores", {})

    if isinstance(components.get("file_validation"), dict):
        fv = components["file_validation"]
        status = "✅ Valid" if fv.get("is_valid", False) else "❌ Invalid"
        fmt = fv.get("detected_format", "Unknown")
        dims = fv.get("image_dimensions", "Unknown")
        print(f"    ├─ File Validator:  {status} ({fmt}, {dims})")
    else:
        print(f"    ├─ File Validator:  {components.get('file_validation', 'N/A')}")

    if isinstance(components.get("exif_analysis"), dict):
        exif = components["exif_analysis"]
        has = "✅ Present" if exif.get("has_exif", False) else "⚠️  Missing"
        edited = "⚠️  Yes" if exif.get("is_edited", False) else "✅ No"
        camera = exif.get("camera_info", {}).get("make", "Unknown")
        score = exif.get("authenticity_score", 0)
        print(f"    ├─ EXIF Analysis:  {has} | Edited: {edited} | Camera: {camera} | Score: {score}%")
    else:
        print(f"    ├─ EXIF Analysis:  {components.get('exif_analysis', 'N/A')}")

    if isinstance(components.get("ela_analysis"), dict):
        ela = components["ela_analysis"]
        suspicious = "⚠️  Yes" if ela.get("is_suspicious", False) else "✅ No"
        mean_err = ela.get("mean_error", 0)
        score = ela.get("authenticity_score", 0)
        print(f"    ├─ ELA Engine:     Suspicious: {suspicious} | Mean Error: {mean_err:.2f} | Score: {score}%")
    else:
        print(f"    ├─ ELA Engine:     {components.get('ela_analysis', 'N/A')}")

    if isinstance(components.get("phash_result"), dict):
        ph = components["phash_result"]
        hash_hex = ph.get("hash_hex", "N/A")
        print(f"    ├─ pHash:          {hash_hex}")
    else:
        print(f"    ├─ pHash:          {components.get('phash_result', 'N/A')}")

    if isinstance(components.get("ai_detection"), dict):
        ai = components["ai_detection"]
        suspected = "⚠️  Yes" if ai.get("is_ai_suspected", False) else "✅ No"
        ai_score = ai.get("overall_ai_score", 0)
        noise = ai.get("noise_score", 0)
        spectral = ai.get("spectral_score", 0)
        patch = ai.get("patch_score", 0)
        print(f"    └─ AI Detector:    Suspected: {suspected} | Score: {ai_score:.0f}% (noise={noise:.0f}, fft={spectral:.0f}, patch={patch:.0f})")
    else:
        print(f"    └─ AI Detector:    {components.get('ai_detection', 'N/A')}")

    # Duplicate check
    dup = components.get("duplicate_check")
    if dup and isinstance(dup, dict):
        dist = dup.get("hamming_distance", "N/A")
        sim = dup.get("similarity_pct", 0)
        verd = dup.get("verdict", "N/A")
        src = dup.get("match_source", "N/A")
        print(f"\n  {BOLD}Duplicate Check:{RESET}")
        print(f"    Nearest Match:   {src}")
        print(f"    Distance:        {dist}/64 | Similarity: {sim:.1f}% | Verdict: {verd}")

    # Risk flags
    if report.risk_flags:
        print(f"\n  {BOLD}⚠️  Risk Flags ({len(report.risk_flags)}):{RESET}")
        for flag in report.risk_flags:
            print(f"    🔸 {flag}")
    else:
        print(f"\n  ✅ No risk flags detected.")

    # Artifacts
    print(f"\n  {BOLD}Artifacts:{RESET}")
    print(f"    SHA-256: {report.image_sha256[:32]}...")
    if report.ela_heatmap_path:
        print(f"    ELA Heatmap:   {report.ela_heatmap_path}")
    if report.ela_composite_path:
        print(f"    ELA Composite: {report.ela_composite_path}")
    if getattr(report, "ai_heatmap_path", None):
        print(f"    AI Heatmap:    {report.ai_heatmap_path}")

    print(f"\n{'━' * 60}\n")


def run_demo():
    """Run the forensic demo on test samples."""
    print_header()

    # Generate test samples
    print(f"  {BOLD}Generating synthetic test samples...{RESET}")
    from tests.create_test_samples import create_test_samples
    samples = create_test_samples(output_dir="tests/test_images")

    # Initialize pipeline
    pipeline = ForensicPipeline(
        output_dir="forensic_output",
        save_artifacts=True,
    )

    # Analyze each test sample
    demo_samples = [
        ("clean_authentic", "Clean Authentic Vehicle Photo"),
        ("tampered_spliced", "Tampered/Spliced Damage"),
        ("edited_software", "Photoshop-Edited Image"),
        ("stripped_exif", "Screenshot/Web Download (No EXIF)"),
        ("executable_disguised", "Executable Disguised as Image"),
        ("polyglot_payload", "Polyglot File (Image + PHP Payload)"),
    ]

    reports = []
    for sample_key, description in demo_samples:
        if sample_key not in samples:
            continue
        print(f"\n  🔍 Analyzing: {BOLD}{description}{RESET}")
        report = pipeline.verify(
            samples[sample_key],
            source_label=sample_key,
        )
        print_report(report)
        reports.append(report)

    # Duplicate detection demo
    print(f"\n{'═' * 60}")
    print(f"  {BOLD}DUPLICATE DETECTION DEMO{RESET}")
    print(f"{'═' * 60}")

    print(f"\n  🔍 Submitting duplicate claim...")
    dup_report = pipeline.verify(
        samples["duplicate_of_clean"],
        source_label="duplicate_claim_B",
    )
    print_report(dup_report)

    # Summary
    print(f"\n{'═' * 60}")
    print(f"  {BOLD}DEMO SUMMARY{RESET}")
    print(f"{'═' * 60}")
    print(f"  Total images analyzed:  {len(reports) + 1}")
    print(f"  Passed:    {sum(1 for r in reports if r.verdict == ForensicVerdict.PASSED)}")
    print(f"  Suspicious: {sum(1 for r in reports if r.verdict == ForensicVerdict.SUSPICIOUS)}")
    print(f"  Rejected:  {sum(1 for r in reports if r.verdict == ForensicVerdict.REJECTED) + (1 if dup_report.verdict == ForensicVerdict.REJECTED else 0)}")
    print(f"  Output:    forensic_output/")
    print(f"{'═' * 60}\n")


def analyze_image(image_path: str):
    """Analyze a single image file."""
    image_path = image_path.strip('\'" ')
    print_header()

    if not os.path.exists(image_path):
        print(f"  ❌ File not found: {image_path}")
        return

    pipeline = ForensicPipeline(
        output_dir="forensic_output",
        save_artifacts=True,
    )

    print(f"  🔍 Analyzing: {BOLD}{image_path}{RESET}")
    report = pipeline.verify(image_path)
    print_report(report)


def analyze_directory(dir_path: str):
    """Analyze all images in a folder."""
    dir_path = dir_path.strip('\'" ')
    print_header()

    p = Path(dir_path)
    if not p.is_dir():
        print(f"  ❌ Directory not found: {dir_path}")
        return

    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    image_files = [f for f in sorted(p.iterdir()) if f.suffix.lower() in extensions]

    if not image_files:
        print(f"  ⚠️  No images found in {dir_path} (supported: jpg, jpeg, png, webp)")
        return

    print(f"  📁 Found {len(image_files)} image(s) in: {BOLD}{dir_path}{RESET}\n")

    pipeline = ForensicPipeline(
        output_dir="forensic_output",
        save_artifacts=True,
    )

    reports = []
    for img_path in image_files:
        print(f"  🔍 Analyzing [{img_path.name}]...")
        rep = pipeline.verify(str(img_path), source_label=img_path.stem)
        print_report(rep)
        reports.append(rep)

    print(f"\n{'═' * 60}")
    print(f"  {BOLD}BATCH SUMMARY ({len(reports)} images){RESET}")
    print(f"{'═' * 60}")
    passed = sum(1 for r in reports if r.verdict == ForensicVerdict.PASSED)
    susp = sum(1 for r in reports if r.verdict == ForensicVerdict.SUSPICIOUS)
    rej = sum(1 for r in reports if r.verdict == ForensicVerdict.REJECTED)
    print(f"  ✅ Passed Authentic:  {passed}")
    print(f"  ⚠️  Suspicious Review: {susp}")
    print(f"  🚫 Fraud Rejected:    {rej}")
    print(f"  Artifacts saved to:   forensic_output/")
    print(f"{'═' * 60}\n")


def compare_images(image_a: str, image_b: str):
    """Compare two images for similarity."""
    image_a = image_a.strip('\'" ')
    image_b = image_b.strip('\'" ')
    print_header()

    for path in [image_a, image_b]:
        if not os.path.exists(path):
            print(f"  ❌ File not found: {path}")
            return

    hasher = PerceptualHasher()
    result = hasher.compare_images(image_a, image_b)

    print(f"  📊 Image Comparison:")
    print(f"    Image A: {image_a}")
    print(f"    Image B: {image_b}")
    print(f"    Hash A:  {result.query_hash}")
    print(f"    Hash B:  {result.match_hash}")
    print(f"    Hamming Distance: {result.hamming_distance}/64")
    print(f"    Similarity: {result.similarity_pct:.1f}%")
    print(f"    Verdict: {result.verdict}")
    print(f"    Duplicate: {'🚫 YES' if result.is_duplicate else '✅ NO'}")
    print()


def interactive_menu():
    """Interactive console prompt for users to check their own images."""
    print_header()
    while True:
        print(f"{BOLD}What would you like to do?{RESET}")
        print(f"  {CYAN}[1]{RESET} Analyze a single vehicle image (type/paste path or drag file)")
        print(f"  {CYAN}[2]{RESET} Analyze an entire folder of vehicle photos")
        print(f"  {CYAN}[3]{RESET} Compare two images for duplicate/manipulation detection")
        print(f"  {CYAN}[4]{RESET} Run built-in synthetic test demo (7 test cases)")
        print(f"  {CYAN}[q]{RESET} Quit")
        choice = input(f"\n{BOLD}Select an option [1/2/3/4/q]: {RESET}").strip().lower()

        if choice == "1":
            path = input(f"\n{BOLD}Enter image path (or drag & drop file here): {RESET}").strip('\'" ')
            if path:
                analyze_image(path)
        elif choice == "2":
            folder = input(f"\n{BOLD}Enter folder path containing images: {RESET}").strip('\'" ')
            if folder:
                analyze_directory(folder)
        elif choice == "3":
            img1 = input(f"\n{BOLD}Enter first image path: {RESET}").strip('\'" ')
            img2 = input(f"{BOLD}Enter second image path: {RESET}").strip('\'" ')
            if img1 and img2:
                compare_images(img1, img2)
        elif choice == "4":
            run_demo()
        elif choice in ("q", "quit", "exit"):
            print("\nExiting AutoForensic AI. Goodbye!")
            break
        else:
            print("\n  ❌ Invalid selection. Please enter 1, 2, 3, 4, or q.\n")


# ══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    if len(sys.argv) == 1:
        # No arguments: launch interactive menu
        interactive_menu()
    elif len(sys.argv) == 2:
        arg = sys.argv[1].strip('\'" ')
        if arg in ("--demo", "-d"):
            run_demo()
        elif arg in ("--interactive", "-i"):
            interactive_menu()
        elif os.path.isdir(arg):
            analyze_directory(arg)
        else:
            analyze_image(arg)
    elif len(sys.argv) == 3:
        compare_images(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  python run_forensics_demo.py                             # Interactive Menu")
        print("  python run_forensics_demo.py <image.jpg>                 # Analyze single image")
        print("  python run_forensics_demo.py <folder_path>               # Analyze entire folder")
        print("  python run_forensics_demo.py <img1.jpg> <img2.jpg>       # Compare two images")
        print("  python run_forensics_demo.py --demo                      # Run built-in demo")
