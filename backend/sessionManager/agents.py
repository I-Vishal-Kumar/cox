"""Multi-agent system with customer support, sales, and general agents."""
import json
import os
import uuid
import shutil
from contextvars import ContextVar
from pathlib import Path
from datetime import datetime, timedelta
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from strands.session import FileSessionManager
from strands_tools import file_read, file_write, editor, calculator

# Context variable for current session_id (thread-safe per request)
current_session_id: ContextVar[str] = ContextVar('current_session_id', default=None)
from config.settings import (
    OPENAI_API_KEY,
    MODEL_ID,
    MAX_TOKENS,
    TEMPERATURE,
    SALES_CONTEXT_PATH,
    SUPPORT_CONTEXT_PATH,
    PRIMARY_CONTEXT_PATH,
    SESSIONS_DIR,
    PRIMARY_AGENT_SYSTEM_PROMPT,
    SUPPORT_AGENT_SYSTEM_PROMPT,
    SALES_AGENT_SYSTEM_PROMPT,
    GENERAL_AGENT_SYSTEM_PROMPT,
    NEGOTIATION_AGENT_SYSTEM_PROMPT,
    ORCHESTRATOR_AGENT_SYSTEM_PROMPT
)

# Initialize OpenAI model
model = OpenAIModel(
    client_args={
        "api_key": OPENAI_API_KEY,
    },
    model_id="gpt-4.1",
    params={
        # "max_tokens": MAX_TOKENS,
        "temperature": 0.7,
    }
)

# Common tools for all agents
common_tools = [file_read, file_write, editor, calculator]

# Goal storage: {session_id: {final_goal: str, questions_asked: list, features_recommended: list}}
_goal_storage = {}

# Session configuration
SESSION_EXPIRE_HOURS = 1  # Sessions expire after 1 hour


def load_context(context_path: Path) -> str:
    """Load context from TXT file."""
    if not context_path.exists():
        raise FileNotFoundError(f"Context file not found: {context_path}")
    with open(context_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_session_manager(agent_name: str, session_id: str, ip: str = None, user_id: str = None):
    """
    Create a session manager for the given session_id.
    
    Args:
        agent_name: Name of the agent (sales, support, general, orchestrator)
        session_id: Session ID to use
        ip: Optional client IP address
        user_id: Optional user ID
        
    Returns:
        FileSessionManager instance
    """
    # Create cache key
    cache_key = f"{agent_name}_{session_id}"
    
    # Create new session manager
    # Try both parameter names as API might vary
    try:
        session_manager = FileSessionManager(
            session_id=cache_key,
            storage_dir=str(SESSIONS_DIR)
        )
    except TypeError:
        # Fallback to session_dir if storage_dir doesn't work
        try:
            session_manager = FileSessionManager(
                session_id=cache_key,
                session_dir=str(SESSIONS_DIR)
            )
        except TypeError:
            # Try with just session_id
            session_manager = FileSessionManager(
                session_id=cache_key
            )
    
    return session_manager


def save_session_metadata(cache_key: str, metadata: dict):
    """Save session metadata to JSON file."""
    try:
        # Create session directory
        session_dir = Path(SESSIONS_DIR) / cache_key
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata file
        metadata_file = session_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"⚠️  Error saving session metadata for {cache_key}: {e}")


# Removed load_session_metadata - no longer needed without global caches


def cleanup_session(cache_key: str):
    """Clean up a single session from disk."""
    try:
        # Remove from disk
        session_dir = Path(SESSIONS_DIR) / cache_key
        if session_dir.exists():
            shutil.rmtree(session_dir)
        
        print(f"🗑️  Cleaned up session: {cache_key}")
    except Exception as e:
        print(f"❌ Error cleaning up session {cache_key}: {e}")


def cleanup_expired_sessions():
    """Clean up expired sessions from disk."""
    # Since we don't track metadata in memory, we'll clean up old session directories
    try:
        sessions_dir = Path(SESSIONS_DIR)
        if not sessions_dir.exists():
            return 0
        
        cleaned = 0
        current_time = datetime.now()
        
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                            expires_at = datetime.fromisoformat(metadata.get("expires_at", "2000-01-01"))
                            if current_time > expires_at:
                                cleanup_session(session_dir.name)
                                cleaned += 1
                    except:
                        pass
        
        if cleaned > 0:
            print(f"🧹 Cleaned up {cleaned} expired session(s)")
        
        return cleaned
    except Exception as e:
        print(f"⚠️  Error cleaning expired sessions: {e}")
        return 0


