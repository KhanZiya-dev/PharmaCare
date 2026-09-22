import os
import time
import logging
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv('backend/.env')

MODEL_NAME = 'gemini-3.5-flash'

PROMPT = (
    "Extract medicine/drug details from this image.\n\n"
    "RULES:\n"
    "1. Read carefully, letter by letter. Do not guess based on common names.\n"
    "2. Preserve exact spelling as written/printed. Do not auto-correct.\n"
    "3. For each medicine, extract:\n"
    "   - name: The brand name (e.g., Augmentin, Azithral, Dolo)\n"
    "   - strength: The dosage strength if visible (e.g., 500mg, 10ml, 250mg/5ml). null if not visible.\n"
    "   - form: The dosage form if identifiable (Tablet, Capsule, Syrup, Cream, Gel, Ointment, "
    "Drops, Injection, Suspension, Inhaler, Powder, Lotion, Spray, Sachet, Respules, Kit). null if not clear.\n"
    "4. Ignore: frequency (1-0-1, BD, TDS, SOS), doctor names, patient details, dates, diagnosis.\n"
    "5. Return ONLY a JSON array of objects.\n"
    '6. Example output: [{"name": "Augmentin DDS", "strength": "400mg", "form": "Suspension"}, '
    '{"name": "Azithral", "strength": "500mg", "form": "Tablet"}]\n'
    '7. If nothing is legible, return: [{"name": "UNCLEAR", "strength": null, "form": null}]'
)

def test():
    keys = os.getenv("GEMINI_API_KEY", "").split(",")
    keys = [k.strip() for k in keys if k.strip()]
    
    img = Image.open(r'C:\Users\Ziyaurrahman Khan\.gemini\antigravity-ide\brain\4ed76808-6be7-40f9-a2d9-53784a4d116c\.user_uploaded\media_1789460236550.png').convert("RGB")
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    
    for key in keys:
        try:
            print(f"Trying key: {key[:10]}...")
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[PROMPT, img],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=2048
                )
            )
            print("Success!")
            print(response.text)
            break
        except Exception as e:
            print(f"Error on key {key[:10]}...: {e}")

if __name__ == "__main__":
    test()
