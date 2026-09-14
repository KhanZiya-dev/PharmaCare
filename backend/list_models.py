import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
for m in genai.list_models():
    print(m.name)
