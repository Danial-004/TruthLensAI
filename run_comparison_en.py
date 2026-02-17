import pandas as pd
from tqdm import tqdm
import time
import logging
import os

# --- 1. ИМПОРТЫ ---
logging.getLogger("transformers").setLevel(logging.ERROR)
from backend.model import FakeNewsDetector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# --- 2. ЗАГРУЗКА ДАННЫХ ---
# ❗️ УКАЖИ ПУТЬ К АНГЛИЙСКОМУ ОБУЧАЮЩЕМУ ФАЙЛУ
PATH_TO_TRAIN_CSV = r"C:\Users\Admin\Desktop\TruthLensAI2\processed_data\dataset_en.csv"
# ❗️ ПУТЬ К НОВОМУ АНГЛИЙСКОМУ ТЕСТУ
PATH_TO_TEST_CSV = r"C:\Users\Admin\Desktop\TruthLensAI2\dataset_en_test.csv"

print("Загрузка АНГЛИЙСКИХ данных...")
try:
    train_df = pd.read_csv(PATH_TO_TRAIN_CSV)
    test_df = pd.read_csv(PATH_TO_TEST_CSV)
except FileNotFoundError as e:
    print(f"❌ ОШИБКА: Файл не найден: {e.filename}")
    print("Пожалуйста, проверь оба пути, особенно PATH_TO_TRAIN_CSV.")
    exit()

# --- Приведение меток к 'real'/'fake' ---
LABEL_COLUMN = 'label' 
TEXT_COLUMN = 'text'   

try:
    train_labels_str = train_df[LABEL_COLUMN].astype(str)
    real_labels_str = test_df[LABEL_COLUMN].astype(str)
    
    label_map = {'0': 'fake', '1': 'real', 'real': 'real', 'fake': 'fake'}
    
    train_labels = train_labels_str.map(label_map)
    real_labels = real_labels_str.map(label_map)
    
    train_texts = train_df[TEXT_COLUMN]
    test_texts = test_df[TEXT_COLUMN]
    
    if train_labels.isnull().any() or real_labels.isnull().any():
        print(f"❌ ОШИБКА: В колонке '{LABEL_COLUMN}' найдены неизвестные значения.")
        exit()

except KeyError as e:
    print(f"❌ ОШИБКА: Не найдена колонка: {e}. Проверь 'text' и 'label'.")
    exit()
    
print(f"Загружено: {len(train_texts)} для обучения, {len(test_texts)} для теста.")
print(f"Примеры меток (должны быть 'real'/'fake'): {train_labels.unique()}")


# --- 3. ML-МОДЕЛЬ (BASELINE / TOYOTA) ---
print("\n--- Обучение ML (Baseline) модели на АНГЛИЙСКИХ данных... ---")
start_time = time.time()

ml_baseline_model = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=10000, stop_words='english')), # Добавили англ. стоп-слова
    ('clf', LogisticRegression(max_iter=1000, random_state=42))
])

ml_baseline_model.fit(train_texts, train_labels)
print(f"✅ ML-модель обучена за {time.time() - start_time:.2f} сек.")

print("Получение предсказаний от ML-модели...")
ml_predictions = ml_baseline_model.predict(test_texts)


# --- 4. DL-МОДЕЛЬ (ТВОЯ / FERRARI) ---
print("\n--- Загрузка DL (Трансформер) модели... ---")
start_time = time.time()
detector = FakeNewsDetector() 

# Ищем английскую модель
dl_model_name = "Не найдена 'en' модель"
if 'en' in detector.classifier_models:
    dl_model_name = detector.classifier_models.get('en').config._name_or_path
else:
    print("ВНИМАНИЕ: Модель для 'en' не найдена в 'backend/models/'.")
    print("Убедись, что у тебя есть папка 'truthlens_en_model'.")
    
print(f"✅ DL-модель ('{dl_model_name}') загружена за {time.time() - start_time:.2f} сек.")

print("Получение предсказаний от DL-модели (на АНГЛИЙСКИХ данных)...")
dl_predictions = []
for text in tqdm(test_texts): 
    # ❗️ ГЛАВНОЕ ИЗМЕНЕНИЕ: используем 'en'
    prediction = detector.predict(text, 'en') 
    dl_predictions.append(prediction['classification'])


# --- 5. РЕЗУЛЬТАТЫ (ТА САМАЯ ТАБЛИЦА) ---
print("\n\n--- ИТОГОВОЕ СРАВНЕНИЕ АНГЛИЙСКИХ МОДЕЛЕЙ ---")

print("\n--- 1. ML (Baseline) модель (LogisticRegression + TF-IDF) ---")
ml_report = classification_report(real_labels, ml_predictions, labels=['fake', 'real'])
print(ml_report)

print(f"\n--- 2. DL (Твоя) модель ({dl_model_name}) ---")
dl_report = classification_report(real_labels, dl_predictions, labels=['fake', 'real'])
print(dl_report)


# --- 6. СОХРАНЕНИЕ РЕЗУЛЬТАТОВ В ФАЙЛ ---
report_filename = "comparison_report_EN.txt" # Новое имя файла
print(f"\n--- Сохранение отчета в '{report_filename}'... ---")

try:
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("--- ИТОГОВОЕ СРАВНЕНИЕ АНГЛИЙСКИХ МОДЕЛЕЙ ---\n")
        f.write(f"Тестовая выборка: {PATH_TO_TEST_CSV}\n")
        f.write(f"Количество тестовых примеров: {len(test_texts)}\n")
        f.write("========================================\n\n")
        
        f.write("--- 1. ML (Baseline) модель (LogisticRegression + TF-IDF) ---\n")
        f.write(ml_report)
        f.write("\n\n")
        
        f.write(f"--- 2. DL (Твоя) модель (Трансформер: {dl_model_name}) ---\n")
        f.write(dl_report)
        f.write("\n\n")
        
    print(f"✅ Отчет успешно сохранен в файл: {os.path.abspath(report_filename)}")
except Exception as e:
    print(f"❌ Не удалось сохранить отчет в файл: {e}")