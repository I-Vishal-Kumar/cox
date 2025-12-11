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