def cleanup_all_sessions():
    """Clean up ALL sessions from disk. Called on startup."""
    global _goal_storage
    
    try:
        # Clear goal storage
        _goal_storage.clear()
        
        # Remove all session directories from disk
        sessions_dir = Path(SESSIONS_DIR)
        if sessions_dir.exists():
            deleted_count = 0
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    try:
                        shutil.rmtree(session_dir)
                        deleted_count += 1
                    except Exception as e:
                        print(f"⚠️  Error deleting session directory {session_dir.name}: {e}")
            
            if deleted_count > 0:
                print(f"🗑️  Deleted {deleted_count} session(s) on startup")
            else:
                print("✅ No sessions to clean up on startup")
        else:
            print("✅ No sessions directory found")
            
    except Exception as e:
        print(f"❌ Error cleaning up all sessions: {e}")


# Load contexts
sales_context = load_context(SALES_CONTEXT_PATH)
support_context = load_context(SUPPORT_CONTEXT_PATH)
primary_context = load_context(PRIMARY_CONTEXT_PATH)
# print(f"Sales context: {sales_context}")
# print(f"Support context: {support_context}")
# print(f"Primary context: {primary_context}")

# No longer loading session metadata on startup


# Tools for asking questions, recommending features, and managing goals
@tool
def ask_question(question: str,previous_summary: str = None) -> str:
    """
    Ask a single question to the customer. Use this tool to gather information one question at a time.
    This helps maintain focus and ensures clear communication.
    
    Args:
        question: The question to ask the customer (one question at a time)
        
    Returns:
        Confirmation that the question should be asked to the customer
    """
    session_id = current_session_id.get()
    if not session_id:
        return f"Question to ask: {question}"
    
    if session_id not in _goal_storage:
        _goal_storage[session_id] = {"final_goal": None, "questions_asked": [], "features_recommended": []}
    
    _goal_storage[session_id]["questions_asked"].append({
        "question": question,
        "timestamp": datetime.now().isoformat()
    })
    
    return f"Question to ask: {question}"

@tool
def recommend_features(features: str) -> str:
    """
    Recommend features to the customer. Use this tool to suggest relevant features based on their needs.
    
    Args:
        features: A description of the features to recommend (can be a list or description)
        
    Returns:
        Confirmation that features should be recommended to the customer
    """
    session_id = current_session_id.get()
    if not session_id:
        return f"Features to recommend: {features}"
    
    if session_id not in _goal_storage:
        _goal_storage[session_id] = {"final_goal": None, "questions_asked": [], "features_recommended": []}
    
    _goal_storage[session_id]["features_recommended"].append({
        "features": features,
        "timestamp": datetime.now().isoformat()
    })
    
    return f"Features to recommend: {features}"

@tool
def get_final_goal() -> str:
    """
    Get the final goal for the current session if it exists. The final goal represents the customer's
    main objective or desired outcome.
    
    Returns:
        The final goal if it exists, otherwise returns a message indicating no goal is set
    """
    session_id = current_session_id.get()
    if session_id and session_id in _goal_storage and _goal_storage[session_id].get("final_goal"):
        return f"Final goal: {_goal_storage[session_id]['final_goal']}"
    return "No final goal has been set for this session yet."

@tool
def set_final_goal(goal: str) -> str:
    """
    Set or update the final goal for the current session. The final goal represents the customer's
    main objective or desired outcome.
    
    Args:
        goal: The final goal or objective for this session
        
    Returns:
        Confirmation that the goal has been set
    """
    session_id = current_session_id.get()
    if not session_id:
        return f"Final goal set: {goal}"
    
    if session_id not in _goal_storage:
        _goal_storage[session_id] = {"final_goal": None, "questions_asked": [], "features_recommended": []}
    
    _goal_storage[session_id]["final_goal"] = goal
    _goal_storage[session_id]["goal_set_at"] = datetime.now().isoformat()
    
    return f"Final goal set: {goal}"


