import os
import google.generativeai as genai
from PIL import Image
import logging
import json
import re

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
        # Optimize: Downscale image to max 800x800 to save bandwidth and tokens
        img = Image.open(image_path).convert('RGB')
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Optimize: Much shorter prompt to save text tokens while keeping strict rules
        prompt = (
            "Extract ONLY medicine/drug names from this image.\n"
            "RULES:\n"
            "1. Ignore dosages (500mg), frequencies (1-0-1), and doctor/patient details.\n"
            "2. Preserve exact spelling. Don't guess if illegible; output 'UNCLEAR'.\n"
            "3. Return ONLY a valid JSON array of strings. No markdown, no explanations.\n"
            "Example: [\"Paracetamol\", \"UNCLEAR\"]"
        )
        
        response = model.generate_content(
            [prompt, img],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=150,
            )
        )
        
        if not response.text:
            return []
            
        # Use regex to find the JSON array in case Gemini adds conversational text
        raw_text = response.text.strip()
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        
        if not match:
            logger.error(f"No JSON array found in Gemini response: {raw_text}")
            return []
            
        json_str = match.group(0)
        
        try:
            parsed_list = json.loads(json_str)
            medicines = [str(m).strip() for m in parsed_list if str(m).strip().upper() != "UNCLEAR" and str(m).strip()]
            return medicines
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Gemini: {json_str}")
            return []
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return []
