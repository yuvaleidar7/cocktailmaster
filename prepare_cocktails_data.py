import pandas as pd
import re

# מילון ההחלפות המלא
REPLACEMENTS = {
    # סירופים וממתיקים
    "demerara sugar syrup": "Sugar Syrup",
    "rich simple syrup": "Sugar Syrup",
    "simple syrup": "Sugar Syrup",
    "sugar syrup": "Sugar Syrup",
    "demerara syrup": "Sugar Syrup",
    "gomme syrup": "Sugar Syrup",
    "gum syrup": "Sugar Syrup",
    "agave syrup": "Agave",
    "agave nectar": "Agave",
    "passion fruit syrup": "Passion Fruit Syrup",
    "maple syrup": "Maple Syrup",
    
    # מיצים 
    "freshly squeezed lemon juice": "Lemon Juice",
    "fresh lemon juice": "Lemon Juice",
    "freshly squeezed lime juice": "Lime Juice",
    "fresh lime juice": "Lime Juice",
    "fresh orange juice": "Orange Juice",

    # וויסקי
    "bourbon whiskey": "Whiskey",
    "rye whiskey": "Whiskey",
    "scotch whisky": "Whiskey",
    "irish whiskey": "Whiskey",
    "tennessee whiskey": "Whiskey",
    "blended whiskey": "Whiskey",
    "single malt scotch": "Whiskey",
    "single malt": "Whiskey",
    "bourbon": "Whiskey",
    "rye": "Whiskey",
    "scotch": "Whiskey",
    "lagavulin 16y": "Smoked Whisky",
    "lagavulin 16": "Smoked Whisky",
    "lagavulin": "Smoked Whisky",

    # ליקרי תפוז
    "cointreau": "Orange Liqueur",
    "triple sec": "Orange Liqueur",
    "grand marnier": "Orange Liqueur",
    "orange curaçao": "Orange Liqueur",

    # קפה וליקרי קפה
    "kahlúa": "Coffee Liqueur",
    "kahlua": "Coffee Liqueur",
    "tia maria": "Coffee Liqueur",
    "fresh espresso": "Espresso",
    "espresso shot": "Espresso",
    "cold brew coffee": "Espresso",
    "cold brew": "Espresso",

    # ג'ין
    "london dry gin": "Gin",
    "plymouth gin": "Gin",
    "old tom gin": "Gin",
    "Dry Gin": "Gin",

    # טקילה ומזקל
    "tequila blanco": "Tequila",
    "tequila silver": "Tequila",
    "tequila reposado": "Tequila",
    "100% agave tequila": "Tequila",
    "blanco tequila": "Tequila",
    "reposado tequila": "Tequila",
    "mezcal espadin": "Mezcal",
    "anejo mezcal": "Mezcal",
    "joven mezcal": "Mezcal",

    # רום וקשאסה
    "white cuban rum": "White Rum",
    "light rum": "White Rum",
    "dark jamaican rum": "Dark Rum",
    "añejo rum": "Dark Rum",
    "Goslings Rum": "Black Rum",
    "Jamaican dark rum": "Dark Rum",
    "Gold Puerto Rican rum": "Dark Rum",
    "cachaça": "Cachaça",
    "cachaca": "Cachaça",

    # ורמוט ואפרטיפים
    "dry french vermouth": "Dry Vermouth",
    "sweet red vermouth": "Sweet Vermouth",
    "lillet blanc": "Lillet",
    "lillet blonde": "Lillet",
    "kina lillet": "Lillet",
    "cocchi americano": "Lillet",
    "campari bitter": "Campari",

    # ליקרי שוקולד / קקאו
    "white crème de cacao": "White Chocolate Liqueur",
    "white creme de cacao": "White Chocolate Liqueur",
    "dark crème de cacao": "Chocolate Liqueur",
    "dark creme de cacao": "Chocolate Liqueur",
    "crème de cacao": "Chocolate Liqueur",
    "creme de cacao": "Chocolate Liqueur",

    # ליקרי דובדבנים
    "maraschino liqueur": "Maraschino Cherry Liqueur",
    "maraschino": "Maraschino Cherry Liqueur",
    "cherry heering": "Cherry Liqueur",
    "heering cherry liqueur": "Cherry Liqueur",
    "cherry brandy": "Cherry Liqueur",

    # ליקרי מנטה / קרם דה מנטה
    "green crème de menthe": "Green Mint Liqueur",
    "green creme de menthe": "Green Mint Liqueur",
    "white crème de menthe": "White Mint Liqueur",
    "white creme de menthe": "White Mint Liqueur",
    "crème de menthe": "Mint Liqueur",
    "creme de menthe": "Mint Liqueur",

    # ליקר פטל שחור / אפרסק / שקדים
    "crème de cassis": "Blackcurrant Liqueur",
    "creme de cassis": "Blackcurrant Liqueur",
    "chambord": "Raspberry Liqueur",
    "peach schnapps": "Peach Liqueur",
    "crème de pêche": "Peach Liqueur",
    "creme de peche": "Peach Liqueur",
    "disaronno": "Amaretto",

    # ליקרים עשבוניים ואניס
    "yellow chartreuse": "Yellow Chartreuse",
    "green chartreuse": "Green Chartreuse",
    "benedictine": "Bénédictine",
    "elderflower liqueur": "Elderflower Liqueur",
    "st germain": "Elderflower Liqueur",
    "st. germain": "Elderflower Liqueur",
    "pernod": "Absinthe",
    "pastis": "Absinthe",
    "ricard": "Absinthe",
    "herbsaint": "Absinthe",

    # סודה ומים מוגזים
    "club soda": "Soda Water",
    "sparkling water": "Soda Water",
    "carbonated water": "Soda Water",

    # סוכר לבן (מוצק)
    "sugar cube": "Sugar",
    "white sugar": "Sugar",
    "powdered sugar": "Sugar",
    "caster sugar": "Sugar",
    "granulated sugar": "Sugar",

    # ביצים, שמנת ומחיות פרי
    "white of one egg": "Egg White",
    "fresh egg white": "Egg White",
    "aquafaba": "Egg White",
    "chickpea water": "Egg White",
    "heavy cream": "Cream",
    "fresh cream": "Cream",
    "single cream": "Cream",
    "cream of coconut": "Coconut Cream", 
    "coco lopez": "Coconut Cream",
    "white peach puree": "Peach Puree",
    "white peach purée": "Peach Puree",
    "peach puree": "Peach Puree",
    "peach purée": "Peach Puree",
    "passion fruit purée": "Passion Fruit Puree",

    # ביטרס
    "angostura aromatic bitters": "Angostura Bitters",
    "aromatic bitters": "Angostura Bitters",

    # ברנדי וקוניאק
    "calvados": "Apple Brandy",
    "applejack": "Apple Brandy",
    "pisco": "Pisco",
    "Apricot Brandy": "Apricot Brandy",
    "cognac vsop": "Cognac",
    "cognac v.s.o.p.": "Cognac",
    
    # וודקה
    "Smirnoff Vodka": "Vodka",
    "citron vodka": "Vodka",
    "absolut citron": "Vodka",
    "lemon vodka": "Vodka",
    
    # מבעבעים
    "champagne": "Sparkling Wine",
    "prosecco": "Sparkling Wine",
    "cava": "Sparkling Wine"
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