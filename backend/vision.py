import os
import google.generativeai as genai
from PIL import Image
import logging
import json

logger = logging.getLogger(__name__)

# Try configuring the API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY is not set in the environment.")

def extract_medicines_from_image(image_path: str) -> list[str]:
    """
    Extracts medicine names from an image using Gemini Pro Vision.
    Returns a list of extracted medicine names.
    """
    if not api_key:
        logger.error("Cannot extract text: GEMINI_API_KEY is missing.")
        return []
        
    try:
        model = genai.GenerativeModel('gemini-3.6-flash')
        img = Image.open(image_path)
        
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
            "'similar sounding' drug unless you are highly confident.\n"
            "4. If a name is fully illegible or you are not confident, write it as "
            "'UNCLEAR' instead of guessing a random medicine name.\n"
            "5. Do not add any medicine that is not visibly present in the image.\n"
            "6. Do not repeat the same medicine twice even if written twice.\n\n"
            "OUTPUT FORMAT: Return ONLY a valid JSON array of strings, nothing else, "
            "no explanation, no markdown formatting, no backticks.\n"
            "Example: [\"Paracetamol\", \"Amoxicillin\", \"UNCLEAR\"]"
        )
        
        response = model.generate_content([prompt, img])
        
        if not response.text:
            return []
            
        # Parse JSON array output
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        try:
            parsed_list = json.loads(raw_text)
            medicines = [str(m).strip() for m in parsed_list if str(m).strip().upper() != "UNCLEAR" and str(m).strip()]
            return medicines
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Gemini: {raw_text}")
            return []
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return []
