import pandas as pd
import re


def clean_and_transform_cocktails(file_path):
    print(f"1. Loading raw data from {file_path}...")
    df = pd.read_csv(file_path, encoding='utf-8')

    # במקרה וחסרות עמודות מסוימות, נמלא בערכי ברירת מחדל
    if 'Preparation' not in df.columns:
        df['Preparation'] = "Combine all ingredients and mix well."
    else:
        df['Preparation'] = df['Preparation'].fillna("Combine all ingredients and mix well.")

    if 'Glassware' not in df.columns:
        df['Glassware'] = "Standard Glass"
    else:
        df['Glassware'] = df['Glassware'].fillna("Standard Glass")

    print("2. Parsing and converting measurements to ml...")

    def convert_measurements(text):
        if not isinstance(text, str): return text

        # המרה קשיחה מאונקיות למיליליטרים
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