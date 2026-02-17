# data/data_preprocessing.py
"""
TruthLens AI - Data Preprocessing Script

This script is designed for offline batch processing of raw datasets (CSV or JSON)
to prepare them for model training. It cleans, normalizes, and filters text data.

Example Usage:
python data_preprocessing.py \
    --input_file raw_data/kazakh_news.csv \
    --output_file processed_data/kazakh_news_cleaned.csv \
    --text_column "article_body" \
    --lang_column "language_code"
"""

import pandas as pd
import re
import argparse
import logging
from typing import Set

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Stopword Lists ---
# Note: These lists can be expanded for better performance.
STOPWORDS_KZ: Set[str] = {
    'және', 'мен', 'бен', 'пен', 'бір', 'туралы', 'үшін', 'арқылы', 'сайын',
    'бойынша', 'деп', 'еді', 'деген', 'ғой', 'да', 'де', 'та', 'те', 'ма', 'ме',
    'ба', 'бе', 'па', 'пе', 'осы', 'сол', 'бұл', 'ол', 'менің', 'сенің', 'оның'
}

STOPWORDS_RU: Set[str] = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то',
    'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за',
    'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'о',
    'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже'
}

STOPWORDS_EN: Set[str] = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
    'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
}

STOPWORDS_MAP = {
    'kz': STOPWORDS_KZ,
    'ru': STOPWORDS_RU,
    'en': STOPWORDS_EN
}


def clean_text(text: str, language: str = 'en') -> str:
    """
    Applies a series of cleaning steps to a single text string.

    Args:
        text (str): The raw text to be cleaned.
        language (str): The language of the text ('kz', 'ru', 'en').

    Returns:
        str: The cleaned and normalized text.
    """
    if not isinstance(text, str):
        return ""

    # 1. Convert to lowercase
    text = text.lower()

    # 2. Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # 3. Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)

    # 4. Remove mentions and hashtags
    text = re.sub(r'@\w+|#\w+', '', text)

    # 5. Remove HTML tags
    text = re.sub(r'<.*?>', '', text)

    # 6. Normalize language-specific characters
    if language == 'ru':
        text = text.replace('ё', 'е')

    # 7. Remove punctuation and numbers
    # For Kazakh, we need to preserve specific letters
    if language == 'kz':
        pattern = r'[^a-zа-яәіңғүұқөһ\s]'
    else:
        pattern = r'[^a-zа-я\s]'
    text = re.sub(pattern, '', text)

    # 8. Tokenize and remove stopwords
    stopwords = STOPWORDS_MAP.get(language, set())
    words = [word for word in text.split() if word not in stopwords and len(word) > 2]

    # 9. Join words back into a single string
    text = " ".join(words)

    # 10. Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def main():
    """
    Main function to run the data processing pipeline from the command line.
    """
    parser = argparse.ArgumentParser(
        description="Clean and preprocess text data for the TruthLens AI model."
    )
    parser.add_argument(
        '--input_file',
        type=str,
        required=True,
        help="Path to the input CSV or JSON file."
    )
    parser.add_argument(
        '--output_file',
        type=str,
        required=True,
        help="Path to save the cleaned CSV file."
    )
    parser.add_argument(
        '--text_column',
        type=str,
        required=True,
        help="Name of the column containing the text to clean."
    )
    parser.add_argument(
        '--lang_column',
        type=str,
        required=True,
        help="Name of the column specifying the language code (kz, ru, en)."
    )
    args = parser.parse_args()

    logging.info(f"Starting preprocessing for file: {args.input_file}")

    # Load data
    try:
        if args.input_file.endswith('.csv'):
            df = pd.read_csv(args.input_file)
        elif args.input_file.endswith('.json'):
            df = pd.read_json(args.input_file, lines=True)
        else:
            logging.error("Unsupported file format. Please use .csv or .json")
            return
    except FileNotFoundError:
        logging.error(f"Input file not found: {args.input_file}")
        return

    logging.info(f"Loaded {len(df)} rows.")
    
    # Check if required columns exist
    if args.text_column not in df.columns or args.lang_column not in df.columns:
        logging.error(f"Text column '{args.text_column}' or language column '{args.lang_column}' not found in the input file.")
        return

    # Apply the cleaning function
    logging.info(f"Cleaning text in column '{args.text_column}'...")
    df['cleaned_text'] = df.apply(
        lambda row: clean_text(row[args.text_column], row[args.lang_column]),
        axis=1
    )

    # Drop rows where cleaned text is empty
    initial_rows = len(df)
    df.dropna(subset=['cleaned_text'], inplace=True)
    df = df[df['cleaned_text'] != '']
    final_rows = len(df)
    
    logging.info(f"Removed {initial_rows - final_rows} empty or invalid rows.")

    # Save the cleaned data
    df.to_csv(args.output_file, index=False, encoding='utf-8')
    logging.info(f"Successfully cleaned data and saved to {args.output_file}")


if __name__ == '__main__':
    main()