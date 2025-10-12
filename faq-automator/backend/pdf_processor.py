# backend/pdf_processor.py

import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pathlib import Path
import pickle

# --- 1. CONFIGURATION ---
DATA_PATH = Path("data")
FAISS_INDEX_PATH = DATA_PATH / "faiss_index"
CHUNKS_PATH = DATA_PATH / "chunks"
FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
CHUNKS_PATH.mkdir(parents=True, exist_ok=True)

print("Loading embedding model...")
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

# --- 2. CORE PDF PROCESSING FUNCTION (IMPROVED) ---
def process_pdf(pdf_path: str, business_id: str) -> dict:
    print(f"Starting to process PDF: {pdf_path} for business: {business_id}")

    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        print(f"Extracted {len(text)} characters from the PDF.")
        if not text.strip():
            return {"status": "error", "message": "No text could be extracted from the PDF."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to read PDF: {e}"}

    # --- Step B: Chunk the Text (IMPROVEMENT: Smaller chunk size) ---
    # We reduce the chunk size to get more specific, smaller pieces of text.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,  # Reduced from 500
        chunk_overlap=30,   # Reduced from 50
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    print(f"Split text into {len(chunks)} chunks.")

    print("Generating embeddings for all chunks...")
    embeddings = EMBEDDING_MODEL.encode(chunks, convert_to_tensor=False)
    
    # --- Step D: Create and Save FAISS Index (IMPROVEMENT: Using Inner Product) ---
    embeddings = np.array(embeddings).astype('float32')
    
    # We MUST normalize the vectors for Inner Product to work correctly
    faiss.normalize_L2(embeddings)

    d = embeddings.shape[1]
    
    # Using IndexFlatIP for Inner Product (cosine similarity)
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    
    index_file = FAISS_INDEX_PATH / f"{business_id}.index"
    faiss.write_index(index, str(index_file))
    print(f"FAISS index saved to: {index_file} (using Inner Product)")

    chunks_file = CHUNKS_PATH / f"{business_id}_chunks.pkl"
    with open(chunks_file, "wb") as f:
        pickle.dump(chunks, f)
    print(f"Text chunks saved to: {chunks_file}")

    return {
        "status": "success",
        "num_chunks": len(chunks),
        "faiss_index_path": str(index_file),
        "chunks_path": str(chunks_file)
    }

# --- 3. SCRIPT EXECUTION BLOCK ---
if __name__ == '__main__':
    sample_pdf_path = str(DATA_PATH / "sample_brochure.pdf")
    test_business_id = "business_01"
    if not Path(sample_pdf_path).exists():
        print(f"ERROR: Sample PDF not found at '{sample_pdf_path}'")
    else:
        result = process_pdf(pdf_path=sample_pdf_path, business_id=test_business_id)
        print("\n--- Processing Complete ---")
        print(result)
        print("---------------------------")