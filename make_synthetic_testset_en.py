import pandas as pd
import random

# --- Settings ---
OUTPUT_PATH = r"C:\Users\Admin\Desktop\TruthLensAI2\dataset_en_test.csv"
N_REAL = 300
N_FAKE = 300

# --- Real news templates ---
real_news_samples = [
    "The government approved a new digital transformation program today.",
    "A new hospital opened in London providing advanced cancer treatment.",
    "NASA successfully launched its latest climate observation satellite.",
    "The World Bank announced additional funding for small businesses.",
    "Scientists discovered a new renewable energy storage method.",
    "The city of New York introduced a plan to reduce traffic emissions.",
    "A new education reform aims to modernize the national curriculum.",
    "Researchers at Oxford developed a more efficient solar panel.",
    "The central bank reported a decline in inflation this quarter.",
    "A new vaccine for seasonal flu has been officially approved."
]

# --- Fake news templates ---
fake_news_samples = [
    "Aliens have landed in Nevada and contacted the local government.",
    "A secret lab in Antarctica is creating human clones, reports claim.",
    "Drinking two liters of cola a day guarantees immortality, experts say.",
    "The Moon is actually hollow and controlled by ancient civilizations.",
    "Dinosaurs have been successfully cloned in a secret Russian lab.",
    "A hidden city was found under the Pacific Ocean, photos suggest.",
    "Scientists confirm that smartphones can read human thoughts.",
    "New vaccine allegedly changes human DNA, conspiracy theorists claim.",
    "The Earth will stop rotating next month, shocking report reveals.",
    "A mysterious signal from space proves aliens are watching us."
]

# --- Helper to mix and expand texts ---
def generate_news(base_list, n):
    """Creates synthetic news by adding random variations."""
    data = []
    for _ in range(n):
        sentence = random.choice(base_list)
        if random.random() > 0.5:
            sentence += " " + random.choice([
                "Officials confirmed this in a press statement.",
                "This information has gone viral on social media.",
                "Eyewitnesses shared photos online.",
                "The community reacted actively to the news.",
                "Experts are currently investigating the case."
            ])
        data.append(sentence)
    return data

# --- Generate synthetic samples ---
real_texts = generate_news(real_news_samples, N_REAL)
fake_texts = generate_news(fake_news_samples, N_FAKE)

# --- Combine and shuffle ---
df_real = pd.DataFrame({"text": real_texts, "label": "real"})
df_fake = pd.DataFrame({"text": fake_texts, "label": "fake"})
df_all = pd.concat([df_real, df_fake]).sample(frac=1, random_state=42).reset_index(drop=True)

# --- Save to CSV ---
df_all.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
print(f"✅ Synthetic English test dataset saved: {OUTPUT_PATH}")
print(df_all.head(5))
print(f"\nDataset size: {len(df_all)} (real={N_REAL}, fake={N_FAKE})")
