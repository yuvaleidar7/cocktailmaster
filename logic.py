import pickle
import numpy as np
import re
import difflib
from thefuzz import fuzz, process

# ====================================================================
# הגדרות וקבועים
# ====================================================================

# מילים שאינן מרכיבים ממשיים — מסוננות כדי למנוע רעש בחיפוש
_FILLER_WORDS = {
    'fresh', 'freshly', 'squeezed', 'dash', 'dashes', 'drops', 'drop',
    'fill', 'top', 'splash', 'slice', 'slices', 'sliced', 'wedges',
    'spoon', 'spoons', 'tsp', 'teaspoon', 'teaspoons', 'tablespoon',
    'pinch', 'few', 'small', 'thin', 'whole', 'optional', 'cut',
    'plain', 'raw', 'into', 'with', 'and', 'the', 'pcs', 'size',
    'chilled', 'powdered', 'superfine', 'granulated', 'cube',
    'sheets', 'dots', 'replace', 'serve', 'mix', 'blended',
    'quarter', 'three', 'between', 'juice', 'syrup'
}

# מיפוי עברית למרכיבים המדויקים כפי שהם מופיעים ב-CSV שלך
_HEBREW_TO_CSV_ENGLISH = {
    "וודקה": "vodka",
    "ג'ין": "dry gin",
    "רום לבן": "white rum",
    "רום מיושן": "aged rum",
    "רום כהה": "jamaican dark rum",
    "רום זהוב": "gold puerto rican rum",
    "טקילה": "tequila",
    "מזקל": "espadin mezcal",
    "ברבון": "bourbon whiskey",
    "וויסקי שיפון": "rye whiskey",
    "קוניאק": "cognac",
    "קמפרי": "campari",
    "אפרול": "aperol",
    "קואנטרו": "cointreau",
    "טריפל סק": "triple sec",
    "ליקר קפה": "kahlúa",
    "אמרטו": "amaretto",
    "ורמוט מתוק": "sweet red vermouth",
    "ורמוט יבש": "dry vermouth",
    "מיץ לימון": "lemon juice",
    "מיץ ליים": "lime juice",
    "מי סוכר": "simple syrup",
    "גרנדין": "grenadine",
    "אנגוסטורה ביטרס": "angostura bitters",
    "חלבון ביצה": "egg white",
    "סודה": "soda water"
}

# ====================================================================
# מנגנון תיקון שגיאות ותרגום
# ====================================================================

def _contains_hebrew(text: str) -> bool:
    return bool(re.search(r'[\u05d0-\u05ea]', text))

def correct_query(raw_query: str) -> str:
    """מעבד את הקלט: מתקן עברית לערכי ה-CSV או מנקה קלט באנגלית."""
    if _contains_hebrew(raw_query):
        words = re.findall(r"[\u05d0-\u05ea'\"]+", raw_query)
        translated = []
        for w in words:
            # ניסיון התאמה למילון העברי
            match = process.extractOne(w, _HEBREW_TO_CSV_ENGLISH.keys(), scorer=fuzz.ratio)
            if match and match[1] >= 80:
                translated.append(_HEBREW_TO_CSV_ENGLISH[match[0]])
            else:
                translated.append(w)
        return ", ".join(translated)
    return raw_query.lower()

# ====================================================================
# שליפת קוקטיילים מתוך ה-BM25 (נתוני ה-CSV)
# ====================================================================

def load_bm25_index():
    with open('bm25_index.pkl', 'rb') as f:
        return pickle.load(f)

