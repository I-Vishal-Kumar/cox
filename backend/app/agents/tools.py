"""LangChain tools for Cox Automotive AI Analytics."""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool, ToolException
from langchain_core.messages import ToolMessage
from pydantic import BaseModel, Field
from sqlalchemy.exc import DatabaseError
from pydantic import ValidationError


# Tool error handling middleware
def create_tool_error_handler():
    """Create error handling middleware for tools."""
    from langchain.agents.middleware import wrap_tool_call
    
    @wrap_tool_call
    def tool_error_handler(request, handler):
        """Handle tool execution errors with context-aware messages."""
        try:
            return handler(request)
        except DatabaseError as e:
            return ToolMessage(
                content=f"Database error: {str(e)}. Please check your query and try again.",
                tool_call_id=request.tool_call["id"]
            )
        except ValidationError as e:
            return ToolMessage(
                content=f"Input validation error: {str(e)}. Please check your parameters.",
                tool_call_id=request.tool_call["id"]
            )
        except ToolException as e:
            return ToolMessage(
                content=f"Tool error: {str(e)}",
                tool_call_id=request.tool_call["id"]
            )
        except Exception as e:
            return ToolMessage(
                content=f"Tool execution failed: {str(e)}. Please try rephrasing your query.",
                tool_call_id=request.tool_call["id"]
            )
    
    return tool_error_handler


# Pydantic models for tool schemas
class SQLGenerationInput(BaseModel):
    """Input schema for SQL generation tool."""
    query: str = Field(description="Natural language question about data")
    context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional context for query generation"
    )


class KPIAnalysisInput(BaseModel):
    """Input schema for KPI analysis tool."""
    data: List[Dict[str, Any]] = Field(description="Query results from database")
    query_type: str = Field(
        description="Type of analysis (fni_analysis, logistics_analysis, plant_analysis, etc.)"
    )
    original_query: str = Field(description="Original user question")


class AnalysisOutput(BaseModel):
    """Output schema for analysis tools."""
    analysis: str = Field(description="Generated analysis text")
    recommendations: List[str] = Field(description="Actionable recommendations")
    timestamp: str = Field(description="Analysis timestamp")


class ChartConfigInput(BaseModel):
    """Input schema for chart configuration tool."""
    query_type: str = Field(description="Type of query for chart selection")
    data: List[Dict[str, Any]] = Field(description="Data to visualize")


class ChartConfigOutput(BaseModel):
    """Output schema for chart configuration."""
    type: str = Field(description="Chart type (bar, pie, line, horizontal_bar)")
    title: str = Field(description="Chart title")
    x_axis: Optional[str] = Field(default=None, description="X-axis field name")
    y_axis: Optional[str] = Field(default=None, description="Y-axis field name")
    labels: Optional[str] = Field(default=None, description="Labels field for pie charts")
    values: Optional[str] = Field(default=None, description="Values field for pie charts")



# Note: Database schema is now fetched dynamically from the database
# See app/utils/schema_utils.py for schema fetching logic


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


