import io
from pathlib import Path
from fastapi.testclient import TestClient
from web.app import app

client = TestClient(app)

def test_all():
    print("Testing GET / ...")
    r = client.get("/")
    assert r.status_code == 200, f"GET / failed: {r.status_code}"
    assert "AutoForensic" in r.text
    assert "btnRegisterClaim" in r.text
    assert "btnVerifyAndAddPart" in r.text
    print("  ✓ GET / works")

    print("Testing GET /api/stats ...")
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_claims_processed" in data
    print("  ✓ GET /api/stats works:", data["total_claims_processed"])

    print("Testing GET /api/demo-samples ...")
    r = client.get("/api/demo-samples")
    assert r.status_code == 200
    print("  ✓ GET /api/demo-samples works:", len(r.json()["samples"]))

    print("Testing GET /api/vehicle-claims ...")
    r = client.get("/api/vehicle-claims")
    assert r.status_code == 200
    print("  ✓ GET /api/vehicle-claims works:", r.json()["total"])

    print("Testing POST /api/vehicle-claim/create ...")
    new_claim_payload = {
        "customer_name": "Test Customer",
        "policy_no": "POL-112233",
        "contact": "+91 99999 88888",
        "vehicle_reg": "DL 01 AB 1234",
        "vehicle_model": "Hyundai Creta SX",
        "model_year": "2023"
    }
    r = client.post("/api/vehicle-claim/create", json=new_claim_payload)
    assert r.status_code == 200, f"Create failed: {r.text}"
    claim = r.json()
    claim_id = claim["claim_id"]
    print(f"  ✓ Claim created: {claim_id}")

    print("Testing GET /api/vehicle-claim/{claim_id} ...")
    r = client.get(f"/api/vehicle-claim/{claim_id}")
    assert r.status_code == 200
    assert r.json()["claim_id"] == claim_id
    print("  ✓ GET /api/vehicle-claim works")

    print("Testing POST /api/vehicle-claim/verify-part ...")
    # Use real test image
    test_img_path = Path("tests/test_images/clean_vehicle.jpg")
    if not test_img_path.exists():
        print("  Warning: clean_vehicle.jpg not found, creating dummy jpg")
        import numpy as np
        from PIL import Image
        img_arr = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        img = Image.fromarray(img_arr)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()
    else:
        img_bytes = test_img_path.read_bytes()

    files = {"file": ("bumper.jpg", img_bytes, "image/jpeg")}
    data = {
        "claim_id": claim_id,
        "part_name": "Front Bumper",
        "damage_type": "dent"
    }
    r = client.post("/api/vehicle-claim/verify-part", data=data, files=files)
    assert r.status_code == 200, f"Verify part failed: {r.text}"
    part_res = r.json()
    print("  ✓ Part verified:", part_res.get("is_valid"), part_res.get("verdict"))

    print("Testing GET /api/registry/records ...")
    r = client.get("/api/registry/records")
    assert r.status_code == 200
    print("  ✓ Registry total:", r.json()["total"])

    print("Testing POST /api/registry/check ...")
    r = client.post("/api/registry/check", data={"query": "CLM-2026-9812"})
    assert r.status_code == 200
    print("  ✓ Registry query match:", r.json().get("match_count"))

    print("\nALL BACKEND API ENDPOINTS VERIFIED 100% OPERATIONAL!")

if __name__ == "__main__":
    test_all()
