"""Main entry point for the multi-agent system."""
import sys
import argparse
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from agents import route_to_agent, cleanup_expired_sessions, cleanup_all_sessions, model
from strands import Agent
import json
import uvicorn
# Initialize FastAPI app
app = FastAPI(title="Multi-Agent AI Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class AIAssistantRequest(BaseModel):
    msg: str
    sessionId: Optional[str] = None
    ip: Optional[str] = None
    user_id: Optional[str] = None

class Result(BaseModel):
    isUserSatisfied: bool = False
    answer: Optional[str] = None
    question: Optional[str] = None

class AIAssistantResponse(BaseModel):
    result: Result
    newMessages: list = []

# Sales Agent Request/Response models
class HistoryItem(BaseModel):
    type: str  # "sender" or "bot"
    content: str

class SalesAgentRequest(BaseModel):
    msg: str = ""
    history: List[HistoryItem] = []

class SalesAgentResult(BaseModel):
    goal: Optional[str] = None
    isAssistantNeeded: bool = False
    reason: str = ""

class SalesAgentResponse(BaseModel):
    status: bool
    result: SalesAgentResult


def interactive_mode(session_id: str = None):
    """Run in interactive mode with conversation history."""
    # Generate session_id if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    print("=" * 60)
    print("Multi-Agent System - Interactive Mode")
    print("=" * 60)
    print(f"Session ID: {session_id}")
    print("Type your message (or 'exit'/'quit' to end):")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                # print("\nGoodbye!")
                break
            
            # Route to appropriate agent with session_id
            response = route_to_agent(user_input, session_id=session_id)
            print("--------------------------------"*4)
            print(f"\n\n\n Orchestrator Agent:\n {response}\n")
            print("--------------------------------"*3)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


def single_query_mode(prompt: str, session_id: str = None):
    """Process a single query and return response."""
    # Generate session_id if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    try:
        response = route_to_agent(prompt, session_id=session_id)
        print(response)
        return response
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    # Clean up all sessions on startup
    cleanup_all_sessions()
    
    parser = argparse.ArgumentParser(
        description="Multi-Agent System with Customer Support, Sales, and General Agents"
    )
    parser.add_argument(
        '-p', '--prompt',
        type=str,
        help='Single prompt to process (non-interactive mode)'
    )
    parser.add_argument(
        '-s', '--session',
        type=str,
        help='Session ID for conversation history (default: auto-generated)'
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode (default if no prompt provided)'
    )
    
    args = parser.parse_args()
    
    # Determine session ID
    session_id = uuid.uuid4()
    print(f"Session ID: {session_id}")
    
    # If prompt provided, run single query mode
    if args.prompt:
        single_query_mode(args.prompt, session_id)
    else:
        # Otherwise run interactive mode
        interactive_mode(session_id)


# API Route
@app.post("/aiAssistant", response_model=AIAssistantResponse)
async def ai_assistant(request: AIAssistantRequest):
    """
    AI Assistant endpoint that processes user prompts through the multi-agent system.
    
    Args:
        request: Request body containing:
            - prompt: User's message/query
            - session_id: Optional session ID for conversation history
            - ip: Optional client IP address
            - user_id: Optional user ID
    
    Returns:
        Response containing:
            - response: AI assistant's response
            - session_id: Session ID used for this request
    """
    try:
        # Get or generate session_id
        if request.sessionId:
            session_id = request.sessionId
        else:
            session_id = str(uuid.uuid4())
        
        # Route the prompt through the agent system
        response = route_to_agent(
            user_prompt=request.msg,
            session_id=session_id,
            ip=request.ip,
            user_id=request.user_id
        )
        
        # Extract answer and question from response
        response_str = str(response)
        # Convert empty strings to None (null in JSON)
        answer = response_str.strip() if response_str and response_str.strip() else None
        question = None  # Can be extracted from response if needed
        
        # Create result object
        result = Result(
            isUserSatisfied=False,  # Default to False, can be determined from response
            answer=answer,
            question=question
        )
        
        return AIAssistantResponse(
            result=result,
            newMessages=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/api/SalesAgent/ask", response_model=SalesAgentResponse)
async def sales_agent_ask(request: SalesAgentRequest):
    """
    Sales Agent endpoint that analyzes chat history to extract sales details.
    
    Args:
        request: Request body containing:
            - msg: Current user message
            - history: Array of chat history items with type ("sender" or "bot") and content
    
    Returns:
        Response containing:
            - result: Object with goal, isAssistantNeeded, and reason
    """
    try:
        # Build history from client payload
        history = []
        previous_history = request.history if request.history else []
        
        for item in previous_history:
            role = "user" if item.type == "sender" else "bot"
            message = item.content if item.content else ""
            history.append({
                "role": role,
                "message": message
            })
        
        # Add current message to history
        if request.msg:
            history.append({
                "role": "user",
                "message": request.msg
            })
        
        # Build system prompt
        system_prompt = """You are a Sales Agent that analyzes the chat history between "bot" and "user".

Output strictly JSON (no extra text, no markdown, no code blocks):

{
  "goal": "<goal_from_salesDetails_or_null>",
  "isAssistantNeeded": false,
  "reason": "<short_reason>"
}

Rules:
- "goal": Must provide if user expressed interest in buying, purchasing, ordering, subscribing, getting pricing, or requesting a quote. Return the goal if specific or non-specific both situations. Return null if no sales interest detected.
- "isAssistantNeeded": Must be true if user expresses interest in buying, purchasing, ordering, subscribing, getting pricing, or requesting a quote. Otherwise false.
- "reason": Short explanation of your analysis.

Analyze the chat history and extract sales details. Output ONLY valid JSON."""
        
        # Format history for the prompt
        history_text = "\n".join([f'{item["role"]}: {item["message"]}' for item in history])
        user_prompt = f"Analyze this chat history:\n\n{history_text}\n\nProvide your analysis as JSON only:"
        
        # Create agent with the system prompt
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=[],
            agent_id=f"sales_analysis_agent_{str(uuid.uuid4())}"
        )
        
        # Invoke agent
        response = agent(user_prompt)
        response_str = str(response).strip()
        
        # Try to extract JSON from response
        # The response might contain markdown code blocks or extra text
        json_str = response_str
        
        # Remove markdown code blocks if present
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object in the response
        try:
            # Find the first { and last } to extract JSON
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx+1]
            
            # Parse JSON
            result_data = json.loads(json_str)
            
            # Extract fields with defaults
            goal = result_data.get("goal")
            if goal == "" or goal is None:
                goal = None
            
            is_assistant_needed = result_data.get("isAssistantNeeded", False)
            reason = result_data.get("reason", "")
            
        except (json.JSONDecodeError, KeyError) as e:
            # If JSON parsing fails, return default values
            goal = None
            is_assistant_needed = False
            reason = f"Error parsing response: {str(e)}"
        
        # Create result object
        result = SalesAgentResult(
            goal=goal,
            isAssistantNeeded=is_assistant_needed,
            reason=reason
        )
        
        return SalesAgentResponse(
            status=True,
            result=result
        )
        
    except Exception as e:
        # Return error response with status false
        error_result = SalesAgentResult(
            goal=None,
            isAssistantNeeded=False,
            reason=f"Error processing request: {str(e)}"
        )
        return SalesAgentResponse(
            status=False,
            result=error_result
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    # Check if running as API server
    cleanup_all_sessions()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    

