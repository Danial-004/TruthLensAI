import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from transformers import pipeline # DL модельді жүктеу үшін
import torch
import warnings
from tqdm import tqdm

# --- Параметрлер ---
# Файл жолдары
TRAINING_DATASET_PATH = "final_training_dataset_kz.csv" # ML үйрету үшін
TEST_DATASET_PATH = "test.csv" # ML және DL тест үшін
relative_model_path = os.path.join("backend", "models", "truthlens_kk_model") # DL модель
MODEL_PATH = os.path.abspath(relative_model_path)
DEVICE = 0 if torch.cuda.is_available() else -1 # DL үшін

# ML модель параметрлері
MAX_FEATURES_TFIDF = 10000 # TF-IDF үшін ең жиі кездесетін сөздер саны

# Ескертулерді өшіру
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ✅✅✅ ӨЗГЕРІС: Тест файлы үшін label_map ҚАЙТАРЫЛДЫ ✅✅✅
label_map_test = {'real': 1, 'fake': 0}

# DL модель болжамдарын сандарға ауыстыру функциясы (өзгеріссіз)
def parse_dl_label(d):
    return 1 if d['label'] == 'LABEL_1' else 0

print("--- ДЕРЕКТЕРДІ ЖҮКТЕУ ---")
try:
    df_train = pd.read_csv(TRAINING_DATASET_PATH, on_bad_lines='skip', engine='python')
    df_test = pd.read_csv(TEST_DATASET_PATH, on_bad_lines='skip', engine='python')
    print(f"✅ '{TRAINING_DATASET_PATH}' ({len(df_train)} қатар) жүктелді.")
    print(f"✅ '{TEST_DATASET_PATH}' ({len(df_test)} қатар) жүктелді.")

    # --- Тренинг деректерін өңдеу (1/0 күтеміз) ---
    df_train.dropna(subset=['text', 'label'], inplace=True)
    df_train['label_numeric'] = pd.to_numeric(df_train['label'], errors='coerce')
    original_train_count = len(df_train)
    df_train.dropna(subset=['label_numeric'], inplace=True)
    dropped_train = original_train_count - len(df_train)
    if dropped_train > 0:
        print(f"⚠️ ЕСКЕРТУ: Тренинг файлынан {dropped_train} жол жарамсыз белгі ('1'/'0'-ден басқа) болғандықтан жойылды.")

    # --- Тест деректерін өңдеу (real/fake күтеміз) ---
    df_test.dropna(subset=['text', 'label'], inplace=True)
    # ✅✅✅ ӨЗГЕРІС: Тест үшін .map(label_map_test) қолданамыз ✅✅✅
    df_test['label'] = df_test['label'].astype(str).str.strip().str.lower() # Кіші әріпке келтіреміз
    df_test['label_numeric'] = df_test['label'].map(label_map_test)
    original_test_count = len(df_test)
    df_test.dropna(subset=['label_numeric'], inplace=True)
    dropped_test = original_test_count - len(df_test)
    if dropped_test > 0:
         print(f"⚠️ ЕСКЕРТУ: Тест файлынан {dropped_test} жол жарамсыз белгі ('real'/'fake'-тен басқа) болғандықтан жойылды.")
    # ✅✅✅ ӨЗГЕРІС АЯҚТАЛДЫ ✅✅✅

    X_train = df_train['text'].tolist()
    y_train = df_train['label_numeric'].astype(int).tolist()
    X_test = df_test['text'].tolist()
    y_test = df_test['label_numeric'].astype(int).tolist()

    # Тексерулер
    if not X_train:
         print(f"🛑 КРИТИКАЛЫҚ ҚАТЕ: Тренинг мәтіндерінің тізімі (X_train) бос! '{TRAINING_DATASET_PATH}' файлын тексеріңіз.")
         exit()
    # ✅✅✅ ӨЗГЕРІС: Тест деректері бос болса, қате шығарып тоқтатамыз ✅✅✅
    if not X_test:
        print(f"🛑 КРИТИКАЛЫҚ ҚАТЕ: Тест мәтіндерінің тізімі (X_test) бос! '{TEST_DATASET_PATH}' файлындағы 'label' бағанында 'real' немесе 'fake' мәндері жоқ немесе дұрыс оқылмады.")
        exit()

    print(f"Тренинг жиынтығы дайын: {len(X_train)} мәтін")
    print(f"Тест жиынтығы дайын: {len(X_test)} мәтін")

    print(f"Тренингтегі белгілер (0/1): {pd.Series(y_train).value_counts().to_dict()}")
    print(f"Тесттегі белгілер (0/1): {pd.Series(y_test).value_counts().to_dict()}") # Енді бос болмауы керек


except FileNotFoundError as e:
    print(f"🛑 ҚАТЕ: Файл табылмады: {e}. Скрипт тоқтатылды.")
    exit()
except KeyError as e:
    print(f"🛑 ҚАТЕ: Файлда '{e}' бағаны жоқ. CSV файлын тексеріңіз ('text', 'label'). Скрипт тоқтатылды.")
    exit()
except Exception as e:
     print(f"🛑 Деректерді жүктеу кезінде қате: {e}")
     exit()

