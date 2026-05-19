import chromadb
import uuid
import re
from prepare_cocktails_data import clean_and_transform_cocktails
from rank_bm25 import BM25Okapi
import pickle

def load_to_vector_db(df, db_path="./cocktails_vector_db"):
    print("\n4. Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)

    try:
        client.delete_collection(name="mixology_collection")
    except:
        pass

    collection = client.create_collection(name="mixology_collection")

    print("5. Preparing documents for embedding...")
    documents = df['Vector_Document'].tolist()

    if 'Image_Path' not in df.columns:
        df['Image_Path'] = 'No Image'
    else:
        df['Image_Path'] = df['Image_Path'].fillna('No Image')

    metadatas = df[['Cocktail Name', 'Glassware', 'Ingredients_Cleaned', 'Image_Path']].rename(
        columns={
            'Cocktail Name': 'name', 
            'Glassware': 'glassware', 
            'Ingredients_Cleaned': 'ingredients_raw',
            'Image_Path': 'image_path' 
        }
    ).to_dict(orient='records')

    ids = [str(uuid.uuid4()) for _ in range(len(documents))]

    print("6. Loading data into ChromaDB...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print("7. Building custom dictionary for spell checker...")
    text_for_dict = " ".join(
        df['Cocktail Name'].dropna().astype(str).tolist() + df['Ingredients'].dropna().astype(str).tolist()).lower()

    custom_words = set(re.findall(r'\b[a-z]{3,}\b', text_for_dict))

    with open('custom_dict.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(custom_words))

    print("8. Building BM25 Keyword Index...")
    tokenized_corpus = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)

    with open('bm25_index.pkl', 'wb') as f:
        pickle.dump({'bm25': bm25, 'ids': ids, 'docs': documents, 'metadatas': metadatas}, f)

    print(f"Success! {len(documents)} cocktails embedded and saved to '{db_path}'.")


if __name__ == "__main__":
    # אנחנו קוראים את הקובץ המקורי שלך
    cocktails_file = "iba_live_scraped_data.csv" 
    
    try:
        print("Starting Data Pipeline...")
        cleaned_data = clean_and_transform_cocktails(cocktails_file)
        
        # --- התוספת שלנו! תשמור לך קובץ כדי שתוכל לראות את השינוי בעיניים ---
        cleaned_data.to_csv("my_cleaned_data_proof.csv", index=False, encoding='utf-8-sig')
        print("✅ Saved a physical proof file: my_cleaned_data_proof.csv")
        # -------------------------------------------------------------------
        
        load_to_vector_db(cleaned_data)
    except Exception as e:
        print(f"Error in pipeline: {e}")