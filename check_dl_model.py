import google.generativeai as genai
import os
from dotenv import load_dotenv

# Загружаем .env, чтобы получить твой ключ
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Ошибка: GEMINI_API_KEY не найден в .env файле!")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    print("--- Список доступных моделей для твоего API ключа ---")
    
    try:
        for model in genai.list_models():
            # Мы ищем модели, которые поддерживают 'generateContent'
            if 'generateContent' in model.supported_generation_methods:
                print(f"Модель: {model.name}")
                print(f"  Дисплей: {model.display_name}\n")
                
    except Exception as e:
        print(f"Произошла ошибка при получении списка моделей: {e}")
        print("---")
        print("Возможная причина: твоя библиотека 'google-generativeai' все еще старая.")
        print("Попробуй еще раз: pip install --upgrade google-generativeai")

print("--- Проверка завершена ---")