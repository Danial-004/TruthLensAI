import pandas as pd
import os

# --- Настройки ---
# ❗️ ИСТОЧНИК ФЕЙКОВ - ТЕПЕРЬ ТВОЙ ФАЙЛ С GPT-ФЕЙКАМИ
FILE_FAKES_SOURCE = "generated_fakes_kz_100.csv"
# ❗️ ИСТОЧНИКИ РЕАЛЬНЫХ - ОРИГИНАЛЬНЫЕ ФАЙЛЫ
FILE_REAL_EGEMEN = "dataset_kz.csv"
FILE_REAL_TENGRI = "tengri_news.csv"

# Файл с обучающими/валидационными данными (чтобы исключить их)
TRAINING_DATA_FILE = "final_golden_dataset.csv"
# Куда сохраняем тестовый набор
OUTPUT_FILE = "final_test_set_100x100_v5_gpt.csv" # Новое имя файла v5

# Сколько примеров каждого класса/источника
NUM_FAKES_NEEDED = 100 # Всего 100 фейков
NUM_REAL_PER_SOURCE = 50 # По 50 реальных с каждого сайта
# --------------------

TEXT_COLUMN = "text"   # Одинаковое имя для всех файлов
LABEL_COLUMN = 'label'

print("--- Создание Финального Тестового Набора v5 (100 GPT-Fake + 100 Real) ---")

# --- 1. Загрузка обучающих данных (чтобы исключить их) ---
try:
    df_train = pd.read_csv(TRAINING_DATA_FILE)
    seen_texts = set(df_train[TEXT_COLUMN].dropna())
    print(f"Загружено {len(seen_texts)} текстов из обучающего/валидационного набора для исключения.")
except FileNotFoundError:
    print(f"🛑 ОШИБКА: Файл обучающих данных '{TRAINING_DATA_FILE}' не найден!")
    exit()

# --- 2. Функция для загрузки, очистки и фильтрации ---
def load_filter_sample(filename, text_col, num_samples, output_label_val, seen_texts_set, filter_label_str=None):
    print(f"\nОбработка файла: {filename}...")
    if not os.path.exists(filename):
        print(f"⚠️ Файл '{filename}' не найден, пропускаем.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(filename)
        # Проверяем наличие нужных колонок
        if text_col not in df.columns or (filter_label_str is not None and LABEL_COLUMN not in df.columns):
             print(f"⚠️ В файле {filename} нет колонок '{text_col}' или '{LABEL_COLUMN}', пропускаем.")
             return pd.DataFrame()

        df.dropna(subset=[text_col, LABEL_COLUMN], inplace=True)
        df = df[df[text_col].str.len() > 50]

        # --- ФИЛЬТРАЦИЯ ПО МЕТКЕ (для файла с фейками от GPT) ---
        if filter_label_str is not None:
            df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(str) # Приводим к строке
            df = df[df[LABEL_COLUMN] == filter_label_str]
            print(f"  Найдено {len(df)} строк с меткой '{filter_label_str}'.")

        # --- Исключаем тексты, которые были в обучении ---
        original_count = len(df)
        df = df[~df[text_col].isin(seen_texts_set)]
        filtered_count = len(df)
        print(f"  Исходных строк (с нужной меткой): {original_count}. Строк после удаления 'виденных': {filtered_count}.")

        if filtered_count < num_samples:
            print(f"⚠️ ВНИМАНИЕ: Недостаточно уникальных строк ({filtered_count} < {num_samples}). Берем все, что есть.")
            num_samples = filtered_count

        if num_samples == 0:
            print(f"  Не найдено подходящих строк.")
            return pd.DataFrame()

        df_sample = df.sample(n=num_samples, random_state=42)
        # Переименовываем колонку и присваиваем нужную метку
        df_sample = df_sample[[text_col]].rename(columns={text_col: TEXT_COLUMN})
        df_sample[LABEL_COLUMN] = output_label_val
        print(f"  Взято {len(df_sample)} случайных строк.")
        return df_sample[[TEXT_COLUMN, LABEL_COLUMN]]

    except Exception as e:
        print(f"❌ ОШИБКА при обработке {filename}: {e}. Файл пропущен.")
        return pd.DataFrame()

# --- 3. Собираем тестовый набор ---
all_test_dfs = []

# Фейки (label=0) из generated_fakes_kz_100.csv
# Важно: В файле от GPT метка может быть '0' (строка)
df_fakes = load_filter_sample(FILE_FAKES_SOURCE, TEXT_COLUMN, NUM_FAKES_NEEDED, 0, seen_texts, filter_label_str='0')
all_test_dfs.append(df_fakes)

# Реальные (label=1)
df_real_e = load_filter_sample(FILE_REAL_EGEMEN, TEXT_COLUMN, NUM_REAL_PER_SOURCE, 1, seen_texts)
all_test_dfs.append(df_real_e)
df_real_t = load_filter_sample(FILE_REAL_TENGRI, TEXT_COLUMN, NUM_REAL_PER_SOURCE, 1, seen_texts)
all_test_dfs.append(df_real_t)

# Объединяем все ЧАСТИ, КОТОРЫЕ УДАЛОСЬ ЗАГРУЗИТЬ
valid_dfs = [df for df in all_test_dfs if df is not None and not df.empty]
if not valid_dfs:
     print("🛑 КРИТИЧЕСКАЯ ОШИБКА: Не удалось собрать ни одной строки для теста. Проверь исходные файлы.")
     exit()

df_test_final = pd.concat(valid_dfs, ignore_index=True)

# Перемешиваем
df_test_final = df_test_final.sample(frac=1, random_state=42).reset_index(drop=True)

# --- 4. Сохранение ---
df_test_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8', quoting=1)

print("\n--- ГОТОВО! ---")
print(f"Создан финальный тестовый набор: {OUTPUT_FILE}")
print(f"Всего строк: {len(df_test_final)}")
print(f"Фейков (label 0): {len(df_test_final[df_test_final[LABEL_COLUMN] == 0])}")
print(f"Реальных (label 1): {len(df_test_final[df_test_final[LABEL_COLUMN] == 1])}")