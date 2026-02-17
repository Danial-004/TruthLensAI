import google.generativeai as genai

# Вставь сюда свой API-ключ
genai.configure(api_key="AIzaSyA2Ssaui-hmoMKbmIVOweM3TseBDEOHj6w")

models = genai.list_models()

print("📋 Доступные модели:\n")
for model in models:
    print(f"🔹 {model.name}")
    print(f"   Поддерживает generate_content: {'generateContent' in model.supported_generation_methods}")
    print(f"   Методы: {model.supported_generation_methods}\n")
