import pickle

with open('bm25_index.pkl', 'rb') as f:
    bm25_data = pickle.load(f)

targets = ["Bee", "Don", "Tommy", "Penicillin", "Spicy Fifty", "Three Dots"]
for meta in bm25_data['metadatas']:
    name = meta.get('name', '')
    if any(t in name for t in targets):
        print(f"--- {name} ---")
        print(repr(meta['ingredients_raw']))
