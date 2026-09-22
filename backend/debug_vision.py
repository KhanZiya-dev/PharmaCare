import sys
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)
from vision import extract_medicines_from_image

print("Testing vision API...")
try:
    import os
    import glob
    # Find any image in the current directory or parent directory
    imgs = glob.glob("*.jpg") + glob.glob("*.png") + glob.glob("../frontend/public/*.jpg") + glob.glob("../frontend/public/*.png")
    if not imgs:
        print("No image found to test.")
    else:
        print(f"Testing with {imgs[0]}")
        res = extract_medicines_from_image(imgs[0])
        print("Result:", res)
except Exception as e:
    traceback.print_exc()
