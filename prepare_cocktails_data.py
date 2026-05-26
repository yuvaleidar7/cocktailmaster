import pandas as pd
import re

# מילון ההחלפות המלא
REPLACEMENTS = {
    # סירופים וממתיקים
    "demerara sugar syrup": "sugar syrup",
    "rich simple syrup": "sugar syrup",
    "simple syrup": "sugar syrup",
    "sugar syrup": "sugar syrup",
    "demerara syrup": "sugar syrup",
    "gomme syrup": "Monin gomme (sugar syrup)",
    "gum syrup": "Monin gum (sugar syrup)",
    "passion fruit syrup": "passion fruit syrup",
    "maple syrup": "maple syrup (sugar syrup)",
    "agave nectar": "agave nectar (sugar syrup)",
    "agave syrup": "agave nectar (sugar syrup)",
    "100% agave nectar": "agave Nectar (sugar syrup)",
    "Honey Syrup": "honey syrup (sugar syrup)",

    # מיצים 
    "freshly squeezed lemon juice": "lemon juice",
    "fresh lemon juice": "lemon juice",
    "freshly squeezed lime juice": "lime juice",
    "fresh lime juice": "lime juice",
    "fresh orange juice": "orange juice",

    # וויסקי
    "bourbon whiskey": "whiskey",
    "rye whiskey": "whiskey",
    "scotch whisky": "whiskey",
    "irish whiskey": "whiskey",
    "tennessee whiskey": "whiskey",
    "blended whiskey": "whiskey",
    "Blended Whiskey": "whiskey",
    "single malt scotch": "whiskey",
    "single malt": "whiskey",
    "bourbon": "whiskey",
    "rye": "whiskey",
    "scotch": "whiskey",
    "Blended Scotch Whisky": "whiskey",
    "Scotch Whisky": "whiskey",

    "lagavulin 16y": "smoked whisky",
    "lagavulin 16": "smoked whisky",
    "lagavulin": "smoked whisky",
    "islay whisky": "smoked whisky",
    "islay whiskey": "smoked whisky",
    "smoked whiskey": "smoked whisky",
    "Smoked Whisky": "smoked whisky",
  
    # ליקרי תפוז
    "cointreau": "orange liqueur",
    "triple sec": "orange liqueur",
    "grand marnier": "orange liqueur",
    "orange curaçao": "orange liqueur",
    "Bitter Campari": "campari",

    # קפה וליקרי קפה
    "kahlúa": "coffee liqueur",
    "kahlua": "coffee liqueur",
    "tia maria": "coffee liqueur",
    "fresh espresso": "espresso",
    "espresso shot": "espresso",
    "cold brew coffee": "espresso",
    "cold brew": "espresso",

    # ג'ין
    "london dry gin": "gin",
    "plymouth gin": "gin",
    "old tom gin": "gin",
    "Dry Gin": "gin",

    # טקילה ומזקל
    "tequila blanco": "tequila",
    "tequila silver": "tequila",
    "tequila reposado": "tequila",
    "Tequila 100% agave": "tequila",
    "100% Agave Tequila": "tequila",
    "100% agave tequila": "tequila",
    "Tequila 100% agave": "tequila",
    "blanco tequila": "tequila",
    "reposado tequila": "tequila",
    "mezcal espadin": "mezcal",
    "anejo mezcal": "mezcal",
    "joven mezcal": "mezcal",
    "Espadin Mezcal": "mezcal",
    

    # רום וקשאסה
    "white cuban rum": "white rum",
    "light rum": "white rum",
    "Cuban Rum":"white rum",
    "Ron Profundo Havana Club":"white rum",
    "Jamaica Overproof White Rum":"white rum",
    "Martinique Molasses Rhum": "white rum",
    "amaica Overproof White Rum": "white rum",
    
    "Goslings Rum": "dark rum (black rum)",

    "dark rum": "dark rum",
    "Gold Puerto Rican rum": "dark rum",
    "Gold Jamaican Rum":"dark rum",
    "Aged Rum":"dark rum",
    "dark jamaican rum": "dark rum",
    "añejo rum": "dark rum",
    "Demerara Rum": "dark rum",
    "Amber Jamaican Rum": "dark rum",

    "cachaça": "cachaça",
    "cachaca": "cachaça",

    # ורמוט ואפרטיפים
    "dry french vermouth": "dry vermouth",
    "sweet red vermouth": "sweet vermouth",
    "lillet blanc": "lillet",
    "lillet blonde": "lillet",
    "kina lillet": "lillet",
    "cocchi americano": "lillet",
    "campari bitter": "campari",
    "Red Tawny Port Wine": "red port wine",

    # ליקרי שוקולד / קקאו
    "white crème de cacao": "white chocolate liqueur",
    "white creme de cacao": "white chocolate liqueur",
    "dark crème de cacao": "chocolate liqueur",
    "dark creme de cacao": "chocolate liqueur",
    "crème de cacao": "chocolate liqueur",
    "creme de cacao": "chocolate liqueur",

    # ליקרי דובדבנים
    "maraschino liqueur": "maraschino cherry liqueur",
    "Maraschino Cherry Liqueur Luxardo": "cherry liqueur",
    "maraschino": "cherry liqueur",
    "cherry heering": "cherry liqueur",
    "heering cherry liqueur": "cherry liqueur",
    "cherry brandy": "cherry liqueur",

    # ליקרי מנטה / קרם דה מנטה
    "green crème de menthe": "green mint liqueur",
    "green creme de menthe": "green mint liqueur",
    "white crème de menthe": "white mint liqueur",
    "white creme de menthe": "white mint liqueur",
    "crème de menthe": "mint liqueur",
    "creme de menthe": "mint liqueur",

    # ליקר פטל שחור / אפרסק / שקדים
    "crème de cassis": "blackcurrant liqueur",
    "creme de cassis": "blackcurrant liqueur",
    "chambord": "raspberry liqueur",
    "peach schnapps": "peach liqueur",
    "crème de pêche": "peach liqueur",
    "creme de peche": "peach liqueur",
    "disaronno": "amaretto",

    # ליקרים עשבוניים ואניס
    "yellow chartreuse": "yellow chartreuse",
    "green chartreuse": "green chartreuse",
    "benedictine": "bénédictine",
    "elderflower liqueur": "elderflower liqueur",
    "st germain": "elderflower liqueur",
    "st. germain": "elderflower liqueur",
    "pernod": "absinthe",
    "pastis": "absinthe",
    "ricard": "absinthe",
    "herbsaint": "absinthe",

    # סודה ומים מוגזים
    "club soda": "soda water",
    "sparkling water": "soda water",
    "carbonated water": "soda water",

    # סוכר לבן (מוצק)
    "sugar cube": "sugar",
    "white sugar": "sugar",
    "powdered sugar": "sugar",
    "caster sugar": "sugar",
    "granulated sugar": "sugar",
    "White Cane Sugar": "sugar",

    # ביצים, שמנת ומחיות פרי
    "white of one egg": "egg white(optional)",
    "fresh egg white": "egg white(optional)",
    "aquafaba": "egg white(optional)",
    "chickpea water": "egg white(optional)",
    "heavy cream": "cream",
    "fresh cream": "cream",
    "single cream": "cream",
    "cream of coconut": "coconut cream", 
    "coco lopez": "coconut cream",
    "white peach puree": "peach puree",
    "white peach purée": "peach puree",
    "peach puree": "peach puree",
    "peach purée": "peach puree",
    "passion fruit purée": "passion fruit puree",

    # ביטרס
    "angostura aromatic bitters": "angostura bitters",
    "aromatic bitters": "angostura bitters",

    # ברנדי וקוניאק
    "calvados": "apple brandy",
    "applejack": "apple brandy",
    "pisco": "pisco",
    "Apricot Brandy": "apricot brandy",
    "cognac vsop": "cognac",
    "cognac v.s.o.p.": "cognac",
    "Brandy": "brandy",
    
    # וודקה
    "Smirnoff Vodka": "vodka",
    "citron vodka": "vodka",
    "absolut citron": "vodka",
    "lemon vodka": "vodka",
    
    # מבעבעים
    "champagne":"sparkling wine",
    "prosecco":"sparkling wine",
    "cava":"sparkling wine",
    "Red Tawny Port Wine":"red port",
    "Chilled Champagne":"sparkling wine",
     "Chilled sparkling wine":"sparkling wine",
}

