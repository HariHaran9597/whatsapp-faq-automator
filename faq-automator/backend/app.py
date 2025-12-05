# backend/app.py

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends # <-- Added 'Depends'
from datetime import datetime
from pathlib import Path
import logging

# Import our Pydantic models
from backend.models import QueryRequest, QueryResponse
# Import the core RAG logic function
from backend.llm_handler import generate_answer
# Import the router from our whatsapp_handler file
from backend.whatsapp_handler import router as whatsapp_router
# Import the PDF processor and Firebase functions
from backend.pdf_processor import process_pdf
from backend.firebase_client import get_analytics_data, update_business_paths
# Import logging configuration
from backend.logging_config import setup_logging, get_logger
# Import security utilities
from backend.security import verify_api_key, optional_verify_api_key

# Setup logging
setup_logging()
logger = get_logger(__name__)

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

logger.info("✅ FastAPI application initialized")

# --- API ENDPOINTS ---

@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint called")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/analytics/{business_id}")
async def get_analytics(business_id: str):
    logger.info(f"Analytics requested for business_id: {business_id}")
    try:
        analytics = await get_analytics_data(business_id)
        if not analytics:
            logger.warning(f"No analytics data found for business_id: {business_id}")
            raise HTTPException(status_code=404, detail="No analytics data found for this business.")
        logger.info(f"Successfully retrieved analytics for {business_id}")
        return analytics
    except Exception as e:
        logger.error(f"Error retrieving analytics for {business_id}: {e}", exc_info=True)
        raise

@app.post("/business/upload-pdf")
async def upload_and_process_pdf(
    business_id: str = Form(...),
    file: UploadFile = File(...),
    api_key: str = Depends(optional_verify_api_key)
):
    """
    Uploads a PDF, saves it, processes it into a FAISS index,
    and updates the business record in Firestore.
    
    Optional API key authentication can be enabled by setting API_KEY in .env
    """
    logger.info(f"PDF upload started for business_id: {business_id}, filename: {file.filename}, authenticated: {api_key is not None}")
    
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Non-PDF file upload attempted: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
        
        # Check file size (max 50MB)
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:
            logger.warning(f"File too large: {file.filename} ({len(file_content)} bytes)")
            raise HTTPException(status_code=413, detail="File size exceeds maximum (50MB)")
        
        # Save file
        file_path = PDF_STORAGE_PATH / f"{business_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        logger.debug(f"PDF saved to: {file_path}")
        
        # Process PDF
        processing_result = process_pdf(str(file_path), business_id)
        if processing_result["status"] != "success":
            logger.error(f"PDF processing failed for {business_id}: {processing_result}")
            raise HTTPException(status_code=500, detail="Failed to process PDF.")
        
        # Update business metadata
        await update_business_paths(
            business_id,
            str(file_path),
            processing_result["faiss_index_path"]
        )
        
        logger.info(f"✅ PDF successfully processed for {business_id}: {processing_result['num_chunks']} chunks created")
        
        return {
            "status": "success",
            "filename": file.filename,
            "num_chunks": processing_result["num_chunks"],
            "message": f"PDF processed and business '{business_id}' updated."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during PDF upload for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during PDF processing.")

@app.post("/query", response_model=QueryResponse)
async def test_query(request: QueryRequest):
    logger.info(f"Query received - business_id: {request.business_id}, query: {request.query}")
    
    try:
        business_metadata = {"business_id": request.business_id}
        final_answer = await generate_answer(request.query, business_metadata)
        
        logger.info(f"✅ Query processed successfully for {request.business_id}")
        return QueryResponse(answer=final_answer)
    
    except Exception as e:
        logger.error(f"Error processing query for {request.business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the query.")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("="*60)
    logger.info("🚀 WhatsApp FAQ Automator starting up...")
    logger.info("="*60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("="*60)
    logger.info("🛑 WhatsApp FAQ Automator shutting down...")
    logger.info("="*60)