# 🚀 Quick Start Guide

## Before You Start
Make sure you have:
- Python 3.9+
- API Keys for: Google Gemini, Twilio, Firebase

## 1️⃣ Configuration (2 minutes)
```bash
cd faq-automator
cp .env.example .env
```
Edit `.env` and add your API keys:
```
GEMINI_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

## 2️⃣ Install & Run (3 minutes)
```bash
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Server running at: `http://localhost:8000`

## 3️⃣ Test It (2 minutes)

### Upload a PDF
```bash
curl -X POST "http://localhost:8000/business/upload-pdf" \
  -F "business_id=business_01" \
  -F "file=@brochure.pdf"
```

### Ask a Question
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "what are your hours?", "business_id": "business_01"}'
```

### View Dashboard
```bash
streamlit run dashboard/streamlit_app.py
```

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│ WhatsApp Message (via Twilio)                    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ WhatsApp Handler (/whatsapp-webhook)            │
│ ├─ Detect text vs voice                         │
│ └─ Transcribe audio if needed (Whisper)         │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ LangGraph Agent                                  │
│ ├─ Retriever Node: Search FAISS index           │
│ └─ Generator Node: Call Gemini API              │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌────────┐ ┌─────────┐ ┌──────────┐
    │FAISS   │ │Gemini   │ │Firebase  │
    │Index   │ │LLM      │ │Firestore │
    └────────┘ └─────────┘ └──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ Response Message (back via Twilio)              │
└─────────────────────────────────────────────────┘
```

## 🔄 Data Flow Example

**User**: "What are your weekday timings?"

```
1. Message arrives at WhatsApp webhook
2. Retriever searches FAISS for similar chunks
   → Found: "Weekday hours: 9 AM - 5 PM"
3. Generator calls Gemini with context + query
4. Gemini responds: "Our weekday hours are 9 AM to 5 PM"
5. Response sent back to WhatsApp
6. Stored in Firebase Firestore for analytics
```

## 📁 File Structure

```
faq-automator/
├── backend/
│   ├── app.py              ← FastAPI server
│   ├── llm_handler.py      ← Gemini integration
│   ├── retriever.py        ← FAISS search
│   ├── langgraph_agent.py  ← Agent with memory
│   ├── whatsapp_handler.py ← Twilio webhook
│   ├── pdf_processor.py    ← PDF → embeddings
│   └── firebase_client.py  ← Database
├── dashboard/
│   └── streamlit_app.py    ← Admin UI
├── data/
│   ├── pdfs/               ← Uploaded files
│   ├── chunks/             ← Text chunks
│   └── faiss_index/        ← Vector database
├── .env.example            ← Copy to .env ⭐
├── requirements.txt
└── SETUP.md                ← Full guide ⭐
```

## ⚠️ Common Issues

| Problem | Solution |
|---------|----------|
| "GEMINI_API_KEY not found" | Check `.env` file exists and has the key |
| "No FAISS index found" | Upload a PDF via `/business/upload-pdf` |
| "KeyError: conversation_history" | ✅ FIXED in v1.1 |
| Conversation history lost | Restart = clears cache (use Firebase in prod) |

## 🎯 Next Steps

1. ✅ Configuration done? → Run the server
2. ✅ Server running? → Upload a test PDF
3. ✅ PDF uploaded? → Test via `/query` endpoint
4. ✅ Works locally? → Set up WhatsApp webhook in Twilio
5. ✅ Testing complete? → Deploy to Render using `Dockerfile`

## 📚 Documentation

- **SETUP.md** - Comprehensive setup guide
- **STATUS.md** - What was fixed and why
- **FIXES_APPLIED.md** - Detailed change log

---

**Ready to go! 🎉**
