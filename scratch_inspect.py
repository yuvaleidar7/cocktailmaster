import pickle, sys, re, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r'c:\Users\yuval\OneDrive\Desktop\cocktailmasterVS')

with open('bm25_index.pkl', 'rb') as f:
    data = pickle.load(f)

print(f'Total cocktails: {len(data["docs"])}')

# --- Parse ingredients from each cocktail ---
def parse_ingredients(raw: str) -> list:
    """Split raw ingredient string into individual ingredient strings."""
    if not raw:
        return []
    clean = raw.replace('\\n', '\n').replace('\\r', '')
    # Try comma / newline / semicolon split first
    parts = [p.strip() for p in re.split(r',|\n|;|<br/?>',clean) if p.strip()]
    if len(parts) <= 1 and len(clean) > 20:
        parts = [p.strip() for p in re.split(r'\band\b|&| - ', clean) if len(p.strip()) > 2]
    # Strip leading "- " or "• "
    cleaned = []
    for p in parts:
        p = re.sub(r'^[-\u2022\*]\s*', '', p).strip()
        # remove measurement prefix like "30 ml " "1 oz " "2 dashes "
        p = re.sub(r'^\d+(?:[./]\d+)?\s*(?:ml|oz|cl|tsp|tbsp|dashes?|drops?|pcs|parts?|slices?|wedges?|leaves?)?\s*', '', p).strip()
        if len(p) > 1:
            cleaned.append(p)
    return cleaned

# Gather all unique ingredients across the whole DB
all_ingredients = set()
cocktail_map = []  # (name, flavor, parsed_ingredients)

for meta in data['metadatas']:
    name = meta.get('name', '?')
    raw = meta.get('ingredients_raw', '')
    flavor = meta.get('flavor', meta.get('taste', ''))
    ings = parse_ingredients(raw)
    cocktail_map.append({'name': name, 'flavor': flavor, 'ingredients': ings, 'raw': raw})
    for ing in ings:
        all_ingredients.add(ing.lower().strip())

print(f'\nTotal unique parsed ingredients: {len(all_ingredients)}')
print()

# Print cocktail ingredient breakdown
for entry in cocktail_map:
    print(f"  {entry['name']!r:30s} | ings={entry['ingredients']}")

print('\n=== ALL UNIQUE INGREDIENTS ===')
for ing in sorted(all_ingredients):
    print(f'  {ing!r}')

print('\n=== FLAVORS ===')
flavors = set(e['flavor'] for e in cocktail_map)
for f in sorted(flavors):
    print(f'  {f!r}')

# Dump as JSON for further use
with open('db_analysis.json', 'w', encoding='utf-8') as out:
    json.dump({
        'total': len(cocktail_map),
        'cocktails': cocktail_map,
        'all_ingredients': sorted(all_ingredients),
        'flavors': sorted(flavors)
    }, out, ensure_ascii=False, indent=2)
print('\nDumped db_analysis.json')
