# backend/models.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional

# This class defines the structure for a simple query request.
# We expect a 'query' (the user's question) and a 'business_id'.
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="The user's question or query")
    business_id: str = Field(..., min_length=1, max_length=100, regex="^[a-zA-Z0-9_-]+$", description="Business identifier")
    
    @field_validator('query')
    @classmethod
    def query_must_not_be_empty_or_whitespace(cls, v: str) -> str:
        """Validate that query is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or contain only whitespace")
        return v.strip()
    
    @field_validator('business_id')
    @classmethod
    def business_id_must_be_valid(cls, v: str) -> str:
        """Validate that business_id follows naming conventions."""
        if not v.strip():
            raise ValueError("Business ID cannot be empty")
        return v.strip()

# This class defines the structure for our API's response.
# We'll send back the answer and optionally the context chunks we used.
class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the user's query")
    context: Optional[list] = Field(default=None, description="Optional context chunks used for generating the answer")