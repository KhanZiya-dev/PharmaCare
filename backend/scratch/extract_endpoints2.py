import requests
import re

def extract():
    print("Downloading main.dart.js...")
    res = requests.get("https://www.zeno.health/main.dart.js")
    if res.status_code == 200:
        content = res.text
        # Look for ecom.zeno.health
        pattern = r"ecom\.zeno\.health[a-zA-Z0-9_/-]+"
        matches = set(re.findall(pattern, content))
        print(f"Found {len(matches)} unique ecom endpoints.")
        for m in sorted(list(matches)):
            print(m)
            
        print("\nLooking for 'search' inside URLs...")
        pattern2 = r"https?://[a-zA-Z0-9_./-]+search[a-zA-Z0-9_/-]*"
        matches2 = set(re.findall(pattern2, content))
        for m in sorted(list(matches2)):
            print(m)
    else:
        print("Failed to download main.dart.js")

if __name__ == "__main__":
    extract()
