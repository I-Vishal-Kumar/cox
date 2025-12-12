"""
Dashboard-specific tools for generating structured data for frontend dashboards.

These tools provide pre-formatted data structures that match frontend requirements,
eliminating the need for separate dashboard endpoints.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from sqlalchemy import text
from app.db.database import get_db
from datetime import datetime
import json


@tool
async def get_weekly_fni_trends(
    weeks: int = 4,
    regions: Optional[List[str]] = None
) -> str:
    """Get F&I revenue trends by week and region for dashboard charts.
    
    Returns weekly revenue data aggregated by region for the specified number of weeks.
    Perfect for populating line/area charts showing revenue trends.
    
    Args:
        weeks: Number of weeks to retrieve (default: 4)
        regions: List of regions to include (default: all regions)
        
    Returns:
        JSON string with weekly trend data in format:
        [
            {
                "week": "Week 1",
                "midwest": 125000,
                "northeast": 98000,
                "southeast": 110000,
                "west": 87000
            },
            ...
        ]
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Build region filter
        region_filter = ""
        if regions:
            region_list = "', '".join(regions)
            region_filter = f"AND d.region IN ('{region_list}')"
        
        # Query to get weekly trends by region
        query = f"""
        WITH weekly_data AS (
            SELECT 
                d.region,
                strftime('%W', f.transaction_date) as week_num,
                'Week ' || (CAST(strftime('%W', f.transaction_date) AS INTEGER) - 
                           CAST(strftime('%W', date('now', '-{weeks*7} days')) AS INTEGER) + 1) as week_label,
                COALESCE(SUM(f.fni_revenue), 0) as revenue
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE f.transaction_date >= date('now', '-{weeks*7} days')
            {region_filter}
            GROUP BY d.region, week_num
            ORDER BY week_num
        )
        SELECT 
            week_label,
            region,
            ROUND(revenue, 2) as revenue
        FROM weekly_data
        ORDER BY week_num, region
        """
        
        result = await db_session.execute(text(query))
        rows = result.fetchall()
        
        if not rows:
            return json.dumps([])
        
        # Transform to frontend format
        weeks_data = {}
        for row in rows:
            week_label = row[0]
            region = row[1].lower()
            revenue = row[2]
            
            if week_label not in weeks_data:
                weeks_data[week_label] = {"week": week_label}
            
            weeks_data[week_label][region] = revenue
        
        result_list = list(weeks_data.values())
        return json.dumps(result_list, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_chart_change_request(
    user_query: str,
    current_charts: Optional[str] = None
) -> str:
    """Analyze user request to change chart types or get chart information.
    
    This tool helps understand user intent when they want to:
    - Change chart types (bar to pie, line to bar, etc.)
    - Get information about charts
    - Modify chart data or filters
    
    Args:
        user_query: User's natural language request about charts
        current_charts: JSON string describing current charts on the page
        
    Returns:
        JSON string with analysis and recommended actions:
        {
            "intent": "change_chart_type" | "get_chart_info" | "filter_data" | "other",
            "chart_id": "chart identifier if applicable",
            "new_chart_type": "bar" | "pie" | "line" | "area" | null,
            "message": "Response message for user",
            "action": "change_type" | "info" | "filter" | "none"
        }
    """
    import json
    import re
    
    # Detect chart type change intent
    chart_type_patterns = {
        'bar': r'\b(bar|bar chart|bars|column|columns)\b',
        'pie': r'\b(pie|pie chart|pie graph|circular)\b',
        'line': r'\b(line|line chart|line graph|trend)\b',
        'area': r'\b(area|area chart|area graph|filled)\b'
    }
    
    # Detect change intent
    change_patterns = [
        r'\b(change|switch|convert|transform|make|show as|display as|render as)\b',
        r'\b(to|into|as a|as an)\b'
    ]
    
    intent = "other"
    new_chart_type = None
    chart_id = None
    action = "none"
    
    query_lower = user_query.lower()
    
    # Check for change intent
    has_change_intent = any(re.search(pattern, query_lower) for pattern in change_patterns)
    
    if has_change_intent:
        intent = "change_chart_type"
        action = "change_type"
        
        # Find which chart type they want
        for chart_type, pattern in chart_type_patterns.items():
            if re.search(pattern, query_lower):
                new_chart_type = chart_type
                break
        
        # Try to identify which chart (if multiple charts exist)
        if current_charts:
            try:
                charts = json.loads(current_charts)
                if isinstance(charts, list) and len(charts) > 0:
                    # Default to first chart if not specified
                    chart_id = charts[0].get('id', 'top-programs')
                    
                    # Try to identify specific chart from query
                    for chart in charts:
                        if chart.get('title', '').lower() in query_lower:
                            chart_id = chart.get('id')
                            break
            except:
                pass
    
    # Check for info request
    info_patterns = [
        r'\b(what|tell me|show|explain|describe|info|information|details)\b',
        r'\b(about|regarding|concerning)\b.*\b(chart|graph|visualization)\b'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in info_patterns):
        intent = "get_chart_info"
        action = "info"
    
    # Build response message
    if intent == "change_chart_type" and new_chart_type:
        message = f"I'll change the chart to a {new_chart_type} chart for you."
    elif intent == "get_chart_info":
        message = "Here's information about the current charts on this dashboard."
    else:
        message = "I understand your request. Let me help you with that."
    
    result = {
        "intent": intent,
        "chart_id": chart_id or "top-programs",
        "new_chart_type": new_chart_type,
        "message": message,
        "action": action
    }
    
    return json.dumps(result, indent=2)


@tool
async def get_enhanced_kpi_data(
    time_period: str = "this_week"
) -> str:
    """Get enhanced KPI data with historical comparisons for dashboard metrics.
    
    Returns comprehensive KPI data including current and previous period metrics
    for accurate change percentage calculations.
    
    Args:
        time_period: Time period for analysis. Options:
                    - "this_week" (default)
                    - "this_month"
                    - "last_7_days"
                    - "last_30_days"
        
    Returns:
        JSON string with KPI data in format:
        {
            "current_period": {
                "total_revenue": 450000,
                "avg_penetration": 68.5,
                "total_transactions": 1250,
                "period_label": "This Week"
            },
            "previous_period": {
                "total_revenue": 420000,
                "avg_penetration": 65.2,
                "total_transactions": 1180,
                "period_label": "Last Week"
            },
            "changes": {
                "revenue_change_pct": 7.14,
                "penetration_change_pct": 5.06,
                "transactions_change_pct": 5.93
            }
        }
    """
    from app.db.database import get_db
    from app.agents.tools import generate_sql_query
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Use the agent to generate SQL for current period
        current_query_result = await generate_sql_query.ainvoke({
            "query": f"Get total F&I revenue, average penetration rate, and transaction count for {time_period.replace('_', ' ')}"
        })
        
        # Use the agent to generate SQL for previous period
        previous_period_map = {
            "this_week": "last week",
            "this_month": "last month",
            "last_7_days": "the 7 days before that",
            "last_30_days": "the 30 days before that"
        }
        previous_period = previous_period_map.get(time_period, "the previous period")
        
        previous_query_result = await generate_sql_query.ainvoke({
            "query": f"Get total F&I revenue, average penetration rate, and transaction count for {previous_period}"
        })
        
        # Parse the results (they come as string representations of data)
        import ast
        
        try:
            current_data_raw = ast.literal_eval(current_query_result)
            previous_data_raw = ast.literal_eval(previous_query_result)
        except:
            # If parsing fails, return error
            return json.dumps({"error": "Failed to parse query results"})
        
        # Extract values from query results
        if not current_data_raw or not previous_data_raw:
            return json.dumps({"error": "No data available for the specified period"})
        
        current_row = current_data_raw[0] if isinstance(current_data_raw, list) else current_data_raw
        previous_row = previous_data_raw[0] if isinstance(previous_data_raw, list) else previous_data_raw
        
        # Build response (handle different possible column names)
        def get_value(row, *possible_keys):
            for key in possible_keys:
                if key in row:
                    return row[key]
            return 0
        
        current_data = {
            "total_revenue": round(get_value(current_row, 'total_revenue', 'revenue', 'fni_revenue') or 0, 2),
            "avg_penetration": round(get_value(current_row, 'avg_penetration', 'penetration', 'penetration_rate') or 0, 2),
            "total_transactions": get_value(current_row, 'total_transactions', 'transaction_count', 'count') or 0,
            "period_label": time_period.replace('_', ' ').title()
        }
        
        previous_data = {
            "total_revenue": round(get_value(previous_row, 'total_revenue', 'revenue', 'fni_revenue') or 0, 2),
            "avg_penetration": round(get_value(previous_row, 'avg_penetration', 'penetration', 'penetration_rate') or 0, 2),
            "total_transactions": get_value(previous_row, 'total_transactions', 'transaction_count', 'count') or 0,
            "period_label": previous_period.title()
        }
        
        # Calculate changes
        def calc_change(current, previous):
            if previous == 0:
                return 0
            return round(((current - previous) / previous) * 100, 2)
        
        changes = {
            "revenue_change_pct": calc_change(current_data["total_revenue"], previous_data["total_revenue"]),
            "penetration_change_pct": calc_change(current_data["avg_penetration"], previous_data["avg_penetration"]),
            "transactions_change_pct": calc_change(current_data["total_transactions"], previous_data["total_transactions"])
        }
        
        result = {
            "current_period": current_data,
            "previous_period": previous_data,
            "changes": changes
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_chart_change_request(
    user_query: str,
    current_charts: Optional[str] = None
) -> str:
    """Analyze user request to change chart types or get chart information.
    
    This tool helps understand user intent when they want to:
    - Change chart types (bar to pie, line to bar, etc.)
    - Get information about charts
    - Modify chart data or filters
    
    Args:
        user_query: User's natural language request about charts
        current_charts: JSON string describing current charts on the page
        
    Returns:
        JSON string with analysis and recommended actions:
        {
            "intent": "change_chart_type" | "get_chart_info" | "filter_data" | "other",
            "chart_id": "chart identifier if applicable",
            "new_chart_type": "bar" | "pie" | "line" | "area" | null,
            "message": "Response message for user",
            "action": "change_type" | "info" | "filter" | "none"
        }
    """
    import json
    import re
    
    # Detect chart type change intent
    chart_type_patterns = {
        'bar': r'\b(bar|bar chart|bars|column|columns)\b',
        'pie': r'\b(pie|pie chart|pie graph|circular)\b',
        'line': r'\b(line|line chart|line graph|trend)\b',
        'area': r'\b(area|area chart|area graph|filled)\b'
    }
    
    # Detect change intent
    change_patterns = [
        r'\b(change|switch|convert|transform|make|show as|display as|render as)\b',
        r'\b(to|into|as a|as an)\b'
    ]
    
    intent = "other"
    new_chart_type = None
    chart_id = None
    action = "none"
    
    query_lower = user_query.lower()
    
    # Check for change intent
    has_change_intent = any(re.search(pattern, query_lower) for pattern in change_patterns)
    
    if has_change_intent:
        intent = "change_chart_type"
        action = "change_type"
        
        # Find which chart type they want
        for chart_type, pattern in chart_type_patterns.items():
            if re.search(pattern, query_lower):
                new_chart_type = chart_type
                break
        
        # Try to identify which chart (if multiple charts exist)
        if current_charts:
            try:
                charts = json.loads(current_charts)
                if isinstance(charts, list) and len(charts) > 0:
                    # Default to first chart if not specified
                    chart_id = charts[0].get('id', 'top-programs')
                    
                    # Try to identify specific chart from query
                    for chart in charts:
                        if chart.get('title', '').lower() in query_lower:
                            chart_id = chart.get('id')
                            break
            except:
                pass
    
    # Check for info request
    info_patterns = [
        r'\b(what|tell me|show|explain|describe|info|information|details)\b',
        r'\b(about|regarding|concerning)\b.*\b(chart|graph|visualization)\b'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in info_patterns):
        intent = "get_chart_info"
        action = "info"
    
    # Build response message
    if intent == "change_chart_type" and new_chart_type:
        message = f"I'll change the chart to a {new_chart_type} chart for you."
    elif intent == "get_chart_info":
        message = "Here's information about the current charts on this dashboard."
    else:
        message = "I understand your request. Let me help you with that."
    
    result = {
        "intent": intent,
        "chart_id": chart_id or "top-programs",
        "new_chart_type": new_chart_type,
        "message": message,
        "action": action
    }
    
    return json.dumps(result, indent=2)


@tool
async def get_filtered_fni_data(
    time_period: str = "this_week",
    dealer_ids: Optional[List[int]] = None,
    regions: Optional[List[str]] = None,
    manager_names: Optional[List[str]] = None
) -> str:
    """Get filtered F&I data for advanced dashboard filtering.
    
    Supports multiple filter dimensions for detailed analysis.
    
    Args:
        time_period: Time period ("this_week", "last_2_weeks", "this_month", "last_month")
        dealer_ids: List of dealer IDs to filter by
        regions: List of regions to filter by
        manager_names: List of finance manager names to filter by
        
    Returns:
        JSON string with filtered F&I transaction data
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Build WHERE clauses
        where_clauses = []
        
        # Time period filter
        period_filters = {
            "this_week": "f.transaction_date >= date('now', 'weekday 0', '-7 days')",
            "last_2_weeks": "f.transaction_date >= date('now', '-14 days')",
            "this_month": "f.transaction_date >= date('now', 'start of month')",
            "last_month": "f.transaction_date >= date('now', 'start of month', '-1 month') AND f.transaction_date < date('now', 'start of month')"
        }
        where_clauses.append(period_filters.get(time_period, period_filters["this_week"]))
        
        # Dealer filter
        if dealer_ids:
            dealer_list = ','.join(map(str, dealer_ids))
            where_clauses.append(f"f.dealer_id IN ({dealer_list})")
        
        # Region filter
        if regions:
            region_list = "', '".join(regions)
            where_clauses.append(f"d.region IN ('{region_list}')")
        
        # Manager filter
        if manager_names:
            manager_list = "', '".join(manager_names)
            where_clauses.append(f"f.finance_manager IN ('{manager_list}')")
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
        SELECT 
            d.name as dealer_name,
            d.region,
            f.finance_manager,
            SUM(f.fni_revenue) as total_revenue,
            AVG(f.penetration_rate) * 100 as avg_penetration,
            COUNT(*) as transaction_count
        FROM fni_transactions f
        JOIN dealers d ON f.dealer_id = d.id
        WHERE {where_clause}
        GROUP BY d.id, d.name, d.region, f.finance_manager
        ORDER BY total_revenue DESC
        LIMIT 100
        """
        
        result = await db_session.execute(text(query))
        rows = result.fetchall()
        
        if not rows:
            return json.dumps([])
        
        # Convert to list of dicts
        data = []
        for row in rows:
            data.append({
                "dealer_name": row[0],
                "region": row[1],
                "finance_manager": row[2],
                "total_revenue": round(row[3], 2),
                "avg_penetration": round(row[4], 2),
                "transaction_count": row[5]
            })
        
        return json.dumps(data, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_chart_change_request(
    user_query: str,
    current_charts: Optional[str] = None
) -> str:
    """Analyze user request to change chart types or get chart information.
    
    This tool helps understand user intent when they want to:
    - Change chart types (bar to pie, line to bar, etc.)
    - Get information about charts
    - Modify chart data or filters
    
    Args:
        user_query: User's natural language request about charts
        current_charts: JSON string describing current charts on the page
        
    Returns:
        JSON string with analysis and recommended actions:
        {
            "intent": "change_chart_type" | "get_chart_info" | "filter_data" | "other",
            "chart_id": "chart identifier if applicable",
            "new_chart_type": "bar" | "pie" | "line" | "area" | null,
            "message": "Response message for user",
            "action": "change_type" | "info" | "filter" | "none"
        }
    """
    import json
    import re
    
    # Detect chart type change intent
    chart_type_patterns = {
        'bar': r'\b(bar|bar chart|bars|column|columns)\b',
        'pie': r'\b(pie|pie chart|pie graph|circular)\b',
        'line': r'\b(line|line chart|line graph|trend)\b',
        'area': r'\b(area|area chart|area graph|filled)\b'
    }
    
    # Detect change intent
    change_patterns = [
        r'\b(change|switch|convert|transform|make|show as|display as|render as)\b',
        r'\b(to|into|as a|as an)\b'
    ]
    
    intent = "other"
    new_chart_type = None
    chart_id = None
    action = "none"
    
    query_lower = user_query.lower()
    
    # Check for change intent
    has_change_intent = any(re.search(pattern, query_lower) for pattern in change_patterns)
    
    if has_change_intent:
        intent = "change_chart_type"
        action = "change_type"
        
        # Find which chart type they want
        for chart_type, pattern in chart_type_patterns.items():
            if re.search(pattern, query_lower):
                new_chart_type = chart_type
                break
        
        # Try to identify which chart (if multiple charts exist)
        if current_charts:
            try:
                charts = json.loads(current_charts)
                if isinstance(charts, list) and len(charts) > 0:
                    # Default to first chart if not specified
                    chart_id = charts[0].get('id', 'top-programs')
                    
                    # Try to identify specific chart from query
                    for chart in charts:
                        if chart.get('title', '').lower() in query_lower:
                            chart_id = chart.get('id')
                            break
            except:
                pass
    
    # Check for info request
    info_patterns = [
        r'\b(what|tell me|show|explain|describe|info|information|details)\b',
        r'\b(about|regarding|concerning)\b.*\b(chart|graph|visualization)\b'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in info_patterns):
        intent = "get_chart_info"
        action = "info"
    
    # Build response message
    if intent == "change_chart_type" and new_chart_type:
        message = f"I'll change the chart to a {new_chart_type} chart for you."
    elif intent == "get_chart_info":
        message = "Here's information about the current charts on this dashboard."
    else:
        message = "I understand your request. Let me help you with that."
    
    result = {
        "intent": intent,
        "chart_id": chart_id or "top-programs",
        "new_chart_type": new_chart_type,
        "message": message,
        "action": action
    }
    
    return json.dumps(result, indent=2)


@tool
async def get_invite_campaign_data(
    date_range: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """Get invite marketing campaign performance data for dashboard.
    
    Returns campaign performance metrics including emails sent, opens, open rates,
    repair orders, and revenue for each campaign.
    
    Args:
        date_range: Optional date range filter (e.g., "Dec 2024", "last 30 days")
        category: Optional category filter (e.g., "Service Reminder", "Maintenance")
        
    Returns:
        JSON string with campaign data in format:
        [
            {
                "campaign_name": "1st Service Due",
                "category": "Service Reminder",
                "emails_sent": 2145,
                "unique_opens": 687,
                "open_rate": 32.0,
                "ro_count": 89,
                "revenue": 26700
            },
            ...
        ]
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Build WHERE clause
        where_clauses = []
        
        # Date range filter
        if date_range:
            # Handle common date range formats
            if "last 30 days" in date_range.lower() or "30 days" in date_range.lower():
                where_clauses.append("send_date >= date('now', '-30 days')")
            elif "last 7 days" in date_range.lower() or "7 days" in date_range.lower():
                where_clauses.append("send_date >= date('now', '-7 days')")
            elif "dec 2024" in date_range.lower():
                where_clauses.append("strftime('%Y-%m', send_date) = '2024-12'")
            elif "nov 2024" in date_range.lower():
                where_clauses.append("strftime('%Y-%m', send_date) = '2024-11'")
            elif "oct 2024" in date_range.lower():
                where_clauses.append("strftime('%Y-%m', send_date) = '2024-10'")
            else:
                # Default to last 30 days if unclear
                where_clauses.append("send_date >= date('now', '-30 days')")
        else:
            where_clauses.append("send_date >= date('now', '-30 days')")
        
        # Category filter
        if category and category.lower() != 'all':
            where_clauses.append(f"campaign_type = '{category}'")
        
        where_clause = " AND ".join(where_clauses)
        
        # Query to get campaign performance
        query = f"""
        SELECT
            campaign_name,
            campaign_type as category,
            SUM(emails_sent) as emails_sent,
            SUM(unique_opens) as unique_opens,
            ROUND(SUM(unique_opens) * 100.0 / NULLIF(SUM(emails_sent), 0), 1) as open_rate,
            SUM(ro_count) as ro_count,
            ROUND(SUM(revenue), 2) as revenue
        FROM marketing_campaigns
        WHERE {where_clause}
        GROUP BY campaign_name, campaign_type
        ORDER BY revenue DESC
        LIMIT 50
        """
        
        result = await db_session.execute(text(query))
        rows = result.fetchall()
        
        if not rows:
            return json.dumps([])
        
        # Convert to list of dicts
        data = []
        for row in rows:
            data.append({
                "campaign_name": row[0],
                "category": row[1],
                "emails_sent": int(row[2]) if row[2] else 0,
                "unique_opens": int(row[3]) if row[3] else 0,
                "open_rate": round(float(row[4]), 1) if row[4] else 0.0,
                "ro_count": int(row[5]) if row[5] else 0,
                "revenue": round(float(row[6]), 2) if row[6] else 0.0
            })
        
        return json.dumps(data, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_chart_change_request(
    user_query: str,
    current_charts: Optional[str] = None
) -> str:
    """Analyze user request to change chart types or get chart information.
    
    This tool helps understand user intent when they want to:
    - Change chart types (bar to pie, line to bar, etc.)
    - Get information about charts
    - Modify chart data or filters
    
    Args:
        user_query: User's natural language request about charts
        current_charts: JSON string describing current charts on the page
        
    Returns:
        JSON string with analysis and recommended actions:
        {
            "intent": "change_chart_type" | "get_chart_info" | "filter_data" | "other",
            "chart_id": "chart identifier if applicable",
            "new_chart_type": "bar" | "pie" | "line" | "area" | null,
            "message": "Response message for user",
            "action": "change_type" | "info" | "filter" | "none"
        }
    """
    import json
    import re
    
    # Detect chart type change intent
    chart_type_patterns = {
        'bar': r'\b(bar|bar chart|bars|column|columns)\b',
        'pie': r'\b(pie|pie chart|pie graph|circular)\b',
        'line': r'\b(line|line chart|line graph|trend)\b',
        'area': r'\b(area|area chart|area graph|filled)\b'
    }
    
    # Detect change intent
    change_patterns = [
        r'\b(change|switch|convert|transform|make|show as|display as|render as)\b',
        r'\b(to|into|as a|as an)\b'
    ]
    
    intent = "other"
    new_chart_type = None
    chart_id = None
    action = "none"
    
    query_lower = user_query.lower()
    
    # Check for change intent
    has_change_intent = any(re.search(pattern, query_lower) for pattern in change_patterns)
    
    if has_change_intent:
        intent = "change_chart_type"
        action = "change_type"
        
        # Find which chart type they want
        for chart_type, pattern in chart_type_patterns.items():
            if re.search(pattern, query_lower):
                new_chart_type = chart_type
                break
        
        # Try to identify which chart (if multiple charts exist)
        if current_charts:
            try:
                charts = json.loads(current_charts)
                if isinstance(charts, list) and len(charts) > 0:
                    # Default to first chart if not specified
                    chart_id = charts[0].get('id', 'top-programs')
                    
                    # Try to identify specific chart from query
                    for chart in charts:
                        if chart.get('title', '').lower() in query_lower:
                            chart_id = chart.get('id')
                            break
            except:
                pass
    
    # Check for info request
    info_patterns = [
        r'\b(what|tell me|show|explain|describe|info|information|details)\b',
        r'\b(about|regarding|concerning)\b.*\b(chart|graph|visualization)\b'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in info_patterns):
        intent = "get_chart_info"
        action = "info"
    
    # Build response message
    if intent == "change_chart_type" and new_chart_type:
        message = f"I'll change the chart to a {new_chart_type} chart for you."
    elif intent == "get_chart_info":
        message = "Here's information about the current charts on this dashboard."
    else:
        message = "I understand your request. Let me help you with that."
    
    result = {
        "intent": intent,
        "chart_id": chart_id or "top-programs",
        "new_chart_type": new_chart_type,
        "message": message,
        "action": action
    }
    
    return json.dumps(result, indent=2)


@tool
async def get_invite_monthly_trends(
    months: int = 6
) -> str:
    """Get invite marketing campaign monthly trends for dashboard charts.
    
    Returns monthly aggregated data for emails sent, opens, repair orders, and revenue.
    
    Args:
        months: Number of months to retrieve (default: 6)
        
    Returns:
        JSON string with monthly trend data in format:
        [
            {
                "month": "Jul",
                "emails": 28500,
                "opens": 8550,
                "ro": 1026,
                "revenue": 168570
            },
            ...
        ]
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Query to get monthly trends
        query = f"""
        SELECT
            strftime('%m', send_date) as month_num,
            CASE strftime('%m', send_date)
                WHEN '01' THEN 'Jan'
                WHEN '02' THEN 'Feb'
                WHEN '03' THEN 'Mar'
                WHEN '04' THEN 'Apr'
                WHEN '05' THEN 'May'
                WHEN '06' THEN 'Jun'
                WHEN '07' THEN 'Jul'
                WHEN '08' THEN 'Aug'
                WHEN '09' THEN 'Sep'
                WHEN '10' THEN 'Oct'
                WHEN '11' THEN 'Nov'
                WHEN '12' THEN 'Dec'
            END as month,
            SUM(emails_sent) as emails,
            SUM(unique_opens) as opens,
            SUM(ro_count) as ro,
            ROUND(SUM(revenue), 2) as revenue
        FROM marketing_campaigns
        WHERE send_date >= date('now', '-{months} months')
        GROUP BY month_num, month
        ORDER BY month_num DESC
        LIMIT {months}
        """
        
        result = await db_session.execute(text(query))
        rows = result.fetchall()
        
        if not rows:
            return json.dumps([])
        
        # Convert to list of dicts
        data = []
        for row in rows:
            data.append({
                "month": row[1],
                "emails": int(row[2]) if row[2] else 0,
                "opens": int(row[3]) if row[3] else 0,
                "ro": int(row[4]) if row[4] else 0,
                "revenue": round(float(row[5]), 2) if row[5] else 0.0
            })
        
        return json.dumps(data, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_chart_change_request(
    user_query: str,
    current_charts: Optional[str] = None
) -> str:
    """Analyze user request to change chart types or get chart information.
    
    This tool helps understand user intent when they want to:
    - Change chart types (bar to pie, line to bar, etc.)
    - Get information about charts
    - Modify chart data or filters
    
    Args:
        user_query: User's natural language request about charts
        current_charts: JSON string describing current charts on the page
        
    Returns:
        JSON string with analysis and recommended actions:
        {
            "intent": "change_chart_type" | "get_chart_info" | "filter_data" | "other",
            "chart_id": "chart identifier if applicable",
            "new_chart_type": "bar" | "pie" | "line" | "area" | null,
            "message": "Response message for user",
            "action": "change_type" | "info" | "filter" | "none"
        }
    """
    import json
    import re
    
    # Detect chart type change intent
    chart_type_patterns = {
        'bar': r'\b(bar|bar chart|bars|column|columns)\b',
        'pie': r'\b(pie|pie chart|pie graph|circular)\b',
        'line': r'\b(line|line chart|line graph|trend)\b',
        'area': r'\b(area|area chart|area graph|filled)\b'
    }
    
    # Detect change intent
    change_patterns = [
        r'\b(change|switch|convert|transform|make|show as|display as|render as)\b',
        r'\b(to|into|as a|as an)\b'
    ]
    
    intent = "other"
    new_chart_type = None
    chart_id = None
    action = "none"
    
    query_lower = user_query.lower()
    
    # Check for change intent
    has_change_intent = any(re.search(pattern, query_lower) for pattern in change_patterns)
    
    if has_change_intent:
        intent = "change_chart_type"
        action = "change_type"
        
        # Find which chart type they want
        for chart_type, pattern in chart_type_patterns.items():
            if re.search(pattern, query_lower):
                new_chart_type = chart_type
                break
        
        # Try to identify which chart (if multiple charts exist)
        if current_charts:
            try:
                charts = json.loads(current_charts)
                if isinstance(charts, list) and len(charts) > 0:
                    # Default to first chart if not specified
                    chart_id = charts[0].get('id', 'top-programs')
                    
                    # Try to identify specific chart from query
                    for chart in charts:
                        if chart.get('title', '').lower() in query_lower:
                            chart_id = chart.get('id')
                            break
            except:
                pass
    
    # Check for info request
    info_patterns = [
        r'\b(what|tell me|show|explain|describe|info|information|details)\b',
        r'\b(about|regarding|concerning)\b.*\b(chart|graph|visualization)\b'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in info_patterns):
        intent = "get_chart_info"
        action = "info"
    
    # Build response message
    if intent == "change_chart_type" and new_chart_type:
        message = f"I'll change the chart to a {new_chart_type} chart for you."
    elif intent == "get_chart_info":
        message = "Here's information about the current charts on this dashboard."
    else:
        message = "I understand your request. Let me help you with that."
    
    result = {
        "intent": intent,
        "chart_id": chart_id or "top-programs",
        "new_chart_type": new_chart_type,
        "message": message,
        "action": action
    }
    
    return json.dumps(result, indent=2)


@tool
async def get_invite_enhanced_kpi_data(
    date_range: Optional[str] = None
) -> str:
    """Get enhanced invite marketing KPI data with period comparisons.
    
    Returns comprehensive KPI data including current and previous period metrics
    for accurate change percentage calculations.
    
    Args:
        date_range: Optional date range (e.g., "Dec 2024", "this month")
        
    Returns:
        JSON string with KPI data in format:
        {
            "current_period": {
                "total_emails_sent": 35000,
                "total_unique_opens": 10500,
                "avg_open_rate": 30.0,
                "total_ro_count": 1200,
                "total_revenue": 300000,
                "period_label": "Dec 2024"
            },
            "previous_period": {
                "total_emails_sent": 31500,
                "total_unique_opens": 9450,
                "avg_open_rate": 30.0,
                "total_ro_count": 1134,
                "total_revenue": 280000,
                "period_label": "Nov 2024"
            },
            "changes": {
                "emails_sent_change": 11.1,
                "opens_change": 11.1,
                "open_rate_change": 0.0,
                "ro_count_change": 5.8,
                "revenue_change": 7.1
            }
        }
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Determine current period filter
        if date_range and "dec 2024" in date_range.lower():
            current_filter = "strftime('%Y-%m', send_date) = '2024-12'"
            previous_filter = "strftime('%Y-%m', send_date) = '2024-11'"
            current_label = "Dec 2024"
            previous_label = "Nov 2024"
        elif date_range and "nov 2024" in date_range.lower():
            current_filter = "strftime('%Y-%m', send_date) = '2024-11'"
            previous_filter = "strftime('%Y-%m', send_date) = '2024-10'"
            current_label = "Nov 2024"
            previous_label = "Oct 2024"
        elif date_range and "this month" in date_range.lower():
            current_filter = "strftime('%Y-%m', send_date) = strftime('%Y-%m', 'now')"
            previous_filter = "strftime('%Y-%m', send_date) = strftime('%Y-%m', date('now', 'start of month', '-1 month'))"
            current_label = "This Month"
            previous_label = "Last Month"
        else:
            # Default to last 30 days vs previous 30 days
            current_filter = "send_date >= date('now', '-30 days')"
            previous_filter = "send_date >= date('now', '-60 days') AND send_date < date('now', '-30 days')"
            current_label = "Last 30 Days"
            previous_label = "Previous 30 Days"
        
        # Get current period data
        current_query = f"""
        SELECT
            SUM(emails_sent) as total_emails_sent,
            SUM(unique_opens) as total_unique_opens,
            ROUND(SUM(unique_opens) * 100.0 / NULLIF(SUM(emails_sent), 0), 1) as avg_open_rate,
            SUM(ro_count) as total_ro_count,
            ROUND(SUM(revenue), 2) as total_revenue
        FROM marketing_campaigns
        WHERE {current_filter}
        """
        
        # Get previous period data
        previous_query = f"""
        SELECT
            SUM(emails_sent) as total_emails_sent,
            SUM(unique_opens) as total_unique_opens,
            ROUND(SUM(unique_opens) * 100.0 / NULLIF(SUM(emails_sent), 0), 1) as avg_open_rate,
            SUM(ro_count) as total_ro_count,
            ROUND(SUM(revenue), 2) as total_revenue
        FROM marketing_campaigns
        WHERE {previous_filter}
        """
        
        current_result = await db_session.execute(text(current_query))
        current_row = current_result.fetchone()
        
        previous_result = await db_session.execute(text(previous_query))
        previous_row = previous_result.fetchone()
        
        # Extract values
        def get_value(row, index, default=0):
            return row[index] if row and row[index] is not None else default
        
        current_data = {
            "total_emails_sent": int(get_value(current_row, 0, 0)),
            "total_unique_opens": int(get_value(current_row, 1, 0)),
            "avg_open_rate": round(float(get_value(current_row, 2, 0)), 1),
            "total_ro_count": int(get_value(current_row, 3, 0)),
            "total_revenue": round(float(get_value(current_row, 4, 0)), 2),
            "period_label": current_label
        }
        
        previous_data = {
            "total_emails_sent": int(get_value(previous_row, 0, 0)),
            "total_unique_opens": int(get_value(previous_row, 1, 0)),
            "avg_open_rate": round(float(get_value(previous_row, 2, 0)), 1),
            "total_ro_count": int(get_value(previous_row, 3, 0)),
            "total_revenue": round(float(get_value(previous_row, 4, 0)), 2),
            "period_label": previous_label
        }
        
        # Calculate changes
        def calc_change(current, previous):
            if previous == 0:
                return 0.0
            return round(((current - previous) / previous) * 100, 1)
        
        changes = {
            "emails_sent_change": calc_change(current_data["total_emails_sent"], previous_data["total_emails_sent"]),
            "opens_change": calc_change(current_data["total_unique_opens"], previous_data["total_unique_opens"]),
            "open_rate_change": calc_change(current_data["avg_open_rate"], previous_data["avg_open_rate"]),
            "ro_count_change": calc_change(current_data["total_ro_count"], previous_data["total_ro_count"]),
            "revenue_change": calc_change(current_data["total_revenue"], previous_data["total_revenue"])
        }
        
        result = {
            "current_period": current_data,
            "previous_period": previous_data,
            "changes": changes
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_chart_change_request(
    user_query: str,
    current_charts: Optional[str] = None
) -> str:
    """Analyze user request to change chart types or get chart information.
    
    This tool helps understand user intent when they want to:
    - Change chart types (bar to pie, line to bar, etc.)
    - Get information about charts
    - Modify chart data or filters
    
    Args:
        user_query: User's natural language request about charts
        current_charts: JSON string describing current charts on the page
        
    Returns:
        JSON string with analysis and recommended actions:
        {
            "intent": "change_chart_type" | "get_chart_info" | "filter_data" | "other",
            "chart_id": "chart identifier if applicable",
            "new_chart_type": "bar" | "pie" | "line" | "area" | null,
            "message": "Response message for user",
            "action": "change_type" | "info" | "filter" | "none"
        }
    """
    import json
    import re
    
    # Detect chart type change intent
    chart_type_patterns = {
        'bar': r'\b(bar|bar chart|bars|column|columns)\b',
        'pie': r'\b(pie|pie chart|pie graph|circular)\b',
        'line': r'\b(line|line chart|line graph|trend)\b',
        'area': r'\b(area|area chart|area graph|filled)\b'
    }
    
    # Detect change intent
    change_patterns = [
        r'\b(change|switch|convert|transform|make|show as|display as|render as)\b',
        r'\b(to|into|as a|as an)\b'
    ]
    
    intent = "other"
    new_chart_type = None
    chart_id = None
    action = "none"
    
    query_lower = user_query.lower()
    
    # Check for change intent
    has_change_intent = any(re.search(pattern, query_lower) for pattern in change_patterns)
    
    if has_change_intent:
        intent = "change_chart_type"
        action = "change_type"
        
        # Find which chart type they want
        for chart_type, pattern in chart_type_patterns.items():
            if re.search(pattern, query_lower):
                new_chart_type = chart_type
                break
        
        # Try to identify which chart (if multiple charts exist)
        if current_charts:
            try:
                charts = json.loads(current_charts)
                if isinstance(charts, list) and len(charts) > 0:
                    # Default to first chart if not specified
                    chart_id = charts[0].get('id', 'top-programs')
                    
                    # Try to identify specific chart from query
                    for chart in charts:
                        if chart.get('title', '').lower() in query_lower:
                            chart_id = chart.get('id')
                            break
            except:
                pass
    
    # Check for info request
    info_patterns = [
        r'\b(what|tell me|show|explain|describe|info|information|details)\b',
        r'\b(about|regarding|concerning)\b.*\b(chart|graph|visualization)\b'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in info_patterns):
        intent = "get_chart_info"
        action = "info"
    
    # Build response message
    if intent == "change_chart_type" and new_chart_type:
        message = f"I'll change the chart to a {new_chart_type} chart for you."
    elif intent == "get_chart_info":
        message = "Here's information about the current charts on this dashboard."
    else:
        message = "I understand your request. Let me help you with that."
    
    result = {
        "intent": intent,
        "chart_id": chart_id or "top-programs",
        "new_chart_type": new_chart_type,
        "message": message,
        "action": action
    }
    
    return json.dumps(result, indent=2)


@tool
async def get_service_appointments(
    appointment_date: Optional[str] = None,
    advisor: Optional[str] = None,
    status: Optional[str] = None,
    customer_name: Optional[str] = None
) -> str:
    """Get service appointments for Engage/Customer Experience Management page.
    
    Retrieves appointments with customer information including loyalty tiers,
    service history, and preferred services. Perfect for answering questions
    about daily schedules, customer arrivals, and appointment management.
    
    Args:
        appointment_date: Date in YYYY-MM-DD format (defaults to today)
        advisor: Filter by advisor name (optional)
        status: Filter by status - not_arrived, checked_in, in_progress, completed, cancelled (optional)
        customer_name: Filter by customer name (optional)
        
    Returns:
        JSON string with appointments data including:
        - appointment details (time, service type, vehicle info)
        - customer information (name, phone, email, loyalty tier)
        - service history and preferences
        - status and RO numbers
    """
    from app.db.database import get_db
    from datetime import date, datetime
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Default to today if not provided
        if appointment_date:
            try:
                query_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            except ValueError:
                query_date = date.today()
        else:
            query_date = date.today()
        
        # Build query
        query = """
            SELECT 
                sa.id,
                sa.appointment_date,
                sa.appointment_time,
                sa.service_type,
                sa.estimated_duration,
                sa.vehicle_vin,
                sa.vehicle_year,
                sa.vehicle_make,
                sa.vehicle_model,
                sa.vehicle_mileage,
                sa.vehicle_icon_color,
                sa.customer_name,
                sa.advisor,
                sa.status,
                sa.ro_number,
                sa.code,
                c.phone,
                c.email,
                c.loyalty_tier,
                c.preferred_services,
                c.service_history_count,
                c.last_visit_date
            FROM service_appointments sa
            LEFT JOIN customers c ON sa.customer_id = c.id
            WHERE sa.appointment_date = :appointment_date
        """
        
        params = {"appointment_date": query_date}
        
        if advisor and advisor != 'All':
            query += " AND sa.advisor = :advisor"
            params["advisor"] = advisor
        
        if status and status != 'All':
            query += " AND sa.status = :status"
            params["status"] = status
        
        if customer_name:
            query += " AND sa.customer_name LIKE :customer_name"
            params["customer_name"] = f"%{customer_name}%"
        
        query += " ORDER BY sa.appointment_time"
        
        result = await db_session.execute(text(query), params)
        rows = result.fetchall()
        columns = result.keys()
        
        appointments = []
        for row in rows:
            apt_dict = dict(zip(columns, row))
            # Parse preferred_services JSON if present
            if apt_dict.get('preferred_services'):
                try:
                    apt_dict['preferred_services'] = json.loads(apt_dict['preferred_services'])
                except:
                    apt_dict['preferred_services'] = []
            else:
                apt_dict['preferred_services'] = []
            appointments.append(apt_dict)
        
        return json.dumps(appointments, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def get_customer_info(
    customer_name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None
) -> str:
    """Get customer information including loyalty tier, service history, and preferences.
    
    Retrieves detailed customer profile for personalized service experience.
    Use this when users ask about specific customers, their history, or preferences.
    
    Args:
        customer_name: Customer name to search for (optional)
        phone: Customer phone number (optional)
        email: Customer email (optional)
        
    Returns:
        JSON string with customer information:
        - Basic info (name, phone, email)
        - Loyalty tier (Platinum, Gold, Silver)
        - Preferred services
        - Service history count
        - Last visit date
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        query = "SELECT * FROM customers WHERE 1=1"
        params = {}
        
        if customer_name:
            query += " AND customer_name LIKE :customer_name"
            params["customer_name"] = f"%{customer_name}%"
        
        if phone:
            query += " AND phone = :phone"
            params["phone"] = phone
        
        if email:
            query += " AND email = :email"
            params["email"] = email
        
        result = await db_session.execute(text(query), params)
        rows = result.fetchall()
        columns = result.keys()
        
        customers = []
        for row in rows:
            cust_dict = dict(zip(columns, row))
            # Parse preferred_services JSON
            if cust_dict.get('preferred_services'):
                try:
                    cust_dict['preferred_services'] = json.loads(cust_dict['preferred_services'])
                except:
                    cust_dict['preferred_services'] = []
            else:
                cust_dict['preferred_services'] = []
            customers.append(cust_dict)
        
        return json.dumps(customers, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def get_appointment_statistics(
    appointment_date: Optional[str] = None,
    advisor: Optional[str] = None
) -> str:
    """Get appointment statistics and summary for a given date.
    
    Provides counts by status, advisor performance, and needs action count.
    Use this when users ask about appointment summaries, statistics, or overviews.
    
    Args:
        appointment_date: Date in YYYY-MM-DD format (defaults to today)
        advisor: Filter by advisor name (optional)
        
    Returns:
        JSON string with statistics:
        - Total appointments
        - Counts by status (not_arrived, checked_in, in_progress, completed, cancelled)
        - Needs action count
        - Advisor breakdown (if advisor not specified)
    """
    from app.db.database import get_db
    from datetime import date, datetime
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Default to today if not provided
        if appointment_date:
            try:
                query_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            except ValueError:
                query_date = date.today()
        else:
            query_date = date.today()
        
        # Get counts by status
        query = """
            SELECT 
                status,
                COUNT(*) as count
            FROM service_appointments
            WHERE appointment_date = :appointment_date
        """
        
        params = {"appointment_date": query_date}
        
        if advisor and advisor != 'All':
            query += " AND advisor = :advisor"
            params["advisor"] = advisor
        
        query += " GROUP BY status"
        
        result = await db_session.execute(text(query), params)
        rows = result.fetchall()
        
        status_counts = {row[0]: row[1] for row in rows}
        total = sum(status_counts.values())
        needs_action = status_counts.get('not_arrived', 0)
        
        # Get advisor breakdown if advisor not specified
        advisor_breakdown = {}
        if not advisor or advisor == 'All':
            advisor_query = """
                SELECT 
                    advisor,
                    COUNT(*) as count
                FROM service_appointments
                WHERE appointment_date = :appointment_date
                GROUP BY advisor
            """
            advisor_result = await db_session.execute(text(advisor_query), params)
            advisor_rows = advisor_result.fetchall()
            advisor_breakdown = {row[0]: row[1] for row in advisor_rows}
        
        stats = {
            "appointment_date": str(query_date),
            "total_appointments": total,
            "status_breakdown": status_counts,
            "needs_action_count": needs_action,
            "advisor_breakdown": advisor_breakdown if advisor_breakdown else None
        }
        
        return json.dumps(stats, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()
