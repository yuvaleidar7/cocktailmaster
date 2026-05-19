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

    "lagavulin 16y": "smoked whisky",
    "lagavulin 16": "smoked whisky",
    "lagavulin": "smoked whisky",
    "islay whisky": "smoked whisky",
    "islay whiskey": "smoked whisky",
    

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
    
    "Goslings Rum": "dark rum (black rum)",

    "dark rum": "dark rum",
    "Gold Puerto Rican rum": "dark rum",
    "Gold Jamaican Rum":"dark rum",
    "Aged Rum":"dark rum",
    "dark jamaican rum": "dark rum",
    "añejo rum": "dark rum",
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
    "champagne": "sparkling wine",
    "prosecco": "sparkling wine",
    "cava": "sparkling wine"
}


def clean_and_transform_cocktails(file_path):
    print(f"1. Loading raw data from {file_path}...")
    df = pd.read_csv(file_path, encoding='utf-8')

    if 'Preparation' not in df.columns:
        df['Preparation'] = "Combine all ingredients and mix well."
    else:
        df['Preparation'] = df['Preparation'].fillna("Combine all ingredients and mix well.")

    if 'Glassware' not in df.columns:
        df['Glassware'] = "Standard Glass"
    else:
        df['Glassware'] = df['Glassware'].fillna("Standard Glass")

    if 'Image_Path' not in df.columns:
        df['Image_Path'] = "No Image"
    else:
        df['Image_Path'] = df['Image_Path'].fillna("No Image")

    print("1.5. Normalizing ingredient names in dataframe...")
    sorted_keys = sorted(REPLACEMENTS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        pattern = re.compile(re.escape(key), re.IGNORECASE)
        # מנקה את רשימת המרכיבים
        df['Ingredients'] = df['Ingredients'].apply(lambda x: pattern.sub(REPLACEMENTS[key], str(x)) if pd.notnull(x) else x)
        # התוספת החדשה - מנקה גם את אופן ההכנה!
        df['Preparation'] = df['Preparation'].apply(lambda x: pattern.sub(REPLACEMENTS[key], str(x)) if pd.notnull(x) else x)

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

    df['Ingredients_Cleaned'] = df['Ingredients'].apply(convert_measurements)
    df['Preparation_Cleaned'] = df['Preparation'].apply(convert_measurements)
    df['Ingredients_Cleaned'] = df['Ingredients_Cleaned'].apply(format_ingredients_as_bullets)

    df['Vector_Document'] = (
            "Cocktail: " + df['Cocktail Name'] + "\n" +
            "Glassware: " + df['Glassware'] + "\n" +
            "Ingredients:\n" + df['Ingredients_Cleaned'] + "\n\n" +
            "Preparation:\n" + df['Preparation_Cleaned']
    )

    print("3. Data transformation complete!")
    return df