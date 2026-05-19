import pandas as pd
from deep_translator import GoogleTranslator
import time

def main():
    print("Loading data...")
    df = pd.read_csv('iba_translated.csv', encoding='utf-8')
    
    # הגדרת המתרגם מאנגלית לעברית
    translator = GoogleTranslator(source='en', target='iw')

    def translate_to_hebrew(text):
        if pd.isna(text) or str(text).strip() == "":
            return text
        
        # מנגנון ניסיון חוזר: מנסה עד 3 פעמים לתרגם את אותה שורה
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # השהיה קטנה למנוע חסימות מגוגל טרנסלייט
                time.sleep(0.4) 
                return translator.translate(str(text))
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Error translating: {text[:30]}... - {e}")
                    return text
                # אם נכשל, ממתין שנייה ומנסה שוב
                time.sleep(1)

    print("Translating Ingredients... (This might take a minute or two)")
    df['Ingredients (Hebrew)'] = df['Ingredients'].apply(translate_to_hebrew)

    print("Translating Preparation...")
    df['Preparation (Hebrew)'] = df['Preparation'].apply(translate_to_hebrew)

    output_filename = 'iba_translated_final.csv'
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print(f"Success! Fully translated file saved as '{output_filename}'")

if __name__ == "__main__":
    main()