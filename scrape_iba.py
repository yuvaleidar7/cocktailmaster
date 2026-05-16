import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_cocktail_links():
    categories = [
        "https://iba-world.com/cocktails/the-unforgettables/",
        "https://iba-world.com/cocktails/the-contemporary/",
        "https://iba-world.com/cocktails/the-new-era/"
    ]

    links = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for category in categories:
        logging.info(f"\n--- Entering Category: {category} ---")

        for page in range(1, 10):
            url = category if page == 1 else f"{category}page/{page}/"
            logging.info(f"Scanning page {page}...")

            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 404:
                    break

                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                found_on_page = 0

                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']

                    # התיקון המנצח: מסננים *רק* לפי הקידומת האמיתית שגילינו!
                    if href.startswith('https://iba-world.com/iba-cocktail/'):
                        if href not in links:
                            links.add(href)
                            found_on_page += 1

                logging.info(f"Found {found_on_page} cocktails on this page.")
                if found_on_page == 0:
                    break

                time.sleep(1)

            except Exception as e:
                logging.error(f"Error scanning {url}: {e}")
                break

    final_links = list(links)
    logging.info(f"\n✅ Total unique cocktails collected: {len(final_links)}")
    return final_links


def scrape_cocktail_page(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # חילוץ שם הקוקטייל
        name_tag = soup.find('h1')
        name = name_tag.text.strip() if name_tag else "Unknown"

        # חילוץ תוכן חסין-תקלות: מנסים את ה-div הרגיל, ואם לא - לוקחים את כל הטקסט של המאמר
        content_div = soup.find('div', class_='elementor-widget-theme-post-content')
        if content_div:
            full_text = content_div.get_text(separator=' ', strip=True)
        else:
            # אם האתר שינה עיצוב, פשוט נשלוף את כל הטקסט מה-body
            full_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""

        if not full_text:
            logging.warning(f"No content found for: {name}")
            return None

        ingredients = full_text
        preparation = "See full text"

        # חיפוש המילה METHOD לחלוקה חכמה
        if "METHOD" in full_text.upper():
            parts = re.split(re.compile(r'METHOD', re.IGNORECASE), full_text)

            # ניקוי הטקסט שלפני ה-METHOD (כדי לחלץ מרכיבים נקיים)
            raw_ingredients = parts[0]
            # חותכים הכל עד המילה INGREDIENTS כדי להיפטר מטקסט מקדים של האתר
            if "INGREDIENTS" in raw_ingredients.upper():
                raw_ingredients = re.split(re.compile(r'INGREDIENTS', re.IGNORECASE), raw_ingredients)[-1]

            ingredients = raw_ingredients.strip()
            preparation = parts[1].strip()

            # חותכים שטויות של סוף עמוד מתוך ההכנה (כמו "GARNISH" או קרדיטים)
            if "GARNISH" in preparation.upper():
                preparation = re.split(re.compile(r'GARNISH', re.IGNORECASE), preparation)[0].strip()

        return {
            'Cocktail Name': name,
            'Ingredients': ingredients,
            'Preparation': preparation,
            'Glassware': 'Standard Glass',
            'Bartender': 'IBA Official',
            'Location': 'Global'
        }

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None


def fetch_live_from_iba(cocktail_name):
    """
    פונקציית גיבוי: מנסה לשאוב מתכון בזמן אמת מהאתר הרשמי של IBA
    """
    print(f"\n[Live Web Search] Checking IBA website for '{cocktail_name}'...")

    # הופכים את השם לפורמט של כתובת (למשל "espresso martini" -> "espresso-martini")
    formatted_name = cocktail_name.strip().lower().replace(" ", "-")

    # משתמשים במבנה הכתובת הנכון שגילינו!
    url = f"https://iba-world.com/iba-cocktail/{formatted_name}/"

    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers, timeout=5)

        # אם לא מצאנו תחת iba-cocktail, ננסה את התבנית השנייה ליתר ביטחון
        if response.status_code != 200:
            url = f"https://iba-world.com/cocktails/{formatted_name}/"
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code != 200:
                print(" -> Not found on IBA live site.")
                return None

        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.find('div', class_='elementor-widget-theme-post-content')
        if content_div:
            full_text = content_div.get_text(separator=' ', strip=True)
        else:
            full_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""

        if not full_text:
            return None

        live_context = (
            f"Cocktail: {cocktail_name.title()}\n"
            f"Source: Live IBA Website Web-Scrape\n"
            f"Raw Data:\n{full_text}"
        )
        print(" -> Success! Downloaded live recipe from IBA.")
        return live_context

    except Exception as e:
        print(f" -> Live search failed: {e}")
        return None


def main():
    logging.info("Starting IBA Scraper Pipeline...")

    # 1. משיגים את כל הלינקים מהקטגוריות
    links = get_cocktail_links()

    if not links:
        logging.error("No links found. Exiting pipeline. Check CSS classes in parser.")
        return

    cocktails_data = []
    test_limit = len(links)  # נשארים על 5 לבדיקה

    logging.info(f"Starting extraction for {test_limit} cocktails...")

    # 2. גירוד הנתונים
    for i, link in enumerate(links[:test_limit]):
        logging.info(f"Scraping [{i + 1}/{test_limit}]: {link}")
        data = scrape_cocktail_page(link)
        if data:
            cocktails_data.append(data)

        time.sleep(1.5)

        # 3. שמירת הנתונים (מחוץ ללולאה!)
    df = pd.DataFrame(cocktails_data)
    csv_filename = "iba_live_scraped_data.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')

    logging.info(f"Scraping complete! {len(df)} cocktails saved to '{csv_filename}'.")


if __name__ == "__main__":
    main()