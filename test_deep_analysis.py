# test_deep_analysis.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import os
import sys
from pprint import pprint
from dotenv import load_dotenv

# --- ГЛАВНОЕ ИСПРАВЛЕНИЕ: ЗАГРУЖАЕМ .env ФАЙЛ ---
print("Загрузка переменных окружения из .env файла...")
load_dotenv()

# Добавляем папку backend в путь, чтобы можно было импортировать модули
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Теперь мы можем импортировать наши модули
from model import FakeNewsDetector
from search_api import WebSearcher
from utils import preprocess_text, get_final_verdict, generate_explanation

def test_analysis(text_to_analyze):
    print("="*50)
    print("🚀 НАЧИНАЕМ ДИАГНОСТИКУ DEEP ANALYSIS")
    print("="*50)

    # Проверяем, на месте ли обученная модель
    model_path = "backend/models/trained_model"
    if not os.path.exists(model_path):
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Папка с обученной моделью не найдена по пути: {model_path}")
        print("Пожалуйста, убедитесь, что вы скачали, распаковали, переименовали и положили модель в нужное место.")
        return
        
    # Проверяем наличие API-ключа
    if not os.getenv("SERP_API_KEY"):
        print("⚠️ ВНИМАНИЕ: SERP_API_KEY не найден в .env файле. Веб-поиск будет использовать резервный метод.")


    try:
        print("\n[Шаг 1/4] Инициализация компонентов...")
        detector = FakeNewsDetector()
        searcher = WebSearcher()
        print("✅ Компоненты успешно инициализированы.")
    except Exception as e:
        print(f"❌ ОШИБКА при инициализации: {e}")
        return

    print(f"\n[Шаг 2/4] Обработка и анализ исходного текста...")
    clean_text = preprocess_text(text_to_analyze)
    initial_prediction = detector.predict(clean_text)
    print("РЕЗУЛЬТАТ ПЕРВИЧНОГО АНАЛИЗА (ОБУЧЕННАЯ МОДЕЛЬ):")
    pprint(initial_prediction)

    print("\n[Шаг 3/4] Поиск доказательств в интернете...")
    search_results = searcher.search(clean_text, language='en', max_results=5)
    if not search_results:
        print("⚠️ Поиск не дал результатов.")
    else:
        print(f"✅ Найдено {len(search_results)} источников.")

    print("\n[Шаг 4/4] Ранжирование источников с помощью NLI-модели...")
    ranked_sources = detector.rank_sources_nli(clean_text, search_results)
    
    if not ranked_sources:
        print("⚠️ После NLI-ранжирования не осталось релевантных источников.")
    else:
        print("РЕЗУЛЬТАТ NLI-РАНЖИРОВАНИЯ (от лучшего к худшему):")
        for source in ranked_sources:
            print(f"  - Источник: {source.get('title')}, БАЛЛ NLI: {source.get('relevance', 'N/A'):.2f}")
    
    # --- ФИНАЛЬНЫЙ ВЕРДИКТ ---
    final_verdict = get_final_verdict(initial_prediction, ranked_sources, original_text=text_to_analyze)
    final_explanation = generate_explanation(final_verdict, 'en') # Язык для примера
    
    print("\n" + "="*50)
    print("🏁 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    print("="*50)
    print(f"Вердикт: {final_verdict.get('classification')}")
    print(f"Уверенность: {final_verdict.get('confidence'):.2%}")
    print(f"Объяснение: {final_explanation}")


if __name__ == "__main__":
    example_text = "New Study Claims Smartphones May Affect Long-Term Memory"
    test_analysis(example_text)