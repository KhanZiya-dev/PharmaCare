import os, time
from PIL import Image
from dotenv import load_dotenv
load_dotenv('backend/.env')
from google import genai
from google.genai import types

ss_path = r"C:\Users\Ziyaurrahman Khan\.gemini\antigravity-ide\brain\4ed76808-6be7-40f9-a2d9-53784a4d116c\.user_uploaded\media_1789460236550.png"
img = Image.open(ss_path).convert("RGB")
img.thumbnail((800, 800), Image.Resampling.LANCZOS)
cropped = img
print("Prescription loaded.")

keys = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]
client = genai.Client(api_key=keys[0])

prompt = (
    "Extract medicine/drug brand names from this image.\n\n"
    "RULES:\n"
    "1. Read carefully, letter by letter. Do not guess based on common names.\n"
    "2. Ignore: dosage (500mg, 10ml), frequency (1-0-1, BD, TDS, SOS), doctor names, patient details, dates, diagnosis.\n"
    "3. Preserve exact spelling as written/printed. Do not auto-correct.\n"
    "4. Return a JSON array of strings.\n"
    "5. If nothing is legible, return: [\"UNCLEAR\"]"
)

t0 = time.time()
res = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=[prompt, cropped],
    config=types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=1024,
        response_mime_type="application/json"
    )
)
print(f"Gemini 3.6 Flash took {time.time()-t0:.2f}s:")
print(res.text)
