import requests
import time
import json

# Use the same prescription image that's cached
# Test the vision-search endpoint directly
img_path = r"d:\BSc.CS\Sem5\Pharmacare\backend\pharmeasy_debug.png"

print("Testing vision-search endpoint...")
start = time.time()

with open(img_path, "rb") as f:
    resp = requests.post(
        "http://localhost:8000/api/vision-search",
        files={"file": ("test.png", f, "image/png")},
        timeout=200,
    )

elapsed = time.time() - start
print(f"Status: {resp.status_code} | Time: {elapsed:.1f}s")
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
