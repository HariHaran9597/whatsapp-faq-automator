# backend/whatsapp_handler.py

from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
import logging
from langchain_core.messages import AIMessage, HumanMessage

# --- MODIFIED IMPORTS ---
# We no longer call generate_answer directly. Instead, we use our new agent.
from backend.voice_transcriber import transcribe_audio
from backend.firebase_client import store_conversation
from backend.langgraph_agent import conversational_agent

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- A simple in-memory cache for conversation history ---
# This dictionary will store the history for each user (keyed by their WhatsApp number).
# In a production system with multiple server instances, you'd use a shared store like Redis.
conversation_history_cache = {}

@router.post("/whatsapp-webhook")
async def handle_whatsapp(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None)
):
    """
    Handles incoming WhatsApp messages, uses a LangGraph agent for conversational
    memory, and ensures a robust 200 OK response is always sent to Twilio.
    """
    sender_id = From
    response = MessagingResponse()
    
    try:
        # --- Initialize variables ---
        text_to_process = ""
        response_prefix = ""
        query_type = "text"
        transcription = None

        # --- Determine if the message is text or voice ---
        if NumMedia > 0 and MediaUrl0:
            query_type = "voice"
            transcribed_text = await transcribe_audio(MediaUrl0)
            text_to_process = transcribed_text
            transcription = transcribed_text
            response_prefix = f"I heard you say: \"{transcribed_text}\"\n\n"
        elif Body:
            text_to_process = Body
        else:
            logger.warning(f"Received an empty message from {sender_id}.")
            response.message("Sorry, I didn't receive a message. Please try sending it again.")
            return Response(content=str(response), media_type="application/xml")

        # --- Use the LangGraph Agent to get a response ---
        if text_to_process:
            # 1. Retrieve the user's past messages from our cache
            history = conversation_history_cache.get(sender_id, [])

            # 2. Invoke the agent with the current state
            result = conversational_agent.invoke({
                "user_query": text_to_process,
                "business_id": "business_01", # Hardcoded for now
                "conversation_history": history
            })
            
            # 3. Extract the final answer from the agent's result
            ai_answer = result.get("ai_answer", "Sorry, I couldn't generate a response.")
            
            # 4. Update the history cache with this new turn
            conversation_history_cache[sender_id] = history + [
                HumanMessage(content=text_to_process),
                AIMessage(content=ai_answer)
            ]

            # --- Log and send the response ---
            logger.info(f"Sending AI answer to {sender_id}: '{ai_answer}'")
            final_response_message = f"{response_prefix}{ai_answer}"
            response.message(final_response_message)

            conversation_log = {
                "user_id": sender_id, "business_id": "business_01",
                "query": text_to_process, "query_type": query_type,
                "transcription": transcription, "answer": ai_answer,
            }
            await store_conversation(conversation_log)
        else:
            response.message("I had trouble understanding your message. Could you please try again?")

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logger.error(f"An unexpected error occurred in the webhook for user {sender_id}: {e}", exc_info=True)
        # Always return a 200 OK response with a friendly error message to Twilio
        error_response = MessagingResponse()
        error_response.message("I'm sorry, I'm having a little trouble right now. Please try your question again in a moment.")
        return Response(content=str(error_response), media_type="application/xml", status_code=200)