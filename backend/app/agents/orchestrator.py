"""
Main orchestrator for Cox Automotive AI Analytics Agent.
Coordinates between different specialized agents based on query type.

This module now uses the new LangChain-based orchestrator while maintaining
backward compatibility with the existing API.
"""

from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from app.agents.base_agent import BaseAgent
from app.agents.sql_agent import SQLAgent, DEMO_QUERIES
from app.agents.kpi_agent import KPIAgent, RootCauseAnalyzer
from app.agents.langchain_orchestrator import LangChainAnalyticsOrchestrator
from app.core.config import settings
import json
import re


class QueryClassifier(BaseAgent):
    """Classifies incoming queries to route to appropriate agents."""

    def get_system_prompt(self) -> str:
        return """You are a query classifier for Cox Automotive's AI analytics platform.

            Classify user queries into one of these categories:

            1. "fni_analysis" - Questions about F&I (Finance & Insurance) revenue, service contracts, gap insurance, penetration rates, dealer performance
            Examples: "Why did F&I revenue drop?", "What's our service contract penetration?"

            2. "logistics_analysis" - Questions about shipments, carriers, delays, routes, delivery times
            Examples: "Who delayed — carrier, route, or weather?", "Show late shipments"

            3. "plant_analysis" - Questions about manufacturing plants, downtime, production, quality issues
            Examples: "Which plants showed downtime?", "What caused the production stoppage?"

            4. "marketing_analysis" - Questions about marketing campaigns, email performance, ROI, Invite dashboard
            Examples: "What's our email open rate?", "Show campaign performance"

            5. "service_analysis" - Questions about service appointments, technicians, customer service
            Examples: "How many appointments today?", "Show no-shows"

            6. "kpi_monitoring" - General KPI questions, trends, comparisons
            Examples: "What are our key metrics?", "Show KPI trends"

            7. "data_catalog" - Questions about available data, schemas, tables
            Examples: "What data do we have?", "Where can I find dealer info?"

            8. "general" - Other questions or conversational queries

            Respond with ONLY the category name, nothing else."""

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classify the query."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("human", "Classify this query: {query}")
        ])

        category = await self.generate_response(prompt, query=query)
        category = category.strip().lower().replace('"', '').replace("'", "")

        return {"category": category, "query": query}


