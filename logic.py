import pickle
import numpy as np
import re
import difflib
import os
from thefuzz import fuzz, process
import groq  
from rank_bm25 import BM25Okapi # הוספתי את הייבוא הזה כדי שהחיפוש יעבוד
import ast

# ====================================================================
# API Key Rotation Configuration
# ====================================================================
_CURRENT_KEY_IDX = 0
# ====================================================================
# Constants & Weighting Configurations
# ====================================================================

_FILLER_WORDS = {
    'fresh', 'freshly', 'squeezed', 'dash', 'dashes', 'drops', 'drop',
    'fill', 'top', 'splash', 'slice', 'slices', 'sliced', 'wedges',
    'spoon', 'spoons', 'tsp', 'teaspoon', 'teaspoons', 'tablespoon',
    'pinch', 'few', 'small', 'thin', 'whole', 'optional', 'cut',
    'plain', 'raw', 'into', 'with', 'and', 'the', 'pcs', 'size',
    'chilled', 'powdered', 'superfine', 'granulated', 'cube',
    'sheets', 'dots', 'replace', 'serve', 'mix', 'blended',
    'quarter', 'three', 'between', 'or', 'can', 'be'
}

_INGREDIENT_SYNONYMS = {
    # סירופים וממתיקים
    "demerara sugar syrup": "sugar syrup",
    "rich simple syrup": "sugar syrup",
    "simple syrup": "sugar syrup",
    "sugar syrup": "sugar syrup",
    "demerara syrup": "sugar syrup",
    "gomme syrup": "sugar syrup",
    "gum syrup": "sugar syrup",
    "agave syrup": "agave",
    "agave nectar": "agave",
    "passion fruit syrup": "passion fruit syrup",
    "maple syrup": "maple syrup",
    "Agave": "Agave Nectar(sugar syrup)",

    
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
    "Blended Whiskey": "whisky",
    "single malt scotch": "whiskey",
    "single malt": "whiskey",
    "bourbon": "whiskey",
    "rye": "whiskey",
    "scotch": "whiskey",
    "lagavulin 16y": "smoked whisky",
    "lagavulin 16": "smoked whisky",
    "lagavulin": "smoked whisky",
    

    # ליקרי תפוז
    "cointreau": "orange liqueur",
    "triple sec": "orange liqueur",
    "grand marnier": "orange liqueur",
    "orange curaçao": "orange liqueur",

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
    
    "Goslings Rum": "black rum",

    "Jamaican dark rum": "dark rum",
    "Gold Puerto Rican rum": "dark rum",
    "Gold Jamaican Rum":"dark rum",
    "Aged Rum":"dark rum",
    "dark jamaican rum": "dark rum",
    "añejo rum": "dark rum",
    "añejo rum": "dark rum",
    "Demerara Rum": "dark rum",




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

    # ליקרי שוקולד / קקאו
    "white crème de cacao": "white chocolate liqueur",
    "white creme de cacao": "white chocolate liqueur",
    "dark crème de cacao": "chocolate liqueur",
    "dark creme de cacao": "chocolate liqueur",
    "crème de cacao": "chocolate liqueur",
    "creme de cacao": "chocolate liqueur",

    # ליקרי דובדבנים
    "maraschino liqueur": "maraschino cherry liqueur",
    "Maraschino Cherry Liqueur Luxardo": "cherry liqueur(Luxardo Maraschino)",
    "maraschino": "cherry liqueur(Luxardo Maraschino)",
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
    "white of one egg": "egg white",
    "fresh egg white": "egg white",
    "aquafaba": "egg white",
    "chickpea water": "egg white",
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

_WEIGHT_CATEGORIES = {
    "base_spirits": {
        "words": ['vodka', 'gin', 'rum', 'tequila', 'mezcal', 'whiskey', 'blended', 'single', 'malt', 'cognac', 'brandy', 'pisco', 'calvados', 'grappa', 'cachaça', 'cachaca', 'smoked'],
        "multiplier": 5
    },
    "liqueurs_wine": {
        "words": ['campari', 'aperol', 'amaretto', 'coffee', 'liqueur', 'drambuie', 'chartreuse', 'crème', 'fernet', 'bénédictine', 'nonino', 'schnapps', 'vermouth', 'lillet', 'champagne', 'prosecco', 'wine', 'port', 'sherry', 'absinthe', 'pernod', 'orange', 'chocolate', 'mint', 'cherry', 'peach', 'elderflower'],
        "multiplier": 4
    },
    "syrups_sweets": {
        "words": ['sugar', 'syrup', 'grenadine', 'honey', 'agave', 'orgeat', 'caramel', 'simple', 'maple', 'passion'],
        "multiplier": 3
    },
    "juices_mixers": {
        "words": ['lemon', 'lime', 'orange', 'grapefruit', 'pineapple', 'cranberry', 'tomato', 'juice', 'soda', 'tonic', 'cola', 'ginger', 'beer', 'ale', 'milk', 'cream', 'coconut', 'water', 'espresso'],
        "multiplier": 2
    },
    "bitters_garnishes_misc": {
        "words": ['bitters', 'angostura', 'peychauds', 'mint', 'basil', 'rosemary', 'salt', 'pepper', 'egg', 'white', 'olive', 'cherry', 'celery', 'twist', 'aquafaba'],
        "multiplier": 1
    }
}

def get_ingredient_weight(ingredient_name: str) -> int:
    """מוצא את המשקל הגבוה ביותר עבור המרכיב לפי הקטגוריות"""
    words = re.sub(r'[^\w\s]', '', ingredient_name.lower()).split()
    max_weight = 0
    for cat, data in _WEIGHT_CATEGORIES.items():
        if any(word in data["words"] for word in words):
            max_weight = max(max_weight, data["multiplier"])
    
    return max_weight if max_weight > 0 else 1

# ====================================================================
# Helper Functions 
# ====================================================================

def correct_query(raw_query: str) -> str:
    return raw_query.lower()

def apply_hierarchical_weights(tokenized_query):
    boosted_query = []
    for word in tokenized_query:
        multiplier = 1
        for cat, data in _WEIGHT_CATEGORIES.items():
            if word in data["words"]:
                multiplier = data["multiplier"]
                break
        boosted_query.extend([word] * multiplier)
    return boosted_query

def _get_image_markdown(metadata):
    image_path_raw = metadata.get('image_path', 'No Image')
    if image_path_raw and image_path_raw != "No Image":
        # 1. קח רק את שם הקובץ (ללא נתיבים)
        filename = os.path.basename(image_path_raw)
        
        # 2. ניקוי אגרסיבי במקרה ש-basename לא הסיר את התיקייה
        # (למשל אם הנתיב היה מורכב או בפורמט שונה)
        filename = filename.replace('cocktail_images/', '')
        filename = filename.replace('cocktail_images\\', '') # עבור Windows אם קיים
        
        return f"![{metadata.get('name', 'Cocktail')}](/images/{filename})"
    return ""

# ====================================================================
# BM25 Candidate Retrieval
# ====================================================================

def load_bm25_index():
    with open('bm25_index.pkl', 'rb') as f:
        return pickle.load(f)
    
def count_recipe_ingredients(raw_ingredients_str):
    """
    פונקציה לספירת מרכיבים שמתמודדת עם נתונים 'מלוכלכים' במבנים שונים
    """
    if not raw_ingredients_str:
        return 1
        
    # שלב 1: ניקוי שבירות שורה שקודדו כמחרוזת בתוך ה-DB
    clean_str = raw_ingredients_str.replace('\\n', '\n').replace('\\r', '')
    
    # שלב 2: ניסיון לפענח אם הנתון נשמר כ-String של רשימה: "['Rum', 'Lime']"
    try:
        parsed_list = ast.literal_eval(clean_str)
        if isinstance(parsed_list, list):
            return len(parsed_list)
    except (ValueError, SyntaxError):
        pass
        
    # שלב 3: פיצול אגרסיבי לפי כל סוגי המפרידים הנפוצים (פסיק, שורה חדשה, נקודה פסיק או HTML)
    parts = [p.strip() for p in re.split(r',|\n|;|<br/?>', clean_str) if p.strip()]
    
    # שלב 4: אם זה עדיין בלוק אחד ארוך, ננסה לחתוך לפי המילה AND או לפי מקפים של Bullet points
    if len(parts) <= 1 and len(clean_str) > 20:
        parts = [p.strip() for p in re.split(r'\band\b|\&| - ', clean_str) if len(p.strip()) > 2]
        
    return max(len(parts), 1)
def _handle_fallback(bm25_data, top_indices, user_ingredients):
    """
    מנגנון חלופי (Fallback) למקרה שלא נמצאה אף התאמה למרכיבים שהוזנו.
    מחזיר את 3 התוצאות המובילות של BM25 כהמלצות כלליות.
    """
    # לוקחים את 3 התוצאות הראשונות (אלו עם סקור ה-BM25 הגבוה ביותר)
    fallback_indices = top_indices[:3]
    
    context_docs = []
    for idx in fallback_indices:
        meta = bm25_data['metadatas'][idx]
        img_md = _get_image_markdown(meta)
        
        context_docs.append(
            f"Match: 0% (Fallback)\n"
            f"Cocktail Name: {meta.get('name', 'Unknown')}\n"
            f"Image Markdown: {img_md}\n"
            f"Original Data:\n{bm25_data['docs'][idx]}"
        )
        
    # מייצרים את מחרוזת ה-match_type שתאותת ל-LLM לעבור לניסוח של חלופות
    ingredients_str = ', '.join(user_ingredients) if user_ingredients else "your ingredients"
    match_type = f"fallback|{ingredients_str}"
    
    return "\n\n--- NEXT CANDIDATE ---\n\n".join(context_docs), match_type

def retrieve_candidates(bm25_data, query, top_k=102):
    # נרמול השאילתה של המשתמש לפני הכל
    query_normalized = query.lower()
    for specific, generic in _INGREDIENT_SYNONYMS.items():
        pattern = re.compile(r'\b' + re.escape(specific) + r'\b')
        query_normalized = pattern.sub(generic, query_normalized)
    
    user_ingredients = [ing.strip() for ing in query_normalized.split(',') if ing.strip()]
    if not user_ingredients:
        return None, "none"

    clean_query = re.sub(r'[^\w\s]', '', query_normalized)
    tokenized_query = clean_query.split()
    tokenized_query = [w for w in tokenized_query if w not in _FILLER_WORDS]
    
    boosted_query = apply_hierarchical_weights(tokenized_query)
    
    corpus_tokens = [re.sub(r'[^\w\s]', '', doc).lower().split() for doc in bm25_data['docs']]
    bm25 = BM25Okapi(corpus_tokens)
    doc_scores = bm25.get_scores(boosted_query)
    top_indices = np.argsort(doc_scores)[::-1]
    
    results = []
    best_overall_match_count = 0
    
    for idx in top_indices[:top_k]:
        raw_ingredients = bm25_data['metadatas'][idx].get('ingredients_raw', '')
        
        # 1. ספירה אגרסיבית מבוססת יחידות מידה (מתעלם מפסיקים ושורות)
        # מחפש מספרים שצמודים למידות כמו ml, oz, dash, pcs וכו'
        measurements = re.findall(r'\b\d+(?:[./]\d+)?\s*(?:ml|oz|dash|dashes|drop|drops|tsp|tbsp|pcs|leaves|cl|part|parts|slice|wedge)\b', raw_ingredients, re.IGNORECASE)
        
        normalized_str = raw_ingredients.replace('\\n', ',').replace('\n', ',').replace(';', ',').replace('<br>', ',')
        comma_separated = [ing.strip() for ing in normalized_str.split(',') if len(ing.strip()) > 2]
        
        # לוקחים את המספר הגבוה מבין השניים כדי להבטיח שלא נפספס מרכיבים
        total_recipe_ingredients = max(len(measurements), len(comma_separated))
        
        if total_recipe_ingredients == 0:
            total_recipe_ingredients = 1 # הגנה מקריסה
            
        recipe_ingredients = raw_ingredients.lower()
        current_matched = []
        current_missing = []
        
        # 2. בדיקה כמה מרכיבים מצאנו בפועל מתוך מה שהמשתמש הקליד
        for u_ing in user_ingredients:
            if fuzz.token_set_ratio(u_ing, recipe_ingredients) >= 80:
                current_matched.append(u_ing)
            else:
                current_missing.append(u_ing)
                
        # 3. חישוב האחוז האמיתי
        match_pct = int((len(current_matched) / total_recipe_ingredients) * 100)
        match_pct = min(match_pct, 100) # הגנה ממעבר של 100%
        
        # --- הדפסת דיבאג לטרמינל שלך כדי שנוכל לראות בדיוק מה קורה ---
        cocktail_name = bm25_data['metadatas'][idx].get('name', 'Unknown')
        print(f"DEBUG: {cocktail_name} | Matched: {len(current_matched)} | Total Ing: {total_recipe_ingredients} | Pct: {match_pct}%")
        
        best_overall_match_count = max(best_overall_match_count, len(current_matched))
        
        results.append({
            'idx': idx,
            'match_pct': match_pct,
            'missing': current_missing,
            'total_recipe_ingredients': total_recipe_ingredients,
            'bm25_score': doc_scores[idx]
        })

    # === סינון, מיון והחזרת נתונים לאפליקציה ===
    
    # סינון: שומרים רק תוצאות עם יותר מ-0% התאמה
    valid_results = [res for res in results if res['match_pct'] > 0]
    
    # מיון: אחוז התאמה הכי גבוה קודם, ואז לפי מינימום מרכיבים חסרים, ואז סקור של BM25
    valid_results.sort(key=lambda x: (
        x['match_pct'], 
        -x['total_recipe_ingredients'], 
        x['bm25_score']
    ), reverse=True)

    # חותכים בחזרה ל-4 התוצאות הטובות ביותר כדי לא להעמיס על ה-LLM
    final_top_results = valid_results[:4]

    # אם אחרי הסינון לא נשארו תוצאות רלוונטיות, עוברים ל-Fallback
    if not final_top_results:
         return _handle_fallback(bm25_data, top_indices, user_ingredients)
    
    # החלטה על סוג המענה (Match Type) עבור הפרומפט של ה-LLM
    if best_overall_match_count == len(user_ingredients):
        match_type = "strict"
    else:
        # לוקחים את הקוקטייל עם האחוז הכי גבוה (הראשון ברשימה הממוינת והמסוננת)
        match_type = f"partial|{', '.join(final_top_results[0]['missing'])}"
        
    # בניית הקונטקסט ל-LLM מתוך 4 התוצאות המובילות בלבד
    context_docs = []
    for res in final_top_results:
        meta = bm25_data['metadatas'][res['idx']]
        img_md = _get_image_markdown(meta)
        
        context_docs.append(
            f"Match: {res['match_pct']}%\n"
            f"Cocktail Name: {meta.get('name', 'Unknown')}\n"
            f"Image Markdown: {img_md}\n"
            f"Original Data:\n{bm25_data['docs'][res['idx']]}"
        )
        
    return "\n\n--- NEXT CANDIDATE ---\n\n".join(context_docs), match_type
# ====================================================================
# LLM Response Generation
# ====================================================================

def stream_llm_response(client_unused, user_input, context, chat_history, match_type="strict"):
    global _CURRENT_KEY_IDX

    system_prompt = (
        "You are an expert, high-end AI Mixologist. Your task is to present cocktail recipes perfectly in English.\n"
        "CRITICAL RULE: Your knowledge is strictly limited to the provided context. You MUST NOT use outside knowledge to modify, expand, or guess ingredient names. If the context says 'whiskey', you MUST write exactly 'whiskey' and NEVER autocorrect it to 'Bourbon' or 'Rye'. If it says 'tequila', do NOT add '100% Agave'. Copy the names exactly as they appear in the source.\n\n"
        "MANDATORY MARKDOWN FORMATTING RULES:\n"
        "1. Each cocktail MUST start with its title as a Markdown Level 3 header on its own fresh line. Example: ### Boulevardier\n"
        "2. The exact 'Image Markdown' string provided in the context MUST be placed on its own line directly below the title header.\n"
        "3. **NEW:** Extract the 'Match' percentage from the context and place it directly under the image like this: **Match:** 80%\n"
        "4. The ingredients MUST be formatted as a standard bulleted list, under the header '**Ingredients:**'. Every single ingredient must be on its own line starting with a hyphen and a space.\n"
        "5. The preparation steps MUST be placed under the header '**Preparation:**'.\n"
        "6. You MUST use DOUBLE NEWLINES (\\n\\n) between sections (Title, Image, Match, Ingredients list, Preparation) to guarantee proper HTML separation.\n\n"
        "FEW-SHOT EXAMPLE FOR STYLE:\n"
        "### Sea Breeze\n"
        "![Sea Breeze](/images/sea_breeze.jpg)\n"
        "**Match:** 100%\n\n"
        "**Ingredients:**\n"
        "- 40 ml Vodka\n"
        "- 120 ml Cranberry Juice\n"
        "- 30 ml Grapefruit Juice\n\n"
        "**Preparation:**\n"
        "Pour all ingredients into a highball glass filled with ice, stir gently and serve."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    if match_type.startswith("fallback"):
        sug = match_type.split("|")[1] if "|" in match_type else "similar items"
        prompt = f"Context:\n{context}\n\nTASK: Start your response with exactly this line: 'I could not find an exact match. Based on similar items (**{sug}**), try these cocktails:'. Then apply the MANDATORY MARKDOWN FORMATTING RULES."
    elif match_type.startswith("partial"):
        missing = match_type.split("|")[1] if "|" in match_type else "some items"
        prompt = f"Context:\n{context}\n\nTASK: Start your response with exactly this line: 'No exact match found for **{missing}**. However, here are recipes based on your other base spirits and ingredients:'. Then apply the MANDATORY MARKDOWN FORMATTING RULES."
    else:
        prompt = f"Context:\n{context}\n\nTASK: Format and present these exact cocktails perfectly. Strictly apply the MANDATORY MARKDOWN FORMATTING RULES."
        
    messages.append({"role": "user", "content": prompt})

    # משיכת המפתחות בצורה דינמית בתוך הפונקציה עם השמות המעודכנים שלך
    keys_pool = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY")]
    keys_pool = [k for k in keys_pool if k] # מסנן ערכים ריקים או None
    
    # הגנה: אם מסיבה כלשהי לא נטענו מפתחות בכלל
    if not keys_pool:
        yield "\n\n⚠️ Configuration Error: No API keys were found in the environment."
        return

    # מוודא שהאינדקס הנוכחי לא חורג מגודל המערך
    if _CURRENT_KEY_IDX >= len(keys_pool):
        _CURRENT_KEY_IDX = 0

    for attempt in range(len(keys_pool)):
        try:
            active_key = keys_pool[_CURRENT_KEY_IDX]
            local_client = groq.Groq(api_key=active_key)

            completion = local_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True,
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return  

        except groq.RateLimitError:
            print(f"⚠️ API Key number {_CURRENT_KEY_IDX + 1} rate limited (429). Switching to the next key...")
            # עדכון למפתח הבא בסבב
            _CURRENT_KEY_IDX = (_CURRENT_KEY_IDX + 1) % len(keys_pool)
            
        except Exception as e:
            # תופס גם שגיאות רשת אחרות
            print(f"⚠️ Unexpected error with API Key {_CURRENT_KEY_IDX + 1}: {e}")
            _CURRENT_KEY_IDX = (_CURRENT_KEY_IDX + 1) % len(keys_pool)

    yield "\n\n⚠️ Error: All available API keys have reached their limits or failed. Please try again later."