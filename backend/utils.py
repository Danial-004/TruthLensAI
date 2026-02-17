# backend/utils.py

import re
from typing import List, Dict, Set
from langdetect import detect, DetectorFactory
import logging
from datetime import datetime
import dateutil.parser as parser

# Инициализация для стабильных результатов langdetect
DetectorFactory.seed = 0
logger = logging.getLogger(__name__)

# --- НОВЫЕ ФУНКЦИИ ПРОВЕРКИ ФАКТОВ ---

def extract_numbers(text: str) -> Set[int]:
    """Извлекает из текста все числа (включая года)."""
    numbers = set()
    # Находит числа, например "45", "1991"
    found_numbers = re.findall(r'\b\d+\b', text)
    for num_str in found_numbers:
        # Игнорируем слишком большие числа, которые не могут быть годами или датами
        if len(num_str) <= 4:
            try:
                numbers.add(int(num_str))
            except ValueError:
                pass # Пропускаем, если что-то пошло не так
            
    # Ищем относительные даты, "XX лет назад"
    # TODO: Это специфично для русского языка, можно расширить для 'kk' и 'en'
    years_ago_match = re.search(r'(\d+)\s+лет\s+назад', text, re.IGNORECASE)
    if years_ago_match:
        try:
            years = int(years_ago_match.group(1))
            calculated_year = datetime.now().year - years
            numbers.add(calculated_year)
        except:
            pass # Игнорируем, если не получилось
            
    return numbers

def check_numerical_consistency(query_text: str, sources: List[Dict]) -> bool:
    """
    Проверяет, совпадают ли числа в запросе и в источниках.
    Возвращает True, если совпадение найдено (консистентно).
    Возвращает False, если совпадение НЕ найдено (НЕ консистентно).
    """
    query_numbers = extract_numbers(query_text)
    
    # Если в запросе нет чисел для проверки, считаем, что все в порядке
    if not query_numbers:
        return True

    for source in sources[:3]: # Проверяем топ-3 источника
        source_text = source.get("title", "") + " " + source.get("snippet", "")
        source_numbers = extract_numbers(source_text)
        
        # Если в источнике есть хоть одно число из запроса, считаем это совпадением
        if query_numbers.intersection(source_numbers):
            return True
            
    # Если мы прошли все источники и не нашли ни одного совпадения чисел
    logger.warning(f"Числа {query_numbers} из запроса не найдены в топ-3 источниках.")
    return False

# --- СТАРЫЕ ФУНКЦИИ (С ИСПРАВЛЕНИЯМИ) ---

def detect_language(text: str) -> str:
    """
    Определяет язык текста. Возвращает 'en', 'ru' или 'kk'.
    Принудительно возвращает 'kk' для казахского.
    """
    try:
        # ✅ ИСПРАВЛЕНО: Сначала быстрая проверка на казахские символы
        kazakh_chars = re.findall(r'[әіңғүұқөһӘІҢҒҮҰҚӨҺ]', text)
        if len(kazakh_chars) > 3:
            return "kk" # <-- ИСПРАВЛЕНО на 'kk'

        # Если казахских букв нет, используем langdetect
        detected = detect(text)
        
        # ✅ ИСПРАВЛЕНО: 'kk' (код langdetect) -> 'kk' (код нашей модели)
        lang_map = {"en": "en", "ru": "ru", "kk": "kk", "uk": "ru", "be": "ru"}
        
        # По умолчанию 'en', если язык не поддерживается
        return lang_map.get(detected, "en")
    except Exception as e:
        logger.warning(f"Ошибка детекции языка: {e}. Используется 'en'.")
        # В случае любой ошибки детекции
        return "en"

def preprocess_text(text: str) -> str:
    """Очищает текст от URL и лишних пробелов."""
    try:
        text = re.sub(r'http\S+|www\S+', '', text) # Удаляем URL
        text = re.sub(r'\s+', ' ', text).strip() # Заменяем \n, \t и двойные пробелы
        return text
    except:
        return text # Возвращаем как есть в случае ошибки

