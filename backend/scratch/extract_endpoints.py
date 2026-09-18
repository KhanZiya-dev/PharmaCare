import requests
import re

def extract():
    print("Downloading main.dart.js...")
    res = requests.get("https://www.zeno.health/main.dart.js")
    if res.status_code == 200:
        content = res.text
        # Look for API paths
        pattern = r"api/[a-zA-Z0-9_-]+/v[0-9]+/[a-zA-Z0-9_/-]+"
        matches = set(re.findall(pattern, content))
        print(f"Found {len(matches)} unique endpoints.")
        for m in sorted(list(matches)):
            print(m)
    else:
        print("Failed to download main.dart.js")

if __name__ == "__main__":
    extract()
