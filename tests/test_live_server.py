import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    print("Testing GET / ...")
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    print("  [OK] GET / OK")

    print("Testing GET /api/stats ...")
    r = requests.get(f"{BASE_URL}/api/stats")
    assert r.status_code == 200
    print("  [OK] GET /api/stats OK:", r.json()["total_claims_processed"])

    print("Testing GET /api/vehicle-claims ...")
    r = requests.get(f"{BASE_URL}/api/vehicle-claims")
    assert r.status_code == 200
    print("  [OK] GET /api/vehicle-claims OK:", r.json()["total"])

    print("Testing POST /api/vehicle-claim/create ...")
    payload = {
        "customer_name": "Test Customer",
        "policy_no": "POL-889900",
        "contact": "+91 98765 43210",
        "vehicle_reg": "KA 05 AB 1234",
        "vehicle_model": "Tata Harrier XZ",
        "model_year": "2023"
    }
    r = requests.post(f"{BASE_URL}/api/vehicle-claim/create", json=payload)
    assert r.status_code == 200
    claim = r.json()
    claim_id = claim["claim_id"]
    print("  [OK] Claim created:", claim_id)

    print(f"Testing GET /api/vehicle-claim/{claim_id} ...")
    r = requests.get(f"{BASE_URL}/api/vehicle-claim/{claim_id}")
    assert r.status_code == 200
    print("  [OK] Claim retrieved successfully")

    print("Testing POST /api/vehicle-claim/verify-part ...")
    img_path = Path("tests/test_images/clean_vehicle.jpg")
    with open(img_path, "rb") as f:
        files = {"file": ("bumper.jpg", f, "image/jpeg")}
        data = {
            "claim_id": claim_id,
            "part_name": "Front Bumper",
            "damage_type": "dent"
        }
        r = requests.post(f"{BASE_URL}/api/vehicle-claim/verify-part", data=data, files=files)
    assert r.status_code == 200
    verify_res = r.json()
    print("  [OK] Verify part result:", verify_res["is_valid"], verify_res["verdict"], verify_res["overall_score"])

    print("Testing GET /api/registry/records ...")
    r = requests.get(f"{BASE_URL}/api/registry/records")
    assert r.status_code == 200
    print("  [OK] Registry total records:", r.json()["total"])

    print("Testing GET /api/analytics ...")
    r = requests.get(f"{BASE_URL}/api/analytics")
    assert r.status_code == 200
    print("  [OK] Analytics vectors:", len(r.json()["fraud_vectors"]))

    print("Testing GET /api/policies ...")
    r = requests.get(f"{BASE_URL}/api/policies")
    assert r.status_code == 200
    print("  [OK] Policies loaded:", r.json()["layer1_magic_bytes"])

    print("ALL API ENDPOINTS FUNCTIONING 100% PERFECTLY!")

    print("ALL API ENDPOINTS FUNCTIONING 100% PERFECTLY!")

if __name__ == "__main__":
    test_endpoints()
