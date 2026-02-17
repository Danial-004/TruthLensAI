import pandas as pd
import requests
import json
import os
import csv
from tqdm import tqdm
import time
import urllib3

# --- 1. Настройки ---
INPUT_FILE = "tengri_news.csv"         # Твой новый файл
OUTPUT_FILE = "generated_fakes_tengri.csv" # Куда сохраняем фейки
TEXT_COLUMN = "text"                   # Убедись, что колонка с текстом называется так
NUM_FAKES_TO_GENERATE = 2000           # Как ты и просил, 2000 штук
# ---------------------

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OUTPUT_COLUMNS = ["original_text", "fake_news_text"]

# Отключаем предупреждения (на всякий случай)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Та же функция для промпта ---
def create_prompt(real_news_text):
    return f"""
    <|begin_of_text|>
    <|start_header_id|>system<|end_header_id|>
    Ты — профессиональный автор дезинформации. Твоя задача — взять реальную новость
    и переписать ее, превратив в убедительный фейк.
    
    ТРЕБОВАНИЯ К ФЕЙКУ:
    1.  Сохрани тему и контекст (если новость о политике, фейк тоже о политике).
    2.  Измени ключевые факты: имена, цифры, даты, места или выводы.
    3.  Текст должен быть на том же языке, что и оригинал (казахский).
    4.  Не добавляй в ответ ничего, кроме самого текста фейка.
    5.  Твой ответ ДОЛЖЕН БЫТЬ в формате JSON.
    
    Вот пример формата:
    {{
        "fake_news_text": "Здесь должен быть сгенерированный тобой фейковый текст..."
    }}
    <|eot_id|>
    
    <|start_header_id|>user<|end_header_id|>
    Вот реальная новость. Сделай из нее фейк по моим правилам:
    
    {real_news_text}
    <|eot_id|>
    
    <|start_header_id|>assistant<|end_header_id|>
    {{
    """

# --- Та же функция для генерации ---
def generate_fake_with_llama(text):
    payload = {
        "model": "llama3",
        "prompt": create_prompt(text),
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60, verify=False)
        response.raise_for_status() 
        response_data = response.json()
        generated_json_string = response_data.get("response")
        
        if not generated_json_string: return None
            
        try:
            start = generated_json_string.find('{')
            end = generated_json_string.rfind('}') + 1
            if start == -1 or end == 0: return None 
            
            clean_json_string = generated_json_string[start:end]
            fake_data = json.loads(clean_json_string)
            return fake_data.get("fake_news_text")
            
        except json.JSONDecodeError:
            return None

    except requests.exceptions.RequestException:
        return None 

# --- ГЛАВНЫЙ КОНВЕЙЕР ---
if __name__ == "__main__":
    # 1. Загружаем реальные новости (Tengrinews)
    try:
        df_real = pd.read_csv(INPUT_FILE)
        if TEXT_COLUMN not in df_real.columns:
            print(f"🛑 ОШИБКА: В файле {INPUT_FILE} нет колонки '{TEXT_COLUMN}'.")
            exit()
        
        # Перемешиваем и берем 2000 случайных
        df_real_sample = df_real.sample(n=NUM_FAKES_TO_GENERATE, random_state=42).reset_index(drop=True)
        print(f"Загружено {len(df_real)} строк из {INPUT_FILE}.")
        print(f"Выбрано {len(df_real_sample)} случайных новостей для генерации фейков.")
        
    except FileNotFoundError:
        print(f"🛑 ОШИБКА: Файл {INPUT_FILE} не найден.")
        exit()
    except ValueError:
        print(f"🛑 ОШИБКА: В файле {INPUT_FILE} меньше {NUM_FAKES_TO_GENERATE} строк. Уменьши лимит.")
        exit()

    # 2. "Умная" загрузка прогресса
    processed_originals = set()
    file_exists = os.path.exists(OUTPUT_FILE)
    
    if file_exists and os.path.getsize(OUTPUT_FILE) > 0:
        try:
            df_fake = pd.read_csv(OUTPUT_FILE)
            if "original_text" in df_fake.columns:
                processed_originals = set(df_fake["original_text"])
            print(f"Найден файл. Уже обработано новостей: {len(processed_originals)}")
        except Exception:
            print(f"Ошибка чтения {OUTPUT_FILE}. Начинаем с нуля.")
            file_exists = False 
            
    # 3. Открываем файл для *дозаписи* (append mode)
    try:
        with open(OUTPUT_FILE, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, quoting=csv.QUOTE_ALL)
            
            if not file_exists or os.path.getsize(OUTPUT_FILE) == 0:
                writer.writeheader()
                print(f"Создан новый файл '{OUTPUT_FILE}'.")

            print("Запускаем конвейер...")
            
            # 4. Главный цикл (Tengrinews)
            for index, row in tqdm(df_real_sample.iterrows(), total=df_real_sample.shape[0], desc="Генерация Tengri-Фейков"):
                
                real_text = row[TEXT_COLUMN]
                
                if pd.isna(real_text) or real_text in processed_originals:
                    continue

                fake_text = generate_fake_with_llama(real_text)
                
                if fake_text:
                    writer.writerow({
                        "original_text": real_text,
                        "fake_news_text": fake_text
                    })
                    f.flush()
                    processed_originals.add(real_text)

    except PermissionError:
        print(f"\n🛑 ОШИБКА: Нет доступа к файлу {OUTPUT_FILE}. Закрой его в Excel.")
        exit()
        
    print(f"Работа завершена. Все фейки сохранены в {OUTPUT_FILE}.")