def retrieve_candidates(bm25_data, query, top_k=4):
    """
    חיפוש קוקטיילים המבוסס על מילים בודדות בתוך המרכיבים.
    ממיין לפי: 1. מקסימום התאמה למרכיבי המשתמש. 2. מינימום מרכיבים נוספים נדרשים.
    """
    # פיצול המרכיבים שהגיעו מה-JS (מופרדים בפסיקים)
    user_ingredients = [ing.strip().lower() for ing in query.split(',') if ing.strip()]
    
    if not user_ingredients:
        return None, "none"

    # שלב א': שליפה ראשונית של 100 מועמדים דרך BM25 למהירות
    clean_query = re.sub(r'[^\w\s]', '', query.lower())
    tokenized_query = clean_query.split()
    scores = bm25_data['bm25'].get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:100]

    candidates = []

    for idx in top_indices:
        ingredients_raw = bm25_data['metadatas'][idx].get('ingredients_raw', '').lower()
        name = bm25_data['metadatas'][idx].get('name', 'Unknown')
        doc = bm25_data['docs'][idx]

        # בדיקה כמה מרכיבים מהמשתמש נמצאים במתכון
        # הלוגיקה: כל המילים של המרכיב (למשל "gold" ו-"rum") חייבות להופיע בשורת המרכיבים
        matched_from_user = []
        for u_ing in user_ingredients:
            u_words = u_ing.split()
            if all(word in ingredients_raw for word in u_words):
                matched_from_user.append(u_ing)
        
        match_count = len(matched_from_user)
        
        if match_count > 0:
            # הערכת כמות המרכיבים הכוללת במתכון (לפי שורות או פסיקים)
            total_in_recipe = len([i for i in re.split(r'[\n,]', ingredients_raw) if i.strip()])
            # כמה מרכיבים המשתמש צריך להוסיף כדי להכין את זה?
            additional_needed = max(0, total_in_recipe - match_count)
            
            candidates.append({
                'doc': doc,
                'name': name,
                'match_count': match_count,
                'additional_needed': additional_needed,
                'missing_user_ingredients': list(set(user_ingredients) - set(matched_from_user))
            })

    if not candidates:
        return _handle_fallback(bm25_data, top_indices, user_ingredients)

    # מיון: קודם כל מי שיש לו הכי הרבה מהמרכיבים שלי, ואז מי שהכי "קצר" (הכי פחות תוספות)
    candidates.sort(key=lambda x: (-x['match_count'], x['additional_needed']))

    best_docs = [f"Cocktail Name: {c['name']}\nOriginal Data:\n{c['doc']}" for c in candidates[:top_k]]
    best_candidate = candidates[0]
    
    if best_candidate['match_count'] == len(user_ingredients):
        return "\n\n--- NEXT CANDIDATE ---\n\n".join(best_docs), "strict"
    else:
        missing_str = ", ".join(best_candidate['missing_user_ingredients'])
        return "\n\n--- NEXT CANDIDATE ---\n\n".join(best_docs), f"partial|{missing_str}"

def _handle_fallback(bm25_data, top_indices, user_ingredients):
    """טיפול במצב שבו אין התאמה לאף מרכיב."""
    candidate_ingredients = set()
    for idx in top_indices[:20]:
        ingredients_raw = bm25_data['metadatas'][idx].get('ingredients_raw', '')
        words = set(re.findall(r'\b[a-z]{3,}\b', ingredients_raw.lower()))
        candidate_ingredients.update(words - _FILLER_WORDS)

    suggestions = []
    for uw in user_ingredients:
        for word in uw.split():
            close = difflib.get_close_matches(word, candidate_ingredients, n=1, cutoff=0.4)
            if close: suggestions.append(close[0])

    suggestions_str = ", ".join(list(set(suggestions))[:3]) if suggestions else "similar items"
    fallback_docs = [f"Cocktail Name: {bm25_data['metadatas'][i].get('name', 'Unknown')}\nOriginal Data:\n{bm25_data['docs'][i]}" for i in top_indices[:3]]
    return "\n\n--- NEXT CANDIDATE ---\n\n".join(fallback_docs), f"fallback|{suggestions_str}"

# ====================================================================
# יצירת תשובה דרך ה-LLM
# ====================================================================

def stream_llm_response(client, user_input, context, chat_history, match_type="strict"):
    # 1. הוספנו הוראה מפורשת לגבי פורמט השם של הקוקטייל
    system_prompt = (
        "You are a professional AI Mixologist. Your knowledge is strictly limited to the provided context. "
        "Use the recipes EXACTLY as they appear, and translate the ingredients, measurements, and instructions to Hebrew. "
        "IMPORTANT: For the cocktail name, you MUST write the Hebrew name and add the original English name in parentheses next to it. Example: **מרגריטה (Margarita)**. "
        "Do not invent ingredients or measurements. Format using Markdown with bold headers and bullet points."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 2. עדכון המשימות כך שיזכירו למודל את הפורמט הנדרש
    if match_type.startswith("fallback"):
        sug = match_type.split("|")[1] if "|" in match_type else "חלופות"
        prompt = f"Context:\n{context}\n\nTASK: Translate the recipes to Hebrew. Start with: 'לא מצאתי התאמה מדויקת. על בסיס מרכיבים דומים (**{sug}**), נסו את הקוקטיילים הבאים:'. Remember the name format: Hebrew (English)."
    elif match_type.startswith("partial"):
        missing = match_type.split("|")[1] if "|" in match_type else "כמה מרכיבים"
        prompt = f"Context:\n{context}\n\nTASK: Translate the recipes to Hebrew. Start with: 'אין התאמה מדויקת עבור **{missing}**. עם זאת, הנה מתכונים שמשתמשים בשאר המרכיבים שלכם:'. Remember the name format: Hebrew (English)."
    else:
        prompt = f"Context:\n{context}\n\nTASK: Format these exact cocktails perfectly. Translate ingredients and instructions to Hebrew. Format the title as: Hebrew Name (English Name)."
        
    messages.append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,
    )

    for chunk in completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content