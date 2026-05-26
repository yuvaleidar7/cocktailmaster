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

    # עדכון המטא-דאטה לשליפת הטעם ושימוש ב-fillna למניעת שגיאות
    metadatas = df[['Cocktail Name', 'Glassware', 'Ingredients_Cleaned', 'Image_Path', 'Flavor Profile']].rename(
        columns={
            'Cocktail Name': 'name', 
            'Glassware': 'glassware', 
            'Ingredients_Cleaned': 'ingredients_raw',
            'Image_Path': 'image_path',
            'Flavor Profile': 'flavor'
        }
    ).fillna('Unknown').to_dict('records')

    ids = [str(uuid.uuid4()) for _ in range(len(documents))]

    print(f"6. Adding {len(documents)} cocktails to ChromaDB (This might take a minute)...")
    
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        print(f"   Batch {i//batch_size + 1}: Embedded items {i} to {end_idx}")

    print("7. Building BM25 Index for keyword search...")
    tokenized_corpus = [re.sub(r'[^\w\s]', '', doc).lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)
    
    print("8. Saving BM25 Index to disk...")
    with open('bm25_index.pkl', 'wb') as f:
        pickle.dump({'bm25': bm25, 'ids': ids, 'docs': documents, 'metadatas': metadatas}, f)

    print(f"Success! {len(documents)} cocktails embedded and saved to '{db_path}'.")


if __name__ == "__main__":
    # שימוש בקובץ הנתונים החדש שכולל את הטעמים
    cocktails_file = "iba_cocktails_flavors_en.csv" 
    
    try:
        print("Starting Data Pipeline...")
        cleaned_data = clean_and_transform_cocktails(cocktails_file)
        
        # שמירת קובץ הוכחה פיזי כדי שתוכל לראות את השינוי
        cleaned_data.to_csv("my_cleaned_data_proof.csv", index=False, encoding='utf-8-sig')
        print("✅ Saved a physical proof file: my_cleaned_data_proof.csv")
        
        load_to_vector_db(cleaned_data)
    except Exception as e:
        print(f"Error in pipeline: {e}")