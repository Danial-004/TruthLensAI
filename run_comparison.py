import pandas as pd
import os
# sklearn импорттары бұл жерде қажет емес, себебі ML моделін тестілемейміз
from sklearn.metrics import classification_report
from transformers import pipeline # DL модельді жүктеу үшін
import torch
import warnings
from tqdm import tqdm

# --- Параметрлер ---
# ✅✅✅ ӨЗГЕРІС: Жаңа тест файлының атын көрсеттік ✅✅✅
FACT_FAKES_TEST_DATASET_PATH = "test_fact_fakes.csv"
relative_model_path = os.path.join("backend", "models", "truthlens_kk_model") # DL модель
MODEL_PATH = os.path.abspath(relative_model_path)
DEVICE = 0 if torch.cuda.is_available() else -1 # DL үшін

# Ескертулерді өшіру
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ✅✅✅ ӨЗГЕРІС: Тест файлында 'real'/'fake' күтеміз ✅✅✅
label_map_test = {'real': 1, 'fake': 0}

# DL модель болжамдарын сандарға ауыстыру функциясы (өзгеріссіз)
def parse_dl_label(d):
    return 1 if d['label'] == 'LABEL_1' else 0

print(f"--- ЭКСПЕРИМЕНТ: ФАКТ-ФЕЙКТЕРДІ ТЕСТІЛЕУ ({FACT_FAKES_TEST_DATASET_PATH}) ---")

print("--- ДЕРЕКТЕРДІ ЖҮКТЕУ ---")
X_test = []
y_test = []
try:
    df_test = pd.read_csv(FACT_FAKES_TEST_DATASET_PATH, on_bad_lines='skip', engine='python')
    print(f"✅ '{FACT_FAKES_TEST_DATASET_PATH}' ({len(df_test)} қатар) жүктелді.")

    # NaN мәндерін жою
    df_test.dropna(subset=['text', 'label'], inplace=True)

    # Тест деректерін өңдеу (real/fake күтеміз)
    df_test['label'] = df_test['label'].astype(str).str.strip().str.lower() # Кіші әріпке келтіреміз
    df_test['label_numeric'] = df_test['label'].map(label_map_test)

    # Маңызды: Түрлендіру мүмкін болмаған (NaN) жолдарды жоямыз
    original_test_count = len(df_test)
    df_test.dropna(subset=['label_numeric'], inplace=True)
    dropped_test = original_test_count - len(df_test)
    if dropped_test > 0:
         print(f"⚠️ ЕСКЕРТУ: Тест файлынан {dropped_test} жол жарамсыз белгі ('real'/'fake'-тен басқа) болғандықтан жойылды.")

    X_test = df_test['text'].tolist()
    y_test = df_test['label_numeric'].astype(int).tolist()

    if not X_test:
        print(f"🛑 КРИТИКАЛЫҚ ҚАТЕ: Тест мәтіндерінің тізімі (X_test) бос! '{FACT_FAKES_TEST_DATASET_PATH}' файлын тексеріңіз.")
        exit()

    print(f"Тест жиынтығы дайын: {len(X_test)} мәтін")
    print(f"Тесттегі белгілер (0/1): {pd.Series(y_test).value_counts().to_dict()}")


except FileNotFoundError as e:
    print(f"🛑 ҚАТЕ: Тест файлы '{FACT_FAKES_TEST_DATASET_PATH}' табылмады. Алдымен оны жасаңыз!")
    print("Нұсқаулық: Шынайы жаңалықтардан фактілерді өзгертіп, фейк деп белгілеңіз.")
    exit()
except KeyError as e:
    print(f"🛑 ҚАТЕ: '{FACT_FAKES_TEST_DATASET_PATH}' файлында '{e}' бағаны жоқ. CSV файлын тексеріңіз ('text', 'label'). Скрипт тоқтатылды.")
    exit()
except Exception as e:
     print(f"🛑 Деректерді жүктеу кезінде қате: {e}")
     exit()

# ===============================================================
# DL МОДЕЛЬДІ (Transformers Pipeline) ФАКТ-ФЕЙКТЕРМЕН ТЕСТІЛЕУ
# ===============================================================
print("\n--- DL МОДЕЛЬДІ ТЕСТІЛЕУ ---")
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

    print(f"DL модель {len(X_test)} факт-фейк тест мәтінін өңдеуде...")
    dl_results = []
    batch_size = 16 if DEVICE == 0 else 1
    for out in tqdm(dl_pipeline(X_test, batch_size=batch_size, truncation=True, max_length=512), total=len(X_test)):
        dl_results.append(out)

    dl_preds = [parse_dl_label(res) for res in dl_results]

    print(f"\n--- DL МОДЕЛЬ НӘТИЖЕЛЕРІ ({FACT_FAKES_TEST_DATASET_PATH}) ---")
    print(classification_report(y_test, dl_preds, target_names=['FAKE (0)', 'REAL (1)']))

except Exception as e:
    print(f"🛑 DL модельді жүктеу немесе тестілеу кезінде қате: {e}")

print("\n--- ЭКСПЕРИМЕНТ АЯҚТАЛДЫ ---")
