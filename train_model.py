# train_model.py
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)

# --- 1. Класс для подготовки данных ---
class FakeNewsDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

# --- 2. Основная функция обучения ---
def train():
    # --- Загрузка данных ---
    print("Загрузка данных...")
    # УКАЖИТЕ ПУТЬ К ВАШЕМУ ФАЙЛУ С ДАННЫМИ
   # Стало:
    df = pd.read_csv("training_data/final_training_dataset.csv")
    texts = df['text'].tolist()
    labels = df['label'].tolist()

    # Разделяем на обучающую и тестовую выборки
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2
    )

    # --- Токенизация ---
    print("Токенизация текста...")
    model_name = "xlm-roberta-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=512)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=512)

    train_dataset = FakeNewsDataset(train_encodings, train_labels)
    val_dataset = FakeNewsDataset(val_encodings, val_labels)

    # --- Настройка обучения ---
    print("Настройка и запуск обучения...")
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    training_args = TrainingArguments(
        output_dir='./results',          # Папка для результатов
        num_train_epochs=3,              # Количество эпох (проходов по данным)
        per_device_train_batch_size=8,   # Размер пакета данных
        per_device_eval_batch_size=8,
        warmup_steps=500,                # Шаги для "прогрева"
        weight_decay=0.01,               # Регуляризация
        logging_dir='./logs',            # Папка для логов
        logging_steps=10,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )

    # --- Запуск обучения ---
    trainer.train()

    # --- Сохранение модели ---
    print("Обучение завершено. Сохранение модели...")
    # Сохраняем в папку, которую наше приложение умеет находить
    model.save_pretrained("backend/models/truthlens_model")
    tokenizer.save_pretrained("backend/models/truthlens_model")
    print("Модель успешно сохранена в backend/models/truthlens_model")

if __name__ == "__main__":
    train()