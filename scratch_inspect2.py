import json, sys
sys.path.insert(0, r'c:\Users\yuval\OneDrive\Desktop\cocktailmasterVS')

d = json.load(open('db_full_analysis.json', encoding='utf-8'))

print("=== NO_RESULT cocktails ===")
for r in d['exact_match_results']:
    if r['status'] == 'NO_RESULT':
        print(f"  {r['name']!r} | base={r.get('base')} | other={r.get('other')}")

print()
print("=== SKIP_EMPTY cocktails ===")
for r in d['exact_match_results']:
    if r['status'] == 'SKIP_EMPTY':
        print(f"  {r['name']!r}")

print()
print("=== HAS ZERO IN MATCH PCTS ===")
for r in d['exact_match_results']:
    if r.get('has_zero_match'):
        print(f"  {r['name']!r} | pcts={r['match_pcts']} | returned={r.get('returned_names')}")

print()
print("=== SINGLE ING EMPTY ===")
for r in d['single_ingredient_results']:
    if r.get('is_empty'):
        print(f"  {r['ingredient']!r} | weight={r['weight']}")

print()
print("=== ALL UNIQUE INGREDIENTS (110) ===")
for ing in d['all_unique_ingredients']:
    w_note = "(NO RESULT)" if any(r['ingredient']==ing and r.get('is_empty') for r in d['single_ingredient_results']) else ""
    print(f"  {ing!r} {w_note}")

print()
print("=== EXACT MATCH PCTS PER COCKTAIL ===")
for r in d['exact_match_results']:
    if r['status'] == 'FOUND':
        print(f"  {r['name']!r:35s} pcts={r['match_pcts']} base={r.get('base')} other={r.get('other')}")
