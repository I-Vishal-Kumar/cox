"""SQL Generation Agent for natural language to SQL conversion."""

from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base_agent import BaseAgent

# Note: Database schema is now fetched dynamically from the database
# See app/utils/schema_utils.py for schema fetching logic
# This allows the schema to stay in sync with actual database structure


class SQLAgent(BaseAgent):
    """Agent for converting natural language queries to SQL.
    
    Note: This class is deprecated in favor of the LangChain tool-based approach.
    Use the generate_sql_query tool from app/agents/tools.py instead.
    """

    def __init__(self, db_session=None):
        super().__init__()
        self.db_session = db_session
        self.schema = None

    async def get_system_prompt(self) -> str:
        """Get system prompt with dynamically fetched schema."""
        from app.utils.schema_utils import get_cached_schema, get_fallback_schema
        
        if self.db_session:
            try:
                schema = await get_cached_schema(self.db_session)
            except Exception:
                schema = get_fallback_schema()
        else:
            schema = get_fallback_schema()
        
        return f"""You are an expert SQL query generator for Cox Automotive's data analytics platform.

Your task is to convert natural language questions into valid SQLite queries.

{schema}

Important rules:
1. Always use proper JOINs when querying across tables
2. Use DATE functions for date filtering: date('now'), date('now', '-7 days'), etc.
3. For "this week", use: WHERE date >= date('now', 'weekday 0', '-7 days')
4. For "last week", use: WHERE date >= date('now', '-14 days') AND date < date('now', '-7 days')
5. Always include relevant aggregations (SUM, AVG, COUNT) when appropriate
6. Use ROUND() for floating point results
7. Add ORDER BY for meaningful sorting
8. Limit results to 100 rows unless specifically asked for more
9. For percentage calculations, multiply by 100
10. When comparing periods, use subqueries or window functions

Return ONLY the SQL query, no explanations."""

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert natural language to SQL query."""
        system_prompt = await self.get_system_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """Convert this question to SQL:

Question: {query}

Additional context (if any): {context}

SQL Query:""")
        ])

        sql_query = await self.generate_response(
            prompt,
            query=query,
            context=str(context) if context else "None"
        )

        # Clean up the SQL query
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()

        return {
            "sql_query": sql_query,
            "original_query": query
        }


# Pre-defined queries for demo scenarios
DEMO_QUERIES = {
    "fni_midwest": """
        WITH this_week AS (
            SELECT
                d.name as dealer_name,
                d.dealer_code,
                SUM(f.fni_revenue) as revenue,
                AVG(f.penetration_rate) as avg_penetration,
                COUNT(*) as transaction_count
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE d.region = 'Midwest'
            AND f.transaction_date >= date('now', '-7 days')
            GROUP BY d.id, d.name, d.dealer_code
        ),
        last_week AS (
            SELECT
                d.name as dealer_name,
                d.dealer_code,
                SUM(f.fni_revenue) as revenue,
                AVG(f.penetration_rate) as avg_penetration
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE d.region = 'Midwest'
            AND f.transaction_date >= date('now', '-14 days')
            AND f.transaction_date < date('now', '-7 days')
            GROUP BY d.id, d.name, d.dealer_code
        )
        SELECT
            tw.dealer_name,
            tw.dealer_code,
            ROUND(tw.revenue, 2) as this_week_revenue,
            ROUND(lw.revenue, 2) as last_week_revenue,
            ROUND((tw.revenue - lw.revenue) / lw.revenue * 100, 2) as change_pct,
            ROUND(tw.avg_penetration * 100, 1) as current_penetration,
            ROUND(lw.avg_penetration * 100, 1) as previous_penetration
        FROM this_week tw
        JOIN last_week lw ON tw.dealer_code = lw.dealer_code
        ORDER BY (tw.revenue - lw.revenue) ASC
        LIMIT 10
    """,

    "logistics_delays": """
        SELECT
            carrier,
            route,
            COUNT(*) as total_shipments,
            SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) as delayed_count,
            ROUND(SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as delay_rate,
            ROUND(AVG(dwell_time_hours), 2) as avg_dwell_time,
            delay_reason
        FROM shipments
        WHERE scheduled_departure >= datetime('now', '-7 days')
        GROUP BY carrier, route, delay_reason
        HAVING delayed_count > 0
        ORDER BY delayed_count DESC
    """,

    "plant_downtime": """
        SELECT
            p.name as plant_name,
            p.plant_code,
            pd.line_number,
            SUM(pd.downtime_hours) as total_downtime,
            pd.reason_category,
            pd.reason_detail,
            pd.is_planned,
            pd.supplier
        FROM plants p
        JOIN plant_downtime pd ON p.id = pd.plant_id
        WHERE pd.event_date >= date('now', '-7 days')
        GROUP BY p.id, p.name, p.plant_code, pd.line_number, pd.reason_category, pd.reason_detail, pd.is_planned, pd.supplier
        ORDER BY total_downtime DESC
    """
}