# ===============================================================
# ML МОДЕЛЬ (TF-IDF + Logistic Regression)
# ===============================================================
print("\n--- ML МОДЕЛЬДІ ҮЙРЕТУ ЖӘНЕ ТЕСТІЛЕУ ---")
ml_preds = [] # Болжамдар тізімі
# ML бөлімі енді орындалуы керек, себебі X_train және X_test бос емес
print("TF-IDF векторлауышын құру...")
vectorizer = TfidfVectorizer(max_features=MAX_FEATURES_TFIDF, ngram_range=(1, 2))
print("TF-IDF: Тренинг деректерін түрлендіру...")
X_train_tfidf = vectorizer.fit_transform(X_train)
print(f"TF-IDF: Тренинг векторының өлшемі: {X_train_tfidf.shape}")

print("Logistic Regression моделін үйрету...")
ml_model = LogisticRegression(solver='liblinear', random_state=42, class_weight='balanced')
ml_model.fit(X_train_tfidf, y_train)
print("✅ ML модель үйретілді.")

print("TF-IDF: Тест деректерін түрлендіру...")
X_test_tfidf = vectorizer.transform(X_test)

print("ML модельмен тест деректерінде болжам жасау...")
ml_preds = ml_model.predict(X_test_tfidf)

print("\n--- ML МОДЕЛЬ НӘТИЖЕЛЕРІ (test.csv) ---")
print(classification_report(y_test, ml_preds, target_names=['FAKE (0)', 'REAL (1)']))

# ===============================================================
# DL МОДЕЛЬ (Transformers Pipeline)
# ===============================================================
print("\n--- DL МОДЕЛЬДІ ТЕСТІЛЕУ (test.csv) ---")
print(f"DL Моделін жүктеу: {MODEL_PATH}")
print(f"Құрылғы: {'GPU' if DEVICE == 0 else 'CPU'}")
dl_preds = [] # Болжамдар тізімі
dl_pipeline = None # Алдын ала анықтаймыз

try:
    dl_pipeline = pipeline(
        "text-classification",
        model=MODEL_PATH,
        tokenizer=MODEL_PATH,
        device=DEVICE
    )
    print("✅ DL модель жүктелді.")

    # DL тестілеу бөлімі енді орындалуы керек
    print(f"DL модель {len(X_test)} тест мәтінін өңдеуде...")
    dl_results = []
    batch_size = 16 if DEVICE == 0 else 1
    for out in tqdm(dl_pipeline(X_test, batch_size=batch_size, truncation=True, max_length=512), total=len(X_test)):
        dl_results.append(out)

    dl_preds = [parse_dl_label(res) for res in dl_results]

    print("\n--- DL МОДЕЛЬ НӘТИЖЕЛЕРІ (test.csv) ---")
    print(classification_report(y_test, dl_preds, target_names=['FAKE (0)', 'REAL (1)']))


except Exception as e:
    print(f"🛑 DL модельді жүктеу немесе тестілеу кезінде қате: {e}")

print("\n--- САЛЫСТЫРУ АЯҚТАЛДЫ ---")


# ===============================================================
# ЧАСТЬ 2: РУЧНОЙ "СЛОЖНЫЙ" ТЕСТ
# ===============================================================
print("\n" + "="*50)
print("--- ЧАСТЬ 2: РУЧНОЙ СТРЕСС-ТЕСТ ---")
print("Введи любой текст на казахском. Для выхода введи 'exit' или 'шығу'.")
print("="*50)

while True:
    try:
        text = input("\n[ТВОЙ ТЕКСТ]: ")
        if text.lower() in ['exit', 'quit', 'шығу', 'стоп']:
            break

        if len(text) < 10:
            print("Слишком короткий текст, введи что-то посерьезнее.")
            continue

        # --- DL Модель Болжамы ---
        if dl_pipeline: # Егер DL модель жүктелсе
            result_dl = dl_pipeline(text)[0]
            label_dl = result_dl['label']
            score_dl = result_dl['score'] * 100
            print("\n--- ВЕРДИКТ DL МОДЕЛИ ---")
            if label_dl == 'LABEL_1':
                print(f"✅ РЕАЛЬНАЯ НОВОСТЬ (С вероятностью {score_dl:.2f}%)")
            else:
                print(f"❌ ФЕЙК (С вероятностью {score_dl:.2f}%)")
        else:
             print("\n--- ВЕРДИКТ DL МОДЕЛИ ---")
             print("⚠️ DL модель жүктелмеген.")

        # --- ML Модель Болжамы ---
        if 'ml_model' in locals() and 'vectorizer' in locals(): # Егер ML модель үйретілсе
            text_tfidf = vectorizer.transform([text])
            ml_pred_manual = ml_model.predict(text_tfidf)[0]
            ml_proba_manual = ml_model.predict_proba(text_tfidf)[0]
            print("\n--- ВЕРДИКТ ML МОДЕЛИ ---")
            if ml_pred_manual == 1:
                print(f"✅ РЕАЛЬНАЯ НОВОСТЬ (С вероятностью {ml_proba_manual[1]*100:.2f}%)")
            else:
                print(f"❌ ФЕЙК (С вероятностью {ml_proba_manual[0]*100:.2f}%)")
        else:
            print("\n--- ВЕРДИКТ ML МОДЕЛИ ---")
            print("⚠️ ML модель үйретілмеген.")

    except NameError as e:
         print(f"🛑 Қолмен тестілеу кезінде қате: {e}. Модельдердің бірі дұрыс жүктелмеген/үйретілмеген болуы мүмкін.")
         # break # Мүмкін жалғастыра беру керек шығар?
    except Exception as e:
        print(f"Ошибка обработки: {e}")
    except KeyboardInterrupt:
        break

print("\nТестирование завершено.")