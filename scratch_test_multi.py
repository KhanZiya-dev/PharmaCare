import os, time, json, logging
from PIL import Image
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", ".env")
load_dotenv(_env_path)

from google import genai
from google.genai import types

MODELS_TO_TRY = ['gemini-3.8-flash', 'gemini-3.6-flash']

def get_api_keys() -> list[str]:
    keys_str = os.getenv("GEMINI_API_KEY")
    if not keys_str:
        return []
    return [k.strip() for k in keys_str.split(",") if k.strip()]

def test_extract(image_path: str):
    api_keys = get_api_keys()
    print(f"Loaded {len(api_keys)} API keys.", flush=True)
    prompt = (
        "Extract medicine/drug brand names from this image.\n\n"
        "RULES:\n"
        "1. Read carefully, letter by letter. Do not guess based on common names.\n"
        "2. Ignore: dosage (500mg, 10ml), frequency (1-0-1, BD, TDS, SOS), "
        "doctor names, patient details, dates, diagnosis.\n"
        "3. Preserve exact spelling as written/printed. Do not auto-correct.\n"
        "4. Return a JSON array of strings.\n"
        "5. If nothing is legible, return: [\"UNCLEAR\"]"
    )

    img = Image.open(image_path).convert('RGB')
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)

    total_start = time.time()
    last_error = None
    for model_name in MODELS_TO_TRY:
        print(f"\n--- Trying Model: {model_name} ---", flush=True)
        for api_key in api_keys:
            key_suffix = api_key[-4:] if len(api_key) > 4 else ""
            try:
                # Use attempts=1 so we don't hang on 429/503 retry delays
                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(
                        retry_options=types.HttpRetryOptions(attempts=1)
                    )
                )
                t0 = time.time()
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, img],
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=1024,
                        response_mime_type="application/json"
                    )
                )
                print(f"Model {model_name} with key ...{key_suffix} SUCCEEDED in {time.time()-t0:.2f}s! Total elapsed: {time.time()-total_start:.2f}s", flush=True)
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.strip("`")
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:].strip()
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict):
                    for v in parsed.values():
                        if isinstance(v, list):
                            parsed = v
                            break
                if isinstance(parsed, list):
                    meds = [str(m).strip() for m in parsed if str(m).strip().upper() != "UNCLEAR" and str(m).strip()]
                    return meds
                return []
            except Exception as e:
                err_str = str(e)
                last_error = e
                print(f"Model {model_name} with key ...{key_suffix} failed in {time.time()-t0:.2f}s: {err_str[:100]}...", flush=True)
                continue

    if last_error:
        raise last_error
    return []

res = test_extract("test_prescription.jpg")
print("\nFinal Extracted Result:", res, flush=True)