@tool
def answer_faq(question: str) -> str:
    """Answer frequently asked questions about our chatbot plans using the FAQ agent."""
    session_id = current_session_id.get()
    system_prompt = (
        "You are a helpful FAQ sales specialist assistant for our chatbot platform. "
        "Use the provided sales context to answer common questions accurately. "
        "If user mentiontiong some competitor platform, then respond like yeah they are our competitor and we are better than them. "
        "Briefly acknowledge their research, highlight our strengths (value, flexibility, support), and invite them to continue the conversation—with no exaggeration or invented claims. "
        "Do not invent features or pricing; stay faithful to the context."
    )
    if sales_context:
        system_prompt += f"\n\nFAQ Reference:\n{sales_context} "
    
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[],
        agent_id=f"faq_agent_{session_id}" if session_id else f"faq_agent_{str(uuid.uuid4())}"
    )
    response = agent(question)
    return str(response)


# Define specialized agents as tools (without session management)
@tool
def handle_sales_query(query: str) -> str:
    """
    Handle sales-related queries including product information, pricing, orders, and purchasing.
    This agent specializes in sales activities and can only assist with sales-related inquiries.
    
    Args:
        query: A sales-related question or request
        
    Returns:
        A response addressing the sales query. If the query is not sales-related, 
        the agent will politely decline and suggest contacting the appropriate department.
    """
    session_id = current_session_id.get()
    # Build system prompt
    system_prompt = SALES_AGENT_SYSTEM_PROMPT
    if sales_context:
        system_prompt += f"\n\nContext Information:\n{sales_context}"
    system_prompt += "\n\nEMOJI USAGE: USE EMOJIS extensively in your responses to make them more engaging and friendly. Use relevant emojis like 🎯, 💰, 📦, ⭐, 🔗, ✅, 💡, 🚀, 🧩, etc. to enhance communication and make your messages more visually appealing."
    system_prompt += "\n\nCRITICAL ANTI-HALLUCINATION: You MUST ONLY provide information from your domain knowledge. NEVER make up products, prices, or features. If information is not in your context, acknowledge the limitation. Route to negotiation agent for price negotiations, support agent for technical issues, and general agent for unrelated queries."
    system_prompt += """
    
    RULES:
    1. Must ask only one question at a time from the context only. Must wait for the answer before asking the next question.
   
    """
    
    additional_tools = [recommend_features, get_final_goal, set_final_goal, answer_faq]
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools= additional_tools,
        agent_id=f"sales_agent_{session_id}" if session_id else f"sales_agent_{str(uuid.uuid4())}"
    )
    response = agent(query)
    return str(response)


@tool
def handle_support_query(query: str) -> str:
    """
    Handle customer support queries including troubleshooting, technical issues, refunds, and account problems.
    This agent specializes in customer support and can only assist with support-related inquiries.
    
    Args:
        query: A customer support-related question or request
        
    Returns:
        A response addressing the support query. If the query is not support-related, 
        the agent will politely decline and suggest contacting the appropriate department.
    """
    session_id = current_session_id.get()
    # Build system prompt
    system_prompt = SUPPORT_AGENT_SYSTEM_PROMPT
    if support_context:
        system_prompt += f"\n\nContext Information:\n{support_context}"
    system_prompt += "\n\nEMOJI USAGE: USE EMOJIS in your responses to make them more friendly and engaging. Feel free to use relevant emojis like ✅, ❌, 🔧, 💡, 📧, 🎯, 🔍, etc. to enhance communication."
    system_prompt += "\n\nCRITICAL: NEVER mention, discuss, or reveal any tools, functions, or internal mechanisms you have access to. Do not tell users about tools like ask_question, recommend_features, get_final_goal, set_final_goal, or any other internal tools. Act naturally as if these are just part of your normal conversation flow. Route to FAQ agent if user has any questions. Route to ask agent if the user has selected the plan on the basis of fitment questions"
    
    additional_tools = [ask_question, recommend_features, get_final_goal, set_final_goal, answer_faq]
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=common_tools + additional_tools,
        agent_id=f"support_agent_{session_id}" if session_id else f"support_agent_{str(uuid.uuid4())}"
    )
    response = agent(query)
    return str(response)


