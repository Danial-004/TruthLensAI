import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Настройки ---
BASE_URL = "https://tengrinews.kz"
START_URL_TEMPLATE = "https://tengrinews.kz/kazakhstan_news/page/{}/" 
PAGES_TO_PARSE = 150  # 150 страниц * ~25 новостей = ~3750 новостей
OUTPUT_FILE = "tengrinews_kz_data.csv"
# -----------------

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def get_article_links(page_url):
    links = []
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_tags = soup.find_all('a', class_='content_main_item_title')
        for tag in article_tags:
            href = tag.get('href')
            if href and href.startswith('/kazakhstan_news/'):
                full_url = BASE_URL + href
                if full_url not in links:
                    links.append(full_url)
    except Exception as e:
        print(f"  Ошибка при загрузке страницы {page_url}: {e}")
    return links

def get_article_details(article_url):
    try:
        response = requests.get(article_url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('h1', class_='content_main_title')
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        date_tag = soup.find('span', class_='date')
        date = date_tag.get_text(strip=True) if date_tag else "N/A"

        text_block = soup.find('div', class_='content_main_text')
        if not text_block: return None

        paragraphs = text_block.find_all('p')
        full_text = "\n".join([p.get_text(strip=True) for p in paragraphs])

        # Очистка от стандартных фраз Tengrinews
        full_text = re.sub(r'Massaget\.kz.*', '', full_text, flags=re.IGNORECASE)
        full_text = re.sub(r'Tengrinews\.kz.*', '', full_text, flags=re.IGNORECASE)
        full_text = re.sub(r'Еlorda Aqparat.*', '', full_text, flags=re.IGNORECASE)
        
        if len(full_text) < 100: return None

        return {"url": article_url, "title": title, "text": full_text, "date": date, "label": 1, "source": "tengrinews.kz"}
    except Exception as e:
        print(f"  Ошибка при загрузке статьи {article_url}: {e}")
        return None

def main():
    print(f"Начинаем парсинг 'tengrinews.kz'. Цель: {PAGES_TO_PARSE} страниц.")
    all_links = []
    for page in tqdm(range(1, PAGES_TO_PARSE + 1), desc="Сбор ссылок (Tengrinews)"):
        page_url = START_URL_TEMPLATE.format(page)
        all_links.extend(get_article_links(page_url))
        time.sleep(0.3) 

    print(f"Собрано {len(all_links)} уникальных ссылок.")
    all_articles = []
    for url in tqdm(all_links, desc="Обработка статей (Tengrinews)"):
        data = get_article_details(url)
        if data: all_articles.append(data)
        time.sleep(0.3) 

    if not all_articles:
        print("Не удалось собрать данные с Tengrinews.kz.")
        return

    df = pd.DataFrame(all_articles)[['url', 'title', 'text', 'date', 'label', 'source']]
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8', quoting=1) 
    print(f"\n[TENGRINEWS.KZ] ГОТОВО! Собрано {len(df)} статей. Файл: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()