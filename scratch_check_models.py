import os, time
from dotenv import load_dotenv
load_dotenv('backend/.env')
from google import genai
from PIL import Image

keys = [k.strip() for k in os.getenv('GEMINI_API_KEY').split(',') if k.strip()]
img = Image.open('test_prescription.jpg')

candidate_models = [
    'gemini-3.8-flash',
    'gemini-3.7-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-2.5-flash',
    'gemini-flash-latest'
]

print("Starting model availability test across keys...")
for model in candidate_models:
    for i, key in enumerate(keys):
        client = genai.Client(api_key=key)
        t0 = time.time()
        try:
            res = client.models.generate_content(
                model=model,
                contents=["Extract medicine names as JSON list: ", img]
            )
            print(f"SUCCESS: {model} with Key {i+1} in {time.time()-t0:.2f}s -> {res.text[:100]}...", flush=True)
            break
        except Exception as e:
            print(f"FAILED: {model} with Key {i+1} in {time.time()-t0:.2f}s -> {type(e).__name__}: {str(e)[:100]}", flush=True)
