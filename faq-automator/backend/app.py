# backend/app.py

from fastapi import FastAPI, HTTPException, UploadFile, File, Form # <-- 'Form' is now imported here
from datetime import datetime
from pathlib import Path

# Import our Pydantic models
from backend.models import QueryRequest, QueryResponse
# Import the core RAG logic function
from backend.llm_handler import generate_answer
# Import the router from our whatsapp_handler file
from backend.whatsapp_handler import router as whatsapp_router
# Import the PDF processor and Firebase functions
from backend.pdf_processor import process_pdf
from backend.firebase_client import get_analytics_data, update_business_paths

# Initialize the FastAPI application
app = FastAPI(
    title="Local Business FAQ Automator",
    description="An AI agent to answer customer questions via WhatsApp.",
    version="1.0.0"
)

# Include the WhatsApp router to make the /whatsapp-webhook endpoint available
app.include_router(whatsapp_router)

# Define storage path for PDFs
PDF_STORAGE_PATH = Path("data/pdfs")
PDF_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# --- API ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/analytics/{business_id}")
async def get_analytics(business_id: str):
    analytics = await get_analytics_data(business_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="No analytics data found for this business.")
    return analytics

@app.post("/business/upload-pdf")
async def upload_and_process_pdf(
    business_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Uploads a PDF, saves it, processes it into a FAISS index,
    and updates the business record in Firestore.
    """
    file_path = PDF_STORAGE_PATH / f"{business_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    processing_result = process_pdf(str(file_path), business_id)
    if processing_result["status"] != "success":
        raise HTTPException(status_code=500, detail="Failed to process PDF.")
        
    await update_business_paths(
        business_id,
        str(file_path),
        processing_result["faiss_index_path"]
    )
    
    return {
        "status": "success",
        "filename": file.filename,
        "num_chunks": processing_result["num_chunks"],
        "message": f"PDF processed and business '{business_id}' updated."
    }

@app.post("/query", response_model=QueryResponse)
async def test_query(request: QueryRequest):
    print(f"Received query for business '{request.business_id}': '{request.query}'")
    try:
        business_metadata = {"business_id": request.business_id}
        final_answer = await generate_answer(request.query, business_metadata)
        return QueryResponse(answer=final_answer)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the query.")