import pandas as pd
import re

# מילון ההחלפות שהגדרת
replacements = {
    # סירופים
    "demerara sugar syrup": "sugar syrup",
    "rich simple syrup": "sugar syrup",
    "simple syrup": "sugar syrup",
    "sugar syrup": "sugar syrup",
    "demerara syrup": "sugar syrup",
    
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
    "single malt scotch": "whiskey",
    "single malt": "whiskey",
    "bourbon": "whiskey",
    "rye": "whiskey",
    "scotch": "whiskey",

    # ליקרי תפוז
    "cointreau": "orange liqueur",
    "triple sec": "orange liqueur",
    "grand marnier": "orange liqueur",
    "orange curaçao": "orange liqueur",

    # ליקרי קפה
    "kahlúa": "coffee liqueur",
    "kahlua": "coffee liqueur",
    "tia maria": "coffee liqueur",

    # ג'ין
    "london dry gin": "gin",
    "plymouth gin": "gin",
    "old tom gin": "gin",

    # טקילה 
    "tequila blanco": "tequila",
    "tequila silver": "tequila",
    "tequila reposado": "tequila",
    "100% agave tequila": "tequila",
    "blanco tequila": "tequila",

    # רום
    "white cuban rum": "white rum",
    "light rum": "white rum",
    "dark jamaican rum": "dark rum",
    "añejo rum": "dark rum",

    # ורמוט
    "dry french vermouth": "dry vermouth",
    "sweet red vermouth": "sweet vermouth",

    # ליקרי שוקולד / קקאו
    "white crème de cacao": "white chocolate liqueur",
    "white creme de cacao": "white chocolate liqueur",
    "dark crème de cacao": "chocolate liqueur",
    "dark creme de cacao": "chocolate liqueur",
    "crème de cacao": "chocolate liqueur",
    "creme de cacao": "chocolate liqueur",

    # ליקרי דובדבנים
    "maraschino liqueur": "maraschino cherry liqueur",
    "maraschino": "maraschino cherry liqueur",
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

    # ליקר פטל שחור / קסיס
    "crème de cassis": "blackcurrant liqueur",
    "creme de cassis": "blackcurrant liqueur",
    "chambord": "raspberry liqueur",

    # ליקרי אפרסק
    "peach schnapps": "peach liqueur",
    "crème de pêche": "peach liqueur",
    "creme de peche": "peach liqueur",

    # ליקר שקדים
    "disaronno": "amaretto",

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

    # ביצים ושמנת 
    "white of one egg": "egg white",
    "fresh egg white": "egg white",
    "heavy cream": "cream",
    "fresh cream": "cream",
    "single cream": "cream",

    # ביטרס
    "angostura aromatic bitters": "angostura bitters",
    "aromatic bitters": "angostura bitters",

    # ברנדי וקוניאק
    "calvados": "apple brandy(calvados)",
    "applejack": "apple brandy",
    "pisco": "pisco brandy(pisco)",
    
    # מבעבעים
    "champagne": "sparkling wine",
    "prosecco": "sparkling wine",
    "cava": "sparkling wine"
}

def clean_ingredients():
    # קריאת הקובץ (וודא שהקובץ נמצא באותה תיקייה של הסקריפט)
    df = pd.read_csv('iba_live_scraped_data.csv')

    # מיון המפתחות לפי אורך יורד כדי למנוע החלפה חלקית של מונחים ארוכים
    sorted_keys = sorted(replacements.keys(), key=len, reverse=True)

    # מעבר על כל מפתח והחלפתו בעמודת ה-Ingredients
    for key in sorted_keys:
        # שימוש בביטוי רגולרי (Regex) שמתעלם מגודל האותיות (IGNORECASE)
        pattern = re.compile(re.escape(key), re.IGNORECASE)
        df['Ingredients'] = df['Ingredients'].apply(lambda x: pattern.sub(replacements[key], str(x)) if pd.notnull(x) else x)

    # שמירת התוצאה לקובץ חדש
    df.to_csv('iba_live_scraped_data_updated.csv', index=False, encoding='utf-8-sig')
    print("הקובץ עודכן ונשמר בהצלחה תחת השם: iba_live_scraped_data_updated.csv")

if __name__ == "__main__":
    clean_ingredients()