@tool
async def generate_sql_query(
    query: str, 
    context: Optional[str] = None
) -> str:
    """Generate and execute SQL query from natural language question, returning the data.
    
    Use this tool when you need to retrieve data from the Cox Automotive database.
    This tool converts natural language questions into valid SQLite queries AND executes them.
    
    Args:
        query: Natural language question about data (e.g., "Show F&I revenue for Midwest dealers")
        context: Optional additional context for query generation
        
    Returns:
        String representation of query results (list of dictionaries) or error message
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate
    from app.core.config import settings
    from app.utils.schema_utils import get_cached_schema, get_fallback_schema
    from sqlalchemy import text
    from app.db.database import get_db
    
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        temperature=0.2,
        api_key=settings.anthropic_api_key
    )
    
    # Get database session
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Fetch database schema dynamically
        try:
            database_schema = await get_cached_schema(db_session)
        except Exception:
            database_schema = get_fallback_schema()
        
        
        system_prompt = f"""You are an expert SQL query generator for Cox Automotive's data analytics platform.

            **Database Environment:**
            - Database: SQLite 3.x
            - ORM: SQLAlchemy 1.4 (async)
            - Execution: Queries are executed using SQLAlchemy's text() function with async sessions

            **Your task:** Convert natural language questions into valid SQLite queries.

            {database_schema}

            **CRITICAL SQLite-Specific Rules:**
            1. **Date Modifiers**: SQLite does NOT support '-X weeks' or '-X months' syntax
               - ✅ CORRECT: date('now', '-28 days') for 4 weeks ago
               - ✅ CORRECT: date('now', '-7 days') for 1 week ago
               - ❌ WRONG: date('now', '-4 weeks') - this returns NULL!
               - ❌ WRONG: date('now', '-1 month') - use '-30 days' instead
            
            2. **Date Functions**: Use SQLite date functions properly
               - Current date: date('now')
               - This week: WHERE date >= date('now', 'weekday 0', '-7 days')
               - Last week: WHERE date >= date('now', '-14 days') AND date < date('now', '-7 days')
               - Last N days: WHERE date >= date('now', '-N days')
            
            3. **NULL Handling**: Always use COALESCE for aggregations that might be NULL
               - ✅ CORRECT: COALESCE(SUM(revenue), 0)
               - ✅ CORRECT: COALESCE(AVG(rate), 0)
               - This prevents NULL results in aggregations
            
            4. **JOINs**: Always use proper JOIN syntax with ON clauses
            
            5. **Aggregations**: Use SUM, AVG, COUNT with COALESCE
            
            6. **Rounding**: Use ROUND(value, 2) for currency/percentages
            
            7. **Ordering**: Add ORDER BY for meaningful sorting
            
            8. **Limits**: ALWAYS use LIMIT clauses to avoid querying all records
               - For analysis queries: Use LIMIT 20-50 (enough for root cause analysis)
               - For dashboard queries: Use LIMIT 100
               - For time-based comparisons: Query both periods separately with LIMIT
               - NEVER query all 3000 records - always filter and limit
            
            9. **Percentages**: Multiply rates by 100 for percentage display
            
            10. **Window Functions**: Use when comparing periods or calculating running totals

            **Return Format:** Return ONLY the SQL query, no explanations or markdown formatting."""
                    
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """Convert this question to SQL:

Question: {query}

Additional context (if any): {context}

SQL Query:""")
        ])
        
        chain = prompt | llm
        response = await chain.ainvoke({
            "query": query,
            "context": context if context else "None"
        })
        
        sql_query = response.content.strip()
        
        # Clean up the SQL query
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Execute the SQL query and return results
        try:
            result = await db_session.execute(text(sql_query))
            rows = result.fetchall()
            
            # Convert to list of dicts
            if rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
                return str(data)[:2000]  # Limit output like MCP example
            else:
                return "Query executed successfully. No rows returned."
        except Exception as e:
            return f"SQL: {sql_query}\n\nError executing query: {str(e)}"
    
    finally:
        # Close the database session
        if db_session:
            await db_session.close()




@tool
async def analyze_kpi_data(
    data: str,  # Changed from List[Dict[str, Any]] to str
    query_type: str,
    original_query: str
) -> Dict[str, Any]:
    """Analyze KPI data and provide insights with recommendations.
    
    Use this tool after retrieving data from generate_sql_query to perform analysis,
    identify anomalies, and provide actionable recommendations.
    
    Args:
        data: Query results from generate_sql_query as a string representation of list of dictionaries
        query_type: Type of analysis (fni_analysis, logistics_analysis, plant_analysis, 
                    marketing_analysis, service_analysis, kpi_monitoring, general)
        original_query: The original user question for context
        
    Returns:
        Dictionary containing analysis text, recommendations list, and timestamp
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate
    from app.core.config import settings
    from datetime import datetime
    import ast
    
    # Parse string data into list of dicts
    try:
        if isinstance(data, str):
            # Try to parse as Python literal
            try:
                parsed_data = ast.literal_eval(data)
            except:
                # If that fails, treat as raw string
                parsed_data = []
        else:
            parsed_data = data
    except Exception as e:
        parsed_data = []
    
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        temperature=0.2,
        api_key=settings.anthropic_api_key
    )
    
    system_prompt = """You are an expert automotive industry analyst specializing in KPI monitoring and root cause analysis.

        Your role is to:
        1. Analyze KPI data and identify anomalies
        2. Provide clear, actionable root cause analysis
        3. Generate recommendations based on data patterns
        4. Explain complex data insights in plain language

        When analyzing data:
        - Compare current vs previous periods
        - Break down by dealer, region, product, or time
        - Identify the main drivers of change
        - Quantify impacts with specific numbers
        - Provide specific, actionable recommendations

        Format your responses with:
        - A brief summary of the finding
        - Bullet points for key data points
        - Clear attribution of causes
        - Actionable recommendations

        Be specific with numbers and percentages. Always include context."""
    
    # Format data as a readable table
    def format_data(data: Any) -> str:
        if not data:
            return "No data available"
        
        if isinstance(data, str):
            return data[:1000]  # Return string as-is, limited
        
        if not isinstance(data, list) or len(data) == 0:
            return "Empty dataset"
        
        headers = list(data[0].keys()) if isinstance(data[0], dict) else []
        if not headers:
            return str(data)[:1000]
        
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        
        for row in data[:20]:  # Limit to 20 rows
            if isinstance(row, dict):
                lines.append(" | ".join(str(row.get(h, "")) for h in headers))
            else:
                lines.append(str(row))
        
        return "\n".join(lines)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this data and provide insights:

