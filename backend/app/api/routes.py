"""API routes for Cox Automotive AI Analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import json
import asyncio
from datetime import datetime
import uuid

from app.db.database import get_db
from app.models.schemas import (
    ChatRequest, ChatResponse, QueryType,
    KPIAlert, DashboardMetric, InviteDashboardData
)
from app.agents.orchestrator import AnalyticsOrchestrator  # Old orchestrator (kept for compatibility)
from app.agents.langchain_orchestrator import LangChainAnalyticsOrchestrator  # New LangChain orchestrator
from app.services.analytics_service import AnalyticsService

router = APIRouter()

# Store conversation histories (in production, use Redis or database)
conversation_store: Dict[str, List[Dict]] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process a natural language query and return analysis.
    Now uses the new LangChain-based orchestrator.
    """
    # Initialize new LangChain orchestrator
    orchestrator = LangChainAnalyticsOrchestrator()

    # Get or create conversation ID
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Get conversation history
    history = conversation_store.get(conversation_id, [])

    # Process the query with new orchestrator
    result = await orchestrator.process_query(
        query=request.message,
        db_session=db,
        session_id=conversation_id,
        conversation_history=history
    )

    # Store in conversation history
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": result.get("analysis", "")})
    conversation_store[conversation_id] = history[-20:]  # Keep last 20 messages

    # Map query type
    query_type_map = {
        "fni_analysis": QueryType.CONVERSATIONAL_BI,
        "fni_midwest": QueryType.CONVERSATIONAL_BI,
        "logistics_analysis": QueryType.CONVERSATIONAL_BI,
        "logistics_delays": QueryType.CONVERSATIONAL_BI,
        "plant_analysis": QueryType.CONVERSATIONAL_BI,
        "plant_downtime": QueryType.CONVERSATIONAL_BI,
        "marketing_analysis": QueryType.CONVERSATIONAL_BI,
        "kpi_monitoring": QueryType.KPI_MONITORING,
        "data_catalog": QueryType.DATA_CATALOG,
        "general": QueryType.CONVERSATIONAL_BI
    }

    return ChatResponse(
        message=result.get("analysis", "I couldn't process that query."),
        conversation_id=conversation_id,
        query_type=query_type_map.get(result.get("query_type", "general"), QueryType.CONVERSATIONAL_BI),
        sql_query=result.get("sql_query"),
        data=result.get("data"),
        chart_config=result.get("chart_config"),
        recommendations=result.get("recommendations", [])
    )


@router.get("/chat/stream")
async def chat_stream(
    message: str = Query(..., description="The user's question"),
    conversation_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream a response for longer queries using the new LangChain orchestrator.
    Provides real-time updates as the agent processes the query.
    """
    async def generate():
        # Initialize new LangChain orchestrator
        orchestrator = LangChainAnalyticsOrchestrator()
        conv_id = conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        history = conversation_store.get(conv_id, [])

        # Send initial acknowledgment
        yield f"data: {json.dumps({'type': 'start', 'conversation_id': conv_id})}\n\n"

        try:
            # Use the new streaming method from LangChain orchestrator
            async for chunk in orchestrator.process_query_stream(
                query=message,
                db_session=db,
                conversation_history=history,
                session_id=conv_id
            ):
                # Forward all chunks from the orchestrator
                yield f"data: {json.dumps(chunk)}\n\n"
                
                # Store final result in conversation history
                if chunk.get("type") == "complete":
                    result = chunk.get("result", {})
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": result.get("analysis", "")})
                    conversation_store[conv_id] = history[-20:]  # Keep last 20 messages
                    
        except Exception as e:
            # Send error message
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/dashboard/invite")
async def get_invite_dashboard(
    dealer_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get data for the Invite (Marketing) dashboard.
    """
    service = AnalyticsService(db)
    data = await service.get_invite_dashboard_data(dealer_id)
    return data


@router.get("/dashboard/fni")
async def get_fni_dashboard(
    region: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get F&I analysis dashboard data.
    """
    service = AnalyticsService(db)
    data = await service.get_fni_analysis(region)
    return data


@router.get("/dashboard/logistics")
async def get_logistics_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get logistics and shipment delay dashboard data.
    """
    service = AnalyticsService(db)
    data = await service.get_logistics_analysis()
    return data


@router.get("/dashboard/plant")
async def get_plant_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get plant downtime analysis dashboard data.
    """
    service = AnalyticsService(db)
    data = await service.get_plant_downtime_analysis()
    return data


@router.get("/kpi/metrics")
async def get_kpi_metrics(
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get KPI metrics with optional filtering.
    """
    service = AnalyticsService(db)
    metrics = await service.get_kpi_metrics(category, region, days)
    return {"metrics": metrics}


@router.get("/kpi/alerts")
async def get_kpi_alerts(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current KPI alerts based on anomaly detection.
    """
    service = AnalyticsService(db)
    alerts = await service.get_alerts()
    return {"alerts": alerts}


@router.get("/data-catalog/tables")
async def get_data_catalog():
    """
    Get data catalog information - available tables and their schemas.
    """
    catalog = {
        "tables": [
            {
                "name": "dealers",
                "description": "Dealer information including location and region",
                "columns": ["id", "dealer_code", "name", "region", "state", "city"],
                "row_count": "~12"
            },
            {
                "name": "fni_transactions",
                "description": "Finance & Insurance transaction records",
                "columns": ["id", "dealer_id", "transaction_date", "fni_revenue", "penetration_rate", "finance_manager"],
                "row_count": "~2,000+"
            },
            {
                "name": "shipments",
                "description": "Vehicle shipment and logistics data",
                "columns": ["shipment_id", "carrier", "route", "status", "delay_reason", "dwell_time_hours"],
                "row_count": "~400+"
            },
            {
                "name": "plant_downtime",
                "description": "Manufacturing plant downtime events",
                "columns": ["plant_id", "event_date", "line_number", "downtime_hours", "reason_category", "supplier"],
                "row_count": "~20"
            },
            {
                "name": "marketing_campaigns",
                "description": "Marketing campaign performance (Xtime Invite)",
                "columns": ["campaign_name", "emails_sent", "unique_opens", "ro_count", "revenue"],
                "row_count": "~1,000+"
            },
            {
                "name": "kpi_metrics",
                "description": "Daily KPI metric values and targets",
                "columns": ["metric_name", "metric_value", "metric_date", "target_value", "variance"],
                "row_count": "~3,000+"
            }
        ],
        "regions": ["Midwest", "Northeast", "Southeast", "West"],
        "kpi_categories": ["Sales", "Service", "F&I", "Marketing", "Logistics"]
    }
    return catalog


@router.get("/demo/scenarios")
async def get_demo_scenarios():
    """
    Get pre-built demo scenarios for testing.
    """
    scenarios = [
        {
            "id": "fni_midwest",
            "title": "F&I Revenue Drop in Midwest",
            "question": "Why did F&I revenue drop across Midwest dealers this week?",
            "category": "F&I Analysis"
        },
        {
            "id": "logistics_delays",
            "title": "Logistics Delays Analysis",
            "question": "Who delayed — carrier, route, or weather?",
            "category": "Logistics"
        },
        {
            "id": "plant_downtime",
            "title": "Plant Downtime & Root Cause",
            "question": "Which plants showed downtime and why?",
            "category": "Manufacturing"
        }
    ]
    return {"scenarios": scenarios}
