"""API routes for Cox Automotive AI Analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    
    **Expected Input (ChatRequest):**
    - message: str - User's natural language query
    - conversation_id: Optional[str] - Session ID for conversation continuity
    - query_type: Optional[QueryType] - Optional query type hint
    
    **Expected Output (ChatResponse):**
    - message: str - AI-generated analysis/response
    - conversation_id: str - Session ID
    - query_type: QueryType - Detected query type
    - sql_query: Optional[str] - SQL query executed (if any)
    - data: Optional[List[Dict[str, Any]]] - Query results data
    - chart_config: Optional[Dict[str, Any]] - Chart configuration for visualization
    - recommendations: Optional[List[str]] - Actionable recommendations
    - sources: Optional[List[str]] - Data sources used
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
    
    **Expected Input (Query Parameters):**
    - message: str (required) - User's natural language query
    - conversation_id: Optional[str] - Session ID for conversation continuity
    
    **Expected Output (Server-Sent Events):**
    - type: "start" | "chunk" | "complete" | "error"
    - conversation_id: str (on start)
    - content: str (on chunk)
    - result: Dict[str, Any] (on complete) - Full ChatResponse data
    - error: str (on error)
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
    
    **Expected Input (Query Parameters):**
    - dealer_id: Optional[int] - Filter by specific dealer ID
    
    **Expected Output (Dict[str, Any]):**
    - program_summary: Dict[str, Any] - Total programs, emails, opens, revenue
    - program_performance: List[Dict[str, Any]] - Campaign performance data
    - monthly_metrics: List[Dict[str, Any]] - Monthly trend data
    - last_updated: str - ISO timestamp
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
    
    **Expected Input (Query Parameters):**
    - region: Optional[str] - Filter by region (Midwest, Northeast, Southeast, West)
    
    **Expected Output (Dict[str, Any]):**
    - weekly_trends: List[Dict[str, Any]] - Weekly F&I revenue trends
    - kpi_data: Dict[str, Any] - KPI metrics and comparisons
    - filtered_data: List[Dict[str, Any]] - Filtered transaction data
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
    
    **Expected Input:**
    - None (no query parameters)
    
    **Expected Output (Dict[str, Any]):**
    - delay_summary: Dict[str, Any] - Overall delay statistics
    - carrier_performance: List[Dict[str, Any]] - Performance by carrier
    - route_analysis: List[Dict[str, Any]] - Route-level delay data
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
    
    **Expected Input:**
    - None (no query parameters)
    
    **Expected Output (Dict[str, Any]):**
    - downtime_summary: Dict[str, Any] - Overall downtime statistics
    - plant_breakdown: List[Dict[str, Any]] - Downtime by plant
    - root_causes: List[Dict[str, Any]] - Root cause analysis
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
    
    **Expected Input (Query Parameters):**
    - category: Optional[str] - Filter by KPI category (Sales, Service, F&I, Marketing, Logistics)
    - region: Optional[str] - Filter by region
    - days: int (default: 30, range: 1-365) - Number of days to look back
    
    **Expected Output (Dict[str, Any]):**
    - metrics: List[Dict[str, Any]] - KPI metric data with values, targets, variances
    """
    service = AnalyticsService(db)
    metrics = await service.get_kpi_metrics(category, region, days)
    return {"metrics": metrics}


