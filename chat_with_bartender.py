import warnings

warnings.filterwarnings("ignore")

import chromadb
import requests
import json
import re
import pickle
import numpy as np
from thefuzz import fuzz, process
from rank_bm25 import BM25Okapi
import logic


def get_db_collection():
    client = chromadb.PersistentClient(path="./cocktails_vector_db")
    return client.get_collection(name="mixology_collection")


def load_bm25_index():
    with open('bm25_index.pkl', 'rb') as f:
        return pickle.load(f)


def analyze_ingredients(cocktail_ingredients, user_words):
    """
    מפריד בין מרכיבים שיש למשתמש לבין אלו שחסרים לו.
    מחזיר רשימה של מרכיבים שחסרים.
    """
    lines = cocktail_ingredients.split('\n')
    missing_ingredients = []

    for line in lines:
        line_clean = line.strip().lower()
        if not line_clean: continue

        # בדיקה האם מילה של המשתמש קיימת בשורת המרכיב הזה
        has_ingredient = any(word in line_clean for word in user_words if len(word) > 2)
        if not has_ingredient:
            # מנקים את המקף לטובת קריאות
            missing_ingredients.append(line.replace("-", "").strip())

    return missing_ingredients


def retrieve_and_rerank_by_ingredients(bm25_data, query, top_k=4):
    user_words = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))
    if not user_words:
        return None

    # שלב 1: שולפים רשת רחבה של 30 קוקטיילים
    tokenized_query = query.lower().split()
    top_indices = np.argsort(bm25_data['bm25'].get_scores(tokenized_query))[::-1][:30]

    candidates = []
    for idx in top_indices:
        ingredients_raw = bm25_data['metadatas'][idx].get('ingredients_raw', '')
        name = bm25_data['metadatas'][idx].get('name', 'Unknown')
        doc = bm25_data['docs'][idx]

        missing_list = analyze_ingredients(ingredients_raw, user_words)

        candidates.append({
            'doc': doc,
            'name': name,
            'missing_count': len(missing_list),
            'missing_list': missing_list
        })

    # שלב 2: מיון מהכי מעט חסר להכי הרבה חסר
    candidates.sort(key=lambda x: x['missing_count'])

    # שלב 3: בונים את הקונטקסט (שומרים את המידע למודל אבל בלי פקודת ההדפסה בטרמינל)
    best_docs = []
    for c in candidates[:top_k]:
        missing_str = ", ".join(c['missing_list']) if c['missing_list'] else "None!"

        context_chunk = (
            f"Cocktail Name: {c['name']}\n"
            f"Missing Count: {c['missing_count']}\n"
            f"Missing Ingredients: {missing_str}\n"
            f"Original Data:\n{c['doc']}"
        )
        best_docs.append(context_chunk)

    # הסרנו את פקודת ההדפסה של Found X closest cocktails
    return "\n\n=== NEXT COCKTAIL ===\n\n".join(best_docs)


def chat_with_llm(user_input, context, chat_history):
    history_text = ""
    if chat_history:
        history_text = "--- Previous Conversation ---\n"
        for msg in chat_history:
            history_text += f"User's previous ingredients: {msg['user']}\nBartender's previous response:\n{msg['bartender']}\n\n"

    system_prompt = f"""You are a strict, professional AI mixologist.
    Your ONLY job is to format and present the cocktails provided in the "Context" section below.

    CRITICAL RULES:
    1. Do NOT invent new cocktails.
    2. Output EVERY SINGLE cocktail listed in the Context IN THE EXACT ORDER they appear.
    3. You MUST provide the FULL '📝 Ingredients' and '👨‍🍳 Preparation Method' for EVERY cocktail, even if the user is missing ingredients. NEVER write things like "(No recipe for this one...)".
    4. ALWAYS use milliliters (ml) for measurements.
    5. NO CHITCHAT. STOP typing when finished.

    Context:
    {context}

    For EACH cocktail in the Context, you MUST use exactly this format and nothing else:
    🍹 Cocktail Name: [Extract Name]
    📝 Ingredients:
    [List EVERY SINGLE ingredient. EVERY ingredient MUST be on a NEW LINE, starting with a dash (-)]

    👨‍🍳 Preparation Method:
    [List exactly as in the 'Original Data' section]
    --------------------------------------------------
    """

    final_prompt = f"{system_prompt}\n{history_text}\nUser's available ingredients: {user_input}\n\nTASK: Output the cocktails from the Context using the strict format above. Ensure every ingredient is on a separate line. Do not skip recipes, do not explain missing items, just output the full formatted recipes and STOP."

    payload = {
        "model": "llama3",
        "prompt": final_prompt,
        "stream": True
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True)
        if response.status_code != 200: return ""

        print("\nBartender: \n", end="", flush=True)
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                word = chunk.get("response", "")
                print(word, end="", flush=True)
                full_response += word
        print("\n")
        return full_response
    except requests.exceptions.ConnectionError:
        print("\n[Connection Error]: Could not connect to Ollama.")
        return ""


if __name__ == "__main__":
    try:
        bm25_data = load_bm25_index()
        # טוענים את רשימות המרכיבים דרך logic (דו-לשוני)
        logic._load_english_ingredients()
        logic._load_hebrew_ingredients()
    except FileNotFoundError:
        print("Error: Missing database. Run 'build_vector_db.py' first.")
        exit()

    print("\n" + "=" * 50)
    print("🍸 Welcome to the AI Bartender (Ingredient Matching Mode)! 🍸")
    print("List the ingredients you have, and I'll find what you can make.")
    print("=" * 50)

    chat_history = []

    while True:
        user_input = input("\nYou (Ingredients): ")
        if user_input.lower() in ['quit', 'exit']:
            break

        # תיקון שגיאות כתיב דו-לשוני (אנגלית + עברית) דרך logic
        final_query = logic.correct_query(user_input)

        context = retrieve_and_rerank_by_ingredients(bm25_data, final_query, top_k=4)  # אפשר לשחק עם המספר הזה

        if not context:
            context = "No closely matching recipes found."

        ai_response = chat_with_llm(user_input, context, chat_history)

        if ai_response:
            chat_history.append({"user": final_query, "bartender": ai_response})
            if len(chat_history) > 3: chat_history.pop(0)