Question: {query}

Query Type: {query_type}

Data:
{data}

Provide a comprehensive analysis with:
1. Summary of the situation
2. Key findings with specific numbers
3. Root cause analysis
4. Actionable recommendations

Analysis:""")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({
        "query": original_query,
        "query_type": query_type,
        "data": format_data(parsed_data)
    })
    
    analysis = response.content
    
    # Extract recommendations from analysis
    def extract_recommendations(analysis: str) -> List[str]:
        recommendations = []
        lines = analysis.split("\n")
        
        in_recommendations = False
        for line in lines:
            line = line.strip()
            if "recommendation" in line.lower():
                in_recommendations = True
                continue
            
            if in_recommendations and line.startswith(("-", "•", "*", "1", "2", "3")):
                rec = line.lstrip("-•* 0123456789.)")
                if rec and len(rec) > 10:
                    recommendations.append(rec.strip())
        
        return recommendations[:5]
    
    return {
        "analysis": analysis,
        "recommendations": extract_recommendations(analysis),
        "timestamp": datetime.now().isoformat()
    }



@tool
async def analyze_fni_revenue_drop(data: str) -> Dict[str, Any]:
    """Analyze F&I (Finance & Insurance) revenue drops and identify root causes.
    
    Use this tool specifically for F&I revenue analysis scenarios where you need
    to identify why revenue declined and which dealers or factors are responsible.
    
    Args:
        data: String representation of data from generate_sql_query (will be parsed automatically)
              Should be a string like "[{'dealer_name': 'ABC', 'revenue': 1000}, ...]"
        
    Returns:
        Dictionary containing detailed analysis, root causes, and recommendations
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate
    from app.core.config import settings
    from datetime import datetime
    
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        temperature=0.2,
        api_key=settings.anthropic_api_key
    )
    
    system_prompt = """You are an expert automotive F&I analyst specializing in root cause analysis.

Focus on:
- Service contract penetration rates
- Gap insurance attachment
- Finance manager performance
- Regional patterns
- Week-over-week changes
- Dealer-specific issues

Provide specific numbers, percentages, and actionable recommendations."""
    
    # Parse string data to List[Dict]
    import ast
    import json
    
    try:
        # Try to parse as Python literal (from generate_sql_query)
        parsed_data = ast.literal_eval(data) if isinstance(data, str) else data
    except:
        try:
            # Try JSON parsing
            parsed_data = json.loads(data) if isinstance(data, str) else data
        except:
            parsed_data = []
    
    if not isinstance(parsed_data, list):
        parsed_data = []
    
    # Format data
    def format_data(data: List[Dict]) -> str:
        if not data:
            return "No data available"
        headers = list(data[0].keys()) if data else []
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        for row in data[:20]:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this F&I revenue data and provide a comprehensive root cause analysis:

Data:
{data}

Answer in this EXACT format:

**F&I Revenue Analysis - [Region]**

F&I revenue in the [region] region [declined/increased] **[X]% vs last week**.

**Key Findings:**
• **[X]%** of the decline came from [top 3 dealers with specific names]
• The main driver was [specific cause: penetration rates, volume, pricing, etc.] with specific numbers
• [Finance manager name] at [dealer name] accounted for a **[X-point drop]** in attachment rate

**Root Cause Analysis:**
[Table or list showing dealer-by-dealer breakdown with this week vs last week revenue and change %]

**Recommendations:**
1. [Specific actionable recommendation]
2. [Specific actionable recommendation]
3. [Specific actionable recommendation]

Provide specific numbers, percentages, dealer names, and finance manager names from the data.

