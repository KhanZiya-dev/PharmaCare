import sys
sys.path.append('backend')
from vision import extract_medicines_from_image

img_path = r'C:\Users\Ziyaurrahman Khan\.gemini\antigravity-ide\brain\4ed76808-6be7-40f9-a2d9-53784a4d116c\.user_uploaded\media_1789460236550.png'
print("Extracting...")
try:
    results = extract_medicines_from_image(img_path)
    print("Results:", results)
except Exception as e:
    print("Error:", e)
