import pickle
import numpy as np
import re
import difflib
import os
from thefuzz import fuzz, process
import groq  
from rank_bm25 import BM25Okapi 
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

_WEIGHT_CATEGORIES = {
    "flavor_profiles": {
        "words": ['sweet', 'sour', 'bitter', 'spicy', 'dry', 'spiritforward', 'spirit-forward'],
        "multiplier": 4  
    },
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
        filename = os.path.basename(image_path_raw)
        filename = filename.replace('cocktail_images/', '')
        filename = filename.replace('cocktail_images\\', '') 
        return f"![{metadata.get('name', 'Cocktail')}](/images/{filename})"
    return ""

# ====================================================================
# BM25 Candidate Retrieval
# ====================================================================

def load_bm25_index():
    with open('bm25_index.pkl', 'rb') as f:
        return pickle.load(f)
    
def count_recipe_ingredients(raw_ingredients_str):
    if not raw_ingredients_str:
        return 1
        
    clean_str = raw_ingredients_str.replace('\\n', '\n').replace('\\r', '')
    
    try:
        parsed_list = ast.literal_eval(clean_str)
        if isinstance(parsed_list, list):
            return len(parsed_list)
    except (ValueError, SyntaxError):
        pass
        
    parts = [p.strip() for p in re.split(r',|\n|;|<br/?>', clean_str) if p.strip()]
    
    if len(parts) <= 1 and len(clean_str) > 20:
        parts = [p.strip() for p in re.split(r'\band\b|\&| - ', clean_str) if len(p.strip()) > 2]
        
    return max(len(parts), 1)

def _handle_fallback(bm25_data, top_indices, user_ingredients):
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
        
    ingredients_str = ', '.join(user_ingredients) if user_ingredients else "your ingredients"
    match_type = f"fallback|{ingredients_str}"
    
    return "\n\n--- NEXT CANDIDATE ---\n\n".join(context_docs), match_type

def retrieve_candidates(bm25_data, base_spirits, other_ingredients, flavor="All", top_k=4):
    # 1. פונקציית עזר לנרמול טקסט (הוצאנו אותה למחרוזת בודדת כדי להפעיל אותה גם על מסד הנתונים)
    def normalize_text(text):
        norm_text = text.lower()
        for specific, generic in _INGREDIENT_SYNONYMS.items():
            # מתרגם מותגים ספציפיים לשמות גנריים כדי שהמערכת תדבר באותה שפה
            norm_text = re.sub(r'\b' + re.escape(specific) + r'\b', generic, norm_text)
        return norm_text.strip()
        
    def normalize_list(ing_list):
        return [normalize_text(ing) for ing in ing_list]

    norm_base_spirits = normalize_list(base_spirits)
    norm_other_ingredients = normalize_list(other_ingredients)
    all_user_ingredients = norm_base_spirits + norm_other_ingredients
    
    if not all_user_ingredients and flavor != "All":
        flavor_matches = []
        for idx, meta in enumerate(bm25_data['metadatas']):
            recipe_flavor = str(meta.get('taste', meta.get('flavor', meta.get('flavor_profile', '')))).lower()
            if flavor.lower() in recipe_flavor:
                flavor_matches.append(idx)
        
        if not flavor_matches:
            return None, "none"
            
        top_indices = flavor_matches[:4]
        context_docs = []
        for idx in top_indices:
            meta = bm25_data['metadatas'][idx]
            img_md = _get_image_markdown(meta)
            
            # התיקון: שליפת הטעם המדויק של הקוקטייל מה-meta גם בחיפוש לפי טעם
            flavor_profile = str(meta.get('taste', meta.get('flavor', meta.get('flavor_profile', 'Not specified')))).title()
            
            context_docs.append(
                f"Match: 100%\n" 
                f"Flavor Profile: {flavor_profile}\n"
                f"Cocktail Name: {meta.get('name', 'Unknown')}\n"
                f"Image Markdown: {img_md}\n"
                f"Original Data:\n{bm25_data['docs'][idx]}"
            )
        return "\n\n--- NEXT CANDIDATE ---\n\n".join(context_docs), f"flavor_only|{flavor}"

    clean_query = re.sub(r'[^\w\s]', '', " ".join(all_user_ingredients))
    tokenized_query = [w for w in clean_query.split() if w not in _FILLER_WORDS]
    boosted_query = apply_hierarchical_weights(tokenized_query)
    
    corpus_tokens = [re.sub(r'[^\w\s]', '', doc).lower().split() for doc in bm25_data['docs']]
    bm25 = BM25Okapi(corpus_tokens)
    doc_scores = bm25.get_scores(boosted_query) if boosted_query else np.zeros(len(bm25_data['docs']))

    # ==========================================
    # 3. שלב הסינון הקשיח (Strict Hard Filtering)
    # ==========================================
    valid_indices = []
    for idx, meta in enumerate(bm25_data['metadatas']):
        if flavor != "All":
            recipe_flavor = str(meta.get('taste', meta.get('flavor', meta.get('flavor_profile', '')))).lower()
            if flavor.lower() not in recipe_flavor:
                continue 

        if norm_base_spirits:
            # התיקון: אנחנו מנרמלים את הרכיבים של הקוקטייל ממסד הנתונים לפני הבדיקה!
            raw_ingredients_norm = normalize_text(meta.get('ingredients_raw', ''))
            has_base = False
            for bs in norm_base_spirits:
                if bs in raw_ingredients_norm:
                    has_base = True
                    break
            if not has_base:
                continue 

        valid_indices.append(idx)
        
    if not valid_indices:
        return None, "none"

    # ==========================================
    # 4. חישוב אחוזים מבוסס משקולות (Weighted Scoring - Updated Jaccard + Penalty)
    # ==========================================
    results = []
    best_overall_match_count = 0
    
    for idx in valid_indices:
        meta = bm25_data['metadatas'][idx]
        raw_ingredients = meta.get('ingredients_raw', '').lower()
        
        # יצירת גרסה מנורמלת של המתכון לבדיקת חיתוכים מדוייקת יותר
        raw_ingredients_norm = normalize_text(raw_ingredients)
        
        measurements = re.findall(r'\b\d+(?:[./]\d+)?\s*(?:ml|oz|dash|dashes|drop|drops|tsp|tbsp|pcs|leaves|cl|part|parts|slice|wedge)\b', raw_ingredients)
        normalized_str = raw_ingredients.replace('\\n', ',').replace('\n', ',').replace(';', ',').replace('<br>', ',')
        comma_separated = [ing.strip() for ing in normalized_str.split(',') if len(ing.strip()) > 2]
        
        # התיקון: נרמול רשימת הרכיבים המפורקת, כדי שמשקאות הבסיס יקבלו את המשקל הגבוה הראוי להם
        comma_separated_norm = normalize_list(comma_separated)
        
        total_recipe_ingredients = max(len(measurements), len(comma_separated))
        if total_recipe_ingredients == 0: total_recipe_ingredients = 1
            
        current_matched = []
        current_missing = [] 
        
        for u_ing in all_user_ingredients:
            # בדיקה מול המחרוזת המנורמלת של הקוקטייל
            if fuzz.token_set_ratio(u_ing, raw_ingredients_norm) >= 80 or u_ing in raw_ingredients_norm:
                current_matched.append(u_ing)
            else:
                current_missing.append(u_ing)
                
        # 1. חישוב משקל כולל של הקוקטייל (על בסיס המרכיבים המנורמלים הנדרשים)
        recipe_weight = sum(get_ingredient_weight(r_ing) for r_ing in comma_separated_norm)
        if recipe_weight == 0: recipe_weight = 1
        
        # 2. חישוב המשקל של המרכיבים התואמים שהמשתמש סימן
        matched_weight = sum(get_ingredient_weight(u_ing) for u_ing in current_matched)
        matched_weight = min(matched_weight, recipe_weight) 
        
        # 3. ספירת מרכיבים חסרים
        missing_count = max(0, total_recipe_ingredients - len(current_matched))
        
        # 4. חישוב ציון החיתוך + הפעלת קנס 
        penalty_per_missing = 0.10
        base_score = matched_weight / recipe_weight
        penalty = missing_count * penalty_per_missing
        
        final_score = base_score - penalty
        match_pct = int(max(0.0, final_score) * 100)
        
        best_overall_match_count = max(best_overall_match_count, len(current_matched))
        
        results.append({
            'idx': idx,
            'match_pct': match_pct,
            'missing': current_missing,
            'total_recipe_ingredients': total_recipe_ingredients,
            'bm25_score': doc_scores[idx],
            'matched_count': len(current_matched)
        })

    results.sort(key=lambda x: (
        x['match_pct'], 
        x['matched_count'],
        x['bm25_score']
    ), reverse=True)

    final_top_results = results[:top_k]
    
    if best_overall_match_count == len(all_user_ingredients) and all_user_ingredients:
        match_type = "strict"
    else:
        match_type = f"partial|{', '.join(final_top_results[0]['missing'])}" if final_top_results[0]['missing'] else "partial|ingredients"
        
    context_docs = []
    for res in final_top_results:
        meta = bm25_data['metadatas'][res['idx']]
        img_md = _get_image_markdown(meta)
        
        # שולפים את פרופיל הטעם מתוך ה-meta כדי להעביר בבירור למודל
        flavor_profile = str(meta.get('taste', meta.get('flavor', meta.get('flavor_profile', 'Not specified')))).title()
        
        context_docs.append(
            f"Match: {res['match_pct']}%\n"
            f"Flavor Profile: {flavor_profile}\n"
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
        "CRITICAL RULE: Your knowledge is strictly limited to the provided context. You MUST NOT use outside knowledge to modify, expand, or guess ingredient names.\n\n"
        "MANDATORY FORMATTING RULES:\n"
        "1. Each cocktail MUST start with its title as a Markdown Level 3 header (###) on a new line.\n"
        "2. To avoid rendering bugs, you MUST use HTML <strong> and <br> tags for the Match and Flavor Profile EXACTLY like this:\n"
        "   <strong>Match:</strong> [X]%<br>\n"
        "   <strong>Flavor Profile:</strong> [Flavor]\n"
        "3. CRITICAL: Do NOT use asterisks (**) for the Match or Flavor Profile lines.\n"
        "4. The exact 'Image Markdown' string provided MUST be placed directly below the Flavor Profile, separated by DOUBLE NEWLINES (\\n\\n).\n"
        "5. The ingredients MUST be formatted as a standard bulleted list, under the header '**Ingredients:**'.\n"
        "6. The preparation steps MUST be placed under the header '**Preparation:**'.\n"
        "7. You MUST use DOUBLE NEWLINES (\\n\\n) between main sections.\n\n" 
        "FEW-SHOT EXAMPLE FOR STYLE:\n"
        "### Sea Breeze\n\n"
        "<strong>Match:</strong> 100%<br>\n"
        "<strong>Flavor Profile:</strong> Sweet & Sour\n\n"
        "![Sea Breeze](/images/sea_breeze.jpg)\n\n"
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
    elif match_type.startswith("flavor_only"): 
        flavor_name = match_type.split("|")[1] if "|" in match_type else "this flavor"
        prompt = f"Context:\n{context}\n\nTASK: Start your response with exactly this line: 'Here are the best **{flavor_name}** cocktails based on your flavor profile preference:'. Then apply the MANDATORY MARKDOWN FORMATTING RULES."
    else:
        prompt = f"Context:\n{context}\n\nTASK: Format and present these exact cocktails perfectly. Strictly apply the MANDATORY MARKDOWN FORMATTING RULES."
    messages.append({"role": "user", "content": prompt})

    keys_pool = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY")]
    keys_pool = [k for k in keys_pool if k] 
    
    if not keys_pool:
        yield "\n\n⚠️ Configuration Error: No API keys were found in the environment."
        return

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
            _CURRENT_KEY_IDX = (_CURRENT_KEY_IDX + 1) % len(keys_pool)
            
        except Exception as e:
            print(f"⚠️ Unexpected error with API Key {_CURRENT_KEY_IDX + 1}: {e}")
            _CURRENT_KEY_IDX = (_CURRENT_KEY_IDX + 1) % len(keys_pool)

    yield "\n\n⚠️ Error: All available API keys have reached their limits or failed. Please try again later."