Analysis:""")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({"data": format_data(parsed_data)})
    
    analysis = response.content
    
    # Extract recommendations
    def extract_recommendations(analysis: str) -> List[str]:
        recommendations = []
        lines = analysis.split("\n")
        in_recommendations = False
        for line in lines:
            line = line.strip()
            if "recommendation" in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and line.startswith(("-", "•", "*", "1", "2", "3")):
                rec = line.lstrip("-•* 0123456789.)")
                if rec and len(rec) > 10:
                    recommendations.append(rec.strip())
        return recommendations[:5]
    
    return {
        "analysis": analysis,
        "recommendations": extract_recommendations(analysis),
        "timestamp": datetime.now().isoformat()
    }


@tool
async def analyze_logistics_delays(data: str) -> Dict[str, Any]:
    """Analyze logistics and shipment delays to identify root causes.
    
    Use this tool for logistics analysis scenarios where you need to determine
    whether delays are caused by carriers, routes, weather, or other factors.
    
    Args:
        data: String representation of data from generate_sql_query (will be parsed automatically)
              Should be a string like "[{'carrier': 'X', 'delayed_count': 24}, ...]"
        
    Returns:
        Dictionary containing delay analysis, root causes, and recommendations
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate
    from app.core.config import settings
    from datetime import datetime
    
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        temperature=0.2,
        api_key=settings.anthropic_api_key
    )
    
    system_prompt = """You are an expert logistics analyst specializing in supply chain optimization.

Focus on:
- Carrier performance
- Route efficiency
- Weather impacts
- Dwell time analysis
- Delay patterns and trends

Provide specific metrics and actionable recommendations for improvement."""
    
    # Parse string data to List[Dict]
    import ast
    import json
    
    try:
        parsed_data = ast.literal_eval(data) if isinstance(data, str) else data
    except:
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
        except:
            parsed_data = []
    
    if not isinstance(parsed_data, list):
        parsed_data = []
    
    # Format data
    def format_data(data: List[Dict]) -> str:
        if not data:
            return "No data available"
        headers = list(data[0].keys()) if data else []
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        for row in data[:20]:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this shipment delay data and provide a comprehensive root cause analysis:

Data:
{data}

Answer in this EXACT format:

**Logistics Delay Analysis - Past 7 Days**

Over the past 7 days, **[X]%** of shipments arrived late.

**Delay Attribution:**
• **[X]%** of delays are concentrated on **[Carrier Name]** on [specific routes]
• Weather was a [minor/major] factor ([X] delays tagged to storms)
• Average dwell time at the origin yard for [Carrier Name] increased from **[X.X] to [X.X] hours**

**Carrier Performance:**
[Table showing carrier, total shipments, delayed count, delay rate, avg dwell time]

**Recommendations:**
1. [Specific actionable recommendation]
2. [Specific actionable recommendation]
3. [Specific actionable recommendation]

Provide specific numbers, percentages, carrier names, routes, and delay reasons from the data.

Analysis:""")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({"data": format_data(parsed_data)})
    
    analysis = response.content
    
    # Extract recommendations
    def extract_recommendations(analysis: str) -> List[str]:
        recommendations = []
        lines = analysis.split("\n")
        in_recommendations = False
        for line in lines:
            line = line.strip()
            if "recommendation" in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and line.startswith(("-", "•", "*", "1", "2", "3")):
                rec = line.lstrip("-•* 0123456789.)")
                if rec and len(rec) > 10:
                    recommendations.append(rec.strip())
        return recommendations[:5]
    
    return {
        "analysis": analysis,
        "recommendations": extract_recommendations(analysis),
        "timestamp": datetime.now().isoformat()
    }


@tool
async def analyze_plant_downtime(data: str) -> Dict[str, Any]:
    """Analyze manufacturing plant downtime and identify root causes.
    
    Use this tool for plant operations analysis where you need to understand
    which plants have downtime issues and what's causing them.
    
    Args:
        data: Plant downtime data including plants, lines, hours, and reasons
        
    Returns:
        Dictionary containing downtime analysis, root causes, and recommendations
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate
    from app.core.config import settings
    from datetime import datetime
    
    llm = ChatAnthropic(
        model=settings.anthropic_model,
        temperature=0.2,
        api_key=settings.anthropic_api_key
    )
    
    system_prompt = """You are an expert manufacturing operations analyst specializing in plant efficiency.

Focus on:
- Downtime hours by plant and line
- Root cause categories (maintenance, quality, supply, equipment)
- Planned vs unplanned downtime
- Supplier-related issues
- Impact on production capacity

Provide specific metrics and actionable recommendations for reducing downtime."""
    
    # Parse string data to List[Dict]
    import ast
    import json
    
    try:
        parsed_data = ast.literal_eval(data) if isinstance(data, str) else data
    except:
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
        except:
            parsed_data = []
    
    if not isinstance(parsed_data, list):
        parsed_data = []
    
    # Format data
    def format_data(data: List[Dict]) -> str:
        if not data:
            return "No data available"
        headers = list(data[0].keys()) if data else []
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        for row in data[:20]:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this plant downtime data and provide a comprehensive root cause analysis:

