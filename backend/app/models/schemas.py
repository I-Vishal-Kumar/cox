from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QueryType(str, Enum):
    CONVERSATIONAL_BI = "conversational_bi"
    KPI_MONITORING = "kpi_monitoring"
    EXECUTIVE_SUMMARY = "executive_summary"
    DATA_CATALOG = "data_catalog"
    ANOMALY_DETECTION = "anomaly_detection"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    query_type: Optional[QueryType] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    query_type: QueryType
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    chart_config: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    sources: Optional[List[str]] = None


class KPIAlert(BaseModel):
    id: str
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    severity: str  # "info", "warning", "critical"
    message: str
    timestamp: datetime
    root_cause: Optional[str] = None


class DashboardMetric(BaseModel):
    name: str
    value: float
    change: float
    trend: str  # "up", "down", "stable"
    unit: Optional[str] = None


class ProgramPerformance(BaseModel):
    program_name: str
    emails_sent: int
    unique_opens: int
    open_rate: float
    ro_count: int
    revenue: float
    category: str


class InviteDashboardData(BaseModel):
    program_summary: Dict[str, Any]
    program_performance: List[ProgramPerformance]
    monthly_metrics: Dict[str, Any]
    alerts: List[KPIAlert]
