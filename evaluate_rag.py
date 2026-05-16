import requests
import json
from chat_with_bartender import load_bm25_index, retrieve_and_rerank_by_ingredients


def generate_answer_for_eval(query, context, model="llama3"):
    """פונקציה שקטה שמחזירה את הטקסט המלא (בלי Streaming) כדי שנוכל לשפוט אותו"""
    system_prompt = (
        "You are a strict mixologist. Answer based ONLY on the provided Context. "
        "ALWAYS use milliliters (ml) for measurements.\n\n"
        f"Context:\n{context}"
    )

    payload = {
        "model": model,
        "prompt": f"{system_prompt}\n\nUser Ingredients: {query}",
        "stream": False
    }

    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return response.json()['response']


def evaluate_with_llm_judge(query, context, generated_answer, judge_model="llama3"):
    """מודל ה-AI קורא את התשובה של עצמו ומעניק לה ציונים כ'שופט'"""
    evaluation_prompt = f"""
    You are an impartial judge evaluating an AI bartender system. 
    The user provided a list of ingredients they have.

    Evaluate the AI's Answer on two metrics from 1 to 5:
    1. Ingredient Efficiency (1-5): Did the AI suggest a cocktail that relies mostly on the User's Ingredients, requiring few extra additions? (5 = perfect match, 1 = requires many extra bottles).
    2. Faithfulness (1-5): Does the Answer rely EXCLUSIVELY on the Context provided? 

    User Ingredients: "{query}"
    Retrieved Context: "{context}"
    AI Answer: "{generated_answer}"

    You MUST respond with ONLY a valid JSON object in this exact format, with no other text or markdown:
    {{
        "Ingredient_Efficiency": <int>,
        "Faithfulness": <int>,
        "Explanation": "<brief 1 sentence explanation>"
    }}
    """

    payload = {
        "model": judge_model,
        "prompt": evaluation_prompt,
        "stream": False,
        "format": "json"  # מכריח את המודל להחזיר JSON נקי
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        return json.loads(response.json()['response'])
    except Exception as e:
        return {"Ingredient_Efficiency": 0, "Faithfulness": 0, "Explanation": f"Evaluation Failed: {str(e)}"}


if __name__ == "__main__":
    print("⚖️ Starting Ingredient-Match Evaluation Pipeline...")

    # טעינת מסד הנתונים
    bm25_data = load_bm25_index()

    # שאלות המבחן שלנו מבוססות על מרכיבים
    test_queries = [
        "vodka, lime juice, ginger beer",
        "tequila, cointreau, lime",
        "rum, mint, sugar, soda"
    ]

    total_efficiency = 0
    total_faithfulness = 0

    for i, query in enumerate(test_queries):
        print(f"\n[{i + 1}/{len(test_queries)}] Testing Ingredients: '{query}'")

        # 1. שליפת מידע (Retrieval)
        context = retrieve_and_rerank_by_ingredients(bm25_data, query)
        if not context:
            print("  -> Failed to retrieve context. Skipping.")
            continue

        # 2. יצירת התשובה (Generation)
        print("  -> Generating answer...")
        answer = generate_answer_for_eval(query, context, model="llama3")

        # 3. העמדה למשפט (Evaluation)
        print("  -> Judging answer...")
        eval_scores = evaluate_with_llm_judge(query, context, answer, judge_model="llama3")

        print("  --- 🏆 Scores ---")
        print(f"  Ingredient Efficiency: {eval_scores.get('Ingredient_Efficiency')}/5")
        print(f"  Faithfulness: {eval_scores.get('Faithfulness')}/5")
        print(f"  Judge's Note: {eval_scores.get('Explanation')}")

        total_efficiency += eval_scores.get('Ingredient_Efficiency', 0)
        total_faithfulness += eval_scores.get('Faithfulness', 0)

    # סיכום ביצועי המערכת
    print("\n" + "=" * 50)
    print("📊 FINAL SYSTEM PERFORMANCE:")
    print(f"Average Ingredient Efficiency: {total_efficiency / len(test_queries):.1f} / 5.0")
    print(f"Average Faithfulness: {total_faithfulness / len(test_queries):.1f} / 5.0")
    print("=" * 50)