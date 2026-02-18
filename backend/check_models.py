import google.generativeai as genai

# Вставь сюда свой API-ключ
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

models = genai.list_models()

print("📋 Доступные модели:\n")
for model in models:
    print(f"🔹 {model.name}")
    print(f"   Поддерживает generate_content: {'generateContent' in model.supported_generation_methods}")
    print(f"   Методы: {model.supported_generation_methods}\n")