@router.get("/kpi/alerts")
async def get_kpi_alerts(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current KPI alerts from stored alerts table.
    
    **Expected Input:**
    - None (no query parameters)
    
    **Expected Output (Dict[str, Any]):**
    - alerts: List[KPIAlert] - List of active KPI alerts
    """
    service = AnalyticsService(db)
    alerts = await service.get_alerts()
    return {"alerts": alerts}


@router.post("/kpi/alerts/detect")
async def detect_anomalies_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger anomaly detection and store results in database.
    
    **Expected Input:**
    - None (no body parameters)
    
    **Expected Output (Dict[str, Any]):**
    - anomalies_detected: int - Number of anomalies found
    - alerts_stored: int - Number of new alerts stored
    - timestamp: str - Detection timestamp
    """
    service = AnalyticsService(db)
    result = await service.detect_and_store_anomalies()
    return result


@router.post("/kpi/alerts/seed")
async def seed_anomalies(
    db: AsyncSession = Depends(get_db)
):
    """
    Seed sample anomalies for testing/demo purposes.
    
    **Expected Input:**
    - None (no body parameters)
    
    **Expected Output (Dict[str, Any]):**
    - alerts_created: int - Number of alerts created
    - timestamp: str - Creation timestamp
    """
    from app.db.models import KPIAlert
    from datetime import datetime, timedelta
    
    service = AnalyticsService(db)
    
    # Create sample alerts
    sample_alerts = [
        {
            'alert_id': f'seed_critical_{datetime.now().strftime("%Y%m%d_%H%M%S")}_1',
            'metric_name': 'F&I Revenue - Midwest',
            'current_value': 42500.0,
            'previous_value': 47800.0,
            'change_percent': -11.1,
            'severity': 'critical',
            'message': 'F&I revenue dropped significantly. Current: 42500.0, Target: 50000.0',
            'root_cause': 'Anomaly detected in F&I Revenue - Midwest. Variance: -11.1%. Investigate root cause of decline.',
            'region': 'Midwest',
            'category': 'F&I',
        },
        {
            'alert_id': f'seed_warning_{datetime.now().strftime("%Y%m%d_%H%M%S")}_2',
            'metric_name': 'Shipment Delays',
            'current_value': 18.0,
            'previous_value': 8.0,
            'change_percent': 125.0,
            'severity': 'warning',
            'message': 'Shipment delay rate increased significantly. Current: 18.0%, Target: 5.0%',
            'root_cause': 'Anomaly detected in Shipment Delays. Variance: 125.0%. Review factors driving increase.',
            'region': 'All',
            'category': 'Logistics',
        },
        {
            'alert_id': f'seed_info_{datetime.now().strftime("%Y%m%d_%H%M%S")}_3',
            'metric_name': 'Service Appointments',
            'current_value': 145.0,
            'previous_value': 132.0,
            'change_percent': 9.8,
            'severity': 'info',
            'message': 'Service appointment volume increased. Current: 145.0, Target: 140.0',
            'root_cause': 'Anomaly detected in Service Appointments. Variance: 9.8%. Monitor trend closely.',
            'region': 'All',
            'category': 'Service',
        },
    ]
    
    created_count = 0
    for alert_data in sample_alerts:
        # Check if already exists
        existing = await db.execute(
            select(KPIAlert).where(KPIAlert.alert_id == alert_data['alert_id'])
        )
        if existing.scalar_one_or_none():
            continue
        
        alert = KPIAlert(
            **alert_data,
            status='active',
            detected_at=datetime.now()
        )
        db.add(alert)
        created_count += 1
    
    await db.commit()
    
    return {
        'alerts_created': created_count,
        'timestamp': datetime.now().isoformat()
    }


@router.post("/kpi/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    dismissed_by: str = Query("user", description="User who dismissed the alert"),
    db: AsyncSession = Depends(get_db)
):
    """
    Dismiss a specific alert.
    
    **Expected Input:**
    - alert_id: str (path parameter) - Alert ID to dismiss
    
    **Expected Output (Dict[str, Any]):**
    - success: bool - Whether dismissal was successful
    - message: str - Status message
    """
    service = AnalyticsService(db)
    success = await service.dismiss_alert(alert_id, dismissed_by)
    
    if success:
        return {"success": True, "message": "Alert dismissed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Alert not found or already dismissed")


@router.get("/kpi/alerts/{alert_id}")
async def get_alert_details(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific alert for investigation.
    
    **Expected Input:**
    - alert_id: str (path parameter) - Alert ID to investigate
    
    **Expected Output (Dict[str, Any]):**
    - alert: Dict with full alert details including investigation notes
    """
    service = AnalyticsService(db)
    alert = await service.get_alert_by_id(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"alert": alert}


@router.get("/inspect/repair-orders")
async def get_repair_orders(
    ro_type: Optional[str] = Query(None),
    shop_type: Optional[str] = Query(None),
    waiter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get repair orders for the inspection dashboard.
    
    **Expected Input (Query Parameters):**
    - ro_type: Optional[str] - Filter by RO type (Standard, Express, Warranty)
    - shop_type: Optional[str] - Filter by shop type (Service, Body Shop, Quick Service)
    - waiter: Optional[str] - Filter by waiter status (Yes, No)
    - search: Optional[str] - Search by RO number or customer name
    
    **Expected Output (Dict[str, Any]):**
    - repair_orders: List[Dict[str, Any]] - List of repair orders with:
      - id: int
      - ro: str (RO number)
      - p: str (Priority)
      - tag: str
      - promised: str (Promised time)
      - promised_date: date
      - e: str (Indicator)
      - customer: str (Customer name)
      - adv: str (Advisor ID)
      - tech: str (Technician ID)
      - mt: str (Metric time)
      - pt: str (Process time in days)
      - status: str (awaiting_dispatch, in_inspection, pending_approval, in_repair, pending_review)
      - ro_type: str
      - shop_type: str
      - waiter: str
      - is_overdue: bool
      - is_urgent: bool
    """
    service = AnalyticsService(db)
    orders = await service.get_repair_orders(ro_type, shop_type, waiter, search)
    return {"repair_orders": orders}


@router.get("/engage/appointments")
async def get_service_appointments(
    date: Optional[str] = Query(None, description="Appointment date (YYYY-MM-DD), defaults to today"),
    advisor: Optional[str] = Query(None, description="Filter by advisor name"),
    status: Optional[str] = Query(None, description="Filter by status (not_arrived, checked_in, in_progress, completed, cancelled)"),
    search: Optional[str] = Query(None, description="Search by customer name, VIN, vehicle, or RO number"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get service appointments for Engage/Customer Experience Management page.
    
    **Expected Input (Query Parameters):**
    - date: Optional[str] - Appointment date in YYYY-MM-DD format (defaults to today)
    - advisor: Optional[str] - Filter by advisor name (use "All" for all advisors)
    - status: Optional[str] - Filter by status (not_arrived, checked_in, in_progress, completed, cancelled, or "All")
    - search: Optional[str] - Search by customer name, VIN, vehicle make/model, or RO number
    
    **Expected Output (Dict[str, Any]):**
    - appointments: List[Dict[str, Any]] - Service appointments with:
      - id: int
      - appointment_date: str (YYYY-MM-DD)
      - appointment_time: str (e.g., "7:00 AM")
      - service_type: str
      - estimated_duration: str (e.g., "45 min")
      - vehicle_vin: str
      - vehicle_year: int
      - vehicle_make: str
      - vehicle_model: str
      - vehicle_mileage: str
      - vehicle_icon_color: str (blue, red, gray)
      - customer_name: str
      - advisor: str
      - status: str
      - ro_number: Optional[str]
      - code: Optional[str]
      - customer_id: Optional[int]
      - phone: Optional[str]
      - email: Optional[str]
      - loyalty_tier: Optional[str] (Platinum, Gold, Silver)
      - preferred_services: List[str]
      - service_history_count: int
      - last_visit_date: Optional[str] (YYYY-MM-DD)
    - needs_action_count: int - Count of appointments needing action
    """
    from datetime import datetime as dt
    
    appointment_date = None
    if date:
        try:
            appointment_date = dt.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    service = AnalyticsService(db)
    appointments = await service.get_service_appointments(
        appointment_date=appointment_date,
        advisor=advisor,
        status=status,
        search=search
    )
    
    needs_action_count = await service.get_appointment_needs_action_count(appointment_date)
    
    return {
        "appointments": appointments,
        "needs_action_count": needs_action_count
    }


@router.post("/engage/check-in/{appointment_id}")
async def check_in_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Check in a service appointment.
    
    **Expected Input:**
    - appointment_id: int (path parameter) - ID of the appointment to check in
    
    **Expected Output (Dict[str, Any]):**
    - success: bool
    - id: int - Appointment ID
    - status: str - Updated status (checked_in)
    - message: Optional[str] - Error message if unsuccessful
    """
    service = AnalyticsService(db)
    result = await service.check_in_appointment(appointment_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Appointment not found"))
    
    return result


@router.get("/data-catalog/tables")
async def get_data_catalog(
    db: AsyncSession = Depends(get_db)
):
    """
    Get data catalog information - available tables and their schemas.
    Dynamically fetched from the database.
    
    **Expected Input:**
    - None (no query parameters)
    
    **Expected Output (Dict[str, Any]):**
    - tables: List[Dict[str, Any]] - Table metadata with name, description, columns, row_count
    - regions: List[str] - Available regions (from dealers table)
    - kpi_categories: List[str] - Available KPI categories (from kpi_metrics table)
    """
    service = AnalyticsService(db)
    catalog = await service.get_data_catalog()
    return catalog


@router.get("/demo/scenarios")
async def get_demo_scenarios():
    """
    Get pre-built demo scenarios for testing.
    
    **Expected Input:**
    - None (no query parameters)
    
    **Expected Output (Dict[str, Any]):**
    - scenarios: List[Dict[str, Any]] - Demo scenarios with:
      - id: str - Scenario identifier
      - title: str - Scenario title
      - question: str - Example question
      - category: str - Scenario category
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
