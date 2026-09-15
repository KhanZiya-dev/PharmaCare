import sys, os, json, re
sys.path.append('./backend')
from dotenv import load_dotenv
load_dotenv('./backend/.env')
from google import genai
from google.genai import types
from PIL import Image

api_key = os.getenv('GEMINI_API_KEY', '').split(',')[0].strip()
client = genai.Client(api_key=api_key)

img = Image.new('RGB', (800, 800), color='white')

prompt = (
    'Extract ONLY medicine/drug names from this image.\n'
    'RULES:\n'
    '1. Ignore dosages (500mg), frequencies (1-0-1), and doctor/patient details.\n'
    '2. Preserve exact spelling. Don\'t guess if illegible; output \'UNCLEAR\'.\n'
    '3. Return ONLY a valid JSON array of strings. No markdown, no explanations.\n'
    'Example: ["Paracetamol", "UNCLEAR"]'
)

try:
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=[prompt, img],
        config=types.GenerateContentConfig(
            max_output_tokens=150,
            response_mime_type="application/json"
        )
    )
    print('RAW:', repr(response.text))
    parsed_list = json.loads(response.text.strip())
    print('PARSED:', parsed_list)
except Exception as e:
    print('EXCEPTION:', str(e))


