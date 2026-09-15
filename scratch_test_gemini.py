import os, json, time
from dotenv import load_dotenv
load_dotenv('backend/.env')
from google import genai
from PIL import Image

keys = [k.strip() for k in os.getenv('GEMINI_API_KEY', '').split(',') if k.strip()]
print(f"Total keys: {len(keys)}")

for i, k in enumerate(keys):
    print(f"\n--- Testing Key {i+1} (...{k[-6:]}) ---")
    client = genai.Client(api_key=k)
    for model in ['gemini-3.8-flash', 'gemini-3.6-flash']:
        t0 = time.time()
        try:
            res = client.models.generate_content(
                model=model,
                contents="Reply with: OK"
            )
            print(f"  Model {model}: SUCCESS in {time.time()-t0:.2f}s -> {res.text.strip()}")
        except Exception as e:
            print(f"  Model {model}: FAILED in {time.time()-t0:.2f}s -> {e}")
