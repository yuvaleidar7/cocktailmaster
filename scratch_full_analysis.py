"""
Deep analysis of the cocktail database - outputs JSON only (no terminal print of non-ASCII).
"""
import pickle, sys, re, json
sys.path.insert(0, r'c:\Users\yuval\OneDrive\Desktop\cocktailmasterVS')
import logic

with open('bm25_index.pkl', 'rb') as f:
    data = pickle.load(f)

SYNONYMS = logic._INGREDIENT_SYNONYMS

def normalize_ing(raw_text):
    text = raw_text.lower().strip()
    for src, dst in SYNONYMS.items():
        text = re.sub(r'\b' + re.escape(src.lower()) + r'\b', dst.lower(), text)
    return text.strip()

def parse_ingredients(raw: str) -> list:
    if not raw:
        return []
    clean = raw.replace('\\n', '\n').replace('\\r', '')
    parts = [p.strip() for p in re.split(r',|\n|;|<br/?>',clean) if p.strip()]
    if len(parts) <= 1 and len(clean) > 20:
        parts = [p.strip() for p in re.split(r'\band\b|&| - ', clean) if len(p.strip()) > 2]
    result = []
    for p in parts:
        p = re.sub(r'^\s*[-\u2022*]\s*', '', p)
        p = re.sub(r'^\d+(?:[./]\d+)?\s*(?:ml|oz|cl|tsp|tbsp|dashes?|drops?|pcs|parts?|slices?|wedges?|leaves?|bar\s+spoon|spoon|teaspoon|tablespoon|pinch|splash)\s*', '', p, flags=re.IGNORECASE)
        p = re.sub(r'^\d+\s*', '', p).strip()
        if len(p) > 1:
            result.append(p)
    return result

# Build complete cocktail registry
cocktail_registry = []
all_unique_ingredients = set()

for meta in data['metadatas']:
    name = meta.get('name', '?')
    raw = meta.get('ingredients_raw', '')
    flavor = meta.get('flavor', meta.get('taste', ''))
    ings = parse_ingredients(raw)
    norm_ings = [normalize_ing(i) for i in ings]

    base_spirits = []
    other_ings = []
    for ing in norm_ings:
        w = logic.get_ingredient_weight(ing)
        if w == 5:
            base_spirits.append(ing)
        else:
            other_ings.append(ing)
        all_unique_ingredients.add(ing)

    cocktail_registry.append({
        'name': name, 'flavor': flavor, 'raw': raw,
        'parsed': ings, 'normalized': norm_ings,
        'base_spirits': base_spirits, 'other_ings': other_ings,
    })

print(f"Cocktails: {len(cocktail_registry)}")
print(f"Unique ingredients: {len(all_unique_ingredients)}")

# Test exact-recipe matching
exact_results = []
for entry in cocktail_registry:
    name = entry['name']
    base = entry['base_spirits']
    other = entry['other_ings']

    if not base and not other:
        exact_results.append({'name': name, 'status': 'SKIP_EMPTY'})
        continue

    try:
        ctx, mtype = logic.retrieve_candidates(data, base, other)
        if ctx is None:
            exact_results.append({'name': name, 'status': 'NO_RESULT',
                                   'base': base, 'other': other})
            continue

        pcts = [int(m) for m in re.findall(r'Match:\s*(\d+)%', ctx)]
        returned_names = re.findall(r'Cocktail Name:\s*(.+)', ctx)
        target_in = any(name.lower() in n.lower() or n.lower() in name.lower()
                       for n in returned_names)
        has_zero = 0 in pcts

        exact_results.append({
            'name': name, 'status': 'FOUND' if target_in else 'NOT_TOP4',
            'match_pcts': pcts, 'returned_names': returned_names,
            'has_zero_match': has_zero,
            'match_type': mtype,
            'base': base, 'other': other,
        })
    except Exception as e:
        exact_results.append({'name': name, 'status': 'EXCEPTION', 'error': str(e)})

print(f"Results: FOUND={sum(1 for r in exact_results if r['status']=='FOUND')}, "
      f"NOT_TOP4={sum(1 for r in exact_results if r['status']=='NOT_TOP4')}, "
      f"NO_RESULT={sum(1 for r in exact_results if r['status']=='NO_RESULT')}, "
      f"SKIP={sum(1 for r in exact_results if r['status']=='SKIP_EMPTY')}")

# Test single ingredient
single_ing_results = []
for ing in sorted(all_unique_ingredients):
    w = logic.get_ingredient_weight(ing)
    base = [ing] if w == 5 else []
    other = [] if w == 5 else [ing]
    try:
        ctx, mtype = logic.retrieve_candidates(data, base, other)
        pcts = [int(m) for m in re.findall(r'Match:\s*(\d+)%', ctx)] if ctx else []
        single_ing_results.append({
            'ingredient': ing, 'weight': w,
            'returned_results': ctx is not None,
            'match_pcts': pcts,
            'has_nonzero': any(p > 0 for p in pcts),
            'is_empty': ctx is None,
        })
    except Exception as e:
        single_ing_results.append({
            'ingredient': ing, 'weight': w, 'exception': str(e)
        })

print(f"Single ing: empty={sum(1 for r in single_ing_results if r.get('is_empty'))}, "
      f"exceptions={sum(1 for r in single_ing_results if 'exception' in r)}")

with open('db_full_analysis.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total_cocktails': len(cocktail_registry),
        'cocktail_registry': cocktail_registry,
        'all_unique_ingredients': sorted(all_unique_ingredients),
        'exact_match_results': exact_results,
        'single_ingredient_results': single_ing_results,
    }, f, ensure_ascii=False, indent=2, default=str)
print("Saved db_full_analysis.json")
