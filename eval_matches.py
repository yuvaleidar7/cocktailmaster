import pandas as pd
import re

user_inventory = [
  'Vodka', 'Gin', 'Tequila', 'Mezcal', 'Whiskey', 'Smoked Whiskey', 'White Rum', 'Dark Rum', 'Brandy', 'Cognac', 'Other Base Spirits',
  'Orange Liqueur', 'Campari', 'Aperol', 'Coffee Liqueur (Kahlúa)', 'Amaretto (Almond)', 'Sweet Vermouth', 'Dry Vermouth', 'Chartreuse', 'Absinthe', 'Sparkling Wine (Champagne / Cava)', 'Wine (White / Red)',
  'Simple Syrup', 'Grenadine', 'Honey Syrup', 'Orgeat (Almond Syrup)', 'Sugar',
  'Lemon Juice', 'Lime Juice', 'Orange Juice', 'Pineapple Juice', 'Grapefruit Juice', 'Cranberry Juice', 'Tomato Juice', 'Soda', 'Ginger Beer', 'Ginger Ale', 'Cola', 'Espresso', 'Cream',
  'Angostura Bitters', 'Orange Bitters', "Peychaud's Bitters", 'Mint', 'Basil', 'Egg White', 'Egg Yolk', 'Salt', 'Tabasco', 'Worcestershire Sauce'
]

inventory_rules = {}
for item in user_inventory:
    item_lower = item.lower()
    if '(' in item_lower:
        base = item_lower.split('(')[0].strip()
        alts = item_lower.split('(')[1].replace(')', '').split(' / ')
        inventory_rules[item] = [base] + [a.strip() for a in alts]
    else:
        inventory_rules[item] = [item_lower]

df = pd.read_csv('iba_live_scraped_data.csv')

results = []

for index, row in df.iterrows():
    name = row['Cocktail Name']
    raw_ing = str(row['Ingredients'])
    
    raw_ing = raw_ing.replace('\\n', '\n')
    lines = [x.strip() for x in re.split(r'\n|\r|<br>|,|;', raw_ing) if len(x.strip()) > 2]
    
    if len(lines) == 1 and len(lines[0]) > 20:
        lines = [x.strip() for x in re.split(r'\band\b|\&| - ', lines[0]) if len(x.strip()) > 2]
    
    total_ingredients = len(lines)
    if total_ingredients == 0:
        continue
        
    missing_ingredients = []
    
    for line in lines:
        line_lower = line.lower()
        matched = False
        for inv_item, rules in inventory_rules.items():
            if any(rule in line_lower for rule in rules):
                matched = True
                break
        if not matched:
            missing_ingredients.append(line)
            
    match_pct = (len(lines) - len(missing_ingredients)) / len(lines) * 100
    
    if match_pct > 0:
        results.append({
            'Cocktail Name': name,
            'Match %': int(match_pct),
            'Missing Ingredients': missing_ingredients
        })

results.sort(key=lambda x: x['Match %'], reverse=True)

with open('output.txt', 'w', encoding='utf-8') as f:
    for res in results:
        missing_str = 'None' if len(res['Missing Ingredients']) == 0 else ', '.join(res['Missing Ingredients'])
        f.write(f"Cocktail Name: {res['Cocktail Name']}\n")
        f.write(f"Match %: {res['Match %']}%\n")
        f.write(f"Missing Ingredients: {missing_str}\n\n")
