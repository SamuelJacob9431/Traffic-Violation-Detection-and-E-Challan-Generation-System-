import requests
import os

API_BASE = "http://localhost:8000"

def test_violation():
    print("Testing Violation Recording...")
    try:
        # Create a dummy image
        with open("test_img.jpg", "wb") as f:
            f.write(b"fake image data")
        
        files = {'image': ('test.jpg', open("test_img.jpg", "rb"), 'image/jpeg')}
        data = {
            'plate_number': 'TEST-9999',
            'violation_type': 'Over Speed',
            'value': 120.5
        }
        
        res = requests.post(f"{API_BASE}/violations/", data=data, files=files)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.json()}")
        
        # Check if it appears in the list
        res = requests.get(f"{API_BASE}/violations/")
        violations = res.json()
        print(f"Total Violations in DB: {len(violations)}")
        for v in violations:
            if v['plate_number'] == 'TEST-9999':
                print("SUCCESS: Test violation found in DB!")
                return
        print("FAILURE: Test violation not found in DB list.")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        if os.path.exists("test_img.jpg"):
            os.remove("test_img.jpg")

if __name__ == "__main__":
    test_violation()
