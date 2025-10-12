# check_models.py

import google.generativeai as genai
from dotenv import load_dotenv
import os

# This loads the GEMINI_API_KEY from your .env file
load_dotenv()

try:
    api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    print("\n--- Finding all models available to your API key ---")
    
    # List all models and find the ones that support 'generateContent'
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Found usable model: {m.name}")

    print("--------------------------------------------------\n")
    print("ACTION: Copy the most appropriate model name from the list above (e.g., 'models/gemini-1.5-flash-latest' or 'models/gemini-pro')")
    print("and paste it into the 'genai.GenerativeModel()' line in your backend/llm_handler.py file.")

except Exception as e:
    print(f"An error occurred: {e}")
    print("Please ensure your GEMINI_API_KEY in the .env file is correct.")