def get_final_verdict(prediction: dict, sources: list, original_text: str) -> dict:
    """
    Принимает решение о финальном вердикте, комбинируя предсказание модели
    и результаты NLI-анализа источников, а также проверку чисел.
    """
    # --- НОВЫЙ ШАГ: ПРОВЕРКА ЧИСЕЛ ---
    # Если источники найдены, И проверка чисел НЕ пройдена (False), 
    # то принудительно ставим "fake"
    if sources and not check_numerical_consistency(original_text, sources):
        logger.info("Вердикт 'fake' из-за несоответствия чисел.")
        return {
            "classification": "fake", 
            "confidence": 0.95, # Высокая уверенность, т.к. факт не совпал
            "explanation_key": "fake_fact_contradiction"
        }

    # --- СТАНДАРТНАЯ ЛОГИКА ---
    CONFIDENCE_THRESHOLD = 0.75 # Порог уверенности для модели
    
    # 1. Ищем сильное опровержение в топ-3 источниках
    strong_contradiction = next((s for s in sources[:3] if s.get("relevance", 0) < -0.6), None)
    if strong_contradiction:
        logger.info("Вердикт 'fake' из-за NLI contradiction.")
        # Уверенность = 0.9 + (0.6 / 10) = 0.96 (если relevance = -0.6)
        conf = 0.9 + abs(strong_contradiction["relevance"]) / 10 
        return {
            "classification": "fake", 
            "confidence": min(conf, 0.99), # Ограничиваем 0.99
            "explanation_key": "fake_contradicted"
        }

    # 2. Ищем сильное подтверждение
    strong_entailment = next((s for s in sources[:3] if s.get("relevance", 0) > 0.7), None)
    if strong_entailment:
        logger.info("Вердикт 'real' из-за NLI entailment.")
        return {
            "classification": "real", 
            "confidence": min(strong_entailment["relevance"], 0.99), 
            "explanation_key": "real_supported"
        }

    # 3. Если NLI не дал четкого ответа, смотрим на вердикт самой модели
    real_prob = prediction.get("real_prob", 0)
    fake_prob = prediction.get("fake_prob", 0)

    if real_prob > CONFIDENCE_THRESHOLD:
        logger.info("Вердикт 'real' из-за высокой уверенности модели.")
        return {"classification": "real", "confidence": real_prob, "explanation_key": "real_high_conf"}
    elif fake_prob > CONFIDENCE_THRESHOLD:
        logger.info("Вердикт 'fake' из-за высокой уверенности модели.")
        return {"classification": "fake", "confidence": fake_prob, "explanation_key": "fake_high_conf"}
    
    # 4. Если уверенность модели низкая (ниже 0.75)
    logger.info("Низкая уверенность модели. Выдан вердикт 'uncertain'.")
    classification = "real" if real_prob > fake_prob else "fake"
    confidence = max(real_prob, fake_prob)
    return {
        "classification": classification, 
        "confidence": confidence, 
        "explanation_key": "uncertain"
    }


def generate_explanation(verdict: dict, language: str) -> str:
    """Возвращает текстовое объяснение вердикта на нужном языке."""
    explanations = {
        "en": {
            "uncertain": "Low confidence classification. The analysis is inconclusive. Please check the sources.",
            "fake_contradicted": "Fake News Detected. The claim is directly contradicted by information found in reliable web sources.",
            "real_supported": "Verified Information. The claim is supported by findings from reliable web sources.",
            "fake_high_conf": "Likely Fake. The text shows stylistic patterns of misinformation, but web sources are inconclusive.",
            "real_high_conf": "Likely Real. The text's style aligns with verified reports, but web sources are inconclusive.",
            "fake_fact_contradiction": "Fake News Detected. Numerical data (like dates or numbers) in the claim does not match information from web sources."
        },
        "ru": {
            "uncertain": "Низкая уверенность в классификации. Анализ не дал однозначного результата. Пожалуйста, проверьте источники.",
            "fake_contradicted": "Обнаружен фейк. Утверждение прямо противоречит информации из надежных веб-источников.",
            "real_supported": "Информация подтверждена. Утверждение подкрепляется данными из надежных веб-источников.",
            "fake_high_conf": "Вероятно, фейк. Текст демонстрирует стилистические признаки дезинформации, но веб-источники не дали однозначного ответа.",
            "real_high_conf": "Вероятно, правда. Стиль текста соответствует проверенным сообщениям, но веб-источники не дали однозначного ответа.",
            "fake_fact_contradiction": "Обнаружен фейк. Числовые данные (например, даты или количество) в утверждении не совпадают с информацией из веб-источников."
        },
        "kk": {
            # (ЗАПОЛНИТЕЛЬ: добавь сюда казахские переводы)
            "uncertain": "Төмен сенімділік. Талдау нақты нәтиже бермеді. Көздерді тексеріңіз.",
            "fake_contradicted": "Жалған ақпарат анықталды. Бұл мәлімдеме сенімді веб-көздердегі ақпаратқа тікелей қайшы келеді.",
            "real_supported": "Ақпарат расталды. Бұл мәлімдеме сенімді веб-көздердегі деректермен расталады.",
            "fake_high_conf": "Ықтимал жалған. Мәтін дезинформацияның стилистикалық белгілерін көрсетеді, бірақ веб-көздер нақты жауап бермеді.",
            "real_high_conf": "Ықтимал шындық. Мәтіннің стилі расталған хабарламаларға сәйкес келеді, бірақ веб-көздер нақты жауап бермеді.",
            "fake_fact_contradiction": "Жалған ақпарат анықталды. Мәлімдемедегі сандық деректер (мысалы, күндер немесе сандар) веб-көздердегі ақпаратқа сәйкес келмейді."
        }
    }
    lang_explanations = explanations.get(language, explanations["en"])
    return lang_explanations.get(verdict["explanation_key"], lang_explanations["uncertain"])