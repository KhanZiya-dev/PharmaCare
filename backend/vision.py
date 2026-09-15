import os
import re
import json
import time
import logging
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Always resolve .env relative to this file (backend/.env)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path if os.path.exists(_env_path) else None)

logger = logging.getLogger(__name__)

# Changed back to gemini-3.6-flash as per user's preference
MODEL_NAME = 'gemini-3.6-flash'

PROMPT = (
    "Extract medicine/drug brand names from this image.\n\n"
    "RULES:\n"
    "1. Read carefully, letter by letter. Do not guess based on common names.\n"
    "2. Ignore: dosage (500mg, 10ml), frequency (1-0-1, BD, TDS, SOS), "
    "doctor names, patient details, dates, diagnosis.\n"
    "3. Preserve exact spelling as written/printed. Do not auto-correct.\n"
    "4. Return ONLY a JSON array of medicine name strings.\n"
    '5. Example output: ["Ubactin", "Rapaflow D"]\n'
    '6. If nothing is legible, return: ["UNCLEAR"]'
)

def get_api_keys() -> list[str]:
    """Returns a list of API keys from the environment variable."""
    keys_str = os.getenv("GEMINI_API_KEY")
    if not keys_str:
        return []
    return [k.strip() for k in keys_str.split(",") if k.strip()]

def _parse_response(raw_text: str) -> list[str]:
    """
    Robustly parse Gemini response into a list of medicine name strings.
    """
    text = raw_text.strip() if raw_text else ""

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except:
                return []
        else:
            return []

    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                data = v
                break
        else:
            return []

    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        name = ""
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("medicine_name") or item.get("name") or item.get("brand") or item.get("drug") or "").strip()
        
        if not name or name.upper() == "UNCLEAR":
            continue

        clean = re.sub(
            r"\s+\d+(\.\d+)?\s*(mg|mcg|ml|gm?|g|tablet|tab|cap|capsule)\b.*$",
            "",
            name,
            flags=re.IGNORECASE,
        ).strip()
        results.append(clean if clean else name)

    return results

def extract_medicines_from_image(image_path: str) -> list[str]:
    """
    Extracts medicine names from an image using the older google.generativeai SDK 
    to prevent hanging/timeouts associated with the new SDK's quota handling.
    """
    api_keys = get_api_keys()

    if not api_keys:
        logger.error("Cannot extract text: GEMINI_API_KEY is missing.")
        return []

    img = Image.open(image_path).convert("RGB")
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)

    total_start = time.time()
    last_error = None

    for api_key in api_keys:
        if time.time() - total_start > 120:
            logger.warning("Aborting vision API call early to prevent 130s timeout on frontend.")
            break

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(MODEL_NAME)

            response = model.generate_content(
                [PROMPT, img],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                )
            )

            raw_text = response.text or ""
            medicines = _parse_response(raw_text)
            
            if medicines:
                return medicines
                
        except Exception as e:
            err_str = str(e).lower()
            last_error = e
            
            if "503" in err_str or "unavailable" in err_str or "404" in err_str or "not_found" in err_str:
                break
                
            continue

    if last_error:
        raise ValueError("AI API Quota Exceeded (Free Tier) across all provided keys. Please try again later.")

    return []
