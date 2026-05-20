import pandas as pd
import re

user_inventory = [
  'Vodka', 'Gin', 'Tequila', 'Mezcal', 'Whiskey', 'Smoked Whiskey', 'White Rum', 'Dark Rum', 'Brandy', 'Cognac', 'Other Base Spirits',
  'Orange Liqueur', 'Campari', 'Aperol', 'Coffee Liqueur (Kahlúa)', 'Amaretto (Almond)', 'Sweet Vermouth', 'Dry Vermouth', 'Chartreuse', 'Absinthe', 'Sparkling Wine (Champagne / Cava)', 'Wine (White / Red)',
  'Simple Syrup', 'Grenadine', 'Honey Syrup', 'Orgeat (Almond Syrup)', 'Sugar',
  'Lemon Juice', 'Lime Juice', 'Orange Juice', 'Pineapple Juice', 'Grapefruit Juice', 'Cranberry Juice', 'Tomato Juice', 'Soda', 'Ginger Beer', 'Ginger Ale', 'Cola', 'Espresso', 'Cream',
  'Angostura Bitters', 'Orange Bitters', "Peychaud's Bitters", 'Mint', 'Basil', 'Egg White', 'Egg Yolk', 'Salt', 'Tabasco', 'Worcestershire Sauce'
]

def get_rules():
    rules = {}
    for item in user_inventory:
        item_lower = item.lower()
        if item == 'Wine (White / Red)':
            rules[item] = ['wine', 'white wine', 'red wine']
        elif item == 'Sparkling Wine (Champagne / Cava)':
            rules[item] = ['sparkling wine', 'champagne', 'cava', 'prosecco']
        elif item == 'Coffee Liqueur (Kahlúa)':
            rules[item] = ['coffee liqueur', 'kahlúa', 'kahlua', 'tia maria']
        elif item == 'Amaretto (Almond)':
            rules[item] = ['amaretto', 'almond liqueur', 'disaronno']
        elif item == 'Orgeat (Almond Syrup)':
            rules[item] = ['orgeat', 'almond syrup']
        elif item == 'Other Base Spirits':
            rules[item] = ['pisco', 'cachaça', 'cachaca', 'calvados', 'applejack', 'aquavit']
        elif item == 'Sugar':
            rules[item] = ['sugar cube', 'white sugar', 'powdered sugar', 'caster sugar', 'granulated sugar', 'sugar']
        elif item == 'Cream':
            rules[item] = ['heavy cream', 'fresh cream', 'single cream', 'cream']
        elif item == 'Soda':
            rules[item] = ['club soda', 'sparkling water', 'carbonated water', 'soda water', 'soda']
        elif item == 'Angostura Bitters':
            rules[item] = ['angostura', 'aromatic bitters']
        elif item == 'Mint':
            rules[item] = ['mint leaves', 'mint sprig', 'mint']
        elif item == 'Basil':
            rules[item] = ['basil leaves', 'basil sprig', 'basil']
        elif item == 'Egg White':
            rules[item] = ['egg white', 'white of one egg', 'aquafaba']
        elif item == 'Egg Yolk':
            rules[item] = ['egg yolk']
        elif item == 'Salt':
            rules[item] = ['salt', 'saline']
        elif item == 'Orange Liqueur':
            rules[item] = ['orange liqueur', 'cointreau', 'triple sec', 'grand marnier', 'curaçao', 'curacao']
        elif item == 'Whiskey':
            rules[item] = ['whiskey', 'whisky', 'bourbon', 'rye', 'scotch']
        elif item == 'Smoked Whiskey':
            rules[item] = ['smoked whiskey', 'smoked whisky', 'islay', 'lagavulin']
        else:
            rules[item] = [item_lower]
    return rules

inventory_rules = get_rules()

df = pd.read_csv('iba_live_scraped_data.csv')
results = []

for index, row in df.iterrows():
    name = row['Cocktail Name']
    raw_ing = str(row['Ingredients'])
    
    raw_ing = raw_ing.replace('\\n', '\n')
    lines = [x.strip() for x in re.split(r'\n|\r|<br>', raw_ing) if len(x.strip()) > 2]
    
    if len(lines) == 1 and len(lines[0]) > 20:
        lines = [x.strip() for x in re.split(r'\band\b|\&', lines[0]) if len(x.strip()) > 2]
    
    total_ingredients = len(lines)
    if total_ingredients == 0:
        continue
        
    missing_ingredients = []
    
    for line in lines:
        line_lower = line.lower()
        matched = False
        
        for inv_item, rules in inventory_rules.items():
            for rule in rules:
                if re.search(r'\b' + re.escape(rule) + r'\b', line_lower):
                    matched = True
                    break
            if matched:
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

with open('output2.txt', 'w', encoding='utf-8') as f:
    for res in results:
        missing_str = 'None' if len(res['Missing Ingredients']) == 0 else ', '.join(res['Missing Ingredients'])
        f.write(f"Cocktail Name: {res['Cocktail Name']}\n")
        f.write(f"Match %: {res['Match %']}%\n")
        f.write(f"Missing Ingredients: {missing_str}\n\n")
