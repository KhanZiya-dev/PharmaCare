import os
import google.generativeai as genai
from PIL import Image
import logging
import json
import re

logger = logging.getLogger(__name__)

def get_api_keys() -> list[str]:
    """Returns a list of API keys from the environment variable."""
    keys_str = os.getenv("GEMINI_API_KEY")
    if not keys_str:
        return []
    # Split by comma and remove empty/whitespace keys
    return [k.strip() for k in keys_str.split(",") if k.strip()]

def extract_medicines_from_image(image_path: str) -> list[str]:
    """
    Extracts medicine names from an image using Gemini Pro Vision.
    Tries multiple API keys if the quota is exceeded.
    Returns a list of extracted medicine names.
    """
    api_keys = get_api_keys()
    
    if not api_keys:
        logger.error("Cannot extract text: GEMINI_API_KEY is missing.")
        return []
        
    last_error = None
    
    # Try each key until one succeeds
    for api_key in api_keys:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3.6-flash')
            # Optimize: Downscale image to max 800x800 to save bandwidth and tokens
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Optimize: Much shorter prompt to save text tokens while keeping strict rules
            prompt = (
                "You are a highly accurate medical OCR system specialized in reading "
                "handwritten prescriptions and medicine box labels.\n\n"
                "TASK: Extract ONLY the medicine/drug brand or generic names from the image.\n\n"
                "STRICT RULES:\n"
                "1. Read every word carefully, letter by letter, before deciding. Do not guess "
                "based on common medicine names if the handwriting doesn't clearly support it.\n"
                "2. Ignore: dosage strengths (e.g. 500mg, 10ml), frequency/instructions "
                "(e.g. 1-0-1, BD, TDS, SOS), doctor names, patient details, dates, and diagnosis text.\n"
                "3. Preserve the exact spelling as written/printed. Do not auto-correct to a "
                "correctly spelled medicine if the handwriting/label explicitly spells it differently.\n"
                "4. Format the output strictly as a JSON array of strings, e.g. [\"MedName1\", \"MedName2\"].\n"
                "5. If you cannot recognize ANY medicine name clearly, output exactly: [\"UNCLEAR\"]\n"
                "6. Do not include markdown formatting like ```json in the output, just the raw array."
            )
            
            response = model.generate_content(
                [prompt, img],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=1024,
                    response_mime_type="application/json"
                )
            )
            
            # Handle successful response parsing
            logger.debug(f"Finish Reason: {response.candidates[0].finish_reason}")
            parsed_list = json.loads(response.text.strip())
            
            if isinstance(parsed_list, list):
                medicines = [str(m).strip() for m in parsed_list if str(m).strip().upper() != "UNCLEAR" and str(m).strip()]
                return medicines
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini: {response.text} Error: {e}")
            logger.error(f"Finish Reason: {response.candidates[0].finish_reason}")
            # If it cut off due to token limits, say so
            if response.candidates[0].finish_reason == 2:
                raise ValueError("Response was cut off. Please increase token limit or try a simpler image.")
            return []
            
        except Exception as e:
            logger.warning(f"Error calling Gemini API with key ending in ...{api_key[-4:] if len(api_key)>4 else ''}: {e}")
            
            # If it's a quota error, we continue to the next key
            if "429" in str(e) or "quota" in str(e).lower():
                last_error = e
                logger.info("Quota exceeded for this key. Trying the next key if available...")
                continue
                
            # If it's some other error, just raise or handle it immediately
            if isinstance(e, ValueError):
                raise e
            return []
            
    # If we loop through all keys and fail due to quota:
    if last_error:
        raise ValueError("AI API Quota Exceeded (Free Tier) across all provided keys. Please try again later.")
        
    return []
