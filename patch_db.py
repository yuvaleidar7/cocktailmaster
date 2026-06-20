import pickle

with open('bm25_index.pkl', 'rb') as f:
    bm25_data = pickle.load(f)

replacements = {
    '- 52.5 ml gin 2 teaspoons honey syrup (sugar syrup) 22.5 ml lemon juice 22.5 ml orange juice': 
    '- 52.5 ml gin\n2 teaspoons honey syrup (sugar syrup)\n22.5 ml lemon juice\n22.5 ml orange juice',
    
    '- 30 ml dark rum 15 ml white rum 15 ml passion fruit syrup 15 ml lime juice 15 ml honey syrup (sugar syrup)':
    '- 30 ml dark rum\n15 ml white rum\n15 ml passion fruit syrup\n15 ml lime juice\n15 ml honey syrup (sugar syrup)',
    
    '- 60 ml whiskey 7.5 ml smoked whisky 22.5 ml lemon juice 22.5 ml honey syrup (sugar syrup) 2-3 quarter size sliced fresh ginger':
    '- 60 ml whiskey\n7.5 ml smoked whisky\n22.5 ml lemon juice\n22.5 ml honey syrup (sugar syrup)\n2-3 quarter size sliced fresh ginger',
    
    '- 50 ml Vodka Vanilla 15 ml Elderflower Cordial 15 ml lime juice 10 ml Monin honey syrup (sugar syrup) 2 thin Slices Red Chili Pepper':
    '- 50 ml Vodka Vanilla\n15 ml Elderflower Cordial\n15 ml lime juice\n10 ml Monin honey syrup (sugar syrup)\n2 thin Slices Red Chili Pepper',
    
    '- 45 ml Rhum Martinique Agricole 15 ml Blended dark rum 7.5 ml Falernum 7.5 ml Allspice Saint Elizabeth15 ml lime juice 15 ml orange juice 15 ml honey syrup (sugar syrup) 2 Dashes Angostura Bitters':
    '- 45 ml Rhum Martinique Agricole\n15 ml Blended dark rum\n7.5 ml Falernum\n7.5 ml Allspice Saint Elizabeth\n15 ml lime juice\n15 ml orange juice\n15 ml honey syrup (sugar syrup)\n2 Dashes Angostura Bitters',
    
    '- 60 ml tequila 30 ml lime juice 30 ml agave nectar (sugar syrup)':
    '- 60 ml tequila\n30 ml lime juice\n30 ml agave nectar (sugar syrup)'
}

changed = 0
for meta in bm25_data['metadatas']:
    raw = meta.get('ingredients_raw', '')
    if raw in replacements:
        meta['ingredients_raw'] = replacements[raw]
        changed += 1

with open('bm25_index.pkl', 'wb') as f:
    pickle.dump(bm25_data, f)
print(f"Patched {changed} cocktails in bm25_index.pkl")
