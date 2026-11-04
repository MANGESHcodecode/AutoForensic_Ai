"""AutoForensic AI - Test Sample Generator"""
import io, os, struct
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def create_test_samples(output_dir="tests/test_images"):
    np.random.seed(42)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    clean = _create_vehicle_panel_image(640, 480)
    clean_path = out / "clean_vehicle.jpg"
    _save_with_exif(clean, str(clean_path), camera_make="Canon", camera_model="EOS R5")
    paths["clean_authentic"] = str(clean_path)
    tampered = clean.copy()
    splice_patch = np.full((100, 150, 3), (40, 40, 220), dtype=np.uint8)
    noise = np.random.randint(0, 30, splice_patch.shape, dtype=np.uint8)
    splice_patch = np.clip(splice_patch.astype(int) + noise, 0, 255).astype(np.uint8)
    tampered[150:250, 200:350] = splice_patch
    tampered_path = out / "tampered_spliced.jpg"
    cv2.imwrite(str(tampered_path), tampered, [cv2.IMWRITE_JPEG_QUALITY, 95])
    paths["tampered_spliced"] = str(tampered_path)
    stripped_path = out / "stripped_exif.jpg"
    cv2.imwrite(str(stripped_path), clean, [cv2.IMWRITE_JPEG_QUALITY, 95])
    paths["stripped_exif"] = str(stripped_path)
    edited_path = out / "edited_photoshop.jpg"
    _save_with_exif(clean, str(edited_path), camera_make="Canon", camera_model="EOS R5", software="Adobe Photoshop CC 2024")
    paths["edited_software"] = str(edited_path)
    poly_path = out / "polyglot_payload.jpg"
    cv2.imwrite(str(poly_path), clean, [cv2.IMWRITE_JPEG_QUALITY, 85])
    with open(str(poly_path), "ab") as f:
        f.write(b"\n<?php echo 'HACKED'; ?>\n")
    paths["polyglot_payload"] = str(poly_path)
    dup_path = out / "duplicate_claim.jpg"
    clean_loaded = cv2.imread(str(clean_path))
    cv2.imwrite(str(dup_path), clean_loaded, [cv2.IMWRITE_JPEG_QUALITY, 90])
    paths["duplicate_of_clean"] = str(dup_path)
    exe_path = out / "fake_image.jpg"
    with open(str(exe_path), "wb") as f:
        f.write(b"MZ" + b"\x00" * 1500)
    paths["executable_disguised"] = str(exe_path)
    stub_path = out / "tiny_stub.jpg"
    with open(str(stub_path), "wb") as f:
        f.write(b"\xFF\xD8\xFF\xE0" + b"\x00" * 50)
    paths["tiny_stub"] = str(stub_path)
    different = _create_different_vehicle_image(640, 480)
    different_path = out / "different_vehicle.jpg"
    cv2.imwrite(str(different_path), different, [cv2.IMWRITE_JPEG_QUALITY, 95])
    paths["different_vehicle"] = str(different_path)
    print(f"Test Samples Generated: {len(paths)} files")
    for name, path in paths.items():
        size = os.path.getsize(path)
        print(f"  [{name:25s}] {size:>8,} bytes")
    return paths

def _create_vehicle_panel_image(width, height):
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        img[y, :] = [int(140+40*ratio), int(130+30*ratio), int(120+20*ratio)]
    ry = height // 3
    for dy in range(-20, 21):
        y = ry + dy
        if 0 <= y < height:
            b = int(40 * (1 - abs(dy) / 20))
            img[y, :] = np.clip(img[y, :].astype(int) + b, 0, 255).astype(np.uint8)
    noise = np.random.normal(0, 5, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    cv2.line(img, (100,200), (350,230), (100,100,100), 1, cv2.LINE_AA)
    return img

def _create_different_vehicle_image(width, height):
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        img[y, :] = [int(40+20*ratio), int(30+20*ratio), int(160+50*ratio)]
    noise = np.random.normal(0, 4, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    cv2.circle(img, (320,240), 60, (50,40,30), -1)
    return img

def _save_with_exif(img_bgr, path, camera_make="Canon", camera_model="EOS R5", software=""):
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    exif_dict = pil_img.getexif()
    exif_dict[0x010F] = camera_make
    exif_dict[0x0110] = camera_model
    exif_dict[0x0132] = "2026:09:23 14:30:00"
    if software:
        exif_dict[0x0131] = software
    exif_bytes = exif_dict.tobytes()
    pil_img.save(path, format="JPEG", quality=95, exif=exif_bytes)

if __name__ == "__main__":
    create_test_samples()
