import logic
from thefuzz import fuzz, process

# Test the Hebrew typo scenario
heb_ingredients = logic._load_hebrew_ingredients()
test_word = "וודקא"  # typo for וודקה

print(f"Input word: {test_word}")
print(f"Hebrew ingredients loaded: {len(heb_ingredients)}")

result = process.extractOne(test_word, heb_ingredients, scorer=fuzz.ratio)
print(f"extractOne result: {result}")

# Test full correct_query flow
corrected = logic.correct_query("וודקא")
print(f"correct_query result: '{corrected}'")

# Also test a working case
corrected2 = logic.correct_query("וודקה")
print(f"correct_query('וודקה') result: '{corrected2}'")
