# backend/model.py (Версия с поддержкой 'kk' модели)

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, XLMRobertaTokenizer
from typing import Dict, List
import logging
import os

logger = logging.getLogger(__name__)

class FakeNewsDetector:
    """
    Класс-менеджер для управления моделями.
    Загружает все доступные языковые модели-"специалисты"
    (например, 'en', 'kk') и выбирает нужную
    в зависимости от языка текста.
    Также содержит NLI модель для ранжирования источников.
    """
    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Используется устройство: {self.device}")

        self.classifier_models: Dict[str, AutoModelForSequenceClassification] = {}
        self.classifier_tokenizers: Dict[str, AutoTokenizer] = {}
        # Путь к папке, где лежат папки с моделями (truthlens_en_model, truthlens_kk_model)
        models_base_path = "backend/models"

        # --- ШАГ 1: АВТОМАТИЧЕСКАЯ ЗАГРУЗКА ВСЕХ КЛАССИФИКАЦИОННЫХ МОДЕЛЕЙ ---
        # Сканирует папку models_base_path и загружает все модели, которые находит.
        # Ожидаются папки вида 'truthlens_xx_model', где xx - код языка (en, kk, ru и т.д.)
        logger.info(f"Поиск моделей классификации в: {models_base_path}")
        try:
            # Проверяем, существует ли базовая папка
            if not os.path.isdir(models_base_path):
                 logger.warning(f"Папка с моделями '{models_base_path}' не найдена!")
            else:
                for item_name in os.listdir(models_base_path):
                    model_path = os.path.join(models_base_path, item_name)
                    # Проверяем, что это папка, что имя соответствует шаблону и есть config.json
                    if (os.path.isdir(model_path) and
                        item_name.startswith("truthlens_") and
                        item_name.endswith("_model") and
                        "config.json" in os.listdir(model_path)):

                        # Извлекаем код языка из имени папки
                        try:
                             # Например, 'truthlens_kk_model' -> 'kk'
                            lang_code = item_name.split('_')[1]
                            if len(lang_code) != 2: # Простая проверка, что это двухбуквенный код
                                raise ValueError("Некорректный код языка в имени папки")
                        except (IndexError, ValueError):
                             logger.warning(f"Не удалось извлечь код языка из имени папки '{item_name}'. Пропускаем.")
                             continue

                        logger.info(f"Найдена модель для языка '{lang_code}'. Загрузка из: {model_path}")
                        try:
                            tokenizer = AutoTokenizer.from_pretrained(model_path)
                            model = AutoModelForSequenceClassification.from_pretrained(model_path)
                            model.to(self.device)
                            model.eval() # Переводим модель в режим оценки

                            self.classifier_models[lang_code] = model
                            self.classifier_tokenizers[lang_code] = tokenizer
                            logger.info(f"✅ Модель для языка '{lang_code}' успешно загружена.")
                        except Exception as load_err:
                             logger.error(f"❌ Ошибка загрузки модели для языка '{lang_code}' из {model_path}: {load_err}", exc_info=True)

            # Проверяем, загрузились ли хоть какие-то модели
            if not self.classifier_models:
                logger.error("🛑 КРИТИЧЕСКАЯ ОШИБКА: Не найдено или не удалось загрузить ни одной обученной модели классификации в 'backend/models/'.")
                # Можно здесь выбросить исключение, чтобы приложение не запустилось
                # raise RuntimeError("Не удалось загрузить модели классификации.")
            else:
                 logger.info(f"Загружены модели классификации для языков: {list(self.classifier_models.keys())}")


            # --- ШАГ 2: ЗАГРУЗКА NLI МОДЕЛИ ДЛЯ РАНЖИРОВАНИЯ ИСТОЧНИКОВ ---
            # Эта модель остается одна, так как она мультиязычная (XLM-R)
            nli_model_name = "joeddav/xlm-roberta-large-xnli"
            logger.info(f"Загрузка NLI модели: {nli_model_name}")
            try:
                self.nli_tokenizer = XLMRobertaTokenizer.from_pretrained(nli_model_name)
                self.nli_model = AutoModelForSequenceClassification.from_pretrained(nli_model_name)
                self.nli_model.to(self.device)
                self.nli_model.eval()
                logger.info("✅ NLI модель успешно загружена.")
            except Exception as nli_err:
                 logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось загрузить NLI модель {nli_model_name}: {nli_err}", exc_info=True)
                 # Если NLI модель важна, можно тоже выбросить исключение
                 # raise RuntimeError("Не удалось загрузить NLI модель.")
                 self.nli_tokenizer = None
                 self.nli_model = None


        except Exception as e:
            logger.error(f"❌ Критическая ошибка во время инициализации FakeNewsDetector: {e}", exc_info=True)
            raise # Перебрасываем исключение, чтобы FastAPI знал о проблеме при старте

    def predict(self, text: str, language: str) -> Dict:
        """
        Предсказывает класс текста ('real' или 'fake'), используя модель
        для указанного языка.

        Args:
            text (str): Текст для анализа.
            language (str): Код языка ('en', 'kk', 'ru', ...).

        Returns:
            Dict: Словарь с ключами 'classification' ('real', 'fake' или 'uncertain')
                  и 'confidence' (вероятность предсказанного класса).
                  В случае ошибки может вернуть 'classification': 'error'.
        """
        # --- ВЫБОР НУЖНОГО КЛАССИФИКАТОРА ---
        model = self.classifier_models.get(language)
        tokenizer = self.classifier_tokenizers.get(language)

        if not model or not tokenizer:
            logger.warning(f"Модель классификации для языка '{language}' не найдена.")
            # --- ВАРИАНТ ОБРАБОТКИ ОТСУТСТВИЯ МОДЕЛИ ---
            # Можно выбрать поведение:
            # 1. Вернуть "неопределенный" результат:
            return {"classification": "uncertain", "confidence": 0.5}
            # 2. Попробовать использовать модель по умолчанию (например, 'en'):
            # default_lang = 'en'
            # if default_lang in self.classifier_models:
            #     logger.warning(f"Используется модель по умолчанию: '{default_lang}'")
            #     model = self.classifier_models[default_lang]
            #     tokenizer = self.classifier_tokenizers[default_lang]
            # else:
            #     logger.error(f"Модель по умолчанию '{default_lang}' также не найдена.")
            #     return {"classification": "error", "confidence": 0.0, "error": "No suitable model found"}
            # 3. Вернуть явную ошибку (текущий код делает это ниже через raise)

        logger.info(f"Используется модель классификации для языка: {language}")
        try:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            # Перемещаем тензоры на нужное устройство
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad(): # Отключаем расчет градиентов для ускорения
                outputs = model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)[0] # Берем [0], так как батч=1

            # --- Определение класса ---
            # Используем id2label из конфигурации модели, если он есть
            id2label = model.config.id2label if hasattr(model.config, 'id2label') else {0: 'REAL', 1: 'FAKE'} # Значения по умолчанию
            predicted_class_id = probabilities.argmax().item()

            label_map = {v.upper(): k for k, v in id2label.items()} # {'REAL': 0, 'FAKE': 1}
            fake_label_id = label_map.get('FAKE', 1) # Ищем ID для FAKE, по умолчанию 1

            fake_prob = probabilities[fake_label_id].item()
            real_prob = probabilities[label_map.get('REAL', 0)].item()

            if fake_prob > real_prob:
                 classification = "fake"
                 confidence = fake_prob
            else:
                 classification = "real"
                 confidence = real_prob

            logger.debug(f"Предсказание ({language}): fake_prob={fake_prob:.4f}, real_prob={real_prob:.4f} -> {classification} (conf: {confidence:.4f})")

            return {
                "classification": classification,
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"Ошибка предсказания классификации для языка '{language}': {e}", exc_info=True)
            # Возвращаем ошибку, которую может обработать app.py
            # Важно: Не возвращай просто строку, а словарь, чтобы соответствовать ожидаемому типу Dict
            return {"classification": "error", "confidence": 0.0, "error": f"Prediction failed for lang {language}"}


    def rank_sources_nli(self, query_text: str, search_results: List[Dict]) -> List[Dict]:
        """
        Ранжирует список результатов поиска (словари с 'snippet', 'url', 'title')
        по релевантности к query_text с использованием NLI модели.
        Добавляет ключ 'relevance' к каждому результату.
        Возвращает отсортированный список.
        """
        if not self.nli_model or not self.nli_tokenizer:
             logger.warning("NLI модель недоступна. Ранжирование источников невозможно.")
             return search_results # Возвращаем как есть

        if not search_results:
            return []

        ranked_results = []
        # Получаем ID для меток из конфигурации NLI модели
        # Значения по умолчанию (0, 1, 2) взяты из стандартной конфигурации xnli
        entailment_id = self.nli_model.config.label2id.get('entailment', 2)
        contradiction_id = self.nli_model.config.label2id.get('contradiction', 0)
        neutral_id = self.nli_model.config.label2id.get('neutral', 1)

        logger.debug(f"NLI label IDs: Entailment={entailment_id}, Contradiction={contradiction_id}, Neutral={neutral_id}")

        for result in search_results:
            snippet = result.get("snippet") or result.get("description") or "" # Используем и snippet, и description
            if len(snippet) < 15: # Пропускаем слишком короткие описания
                 logger.debug(f"Пропуск источника из-за короткого сниппета: {result.get('url')}")
                 continue

            # NLI модель ожидает пару: (premise, hypothesis)
            # premise - это текст источника (snippet), hypothesis - это утверждение (query_text)
            premise, hypothesis = snippet, query_text

            try:
                inputs = self.nli_tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, max_length=256).to(self.device)

                with torch.no_grad():
                    outputs = self.nli_model(**inputs)
                    probabilities = torch.softmax(outputs.logits, dim=-1)[0]

                # Считаем релевантность как (вероятность подтверждения - вероятность противоречия)
                # Это простой способ, можно использовать и другие метрики
                relevance = probabilities[entailment_id].item() - probabilities[contradiction_id].item()
                # Можно добавить и neutral_prob для отладки
                # neutral_prob = probabilities[neutral_id].item()
                # logger.debug(f"NLI scores for '{result.get('title', '')[:30]}...': E={probabilities[entailment_id]:.3f}, C={probabilities[contradiction_id]:.3f}, N={neutral_prob:.3f} -> Relevance={relevance:.3f}")


                result_copy = result.copy()
                result_copy["relevance"] = relevance
                ranked_results.append(result_copy)
            except Exception as nli_pred_err:
                 logger.warning(f"Ошибка NLI предсказания для источника {result.get('url')}: {nli_pred_err}", exc_info=False) # Не логируем весь трейсбек
                 continue # Пропускаем этот источник

        # Сортируем результаты по убыванию релевантности
        ranked_results.sort(key=lambda x: x.get("relevance", -1.0), reverse=True)

        logger.info(f"Ранжировано {len(ranked_results)} источников с помощью NLI.")
        return ranked_results