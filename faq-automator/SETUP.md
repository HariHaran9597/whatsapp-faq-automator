# Setup Instructions

## Prerequisites
- Python 3.9+
- Docker (for deployment)
- API Keys for:
  - Google Gemini API
  - Twilio Account
  - Firebase Account

## Local Setup

### 1. Clone and Install Dependencies
```bash
cd faq-automator
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

Then fill in `.env` with:
- `GEMINI_API_KEY`: Get from https://aistudio.google.com/app/apikeys
- `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN`: Get from https://www.twilio.com/console
- `FIREBASE_CREDENTIALS_PATH`: Download JSON from Firebase Console

### 3. Upload a PDF (Test)
```bash
curl -X POST "http://localhost:8000/business/upload-pdf" \
  -F "business_id=business_01" \
  -F "file=@path/to/your/brochure.pdf"
```

### 4. Start the Server
```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test Query Endpoint
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "what are your hours?", "business_id": "business_01"}'
```

### 6. Run Dashboard
```bash
streamlit run dashboard/streamlit_app.py
```

## Deployment to Render

1. Push code to GitHub
2. Connect repository to Render
3. Set environment variables in Render dashboard
4. Upload Firebase credentials file as secret
5. Deploy!

## Troubleshooting

### "No FAISS index found"
- Upload a PDF first using the `/business/upload-pdf` endpoint

### "GEMINI_API_KEY not found"
- Check `.env` file exists and has the correct key
- Restart the server

### Conversation history not persisting
- Server restart clears in-memory cache
- Use Firebase for persistent storage in production

## Project Structure
```
backend/
├── app.py               # FastAPI server
├── llm_handler.py       # Gemini integration
├── retriever.py         # FAISS search
├── pdf_processor.py     # PDF → embeddings → FAISS
├── langgraph_agent.py   # Conversational memory
├── whatsapp_handler.py  # Twilio integration
├── firebase_client.py   # Database & analytics
├── voice_transcriber.py # Whisper transcription
└── config.py            # Settings

dashboard/
└── streamlit_app.py     # Admin dashboard

data/
├── pdfs/                # Uploaded PDFs
├── chunks/              # Pickled text chunks
└── faiss_index/         # Vector indices
```

## API Endpoints

- `GET /health` - Health check
- `POST /business/upload-pdf` - Upload PDF
- `POST /query` - Test query
- `POST /whatsapp-webhook` - WhatsApp messages
- `GET /analytics/{business_id}` - Get analytics

## Recent Fixes (v1.1)

✅ Fixed: Prompt template missing `conversation_history` placeholder
✅ Added: Error handling in LangGraph agent
✅ Added: Better error messages for missing FAISS indices
✅ Added: Improved exception handling in WhatsApp handler
✅ Added: `.env.example` template file
