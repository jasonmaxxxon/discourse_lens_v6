import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
# 確保 API Key 存在
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=api_key)
    print("🔍 Listing available models...")
    try:
        found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                found = True
        if not found:
            print("⚠️ No models found with generateContent support.")
    except Exception as e:
        print(f"❌ Error: {e}")
