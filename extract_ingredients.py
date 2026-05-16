"""
Extract all unique ingredients from iba_live_scraped_data.csv
Output to a UTF-8 file to avoid encoding issues.
"""
import csv
import re
import json

def normalize_ingredient(name):
    """Normalize an extracted ingredient name."""
    name = name.strip().strip(',').strip()
    # Remove leading adjectives/qualifiers
    name = re.sub(r'^(?:Fresh|Freshly|Squeezed|Chilled|Raw|Good quality)\s+', '', name, flags=re.IGNORECASE)
    # Remove "(Optional)" suffix
    name = re.sub(r'\s*\(Optional\)\s*$', '', name, flags=re.IGNORECASE)
    # Remove trailing notes
    name = re.sub(r'\s*\(.*?\)\s*$', '', name)
    return name.strip()

def extract_ingredients_from_csv():
    """
    Parse each cocktail row and manually extract ingredient names
    by reading the Ingredients field carefully.
    """
    all_ingredients = set()

    with open('iba_live_scraped_data.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get('Ingredients', '')
            if not raw:
                continue
            
            # Strategy: split on measurement patterns
            # Patterns like "30 ml", "2 dashes", "1 tsp", "6 pcs", etc.
            # Each ingredient starts with a measurement
            segments = re.split(
                r'(?:^|\s)(?=\d+(?:[./]\d+)?\s*(?:ml|cl|tsp|teaspoon|teaspoons|tablespoon|bar spoon|bar spoons|dashes?|drops?|pcs|grams?)\b)',
                raw, flags=re.IGNORECASE
            )
            
            for seg in segments:
                seg = seg.strip()
                if not seg:
                    continue
                # Remove the leading measurement
                cleaned = re.sub(
                    r'^\d+(?:[./]\d+)?\s*(?:ml|cl|tsp|teaspoon|teaspoons|tablespoon|bar spoon|bar spoons|dashes?|drops?|pcs|grams?)\s*',
                    '', seg, flags=re.IGNORECASE
                )
                # Also handle "A splash of", "A pinch of", "Few", "Top up with", etc.
                cleaned = re.sub(r'^(?:A\s+splash\s+of\s+|A\s+pinch\s+of\s+|Few\s+|Top\s+(?:up\s+)?(?:with\s+)?|Fill\s+(?:up\s+)?(?:with\s+)?|Splash\s+of\s+)', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'^(?:of\s+)', '', cleaned, flags=re.IGNORECASE)
                cleaned = normalize_ingredient(cleaned)
                if cleaned and len(cleaned) > 1:
                    all_ingredients.add(cleaned)

    return sorted(all_ingredients)

if __name__ == '__main__':
    ings = extract_ingredients_from_csv()
    with open('extracted_ingredients.json', 'w', encoding='utf-8') as f:
        json.dump(ings, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(ings)} unique ingredients. Saved to extracted_ingredients.json")