@tool
def handle_general_query(query: str) -> str:
    """
    Handle general queries and questions that are not specifically sales or support related.
    This agent can assist with a wide range of general questions and tasks.
    
    Args:
        query: A general question or request
        
    Returns:
        A response addressing the general query
    """
    session_id = current_session_id.get()
    system_prompt = GENERAL_AGENT_SYSTEM_PROMPT
    system_prompt += "\n\nEMOJI USAGE: USE EMOJIS in your responses to make them more engaging and friendly. Feel free to use relevant emojis to enhance communication."
    system_prompt += "\n\nCRITICAL: NEVER mention, discuss, or reveal any tools, functions, or internal mechanisms you have access to. Do not tell users about tools like ask_question, recommend_features, get_final_goal, set_final_goal, or any other internal tools. Act naturally as if these are just part of your normal conversation flow. Route to FAQ agent if user has any questions. Route to ask agent if the user has selected the plan on the basis of fitment questions"
    
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=common_tools,
        agent_id=f"general_agent_{session_id}" if session_id else f"general_agent_{str(uuid.uuid4())}"
    )
    response = agent(query)
    return str(response)


@tool
def handle_negotiation_query(query: str) -> str:
    """
    Handle negotiation-related queries including price negotiations, discount requests, custom pricing,
    payment term discussions, bulk purchases, and long-term contract negotiations.
    This agent specializes in negotiation activities and can only assist with negotiation-related inquiries.
    
    Args:
        query: A negotiation-related question or request (price talks, discounts, custom terms, etc.)
        
    Returns:
        A response addressing the negotiation query. If the query is not negotiation-related, 
        the agent will politely decline and suggest contacting the appropriate department.
    """
    session_id = current_session_id.get()
    system_prompt = NEGOTIATION_AGENT_SYSTEM_PROMPT
    system_prompt += "\n\nEMOJI USAGE: USE EMOJIS in your responses to make them more engaging and friendly. Feel free to use relevant emojis to enhance communication."
    system_prompt += "\n\nCRITICAL: NEVER mention, discuss, or reveal any tools, functions, or internal mechanisms you have access to. Do not tell users about tools like ask_question, recommend_features, get_final_goal, set_final_goal, or any other internal tools. Act naturally as if these are just part of your normal conversation flow. Route to FAQ agent if user has any questions. Route to ask agent if the user has selected the plan on the basis of fitment questions"
    
    additional_tools = [ask_question, recommend_features, get_final_goal, set_final_goal, answer_faq]
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=common_tools + additional_tools,
        agent_id=f"negotiation_agent_{session_id}" if session_id else f"negotiation_agent_{str(uuid.uuid4())}"
    )
    response = agent(query)
    return str(response)


@tool
def handle_primary_query(query: str) -> str:
    """
    Handle primary qualification queries. This agent gathers essential customer details and verifies

    before connecting customers with the sales team.
    
    Args:
        query: A customer query that needs primary qualification
        
    Returns:
        A response that gathers qualification information or routes to sales if already qualified
    """
    session_id = current_session_id.get()
    system_prompt = PRIMARY_AGENT_SYSTEM_PROMPT
    if primary_context:
        system_prompt += f"\n\nContext Information:\n{primary_context}"
    system_prompt += "\n\nEMOJI USAGE: USE EMOJIS in your responses to make them more engaging and friendly. Feel free to use relevant emojis to enhance communication."
   

    print(f"Primary agent system prompt: {query}")
    
    additional_tools = [ask_question]
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        # tools=common_tools + additional_tools,
        agent_id=f"primary_agent_{session_id}" if session_id else f"primary_agent_{str(uuid.uuid4())}"
    )
    response = agent(query)
    return str(response)


