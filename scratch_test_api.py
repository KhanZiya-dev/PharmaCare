import requests
import time

url = "http://localhost:8000/api/vision-search"
image_path = "test_prescription.jpg"

print(f"Uploading {image_path} to {url}...")
t0 = time.time()

with open(image_path, "rb") as f:
    resp = requests.post(url, files={"file": ("prescription.jpg", f, "image/jpeg")}, timeout=35)

elapsed = time.time() - t0
print(f"Status: {resp.status_code} in {elapsed:.2f}s")

if resp.status_code == 200:
    data = resp.json()
    print(f"Extracted medicines: {data.get('extracted_text', [])}")
    print(f"DB matches: {len(data.get('results', []))}")
    print(f"Not found: {data.get('not_found', [])}")
else:
    print(f"Error: {resp.text}")
