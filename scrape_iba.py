import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import re
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

IMAGE_DIR = "cocktail_images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)


def get_cocktail_links():
    categories = [
        "https://iba-world.com/cocktails/the-unforgettables/",
        "https://iba-world.com/cocktails/the-contemporary/",
        "https://iba-world.com/cocktails/the-new-era/"
    ]

    cocktail_map = {} # משנים למילון: קישור קוקטייל -> קישור תמונה מהגריד
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

                    if href.startswith('https://iba-world.com/iba-cocktail/'):
                        found_on_page += 1
                        
                        # התיקון: שולפים את התמונה ישירות מהכרטיסייה של הקוקטייל בגריד
                        img_tag = a_tag.find('img')
                        if img_tag and img_tag.get('src'):
                            cocktail_map[href] = img_tag['src']
                        elif href not in cocktail_map:
                            # אם הגענו לקישור של הטקסט/כותרת (שאין בו תמונה), נשמור רק אם לא מצאנו את התמונה קודם
                            cocktail_map[href] = None

                logging.info(f"Scanned page {page}. Unique cocktails in map so far: {len(cocktail_map)}")
                if found_on_page == 0:
                    break

                time.sleep(1)

            except Exception as e:
                logging.error(f"Error scanning {url}: {e}")
                break

    logging.info(f"\n✅ Total unique cocktails collected: {len(cocktail_map)}")
    return cocktail_map


def scrape_cocktail_page(url, pre_extracted_image_url=None):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # חילוץ שם הקוקטייל
        name_tag = soup.find('h1')
        name = name_tag.text.strip() if name_tag else "Unknown"

        # --- חילוץ והורדת התמונה ---
        image_path = "No Image"
        image_url = pre_extracted_image_url if pre_extracted_image_url else ""
        
        # גיבוי: אם לא הגיעה תמונה מהגריד, מנסים בכל זאת לגרד מהעמוד הפנימי
        if not image_url:
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image['content']

        if image_url:
            try:
                if image_url.startswith('/'):
                    image_url = f"https://iba-world.com{image_url}"

                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
                filename = f"{safe_name}.jpg"
                local_path = os.path.join(IMAGE_DIR, filename)
                
                if not os.path.exists(local_path):
                    img_data = requests.get(image_url, headers=headers, timeout=10).content
                    with open(local_path, 'wb') as f:
                        f.write(img_data)
                
                image_path = local_path
                logging.info(f" -> Image saved for {name}")
            except Exception as img_e:
                logging.warning(f" -> Failed to download image for {name}: {img_e}")
        else:
            logging.warning(f" -> No image available for {name}")
        # ------------------------------------------

        # חילוץ תוכן חסין-תקלות
        content_div = soup.find('div', class_='elementor-widget-theme-post-content')
        if content_div:
            full_text = content_div.get_text(separator=' ', strip=True)
        else:
            full_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""

        if not full_text:
            logging.warning(f"No content found for: {name}")
            return None

        ingredients = full_text
        preparation = "See full text"

        if "METHOD" in full_text.upper():
            parts = re.split(re.compile(r'METHOD', re.IGNORECASE), full_text)

            raw_ingredients = parts[0]
            if "INGREDIENTS" in raw_ingredients.upper():
                raw_ingredients = re.split(re.compile(r'INGREDIENTS', re.IGNORECASE), raw_ingredients)[-1]

            ingredients = raw_ingredients.strip()
            preparation = parts[1].strip()

            if "GARNISH" in preparation.upper():
                preparation = re.split(re.compile(r'GARNISH', re.IGNORECASE), preparation)[0].strip()

        return {
            'Cocktail Name': name,
            'Ingredients': ingredients,
            'Preparation': preparation,
            'Glassware': 'Standard Glass',
            'Bartender': 'IBA Official',
            'Location': 'Global',
            'Image_URL': image_url,       
            'Image_Path': image_path      
        }

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None


def main():
    logging.info("Starting IBA Scraper Pipeline...")

    # 1. משיגים את מילון הקישורים והתמונות
    cocktail_map = get_cocktail_links()

    if not cocktail_map:
        logging.error("No links found. Exiting pipeline.")
        return

    cocktails_data = []
    items_list = list(cocktail_map.items())
    test_limit = len(items_list)

    logging.info(f"Starting extraction for {test_limit} cocktails...")

    # 2. גירוד הנתונים
    for i, (link, pre_img_url) in enumerate(items_list[:test_limit]):
        logging.info(f"Scraping [{i + 1}/{test_limit}]: {link}")
        data = scrape_cocktail_page(link, pre_extracted_image_url=pre_img_url)
        if data:
            cocktails_data.append(data)

        time.sleep(1.5)

    # 3. שמירת הנתונים
    df = pd.DataFrame(cocktails_data)
    csv_filename = "iba_live_scraped_data.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')

    logging.info(f"Scraping complete! {len(df)} cocktails saved to '{csv_filename}'.")
    logging.info(f"Images are saved in the '{IMAGE_DIR}' directory.")


if __name__ == "__main__":
    main()