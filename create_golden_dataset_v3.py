import pandas as pd
import os

# --- 1. Настройки Файлов ---
FILE_FAKES_EGEMEN = "generated_fakes_kz.csv"    # Llama-Egemen
FILE_FAKES_TENGRI = "generated_fakes_tengri.csv"  # Llama-Tengri
FILE_REAL_EGEMEN = "dataset_kz.csv"           # Egemen.kz
FILE_REAL_TENGRI = "tengri_news.csv"         # Tengrinews.kz

OUTPUT_FILE = "final_golden_dataset.csv" # Наш финальный датасет

TEXT_COLUMN_REAL = "text" # Как называется колонка в real-файлах
TEXT_COLUMN_FAKE = "fake_news_text" # Как называется колонка в fake-файлах

# --- 2. Загрузка Фейков (label=0) ---
print("--- Загрузка ФЕЙКОВ (label=0) ---")
try:
    df_fakes_egemen = pd.read_csv(FILE_FAKES_EGEMEN)
    df_fakes_egemen = df_fakes_egemen[[TEXT_COLUMN_FAKE]].rename(columns={TEXT_COLUMN_FAKE: 'text'})
    print(f"✅ Загружено {len(df_fakes_egemen)} фейков (Llama-Egemen)")
    
    df_fakes_tengri = pd.read_csv(FILE_FAKES_TENGRI)
    df_fakes_tengri = df_fakes_tengri[[TEXT_COLUMN_FAKE]].rename(columns={TEXT_COLUMN_FAKE: 'text'})
    print(f"✅ Загружено {len(df_fakes_tengri)} фейков (Llama-Tengri)")
    
    df_fakes_combined = pd.concat([df_fakes_egemen, df_fakes_tengri], ignore_index=True)
    df_fakes_combined['label'] = 0
    num_fakes = len(df_fakes_combined)
    print(f"Итого фейков: {num_fakes}")

except FileNotFoundError as e:
    print(f"🛑 ОШИБКА: Файл не найден: {e}. Убедись, что оба файла с фейками существуют.")
    exit()

# --- 3. Загрузка Реальных (label=1) ---
print("\n--- Загрузка РЕАЛЬНЫХ (label=1) ---")
try:
    df_real_egemen = pd.read_csv(FILE_REAL_EGEMEN)
    df_real_egemen = df_real_egemen[[TEXT_COLUMN_REAL]].rename(columns={TEXT_COLUMN_REAL: 'text'})
    print(f"✅ Загружено {len(df_real_egemen)} новостей (Egemen).")
    
    df_real_tengri = pd.read_csv(FILE_REAL_TENGRI)
    df_real_tengri = df_real_tengri[[TEXT_COLUMN_REAL]].rename(columns={TEXT_COLUMN_REAL: 'text'})
    print(f"✅ Загружено {len(df_real_tengri)} новостей (Tengrinews).")

except FileNotFoundError as e:
    print(f"🛑 ОШИБКА: Файл не найден: {e}. Убедись, что оба файла с реальными новостями существуют.")
    exit()

# --- 4. Балансировка Реальных ---
# Мы хотим, чтобы реальные новости были 50/50 из обоих источников
# Нам нужно всего `num_fakes` реальных новостей
num_real_needed_each = num_fakes // 2 

print(f"\nБалансировка: нам нужно {num_fakes} реальных новостей.")
print(f"Берем {num_real_needed_each} (Egemen) и {num_real_needed_each} (Tengrinews).")

df_real_egemen = df_real_egemen.sample(n=num_real_needed_each, random_state=42)
df_real_tengri = df_real_tengri.sample(n=num_real_needed_each, random_state=42)

df_real_combined = pd.concat([df_real_egemen, df_real_tengri], ignore_index=True)
df_real_combined['label'] = 1

# --- 5. Финальная Сборка и Перемешивание ---
print("Объединение реальных и фейковых...")
df_final = pd.concat([df_fakes_combined, df_real_combined], ignore_index=True)

print("Перемешивание...")
df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

# Очистка от пустых строк
df_final.dropna(subset=['text'], inplace=True)
df_final = df_final[df_final['text'].str.len() > 50]

# --- 6. Сохранение ---
df_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8', quoting=1)

print("\n--- ГОТОВО! ---")
print(f"Создан 'Бронебойный' датасет: {OUTPUT_FILE}")
print(f"Всего строк: {len(df_final)}")
print(f"Фейков (label 0): {len(df_final[df_final['label'] == 0])}")
print(f"Реальных (label 1): {len(df_final[df_final['label'] == 1])}")
