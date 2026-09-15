import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
from google import genai
from google.genai import types
from PIL import Image

keys = [k.strip() for k in os.getenv('GEMINI_API_KEY').split(',') if k.strip()]
client = genai.Client(api_key=keys[1])
img = Image.open('test_prescription.jpg')

prompt = """Extract medicine/drug brand names from this image.
RULES:
1. Read carefully, letter by letter.
2. Ignore dosage, frequency, doctor names, patient details.
3. Preserve exact spelling as written/printed.
4. Return a JSON array of strings, e.g. ["Ubactin", "Rapaflow D"].
5. If nothing is legible, return: ["UNCLEAR"]
"""

res = client.models.generate_content(
    model='gemini-3.6-flash',
    contents=[prompt, img],
    config=types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=2048,
        response_mime_type='application/json'
    )
)

print("Finish reason:", res.candidates[0].finish_reason)
print("Response text:")
print(res.text)
