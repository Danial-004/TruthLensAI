import google.generativeai as genai
import os


def list_my_models():
    # Сіздің барлық кодтарыңызды осы функцияның ішіне кіргізіңіз (шегініспен/TAB)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("API Key not found")
        return
        
    genai.configure(api_key=api_key)

    models = genai.list_models()
    print("Available models:")
    for model in models:
        print(model)
if __name__ == "__main__":
    list_my_models()