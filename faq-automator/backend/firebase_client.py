# backend/firebase_client.py

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from collections import Counter

from backend.config import settings

DB = None

# --- 1. INITIALIZE FIREBASE ADMIN SDK ---
try:
    print("Attempting to initialize Firebase...")
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    DB = firestore.client()
    print("✅ Firebase Firestore initialized successfully.")
except Exception as e:
    print(f"❌ An unexpected error occurred during Firebase initialization: {e}")
    DB = None

# --- 2. CONVERSATION FUNCTIONS ---

async def store_conversation(conversation_data: dict):
    """Stores a single conversation turn in the 'conversations' collection."""
    if not DB: return
    try:
        conversations_ref = DB.collection('conversations')
        conversation_data['timestamp'] = datetime.now()
        conversations_ref.add(conversation_data)
        print(f"Successfully stored conversation for user: {conversation_data.get('user_id')}")
    except Exception as e:
        print(f"Error storing conversation in Firestore: {e}")

async def get_conversations(business_id: str, limit: int = 50) -> list:
    """Fetches the last N conversations for a given business from Firestore."""
    if not DB: return []
    try:
        conversations_ref = DB.collection('conversations')
        query = conversations_ref.where(field_path='business_id', op_string='==', value=business_id).order_by(
            'timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        conversations = [doc.to_dict() for doc in docs]
        print(f"Fetched {len(conversations)} conversations from Firestore.")
        return conversations
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return []

# --- 3. BUSINESS METADATA FUNCTIONS ---

async def get_business_by_id(business_id: str) -> dict:
    """Fetches a business document from Firestore by its ID."""
    if not DB: return {}
    doc_ref = DB.collection('businesses').where(field_path='business_id', op_string='==', value=business_id).limit(1)
    docs = list(doc_ref.stream())
    if docs:
        return docs[0].to_dict()
    return {}

async def update_business_paths(business_id: str, pdf_path: str, faiss_path: str):
    """Updates a business document with new file paths."""
    if not DB: return
    doc_ref_query = DB.collection('businesses').where('business_id', '==', business_id).limit(1)
    docs = list(doc_ref_query.stream())
    if docs:
        doc_id = docs[0].id
        doc_ref = DB.collection('businesses').document(doc_id)
        doc_ref.update({'pdf_url': pdf_path, 'faiss_index_path': faiss_path})
        print(f"Updated paths for business {business_id}")

# --- 4. ANALYTICS FUNCTIONS ---

async def get_analytics_data(business_id: str) -> dict:
    """Fetches all conversations for a business and computes analytics."""
    if not DB: return {}
    try:
        conversations_ref = DB.collection('conversations')
        query = conversations_ref.where(field_path='business_id', op_string='==', value=business_id)
        docs = query.stream()
        conversations = [doc.to_dict() for doc in docs]

        if not conversations:
            return {"total_queries": 0, "query_type_counts": {}, "top_queries": []}

        total_queries = len(conversations)
        query_type_counts = Counter(conv.get('query_type', 'unknown') for conv in conversations)
        top_queries = Counter(
            conv.get('query', '').lower().strip() for conv in conversations
        ).most_common(10)

        return {
            "total_queries": total_queries,
            "query_type_counts": dict(query_type_counts),
            "top_queries": [{"query": q, "count": c} for q, c in top_queries]
        }
    except Exception as e:
        print(f"Error fetching analytics data: {e}")
        return {}