Data:
{data}

Answer in this EXACT format:

**Plant Downtime Analysis - This Week**

[Number] plants recorded significant downtime this week:

**Plant [Name] — [Location]** ([X.X] hours total)
• Mostly on [Line Number]
• [Root cause 1]: **[X.X hours]** - [specific detail]
• [Root cause 2]: **[X.X hours]** - [specific detail]
• [Additional detail if relevant, e.g., defect rate is X.X normal]

**Plant [Name] — [Location]** ([X.X] hours)
• [Line Number] stoppage
• [Root cause]: **[X.X hours]** - [specific detail, e.g., component shortage from Supplier X]

**Plant [Name] — [Location]** ([X.X] hours)
• [Line Number]
• [Root cause]: **[X.X hours]** - [specific detail]

**Recommendations:**
1. **[Plant Name]**: [Specific actionable recommendation]
2. **[Plant Name]**: [Specific actionable recommendation]
3. **[Plant Name]**: [Specific actionable recommendation]

Provide specific numbers, plant names, line numbers, downtime hours, and root cause details from the data.

Analysis:""")
    ])
    
    chain = prompt | llm
    response = await chain.ainvoke({"data": format_data(parsed_data)})
    
    analysis = response.content
    
    # Extract recommendations
    def extract_recommendations(analysis: str) -> List[str]:
        recommendations = []
        lines = analysis.split("\n")
        in_recommendations = False
        for line in lines:
            line = line.strip()
            if "recommendation" in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and line.startswith(("-", "•", "*", "1", "2", "3")):
                rec = line.lstrip("-•* 0123456789.)")
                if rec and len(rec) > 10:
                    recommendations.append(rec.strip())
        return recommendations[:5]
    
    return {
        "analysis": analysis,
        "recommendations": extract_recommendations(analysis),
        "timestamp": datetime.now().isoformat()
    }



@tool
def generate_chart_configuration(
    query_type: str,
    data: List[Dict[str, Any]],
    chart_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Generate chart configuration based on query type and data structure.
    
    Use this tool to create visualization configurations for displaying data
    in charts. Chart configurations are loaded from app/config/chart_configs.json
    and automatically selected based on query type and data characteristics.
    
    The tool supports multiple chart types per query type and intelligently
    selects the best visualization based on data structure (time series,
    categorical, etc.).
    
    Args:
        query_type: Type of query (fni_analysis, logistics_analysis, plant_analysis, 
                    marketing_analysis, kpi_monitoring, service_analysis, etc.)
        data: The data to visualize as list of dictionaries
        chart_name: Optional specific chart name to use (e.g., "revenue_comparison")
        
    Returns:
        Chart configuration dictionary with type, title, axes, labels, or None if no chart needed
        
    Examples:
        - For F&I analysis: Returns horizontal bar chart for revenue comparison
        - For logistics: Returns pie chart for delay distribution
        - For time series: Returns line chart for trends
        - For categorical data: Returns pie/donut chart for distribution
    """
    from app.utils.chart_utils import get_chart_manager
    
    if not data:
        return None
    
    # Get chart configuration manager
    chart_manager = get_chart_manager()
    
    # Get appropriate chart configuration
    config = chart_manager.get_config(
        query_type=query_type,
        chart_name=chart_name,
        data=data
    )
    
    if not config:
        return None
    
    # Validate that required fields exist in data
    if data and len(data) > 0:
        first_row = data[0]
        columns = list(first_row.keys())
        
        # Update config with actual column names if needed
        if config.get('x_axis') and config['x_axis'] not in columns:
            # Try to find a suitable column
            if len(columns) > 0:
                config['x_axis'] = columns[0]
        
        if config.get('y_axis') and config['y_axis'] not in columns:
            # Try to find a suitable numeric column
            if len(columns) > 1:
                config['y_axis'] = columns[1]
    
    return config
