# backend/models.py

from pydantic import BaseModel
from typing import Optional

# This class defines the structure for a simple query request.
# We expect a 'query' (the user's question) and a 'business_id'.
class QueryRequest(BaseModel):
    query: str
    business_id: str

# This class defines the structure for our API's response.
# We'll send back the answer and optionally the context chunks we used.
class QueryResponse(BaseModel):
    answer: str
    context: Optional[list] = None