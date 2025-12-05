# backend/retriever.py

import faiss
import numpy as np
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict

# --- 1. CONFIGURATION ---
DATA_PATH = Path("data")
FAISS_INDEX_PATH = DATA_PATH / "faiss_index"
CHUNKS_PATH = DATA_PATH / "chunks"

print("Loading embedding model for retriever...")
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

# --- 2. CORE RETRIEVAL FUNCTION (IMPROVED) ---
def retrieve_context(query: str, business_id: str, top_k: int = 3) -> List[Dict]:
    print(f"Retrieving context for query: '{query}' for business: {business_id}")

    index_file = FAISS_INDEX_PATH / f"{business_id}.index"
    chunks_file = CHUNKS_PATH / f"{business_id}_chunks.pkl"

    if not index_file.exists() or not chunks_file.exists():
        print(f"Warning: No FAISS index found for business_id '{business_id}'. Please upload a PDF first.")
        return []

    try:
        index = faiss.read_index(str(index_file))
        with open(chunks_file, "rb") as f:
            chunks = pickle.load(f)
    except Exception as e:
        print(f"Error loading files: {e}")
        return []

    # --- Step D: Embed the user's query (IMPROVEMENT: Normalize the query vector) ---
    query_embedding = EMBEDDING_MODEL.encode([query], convert_to_tensor=False)
    query_embedding = np.array(query_embedding).astype('float32')
    
    # MUST normalize the query embedding as well
    faiss.normalize_L2(query_embedding)

    # --- Step E: Search the FAISS index ---
    # The 'search' method now returns similarity scores directly (higher is better).
    scores, indices = index.search(query_embedding, top_k)

    # --- Step F: Format the results ---
    results = []
    for i in range(len(indices[0])):
        chunk_index = indices[0][i]
        if chunk_index != -1:
            results.append({
                "chunk_text": chunks[chunk_index],
                # The score is now a direct similarity score from the Inner Product index
                "similarity_score": scores[0][i]
            })

    print(f"Found {len(results)} relevant chunks.")
    return results

# --- 3. SCRIPT EXECUTION BLOCK ---
if __name__ == '__main__':
    test_query = "what are the weekday batch timings" # Change this to a question relevant to your PDF
    test_business_id = "business_01"
    
    retrieved_chunks = retrieve_context(test_query, test_business_id)

    print("\n--- Retrieval Complete ---")
    if retrieved_chunks:
        for i, chunk in enumerate(retrieved_chunks):
            print(f"Result {i+1}:")
            print(f"  Similarity Score: {chunk['similarity_score']:.4f}")
            print(f"  Text: {chunk['chunk_text']}")
            print("-" * 20)
    else:
        print("No relevant chunks were found.")
    print("--------------------------")