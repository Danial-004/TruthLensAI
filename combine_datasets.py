# combine_datasets.py (НОВАЯ ВЕРСИЯ ДЛЯ РАЗДЕЛЬНЫХ ДАТАСЕТОВ)
import pandas as pd
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATA_FOLDER = "training_data"
# Папка для сохранения результатов
OUTPUT_FOLDER = "processed_data"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Конфигурация всех исходных файлов
FILE_CONFIGS = {
    'en_real': {'path': 'True.csv', 'text_col': 'text', 'label': 0, 'lang': 'en', 'sep': ','},
    'en_fake': {'path': 'Fake.csv', 'text_col': 'text', 'label': 1, 'lang': 'en', 'sep': ','},
    'ru': {
        'path': 'russian_news_dataset.csv',
        'text_col': 'title',
        'label_col': 'is_fake',
        'lang': 'ru',
        'sep': '\t'
    },
    'kz_real': {'path': 'tengri_news.csv', 'text_col': 'text', 'label': 0, 'lang': 'kz', 'sep': ','},
    'kz_fake': {'path': 'kazakhfakedata_clean.csv', 'text_col': 'text', 'label': 1, 'lang': 'kz', 'sep': ','},
}

def process_and_save_datasets():
    """
    Читает все исходные файлы, группирует их по языкам и сохраняет
    в отдельные, очищенные CSV файлы.
    """
    all_data = []
    logging.info("Начинаем обработку исходных файлов...")

    for key, config in FILE_CONFIGS.items():
        filepath = os.path.join(DATA_FOLDER, config['path'])
        try:
            logging.info(f"Читаем файл: {filepath}")
            df = pd.read_csv(filepath, sep=config['sep'], on_bad_lines='warn')

            if 'label_col' in config: # Для файлов, где метки в отдельной колонке (russian_news)
                df_processed = df[[config['text_col'], config['label_col']]].rename(columns={
                    config['text_col']: 'text',
                    config['label_col']: 'label'
                })
            else: # Для файлов, где метки мы задаем сами (True.csv, Fake.csv)
                df_processed = df[[config['text_col']]].rename(columns={config['text_col']: 'text'})
                df_processed['label'] = config['label']

            df_processed['language'] = config['lang']
            all_data.append(df_processed)
            logging.info(f"✅ Успешно обработано {len(df_processed)} строк из {config['path']}")

        except FileNotFoundError:
            logging.warning(f"⚠️ Файл не найден, пропускаем: {filepath}")
        except Exception as e:
            logging.error(f"❌ Ошибка при чтении файла {filepath}: {e}")

    if not all_data:
        logging.error("Не найдено данных для обработки. Завершение.")
        return

    # Объединяем все в один большой датафрейм для удобства
    final_df = pd.concat(all_data, ignore_index=True)
    final_df.dropna(subset=['text'], inplace=True) # Удаляем строки без текста
    final_df = final_df[final_df['text'].str.len() > 50] # Удаляем слишком короткие тексты
    final_df['label'] = final_df['label'].astype(int)

    logging.info(f"Общее количество обработанных строк: {len(final_df)}")

    # Разделяем и сохраняем по языкам
    for lang_code in final_df['language'].unique():
        lang_df = final_df[final_df['language'] == lang_code]
        # Перемешиваем данные внутри каждого языка
        lang_df = lang_df.sample(frac=1).reset_index(drop=True)
        
        output_path = os.path.join(OUTPUT_FOLDER, f"dataset_{lang_code}.csv")
        lang_df.to_csv(output_path, index=False)
        logging.info(f"💾 Датасет для языка '{lang_code}' сохранен в {output_path} ({len(lang_df)} строк)")

if __name__ == "__main__":
    process_and_save_datasets()