"""
Deep analysis of the cocktail database to understand:
1. What ingredients are present
2. How the matching algorithm handles them
3. What match percentages specific recipes produce
"""
import pickle, sys, re, json
import logic

sys.path.insert(0, r'c:\Users\yuval\OneDrive\Desktop\cocktailmasterVS')

with open('bm25_index.pkl', 'rb') as f:
    data = pickle.load(f)

# _INGREDIENT_SYNONYMS from logic for normalization
SYNONYMS = logic._INGREDIENT_SYNONYMS
FILLER_WORDS = logic._FILLER_WORDS

def normalize_ing(raw_text):
    """Apply synonym normalization to a single ingredient string."""
    text = raw_text.lower().strip()
    for src, dst in SYNONYMS.items():
        text = re.sub(r'\b' + re.escape(src.lower()) + r'\b', dst.lower(), text)
    return text.strip()

def clean_measurement(text):
    """Remove ml/oz/dash amounts from beginning."""
    text = re.sub(r'^\s*[-\u2022*]\s*', '', text)
    text = re.sub(r'^\d+(?:[./]\d+)?\s*(?:ml|oz|cl|tsp|tbsp|dashes?|drops?|pcs|parts?|slices?|wedges?|leaves?|bar\s+spoon|spoon|teaspoon|tablespoon|pinch|splash)\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d+\s*', '', text)
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
        p = clean_measurement(p)
        if len(p) > 1:
            result.append(p)
    return result

# Build complete cocktail registry
cocktail_registry = []
for meta in data['metadatas']:
    name = meta.get('name', '?')
    raw = meta.get('ingredients_raw', '')
    flavor = meta.get('flavor', meta.get('taste', ''))
    ings = parse_ingredients(raw)
    norm_ings = [normalize_ing(i) for i in ings]
    
    # Classify each ingredient
    base_spirits = []
    other_ings = []
    for ing in norm_ings:
        w = logic.get_ingredient_weight(ing)
        if w == 5:  # base spirit
            base_spirits.append(ing)
        else:
            other_ings.append(ing)
    
    cocktail_registry.append({
        'name': name,
        'flavor': flavor,
        'raw': raw,
        'parsed': ings,
        'normalized': norm_ings,
        'base_spirits': base_spirits,
        'other_ings': other_ings,
    })

# Test each cocktail with its exact ingredients
print("=== COCKTAIL-BY-COCKTAIL EXACT MATCH TEST ===")
results = []
for entry in cocktail_registry:
    name = entry['name']
    base = entry['base_spirits']
    other = entry['other_ings']
    
    if not base and not other:
        results.append({'name': name, 'status': 'SKIP_EMPTY', 'match_pcts': []})
        print(f"  SKIP  {name!r} - no parsed ingredients")
        continue
    
    ctx, mtype = logic.retrieve_candidates(data, base, other)
    
    if ctx is None:
        results.append({'name': name, 'status': 'NO_RESULT', 'match_pcts': [], 'base': base, 'other': other})
        print(f"  FAIL  {name!r} - returned None | base={base} | other={other}")
        continue
    
    # Extract match percentages and cocktail names from context
    pcts = [int(m) for m in re.findall(r'Match:\s*(\d+)%', ctx)]
    returned_names = re.findall(r'Cocktail Name:\s*(.+)', ctx)
    
    # Check if the target cocktail is in the results
    target_in_results = any(name.lower() in n.lower() or n.lower() in name.lower() 
                           for n in returned_names)
    
    status = 'FOUND' if target_in_results else 'NOT_TOP4'
    results.append({
        'name': name,
        'status': status,
        'match_pcts': pcts,
        'returned_names': returned_names,
        'base': base,
        'other': other,
        'match_type': mtype,
    })
    print(f"  {status:10s} {name!r:30s} | pcts={pcts} | returned={returned_names}")

print()
print(f"Total: {len(results)}")
found = sum(1 for r in results if r['status']=='FOUND')
not_top4 = sum(1 for r in results if r['status']=='NOT_TOP4')
no_result = sum(1 for r in results if r['status']=='NO_RESULT')
skipped = sum(1 for r in results if r['status']=='SKIP_EMPTY')
print(f"FOUND: {found}, NOT_TOP4: {not_top4}, NO_RESULT: {no_result}, SKIPPED: {skipped}")

with open('exact_match_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print("Saved exact_match_results.json")
