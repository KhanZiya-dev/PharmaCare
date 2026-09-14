import os
import google.generativeai as genai
from PIL import Image
import logging

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
            "You are a medical text extractor. Look at this image (which could be a handwritten prescription "
            "or a medicine box) and extract only the names of the medicines or drugs present. "
            "Ignore dosages (like 100mg), instructions (like 1-1), doctor names, or other irrelevant text. "
            "Just list the medicine names separated by commas. E.g. Paracetamol, Amoxicillin"
        )
        
        response = model.generate_content([prompt, img])
        
        if not response.text:
            return []
            
        # Parse comma separated list
        raw_text = response.text.strip()
        medicines = [m.strip() for m in raw_text.split(",") if m.strip()]
        
        return medicines
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return []
