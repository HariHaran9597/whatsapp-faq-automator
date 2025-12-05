# backend/llm_handler.py

import google.generativeai as genai
from typing import List, Dict

# Import the settings instance
from backend.config import settings
# Import the retriever function we just built
from backend.retriever import retrieve_context

# --- 1. CONFIGURE THE GEMINI MODEL ---
# Configure the generative AI library with the API key
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    # Initialize the model
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20')
    print("Gemini model initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    MODEL = None

# --- 2. DEFINE THE PROMPT TEMPLATE ---
# This is a crucial part of RAG. We instruct the model on how to behave.
# It's a "meta-prompt" that guides the final answer generation.
PROMPT_TEMPLATE = """
You are a helpful and friendly assistant for a local business.

Your job is to answer a customer's question based *only* on the provided context.

STRICT RULES:
1. Use *only* the information from the 'CONTEXT' section. Do not use any of your outside knowledge.
2. If the answer is not in the 'CONTEXT', you *must* respond with: "I'm sorry, I don't have that information in the brochure. Please contact the business directly for more details."
3. Be concise and answer in a friendly, conversational tone.
4. Do not mention the word 'context' or 'brochure' in your answer. Just provide the information.

CONVERSATION HISTORY (for context only):
{conversation_history}

CONTEXT:
{retrieved_chunks}

CUSTOMER QUESTION:
{user_query}

YOUR ANSWER:
"""

# --- 3. CORE ANSWER GENERATION FUNCTION ---
async def generate_answer(query: str, business_metadata: dict) -> str:
    """
    Generates a final answer using the RAG pipeline.

    Args:
        query (str): The user's question.
        business_metadata (dict): A dictionary containing business details,
                                  like 'business_id'.

    Returns:
        str: The generated, human-friendly answer.
    """
    if MODEL is None:
        return "The AI model is not available at the moment. Please try again later."

    business_id = business_metadata.get("business_id", "default")

    # --- Step A: Retrieve context from our FAISS index ---
    context_chunks = retrieve_context(query, business_id, top_k=3)

    if not context_chunks:
        return "I'm sorry, I couldn't find any relevant information to answer your question. Please try rephrasing or contact the business."

    # --- Step B: Format the retrieved chunks for the prompt ---
    # We'll combine the text from the retrieved chunks into a single block.
    context_str = "\n---\n".join([chunk['chunk_text'] for chunk in context_chunks])

    # --- Step C: Fill in the prompt template ---
    formatted_prompt = PROMPT_TEMPLATE.format(
        retrieved_chunks=context_str,
        user_query=query,
        conversation_history=""  # No history in simple RAG mode
    )

    # --- Step D: Call the Gemini API ---
    try:
        print("\n--- Calling Gemini API ---")
        response = MODEL.generate_content(formatted_prompt)
        print("--- Gemini API call successful ---\n")
        return response.text.strip()
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return "There was an issue generating a response. Please try again."


# --- 4. SCRIPT EXECUTION BLOCK ---
import asyncio

if __name__ == '__main__':
    # Define a test query and business metadata
    test_query = "what are the weekday batch timings"
    test_business_metadata = {"business_id": "business_01"}

    # Define an async function to run our test
    async def main():
        final_answer = await generate_answer(test_query, test_business_metadata)
        print("\n--- RAG Pipeline Complete ---")
        print(f"Question: {test_query}")
        print(f"Final Answer: {final_answer}")
        print("-----------------------------")

    # Run the async main function
    asyncio.run(main())