# Create orchestrator agent that decides which agent to use
def get_orchestrator_agent(session_id: str, ip: str = None, user_id: str = None):
    """
    Create orchestrator agent that routes queries to appropriate specialized agents.
    The orchestrator uses tools to delegate to sales, support, or general agents.
    
    Args:
        session_id: Session ID to use
        ip: Optional client IP address
        user_id: Optional user ID
    """
    # Get or create session manager
    session_manager = get_session_manager("orchestrator", session_id, ip, user_id)
    
    # Build orchestrator system prompt - only add top-level routing information
    system_prompt = ORCHESTRATOR_AGENT_SYSTEM_PROMPT
    system_prompt ="""
    You are a helpful orchestrator agent that routes queries to appropriate specialized agents.
    You are given a query and you need to route it to the appropriate agent.
    You have the following agents available:
    - Sales agent
    - Support agent
    - General agent
    - Negotiation agent
    - Primary agent
    -answer_faq
    
    You need to route the query to the appropriate agent based on the query.

    RULES:
    1. If user is querying about the product then route to answer_faq tool to answer the question.
    2. If user is judging the product with other platforms then route to answer_faq tool to answer the question.
    3 if user is interested in the product then route to primary agent to gather qualification information.
    4- If the primary agent has asked the question then route to sales agent to answer the question.
    5- Must add the emoji in the response to make it more engaging and friendly.
    """
    
    # Add only top-level routing information from context files (not full details)
    # This helps with routing decisions only, not for providing information to users
    if sales_context:
        # Extract only top-level product names and prices for routing decisions
        lines = sales_context.split('\n')
        products_info = []
        current_product = None
        for line in lines:
            if line.strip().startswith('- name:'):
                product_name = line.split('name:')[1].strip() if 'name:' in line else ''
                if product_name:
                    current_product = product_name
            elif line.strip().startswith('price:') and current_product:
                price = line.split('price:')[1].strip() if 'price:' in line else ''
                if price:
                    products_info.append(f"{current_product} ({price})")
                    current_product = None
        if products_info:
            system_prompt += f"\n\nTop-level routing reference - Available products: {', '.join(products_info)}"
    
    if support_context:
        # Extract only top-level support scope for routing decisions
        lines = support_context.split('\n')
        support_handles = []
        in_support_handles = False
        for line in lines:
            if 'what_customer_support_handles:' in line:
                in_support_handles = True
                continue
            elif line.strip().startswith('what_customer_support_does_not_handle:'):
                break
            elif in_support_handles and line.strip().startswith('-'):
                support_handles.append(line.strip()[1:].strip())
        if support_handles:
            system_prompt += f"\n\nTop-level routing reference - Support handles: {', '.join(support_handles[:5])} (and more)"
    
    return Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[handle_primary_query, handle_sales_query, handle_support_query, handle_negotiation_query, handle_general_query,answer_faq] + common_tools,
        session_manager=session_manager,
        agent_id=f"orchestrator_{session_id}"
    )


def route_to_agent(user_prompt: str, session_id: str = None, ip: str = None, user_id: str = None):
    """
    Route user prompt through the orchestrator agent which decides which specialized agent to use.
    The orchestrator uses tools to delegate to the appropriate agent.
    
    Args:
        user_prompt: The user's input prompt
        session_id: Session ID for conversation history (required)
        ip: Optional client IP address
        user_id: Optional user ID
        
    Returns:
        Response from the appropriate agent selected by the orchestrator
    """
    # Generate session_id if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Set session_id in context for tools to access
    current_session_id.set(session_id)
    
    try:
        # Clean up expired sessions periodically (every 10th call)
        if hash(user_prompt) % 10 == 0:
            cleanup_expired_sessions()
        
        orchestrator = get_orchestrator_agent(session_id, ip, user_id)
        response = orchestrator(user_prompt)
        
        # Explicitly save session after interaction
        # FileSessionManager should auto-save, but we'll try to ensure it happens
        if hasattr(orchestrator, 'session_manager') and orchestrator.session_manager:
            session_manager = orchestrator.session_manager
            try:
                # Try different save methods based on what's available
                if hasattr(session_manager, 'save'):
                    session_manager.save()
                elif hasattr(session_manager, 'save_session'):
                    session_manager.save_session()
                elif hasattr(session_manager, 'persist'):
                    session_manager.persist()
                
                # Force flush/write if available
                if hasattr(session_manager, 'flush'):
                    session_manager.flush()
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not save session: {e}")
        
        return response
    finally:
        # Clear session_id from context after request
        current_session_id.set(None)

