# tests/test_model.py
"""
Unit Tests for the FakeNewsDetector ML Model

This script tests the core functionalities of the FakeNewsDetector class,
including model initialization, prediction, and source ranking.

To run these tests:
1. Make sure you are in the `backend/` directory.
2. Run the command: pytest -v
"""

import pytest
from backend.model import FakeNewsDetector
from typing import Dict, List

# --- Pytest Fixture ---
# Эта фикстура создает один экземпляр FakeNewsDetector для всех тестов в этом файле.
# scope="module" означает, что модели загрузятся в память только один раз,
# что сильно ускоряет выполнение тестов.
@pytest.fixture(scope="module")
def detector() -> FakeNewsDetector:
    """Provides a shared instance of the FakeNewsDetector."""
    try:
        return FakeNewsDetector()
    except Exception as e:
        # Если модели не скачаны, тест будет пропущен с сообщением.
        pytest.skip(f"Skipping model tests. Could not load models: {e}")


# --- Test Cases ---

def test_model_initialization(detector: FakeNewsDetector):
    """
    Test 1: Check if the FakeNewsDetector and its components initialize correctly.
    """
    assert detector is not None
    assert detector.tokenizer is not None, "Tokenizer should be loaded."
    assert detector.model is not None, "Classification model should be loaded."
    assert detector.embedder is not None, "Embedding model should be loaded."


@pytest.mark.parametrize("text, language", [
    ("Scientists have discovered water on Mars, a finding that could have significant implications for future space exploration.", "en"),
    ("Вчера в Москве прошел сильный снегопад, который привел к транспортному коллапсу в центре города.", "ru"),
    ("Бүгін Астана қаласында жаңа технологиялық хабтың тұсаукесері өтті, шараға көптеген инвесторлар қатысты.", "kz")
])
def test_predict_functionality(detector: FakeNewsDetector, text: str, language: str):
    """
    Test 2: Check the predict() method for different languages.
    Ensures it returns a dictionary with the correct keys and data types.
    """
    result = detector.predict(text, language)

    # Проверяем структуру ответа
    assert isinstance(result, dict), "Prediction result should be a dictionary."
    assert "label" in result, "Result must contain a 'label' key."
    assert "confidence" in result, "Result must contain a 'confidence' key."
    assert "keywords" in result, "Result must contain a 'keywords' key."

    # Проверяем типы данных
    assert isinstance(result["label"], int), "Label should be an integer (0 or 1)."
    assert isinstance(result["confidence"], float), "Confidence should be a float."
    assert 0.0 <= result["confidence"] <= 1.0, "Confidence score must be between 0 and 1."
    assert isinstance(result["keywords"], list), "Keywords should be a list."


def test_rank_sources(detector: FakeNewsDetector):
    """
    Test 3: Check the rank_sources() method.
    Ensures it correctly calculates relevance and sorts the sources.
    """
    query_text = "The president signed a new decree on environmental protection."

    # Моделируем результаты поиска из search_api.py
    mock_search_results: List[Dict] = [
        {"title": "Sports News Today", "url": "http://example.com/sports", "snippet": "A great victory for the local football team."},
        {"title": "Official Government Portal", "url": "http://example.com/gov", "snippet": "A new presidential decree regarding ecology and environmental protection was signed into law."},
        {"title": "Cooking Recipes", "url": "http://example.com/cooking", "snippet": "How to bake the perfect apple pie."}
    ]

    ranked_sources = detector.rank_sources(query_text, mock_search_results)

    # Проверяем, что все источники на месте и имеют новое поле 'relevance'
    assert len(ranked_sources) == len(mock_search_results), "Should return the same number of sources."
    assert "relevance" in ranked_sources[0], "Each source should have a 'relevance' score."

    # Проверяем, что источники отсортированы по релевантности (по убыванию)
    relevance_scores = [source["relevance"] for source in ranked_sources]
    assert relevance_scores == sorted(relevance_scores, reverse=True), "Sources should be sorted by relevance."

    # Проверяем, что самый релевантный источник теперь на первом месте
    assert "Government Portal" in ranked_sources[0]["title"], "The most relevant source should be ranked first."