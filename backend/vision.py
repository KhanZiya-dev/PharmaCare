import os
import re
import json
import time
import logging
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

# Always resolve .env relative to this file (backend/.env)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path if os.path.exists(_env_path) else None)

logger = logging.getLogger(__name__)

# Model fallback chain: most reliable first
# gemini-3.5-flash: stable, high quota, fast (7-14s)
# gemini-3.6-flash: stable but sometimes slow or 503 during peak
# gemini-3.8-flash: best quality but only 20 req/day on free tier
MODELS_TO_TRY = ['gemini-3.5-flash', 'gemini-3.6-flash', 'gemini-3.8-flash']

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
    Handles: plain JSON arrays, markdown code blocks, dict wrappers, 
    list-of-dicts with name/medicine_name keys.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Try direct JSON parse first
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: extract the first JSON array via regex
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                logger.error(f"Could not parse any JSON from response: {text[:200]}")
                return []
        else:
            logger.error(f"No JSON array found in response: {text[:200]}")
            return []

    # If response is a dict wrapping a list, unwrap it
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
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            # Handle {"medicine_name": "X"} or {"name": "X"} etc.
            name = str(
                item.get("medicine_name")
                or item.get("name")
                or item.get("brand")
                or item.get("drug")
                or ""
            ).strip()
        else:
            continue

        if not name or name.upper() == "UNCLEAR":
            continue

        # Strip trailing dosage info (e.g. "Ubactin 100mg" -> "Ubactin")
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
    Extracts medicine names from an image using Gemini Flash models.
    Uses a multi-model fallback chain with retry rounds and smart delays
    to handle transient quota/503 errors within the frontend's 30-second
    timeout.
    """
    api_keys = get_api_keys()

    if not api_keys:
        logger.error("Cannot extract text: GEMINI_API_KEY is missing.")
        return []

    # Downscale image to save bandwidth and tokens
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)

    total_start = time.time()
    last_error = None

    # Retry the entire model+key matrix up to MAX_ROUNDS times.
    # Free-tier quota often resets within a few seconds, so a short
    # pause between rounds recovers from transient 429s.
    MAX_ROUNDS = 2
    ROUND_PAUSE = 3  # seconds to wait before retrying after all keys fail

    for round_num in range(MAX_ROUNDS):
        if round_num > 0:
            elapsed = time.time() - total_start
            if elapsed + ROUND_PAUSE > 25:
                logger.warning(
                    f"No time budget for retry round {round_num + 1} "
                    f"(elapsed {elapsed:.1f}s), giving up."
                )
                break
            logger.info(
                f"All keys exhausted in round {round_num}. "
                f"Waiting {ROUND_PAUSE}s before retry..."
            )
            time.sleep(ROUND_PAUSE)

        quota_failures = 0  # track how many 429s we hit this round

        for model_name in MODELS_TO_TRY:
            # Budget check: if we've already spent >24s, abort
            elapsed = time.time() - total_start
            if elapsed > 24:
                logger.warning(
                    f"Aborting model loop after {elapsed:.1f}s to avoid "
                    f"frontend timeout."
                )
                break

            for api_key in api_keys:
                # Budget check per key attempt
                elapsed = time.time() - total_start
                if elapsed > 24:
                    break

                key_hint = (
                    f"...{api_key[-4:]}" if len(api_key) > 4 else "***"
                )
                t0 = time.time()
                try:
                    # attempts=1 prevents the SDK from retrying 429/503
                    # internally (default is 4 retries with exponential
                    # backoff = 30-60s wasted)
                    client = genai.Client(
                        api_key=api_key,
                        http_options=types.HttpOptions(
                            retry_options=types.HttpRetryOptions(attempts=1)
                        ),
                    )

                    response = client.models.generate_content(
                        model=model_name,
                        contents=[PROMPT, img],
                        config=types.GenerateContentConfig(
                            temperature=0.0,
                            max_output_tokens=1024,
                            response_mime_type="application/json",
                        ),
                    )
                    duration = time.time() - t0
                    logger.info(
                        f"Gemini {model_name} (key {key_hint}) succeeded "
                        f"in {duration:.1f}s"
                    )

                    # response.text can be None on some edge cases
                    raw_text = response.text or ""
                    if not raw_text.strip():
                        logger.warning(
                            f"Empty response from {model_name} "
                            f"(key {key_hint}), trying next."
                        )
                        continue

                    medicines = _parse_response(raw_text)
                    if medicines:
                        return medicines
                    # Parsed but got no medicines → try next combo
                    logger.warning(
                        f"Empty parse result from {model_name}, "
                        f"trying next."
                    )

                except Exception as e:
                    err_str = str(e).lower()
                    duration = time.time() - t0
                    logger.warning(
                        f"Error {model_name} (key {key_hint}) "
                        f"in {duration:.1f}s: {str(e)[:120]}"
                    )
                    last_error = e

                    # 429 quota exhausted → skip to next key for same
                    # model, add small delay to ease pressure
                    if "429" in err_str or "quota" in err_str:
                        quota_failures += 1
                        time.sleep(0.5)
                        continue

                    # 503 unavailable → skip to next model entirely
                    if "503" in err_str or "unavailable" in err_str:
                        break

                    # 404 model not found → skip model
                    if "404" in err_str or "not_found" in err_str:
                        break

                    # Any other error → try next key
                    continue

        # If this round had no quota failures, retrying won't help
        if quota_failures == 0:
            break

    # All combos and rounds exhausted
    if last_error:
        raise ValueError(
            "AI service is temporarily unavailable (quota/demand). "
            "Please try again in a few seconds."
        )

    return []
