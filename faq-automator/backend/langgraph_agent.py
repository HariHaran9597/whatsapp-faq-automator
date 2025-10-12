# backend/langgraph_agent.py

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
# --- THIS IS THE FIX ---
# We need to import 'Annotated' from the typing library
from typing import TypedDict, List, Annotated 
import operator

# We will reuse our existing retriever and LLM handler functions as tools for the agent
from backend.retriever import retrieve_context
from backend.llm_handler import MODEL, PROMPT_TEMPLATE # Import the model and template directly

# --- 1. Define the State of our Agent ---
# The state is the "memory" that gets passed between steps in the graph.
class AgentState(TypedDict):
    # The 'operator.add' line means that every time a new message comes in,
    # it gets ADDED to the existing list, rather than replacing it.
    conversation_history: Annotated[List[HumanMessage | AIMessage], operator.add]
    business_id: str
    user_query: str
    retrieved_context: str # Added to hold the context
    ai_answer: str # Added to hold the final answer

# --- 2. Define the Nodes (the "workers" of the agent) ---

def retriever_node(state: AgentState) -> dict:
    """
    This node retrieves context from the vector database based on the user's query.
    """
    print("---AGENT: RETRIEVER NODE---")
    user_query = state["user_query"]
    business_id = state["business_id"]
    
    # Get the full conversation history to provide more context for the search
    history = state.get("conversation_history", [])
    # Create a contextualized query including recent history
    contextual_query = f"{history[-2].content if len(history) > 1 else ''}\n{history[-1].content if history else ''}\n{user_query}"

    context_chunks = retrieve_context(contextual_query, business_id, top_k=3)
    context_str = "\n---\n".join([chunk['chunk_text'] for chunk in context_chunks])
    
    return {"retrieved_context": context_str}


def generation_node(state: AgentState) -> dict:
    """
    This node generates an answer using the LLM, based on the retrieved context
    and the conversation history.
    """
    print("---AGENT: GENERATION NODE---")
    user_query = state["user_query"]
    context = state.get("retrieved_context", "")
    history = state.get("conversation_history", [])
    
    # Format the conversation history for the prompt
    history_str = "\n".join([f"{type(msg).__name__}: {msg.content}" for msg in history])

    formatted_prompt = PROMPT_TEMPLATE.format(
        retrieved_chunks=context,
        conversation_history=history_str,
        user_query=user_query
    )
    
    response = MODEL.generate_content(formatted_prompt)
    
    return {"ai_answer": response.text.strip()}


# --- 3. Build the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("retriever", retriever_node)
workflow.add_node("generator", generation_node)

workflow.set_entry_point("retriever")
workflow.add_edge("retriever", "generator")
workflow.add_edge("generator", END)

conversational_agent = workflow.compile()
print("✅ LangGraph conversational agent compiled successfully.")