class AnalyticsOrchestrator:
    """
    Main orchestrator that coordinates between different agents.
    Uses a multi-agent architecture where:
    1. QueryClassifier determines the type of query
    2. SQLAgent generates SQL for data retrieval
    3. KPIAgent provides analysis and insights
    """

    def __init__(self):
        self.classifier = QueryClassifier()
        self.sql_agent = SQLAgent()
        self.kpi_agent = KPIAgent()
        self.rca_analyzer = RootCauseAnalyzer(self.kpi_agent)

        # LLM for final response synthesis
        self.llm = ChatAnthropic(
            model=settings.anthropic_model,
            temperature=0.2,
            api_key=settings.anthropic_api_key
        )
    
    async def process_query(
        self,
        query: str,
        db_session=None,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent pipeline.

        1. Classify the query
        2. Generate SQL if needed
        3. Execute SQL and get data
        4. Analyze data with KPI agent
        5. Generate final response
        """
        # Step 1: Classify the query
        classification = await self.classifier.process(query)
        query_type = classification["category"]

        # Step 2: Determine if this is a demo scenario
        demo_scenario = self._detect_demo_scenario(query)

        result = {
            "query": query,
            "query_type": query_type,
            "sql_query": None,
            "data": None,
            "analysis": None,
            "recommendations": [],
            "chart_config": None
        }

        # Step 3: Generate and execute SQL
        if demo_scenario:
            # Use pre-defined demo queries for consistent results
            result["sql_query"] = DEMO_QUERIES.get(demo_scenario, "")
        else:
            sql_result = await self.sql_agent.process(query)
            result["sql_query"] = sql_result["sql_query"]

        # Step 4: Execute SQL if we have a database session
        if db_session and result["sql_query"]:
            try:
                from sqlalchemy import text
                query_result = await db_session.execute(text(result["sql_query"]))
                rows = query_result.fetchall()
                columns = query_result.keys()
                result["data"] = [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                result["error"] = str(e)
                result["data"] = []

        # Step 5: Generate analysis
        if result["data"] or demo_scenario:
            analysis_result = await self._generate_analysis(
                query, query_type, result["data"], demo_scenario
            )
            result["analysis"] = analysis_result.get("analysis", "")
            result["recommendations"] = analysis_result.get("recommendations", [])

        # Step 6: Generate chart configuration if applicable
        result["chart_config"] = self._generate_chart_config(query_type, result["data"])

        return result

    def _detect_demo_scenario(self, query: str) -> Optional[str]:
        """Detect if query matches a demo scenario."""
        query_lower = query.lower()

        if any(term in query_lower for term in ["f&i", "fni", "finance", "midwest"]):
            if any(term in query_lower for term in ["drop", "decline", "down", "why"]):
                return "fni_midwest"

        if any(term in query_lower for term in ["delay", "carrier", "route", "weather", "shipment"]):
            return "logistics_delays"

        if any(term in query_lower for term in ["plant", "downtime", "production", "manufacturing"]):
            return "plant_downtime"

        return None

    async def _generate_analysis(
        self,
        query: str,
        query_type: str,
        data: List[Dict],
        demo_scenario: Optional[str]
    ) -> Dict[str, Any]:
        """Generate analysis based on query type."""
        context = {
            "data": data or [],
            "query_type": query_type
        }

        # For demo scenarios, use specialized analyzers
        if demo_scenario == "fni_midwest":
            return await self.rca_analyzer.analyze_fni_drop({"comparison_data": data})
        elif demo_scenario == "logistics_delays":
            return await self.rca_analyzer.analyze_logistics_delays({"delay_data": data})
        elif demo_scenario == "plant_downtime":
            return await self.rca_analyzer.analyze_plant_downtime({"downtime_data": data})

        # For general queries, use the KPI agent
        return await self.kpi_agent.process(query, context)

    def _generate_chart_config(self, query_type: str, data: List[Dict]) -> Optional[Dict[str, Any]]:
        """Generate chart configuration based on query type and data."""
        if not data:
            return None

        # Determine appropriate chart type
        if query_type in ["fni_analysis", "marketing_analysis"]:
            return {
                "type": "bar",
                "title": "Performance Comparison",
                "x_axis": list(data[0].keys())[0] if data else "category",
                "y_axis": list(data[0].keys())[1] if data and len(data[0]) > 1 else "value"
            }
        elif query_type == "logistics_analysis":
            return {
                "type": "pie",
                "title": "Delay Distribution",
                "labels": "delay_reason",
                "values": "count"
            }
        elif query_type == "plant_analysis":
            return {
                "type": "horizontal_bar",
                "title": "Downtime by Plant/Line",
                "x_axis": "downtime_hours",
                "y_axis": "plant_name"
            }
        elif query_type == "kpi_monitoring":
            return {
                "type": "line",
                "title": "KPI Trend",
                "x_axis": "date",
                "y_axis": "value"
            }

        return None

    async def get_quick_insights(self, db_session=None) -> Dict[str, Any]:
        """Get quick insights for dashboard display."""
        insights = {
            "alerts": [],
            "key_metrics": [],
            "recent_anomalies": []
        }

        # This would query the database for current KPI status
        # For demo, return pre-defined insights

        insights["alerts"] = [
            {
                "id": "alert_001",
                "severity": "warning",
                "metric": "F&I Revenue - Midwest",
                "message": "F&I revenue down 11% vs last week in Midwest region",
                "timestamp": "2024-01-15T09:00:00Z"
            },
            {
                "id": "alert_002",
                "severity": "critical",
                "metric": "Shipment Delays",
                "message": "18% of shipments delayed - Carrier X on Chicago-Detroit route",
                "timestamp": "2024-01-15T08:30:00Z"
            }
        ]

        return insights