def apply_replacements(text, replacements_dict):
    if not isinstance(text, str):
        return text
    
    text = text.replace('\n', ', ')
    
    for original, replacement in replacements_dict.items():
        pattern = re.compile(r'\b' + re.escape(original) + r'\b', re.IGNORECASE)
        text = pattern.sub(replacement, text)
    return text

def clean_and_transform_cocktails(file_path):
    print("1. Loading raw data...")
    df = pd.read_csv(file_path, encoding='utf-8')

    print("2. Parsing and converting measurements to ml...")

    def convert_measurements(text):
        if not isinstance(text, str): return text
        def replacer_oz(match):
            oz_val = float(match.group(1))
            return f"{round(oz_val * 30)} ml"
        return re.sub(r'(\d*\.?\d+)\s*oz\b', replacer_oz, text, flags=re.IGNORECASE)

    def format_ingredients_as_bullets(text):
        if not isinstance(text, str): return text
        if '\n' in text:
            items = text.split('\n')
        else:
            items = text.split(',')
        return "\n".join([f"- {ing.strip()}" for ing in items if ing.strip()])

    # --- התיקון: הפעלת פונקציית ההחלפה על המרכיבים ואופן ההכנה ---
    df['Ingredients'] = df['Ingredients'].apply(lambda x: apply_replacements(x, REPLACEMENTS))
    df['Preparation'] = df['Preparation'].apply(lambda x: apply_replacements(x, REPLACEMENTS))
    # --------------------------------------------------------------

    df['Ingredients_Cleaned'] = df['Ingredients'].apply(convert_measurements)
    df['Preparation_Cleaned'] = df['Preparation'].apply(convert_measurements)
    df['Ingredients_Cleaned'] = df['Ingredients_Cleaned'].apply(format_ingredients_as_bullets)

    # הוספת Flavor Profile למסמך הוקטורי כדי שיהיה ניתן לחפש אותו
    df['Vector_Document'] = (
            "Cocktail: " + df['Cocktail Name'] + "\n" +
            "Flavor Profile: " + df['Flavor Profile'].fillna('Unknown') + "\n" +
            "Glassware: " + df['Glassware'] + "\n" +
            "Ingredients:\n" + df['Ingredients_Cleaned'] + "\n\n" +
            "Preparation:\n" + df['Preparation_Cleaned']
    )

    print("3. Data transformation complete!")
    return df