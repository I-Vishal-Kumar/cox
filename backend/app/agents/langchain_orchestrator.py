"""
LangChain-based orchestrator for Cox Automotive AI Analytics.
Uses create_agent with tools for flexible, streaming-capable query processing.
"""

from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass, field

from pathlib import Path
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from app.core.config import settings
from app.agents.tools import (
    generate_sql_query,
    analyze_kpi_data,
    analyze_fni_revenue_drop,
    analyze_logistics_delays,
    analyze_plant_downtime,
    generate_chart_configuration,
    create_tool_error_handler,
    DEMO_QUERIES
)
from app.utils.chart_utils import get_chart_manager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio


# Strands imports for session management
try:
    from strands.types.session import Session, SessionType, SessionAgent, SessionMessage
    from strands.types.content import Message
    from strands.session import FileSessionManager
except ImportError:
    Session = None
    SessionType = None
    SessionAgent = None
    SessionMessage = None
    Message = None
    FileSessionManager = None

# Agent ID for the orchestrator
AGENT_ID = "langchain_orchestrator"

# Session storage directory
SESSIONS_DIR = Path("data/sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AnalyticsContext:
    """Runtime context for analytics operations."""
    db_session: Optional[AsyncSession] = None
    session_id: Optional[str] = None
    session_manager: Optional[Any] = None  # FileSessionManager instance
    conversation_history: List[Dict] = field(default_factory=list)


def get_session_manager(session_id: str):
    """
    Create a FileSessionManager for the given session_id.
    
    Args:
        session_id: Session ID to use
        
    Returns:
        FileSessionManager instance or None if not available
    """
    try:
        if not FileSessionManager:
            return None
            
        # Create cache key for analytics
        cache_key = f"analytics_{session_id}"
        
        # Try different parameter names as API might vary
        try:
            return FileSessionManager(
                session_id=cache_key,
                storage_dir=str(SESSIONS_DIR)
            )
        except TypeError:
            try:
                return FileSessionManager(
                    session_id=cache_key,
                    session_dir=str(SESSIONS_DIR)
                )
            except TypeError:
                return FileSessionManager(session_id=cache_key)
    except ImportError:
        # FileSessionManager not available, return None
        return None


class LangChainAnalyticsOrchestrator:
    """
    Modern LangChain-based orchestrator using create_agent and tools.
    
    This orchestrator uses LangChain's ReAct pattern where a single agent
    intelligently selects and sequences tools based on query requirements.
    Supports streaming responses and dynamic tool selection.
    """

    def __init__(self, db_session_factory=None, sessions_dir: Optional[Path] = None):
        """
        Initialize the orchestrator with LangChain agent.
        
        Args:
            db_session_factory: Factory function to create database sessions
            sessions_dir: Directory for session storage (defaults to data/sessions)
        """
        self.db_session_factory = db_session_factory
        self.sessions_dir = sessions_dir or SESSIONS_DIR
        
        # Initialize LLM with OpenRouter configuration
        # Since we only have OpenRouter key, use OpenRouter configuration
        self.llm = ChatOpenAI(
            model=settings.openrouter_model,
            temperature=0.3,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            streaming=True
        )
        
        # Define available tools
        from app.agents.dashboard_tools import (
            get_weekly_fni_trends,
            get_enhanced_kpi_data,
            get_filtered_fni_data
        )
        
        self.tools = [
            generate_sql_query,
            analyze_kpi_data,
            analyze_fni_revenue_drop,
            analyze_logistics_delays,
            analyze_plant_downtime,
            generate_chart_configuration,
            # Dashboard-specific tools
            get_weekly_fni_trends,
            get_enhanced_kpi_data,
            get_filtered_fni_data,
        ]
        
        # Create the agent (without middleware for now to avoid async issues)
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self._get_system_prompt()
        )
        
        # Chart manager for visualization configs
        self.chart_manager = get_chart_manager()
    
    def _get_system_prompt(self) -> str:
        """
        Get the enhanced system prompt that guides tool selection and usage.
        
        Returns:
            System prompt string with scenario detection and tool selection guidance
        """
        return """You are an expert AI analytics assistant for Cox Automotive.

Your role is to help users analyze automotive business data including F&I revenue, logistics, manufacturing, marketing, and service operations.

**Available Tools:**

**Data Retrieval:**
1. **generate_sql_query** - Generates SQL from natural language AND executes it, returning the data as a string

**Analysis Tools:**
2. **analyze_kpi_data** - Analyzes data and provides insights (parses string data from generate_sql_query)
3. **analyze_fni_revenue_drop** - Specialized F&I revenue analysis (parses string data)
4. **analyze_logistics_delays** - Specialized logistics analysis (parses string data)
5. **analyze_plant_downtime** - Specialized manufacturing analysis (parses string data)

**Visualization:**
6. **generate_chart_configuration** - Creates visualizations (parses string data)

**Dashboard Tools (return structured JSON):**
7. **get_weekly_fni_trends** - Get weekly F&I revenue trends by region
8. **get_enhanced_kpi_data** - Get KPI data with period comparisons
9. **get_filtered_fni_data** - Get filtered F&I data by time/dealer/region/manager

**WORKFLOW:**

When a user asks a data question:

1. Call `generate_sql_query(query="user's question")` - this will return the data as a string
2. The tool output will be a string representation of the data (list of dictionaries)
3. Pass this string data to analysis tools like `analyze_kpi_data(data=<string from step 1>, ...)`
4. Provide the analysis to the user

**IMPORTANT**: 
- `generate_sql_query` executes the query and returns data directly - you don't need to execute anything
- Analysis tools expect the data parameter to be the string output from `generate_sql_query`
- If the user asks a greeting like "hello", respond naturally without using tools

**JSON-ONLY RESPONSE MODE:**

If the user's query includes phrases like:
- "return as JSON"
- "give me JSON"
- "format as JSON"
- "JSON only"
- "raw data"

Then you should:
1. Call the appropriate dashboard tool (get_weekly_fni_trends, get_enhanced_kpi_data, etc.)
2. Return ONLY the JSON data from the tool, with NO additional text or explanation
3. Do NOT add any conversational text before or after the JSON

**Example:**
User: "Get weekly F&I revenue trends for the last 4 weeks, return as JSON"
You should respond with ONLY:
```json
[
  {
    "week": "Week 1",
    "midwest": 318012.89,
    ...
  }
]
```

Respond directly to the user's query below."""
    
    async def process_query(
        self,
        query: str,
        db_session=None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the LangChain agent.
        
        Args:
            query: User's natural language question
            db_session: Database session for query execution
            session_id: Session ID for conversation persistence
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary containing query results, analysis, and visualizations
        """
        # Detect demo scenarios using query and conversation history
        demo_scenario = self._detect_demo_scenario(query, conversation_history)
        
        result = {
            "query": query,
            "query_type": demo_scenario or "general",
            "sql_query": None,
            "data": None,
            "analysis": None,
            "recommendations": [],
            "chart_config": None,
            "demo_scenario": demo_scenario
        }
        
        try:
            # Demo mode - bypass LLM and use pre-built responses
            if settings.demo_mode and demo_scenario:
                return await self._handle_demo_scenario(demo_scenario, db_session, result)
            
            # Get or create session manager
            session_manager: Optional[Any] = None
            if session_id:
                session_manager = get_session_manager(session_id)
                # Create session if it doesn't exist
                if not session_manager.read_session(session_id):
                    session_obj = Session(session_id=session_id, session_type=SessionType.AGENT)
                    session_manager.create_session(session=session_obj)
            
            # Create context
            context = AnalyticsContext(
                db_session=db_session,
                session_id=session_id,
                session_manager=session_manager,
                conversation_history=conversation_history or []
            )
            
            # Build messages for agent (with session manager support)
            messages = self._build_messages(
                query=query,
                conversation_history=conversation_history,
                session_manager=session_manager
            )
            
            # Invoke agent (non-streaming for now)
            response = await self.agent.ainvoke(
                {"messages": messages},
                context=context
            )
            
            # Extract results from agent response
            result["analysis"] = self._extract_analysis(response)
            
            # Try to extract structured data if SQL was executed
            if db_session and demo_scenario:
                # Use demo query
                result["sql_query"] = DEMO_QUERIES.get(demo_scenario, "")
                if result["sql_query"]:
                    result["data"] = await self._execute_sql(
                        result["sql_query"], 
                        db_session
                    )
            
            # Generate chart config if we have data
            if result["data"]:
                result["chart_config"] = self.chart_manager.get_config(
                    query_type=result["query_type"],
                    data=result["data"]
                )
            
        except Exception as e:
            result["error"] = str(e)
            result["analysis"] = f"I encountered an error processing your query: {str(e)}"
        
        return result
    

    
    def _detect_demo_scenario(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """
        Detect if query matches a demo scenario using query and conversation context.
        
        Args:
            query: User query string
            conversation_history: Recent conversation messages for context
            
        Returns:
            Demo scenario name or None
        """
        query_lower = query.lower()
        
        # Build context from recent conversation
        context_text = query_lower
        if conversation_history:
            # Add last 3 messages for context
            for msg in conversation_history[-3:]:
                content = msg.get("content", "").lower()
                context_text += " " + content
        
        # F&I scenario detection
        fni_keywords = ["f&i", "fni", "finance", "insurance", "midwest", "penetration", "service contract"]
        fni_action_keywords = ["drop", "decline", "down", "why", "cause", "reason", "problem"]
        
        has_fni = any(term in context_text for term in fni_keywords)
        has_action = any(term in context_text for term in fni_action_keywords)
        
        if has_fni and has_action:
            return "fni_midwest"
        
        # Logistics scenario detection
        logistics_keywords = ["delay", "carrier", "route", "weather", "shipment", "delivery", "late", "dwell"]
        if any(term in context_text for term in logistics_keywords):
            return "logistics_delays"
        
        # Plant scenario detection
        plant_keywords = ["plant", "downtime", "production", "manufacturing", "line", "maintenance", "quality"]
        if any(term in context_text for term in plant_keywords):
            return "plant_downtime"
        
        return None
    

    
    async def _execute_sql(self, sql_query: str, db_session) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        Args:
            sql_query: SQL query string
            db_session: Database session
            
        Returns:
            List of result dictionaries
        """
        try:
            query_result = await db_session.execute(text(sql_query))
            rows = query_result.fetchall()
            columns = query_result.keys()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return []
    
    def _extract_analysis(self, response: Any) -> str:
        """
        Extract analysis text from agent response.
        
        Args:
            response: Agent response object
            
        Returns:
            Analysis text string
        """
        # Extract content from response
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, dict):
            return response.get('output', str(response))
        else:
            return str(response)
    



    async def process_query_stream(
        self,
        query: str,
        db_session: Optional[AsyncSession] = None,
        conversation_history: Optional[List[Dict]] = None,
        session_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a user query with enhanced streaming responses and proper context management.
        
        This method provides real-time updates as the agent processes the query,
        including tool execution status, intermediate results, and final analysis.
        Uses FileSessionManager for conversation persistence.
        
        Args:
            query: User's natural language question
            db_session: Database session for query execution
            conversation_history: Previous conversation messages
            session_id: Session ID for conversation persistence
            
        Yields:
            Chunks of the response with type indicators:
            - {"type": "status", "content": "..."} - Status updates
            - {"type": "tool_start", "tool": "...", "input": {...}} - Tool execution start
            - {"type": "tool_end", "tool": "...", "output": {...}} - Tool execution end
            - {"type": "chunk", "content": "..."} - LLM response chunks
            - {"type": "data", "data": [...]} - Retrieved data
            - {"type": "analysis", "content": "..."} - Analysis text
            - {"type": "chart", "config": {...}} - Chart configuration
            - {"type": "complete", "result": {...}} - Final complete result
            - {"type": "error", "error": "..."} - Error information
        """
        # Get or create session manager
        session_manager: Optional[Any] = None
        if session_id:
            session_manager = get_session_manager(session_id)
            # Create session if it doesn't exist
            if not session_manager.read_session(session_id):
                session_obj = Session(session_id=session_id, session_type=SessionType.AGENT)
                session_manager.create_session(session=session_obj)
        
        # Create context with proper async context management
        context = AnalyticsContext(
            db_session=db_session,
            session_id=session_id,
            session_manager=session_manager,
            conversation_history=conversation_history or []
        )
        
        result = {
            "query": query,
            "query_type": None,
            "sql_query": None,
            "data": None,
            "analysis": "",
            "recommendations": [],
            "chart_config": None
        }
        
        try:
            # Yield initial status
            yield {
                "type": "status",
                "content": "Processing your query..."
            }
            
            # Detect demo scenario using query and conversation history
            demo_scenario = self._detect_demo_scenario(query, conversation_history)
            if demo_scenario:
                yield {
                    "type": "status",
                    "content": f"Detected demo scenario: {demo_scenario}"
                }
                result["demo_scenario"] = demo_scenario
                
                # Handle demo mode
                if settings.demo_mode:
                    demo_result = await self._handle_demo_scenario(demo_scenario, db_session, result)
                    yield {
                        "type": "chunk",
                        "content": demo_result["analysis"]
                    }
                    if demo_result.get("data"):
                        yield {
                            "type": "data",
                            "data": demo_result["data"]
                        }
                    if demo_result.get("chart_config"):
                        yield {
                            "type": "chart",
                            "config": demo_result["chart_config"]
                        }
                    yield {
                        "type": "complete",
                        "result": demo_result
                    }
                    # Save assistant response to session
                    if session_manager and demo_result["analysis"]:
                        try:
                            actual_session_id = session_manager.session_id
                            ai_msg = Message(role="assistant", content=demo_result["analysis"])
                            
                            # Determine next message ID
                            messages = session_manager.list_messages(actual_session_id, AGENT_ID)
                            next_id = len(messages)
                            
                            session_msg = SessionMessage.from_message(message=ai_msg, index=next_id)
                            session_manager.create_message(actual_session_id, AGENT_ID, session_msg)
                        except Exception as e:
                            print(f"Failed to save assistant message: {e}")
                    return
            
            # Use demo scenario as query type
            result["query_type"] = demo_scenario or "general"
            
            # Ensure agent exists BEFORE building messages (so history can be loaded)
            if session_manager and SessionAgent:
                try:
                    # Use session_manager.session_id to get the actual session ID (with prefix)
                    actual_session_id = session_manager.session_id
                    print(f"[DEBUG] Checking if agent exists for session {actual_session_id}")
                    agent = session_manager.read_agent(actual_session_id, AGENT_ID)
                    print(f"[DEBUG] Agent read result: {agent}")
                    if not agent:
                        print(f"[DEBUG] Creating agent for session {actual_session_id}")
                        session_agent = SessionAgent(
                            agent_id=AGENT_ID,
                            state={},
                            conversation_manager_state={}
                        )
                        print(f"[DEBUG] SessionAgent object created: {session_agent}")
                        session_manager.create_agent(actual_session_id, session_agent)
                        print(f"[DEBUG] Agent created successfully")
                except Exception as e:
                    print(f"[ERROR] Failed to ensure agent exists: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Build messages (with session manager support)
            print(f"[DEBUG] Building messages for query: {query}")
            print(f"[DEBUG] Conversation history provided: {conversation_history}")
            print(f"[DEBUG] Session manager: {session_manager}")
            messages = self._build_messages(
                query=query,
                conversation_history=conversation_history,
                session_manager=session_manager
            )
            print(f"[DEBUG] Built messages count: {len(messages)}")
            for i, msg in enumerate(messages):
                print(f"[DEBUG] Message {i}: {type(msg).__name__} - {msg.content[:100] if hasattr(msg, 'content') else msg}")
            
            # Save user message to session
            if session_manager and SessionMessage:
                try:
                    # Use session_manager.session_id to get the actual session ID (with prefix)
                    actual_session_id = session_manager.session_id
                    
                    # Create user message
                    user_msg = Message(role="user", content=query)
                    
                    # Determine next message ID
                    messages_list = session_manager.list_messages(actual_session_id, AGENT_ID)
                    next_id = len(messages_list)
                    
                    session_msg = SessionMessage.from_message(message=user_msg, index=next_id)
                    session_manager.create_message(actual_session_id, AGENT_ID, session_msg)
                    print(f"[DEBUG] Saved user message with ID {next_id} to session {actual_session_id}")
                except Exception as e:
                    print(f"Failed to save user message: {e}")
            
            # Configure runnable with context
            config = RunnableConfig(
                metadata={
                    "session_id": session_id,
                    "db_session": db_session,
                    "session_manager": session_manager
                }
            )
            
            # Stream agent response with proper error handling
            analysis_chunks = []
            
            try:
                # Use astream for simpler streaming
                async for chunk in self.agent.astream(
                    {"messages": messages},
                    config=config
                ):
                    # Extract content from chunk
                    if isinstance(chunk, dict):
                        # Handle LangGraph chunk format: {'node_name': {'messages': [AIMessage(...)]}}
                        for key, value in chunk.items():
                            if isinstance(value, dict) and "messages" in value:
                                messages = value["messages"]
                                if messages and isinstance(messages, list):
                                    last_message = messages[-1]
                                    if hasattr(last_message, "content"):
                                        content = last_message.content
                                        if content:
                                            analysis_chunks.append(content)
                                            yield {
                                                "type": "chunk",
                                                "content": content
                                            }
                        
                        # Handle standard dict format (fallback)
                        if "output" in chunk:
                            content = chunk["output"]
                            analysis_chunks.append(str(content))
                            yield {
                                "type": "chunk",
                                "content": str(content)
                            }
                            
                    elif hasattr(chunk, "content"):
                        content = chunk.content
                        if content:
                            analysis_chunks.append(content)
                            yield {
                                "type": "chunk",
                                "content": content
                            }
                
                # Combine analysis chunks
                result["analysis"] = "".join(analysis_chunks)
                
                # If demo scenario, execute demo query
                if demo_scenario and db_session:
                    demo_sql = DEMO_QUERIES.get(demo_scenario)
                    if demo_sql:
                        result["sql_query"] = demo_sql
                        data = await self._execute_sql(demo_sql, db_session)
                        result["data"] = data
                        yield {
                            "type": "data",
                            "data": data
                        }
                
                # Generate chart config if we have data
                if result["data"] and result["query_type"]:
                    chart_config = self.chart_manager.get_config(
                        query_type=result["query_type"],
                        data=result["data"]
                    )
                    if chart_config:
                        result["chart_config"] = chart_config
                        yield {
                            "type": "chart",
                            "config": chart_config
                        }
                
                # Yield final complete result
                yield {
                    "type": "complete",
                    "result": result
                }

                # Save assistant response to session
                if session_manager and result["analysis"]:
                    try:
                        actual_session_id = session_manager.session_id
                        ai_msg = Message(role="assistant", content=result["analysis"])
                        
                        # Determine next message ID
                        messages = session_manager.list_messages(actual_session_id, AGENT_ID)
                        next_id = len(messages)
                        
                        session_msg = SessionMessage.from_message(message=ai_msg, index=next_id)
                        session_manager.create_message(actual_session_id, AGENT_ID, session_msg)
                        print(f"[DEBUG] Saved assistant message with ID {next_id} to session {actual_session_id}")
                    except Exception as e:
                        print(f"Failed to save assistant message: {e}")
                
            except asyncio.CancelledError:
                # Handle streaming interruption gracefully
                yield {
                    "type": "status",
                    "content": "Stream interrupted by user"
                }
                # Cleanup resources
                if db_session:
                    await db_session.rollback()
                raise
            
        except Exception as e:
            # Handle errors gracefully
            yield {
                "type": "error",
                "error": str(e),
                "message": f"An error occurred: {str(e)}"
            }
            # Cleanup on error
            if db_session:
                await db_session.rollback()
    
    def _get_conversation_history_from_session(
        self, 
        session_manager: Optional[Any]
    ) -> List[Dict]:
        """
        Retrieve conversation history from session manager.
        
        Args:
            session_manager: FileSessionManager instance
            
        Returns:
            List of conversation messages
        """
        print(f"[DEBUG _get_conversation_history_from_session] Called with session_manager: {session_manager}")
        if not session_manager:
            print(f"[DEBUG _get_conversation_history_from_session] No session manager, returning empty list")
            return []
        
        try:
            # Use list_messages API
            if hasattr(session_manager, 'list_messages'):
                # We need the session_id used to initialize the manager.
                # The manager instance might have it.
                session_id = getattr(session_manager, 'session_id', None)
                
                if session_id:
                    print(f"[DEBUG _get_conversation_history_from_session] Found session_id: {session_id}")
                    # We pass None for agent_id as we are not using agents in that sense yet
                    # But wait, we are using AGENT_ID constant now
                    # Let's try to use AGENT_ID if available, or fallback
                    agent_id = AGENT_ID if 'AGENT_ID' in globals() else "langchain_orchestrator"
                    print(f"[DEBUG _get_conversation_history_from_session] Using agent_id: {agent_id}")
                    
                    try:
                        messages = session_manager.list_messages(session_id=session_id, agent_id=agent_id, limit=20)
                        print(f"[DEBUG _get_conversation_history_from_session] Retrieved {len(messages)} messages")
                    except Exception as e:
                        # Fallback if agent doesn't exist yet or messages directory not created
                        error_msg = str(e)
                        if "Messages directory missing" in error_msg or "does not exist" in error_msg:
                            print(f"[DEBUG _get_conversation_history_from_session] No messages yet (first conversation): {error_msg}")
                        else:
                            print(f"[DEBUG _get_conversation_history_from_session] Failed to list messages: {e}")
                        return []
                    
                    history = []
                    for msg in messages:
                        # msg is SessionMessage, so it has .message attribute which is Message dict
                        if hasattr(msg, 'message'):
                            inner_msg = msg.message
                            if isinstance(inner_msg, dict):
                                history.append({
                                    "role": inner_msg.get("role"),
                                    "content": inner_msg.get("content")
                                })
                        elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                             history.append({
                                "role": msg.role,
                                "content": msg.content
                            })
                    print(history)
                    return history
        except Exception as e:
            print(f"Error reading history: {e}")
            pass
        
        return []
    
    def _build_messages(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict]] = None,
        session_manager: Optional[Any] = None
    ) -> List:
        """
        Build message list for agent from query and history.
        Retrieves history from session manager if not provided.
        
        Args:
            query: Current user query
            conversation_history: Previous conversation messages (optional)
            session_manager: FileSessionManager instance (optional)
            
        Returns:
            List of LangChain message objects
        """
        messages = []
        
        # Get conversation history from session manager if not provided
        print(f"[DEBUG _build_messages] conversation_history param: {conversation_history}")
        print(f"[DEBUG _build_messages] session_manager: {session_manager}")
        if not conversation_history and session_manager:
            print(f"[DEBUG _build_messages] Loading history from session manager...")
            conversation_history = self._get_conversation_history_from_session(session_manager)
            print(f"[DEBUG _build_messages] Loaded history: {conversation_history}")
        
        # Add conversation history (last 5 messages for context)
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user" or role == "human":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant" or role == "ai":
                    messages.append(AIMessage(content=content))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        return messages
    
    async def _handle_demo_scenario(self, demo_scenario: str, db_session, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle demo scenarios without LLM."""
        
        # Execute demo SQL query
        if db_session and demo_scenario in DEMO_QUERIES:
            result["sql_query"] = DEMO_QUERIES[demo_scenario]
            result["data"] = await self._execute_sql(result["sql_query"], db_session)
        
        # Generate demo analysis based on scenario
        if demo_scenario == "fni_midwest":
            result["analysis"] = """Based on the data analysis, F&I revenue dropped across Midwest dealers this week due to several key factors:

**Root Cause Analysis:**
1. **Penetration Rate Decline**: Service contract penetration dropped from 42% to 38% across Midwest dealers
2. **Dealer Performance Issues**: 3 underperforming dealers (ABC Ford, XYZ Nissan, Midtown Auto) contributed to 60% of the revenue decline
3. **Finance Manager Training Gap**: New finance managers at these locations lack proper F&I sales training
4. **Seasonal Impact**: Winter weather reduced customer foot traffic by 15%

**Key Metrics:**
- F&I Revenue: Down 11% vs last week ($2.1M vs $2.4M)
- Service Contract Sales: Down 18% 
- Gap Insurance: Down 8%
- Affected Dealers: 5 out of 12 Midwest locations

**Recommendations:**
1. Immediate F&I training for underperforming finance managers
2. Implement daily F&I performance tracking dashboard
3. Review pricing strategy for winter months
4. Deploy F&I coaching resources to ABC Ford, XYZ Nissan, and Midtown Auto"""
            
        elif demo_scenario == "logistics_delays":
            result["analysis"] = """Analysis of shipment delays reveals a multi-factor attribution:

**Delay Attribution:**
1. **Carrier Issues (45%)**: Carrier X experiencing driver shortages on Chicago-Detroit route
2. **Weather Impact (30%)**: Winter storms caused 2-day delays across Midwest corridor  
3. **Route Congestion (25%)**: I-94 construction increased dwell time by 8 hours average

**Key Findings:**
- 18% of shipments delayed (vs 5% target)
- Average delay: 2.3 days
- Most affected route: Chicago → Detroit (67% of delays)
- Peak delay period: Monday-Wednesday

**Immediate Actions:**
1. Switch 40% of Chicago-Detroit volume to Carrier Y (backup)
2. Implement weather-based routing alerts
3. Negotiate expedited service with Carrier X for critical shipments"""
            
        elif demo_scenario == "plant_downtime":
            result["analysis"] = """Plant downtime analysis shows concentrated issues at specific facilities:

**Downtime Summary:**
- **Plant A (Kentucky)**: 12 hours downtime - Supplier part shortage (Brake Components Inc.)
- **Plant B (Ohio)**: 8 hours downtime - Planned maintenance overrun on Line 2
- **Plant C (Michigan)**: 4 hours downtime - Quality hold on paint system

**Root Causes:**
1. **Supplier Issues (50%)**: Brake Components Inc. delivery delays due to raw material shortage
2. **Maintenance Overruns (33%)**: Line 2 maintenance took 3 hours longer than scheduled
3. **Quality Issues (17%)**: Paint system calibration problems

**Impact:**
- Total Production Loss: 340 units
- Revenue Impact: $8.5M
- Recovery Timeline: 2-3 days

**Action Plan:**
1. Activate backup supplier for brake components
2. Review maintenance scheduling procedures
3. Implement predictive maintenance on paint systems"""
        
        else:
            result["analysis"] = f"Demo analysis for scenario: {demo_scenario}"
        
        # Generate chart config
        if result["data"]:
            result["chart_config"] = self.chart_manager.get_config(
                query_type=demo_scenario,
                data=result["data"]
            )
        
        return result
    

