"""
Advanced analytics tools for enterprise use cases:
- Data quality checks
- Executive summaries
- Anomaly detection
- Model performance analysis
- Stockout risk
- Repeat repair analysis
- Dashboard builder

These tools use LLM agents for flexible, intelligent processing rather than hardcoded logic.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_anthropic  import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import text
from datetime import datetime, date, timedelta
import json
from app.agents.tools import generate_sql_query
from app.core.config import settings
from app.utils.schema_utils import get_cached_schema, get_fallback_schema


@tool
async def check_data_quality(
    user_query: str,
    table_name: Optional[str] = None,
    check_type: Optional[str] = None
) -> str:
    """Check data quality issues like missing VINs, inconsistent timestamps, null values.
    Uses LLM agent to intelligently determine what checks to run based on user query.
    
    Args:
        user_query: Natural language query about data quality (e.g., "Check for missing VINs", "Find data quality issues")
        table_name: Specific table to check (optional, will be inferred from query if not provided)
        check_type: Type of check - 'missing_vin', 'inconsistent_timestamps', 'null_values', 'duplicates', 'all' (optional, inferred from query)
    
    Returns:
        JSON string with data quality issues found
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Use LLM to determine what checks to run based on user query
        llm = ChatAnthropic(
            model=settings.anthropic_model,
            temperature=0.2,
            api_key=settings.anthropic_api_key
        )
        
        # Get schema for context
        try:
            schema = await get_cached_schema(db_session)
        except:
            schema = get_fallback_schema()
        
        check_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a data quality analysis agent for Cox Automotive's SQLite database.

**Database Context:**
- Database: SQLite 3.x
- Schema: {schema[:1000]}...

**Your task:** Analyze the user's data quality query and determine:
1. Which tables to check (if not specified)
2. Which types of checks to perform
3. What specific columns/fields to examine

**Available Check Types:**
- missing_vin: Check for missing VIN numbers in vehicle-related tables
- inconsistent_timestamps: Check for logical timestamp errors (e.g., actual < scheduled)
- null_values: Check for NULL values in critical columns
- duplicates: Check for duplicate records
- all: Run all checks

**SQLite Date Functions:**
- Use date('now', '-N days') for date ranges (NOT '-N weeks' or '-N months')
- Example: date('now', '-30 days') for last 30 days

Return JSON with:
{{
    "tables_to_check": ["table1", "table2"],
    "check_types": ["missing_vin", "null_values"],
    "specific_columns": ["column1", "column2"],
    "reasoning": "Why these checks are needed"
}}"""),
            ("human", "User query: {query}\n\nTable name (if provided): {table_name}\n\nCheck type (if provided): {check_type}\n\nDetermine what data quality checks to perform:")
        ])
        
        check_plan = await (check_prompt | llm).ainvoke({
            "query": user_query,
            "table_name": table_name or "not specified",
            "check_type": check_type or "not specified"
        })
        
        # Parse LLM response to get check plan
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', check_plan.content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                # Fallback: infer from query
                plan = {
                    "tables_to_check": [table_name] if table_name else ["service_appointments", "repair_orders", "fni_transactions"],
                    "check_types": [check_type] if check_type else ["all"],
                    "specific_columns": [],
                    "reasoning": "Inferred from query"
                }
        except:
            # Fallback plan
            plan = {
                "tables_to_check": [table_name] if table_name else ["service_appointments", "repair_orders"],
                "check_types": [check_type] if check_type else ["all"],
                "specific_columns": []
            }
        
        issues = []
        check_types = plan.get("check_types", ["all"])
        tables_to_check = plan.get("tables_to_check", [])
        
        # Check for missing VINs in service appointments and repair orders
        if "all" in check_types or "missing_vin" in check_types:
            vin_tables = [t for t in tables_to_check if t in ["service_appointments", "repair_orders"]]
            if not vin_tables:
                vin_tables = ["service_appointments", "repair_orders"]
            
            for table in vin_tables:
                col = "vehicle_vin"
                try:
                    result = await db_session.execute(text(f"""
                        SELECT COUNT(*) as total, 
                               SUM(CASE WHEN {col} IS NULL OR {col} = '' THEN 1 ELSE 0 END) as missing
                        FROM {table}
                        WHERE created_at >= date('now', '-30 days')
                    """))
                    row = result.fetchone()
                    if row and row[1] > 0:
                        issues.append({
                            "type": "missing_vin",
                            "table": table,
                            "column": col,
                            "missing_count": row[1],
                            "total_count": row[0],
                            "percentage": round((row[1] / row[0] * 100) if row[0] > 0 else 0, 2),
                            "severity": "high" if (row[1] / row[0] > 0.1) else "medium"
                        })
                except:
                    pass
        
        # Check for inconsistent timestamps
        if "all" in check_types or "inconsistent_timestamps" in check_types:
            timestamp_checks = [
                ("shipments", "scheduled_departure", "actual_departure"),
                ("shipments", "scheduled_arrival", "actual_arrival"),
            ]
            
            for table, scheduled_col, actual_col in timestamp_checks:
                try:
                    result = await db_session.execute(text(f"""
                        SELECT COUNT(*) as total,
                               SUM(CASE WHEN {actual_col} < {scheduled_col} THEN 1 ELSE 0 END) as inconsistent
                        FROM {table}
                        WHERE {scheduled_col} IS NOT NULL AND {actual_col} IS NOT NULL
                    """))
                    row = result.fetchone()
                    if row and row[1] > 0:
                        issues.append({
                            "type": "inconsistent_timestamps",
                            "table": table,
                            "scheduled_column": scheduled_col,
                            "actual_column": actual_col,
                            "inconsistent_count": row[1],
                            "total_count": row[0],
                            "severity": "high"
                        })
                except:
                    pass
        
        # Check for null values in critical columns
        if "all" in check_types or "null_values" in check_types:
            null_checks = [
                ("fni_transactions", "fni_revenue"),
                ("marketing_campaigns", "emails_sent"),
                ("service_appointments", "appointment_date"),
            ]
            
            for table, col in null_checks:
                try:
                    result = await db_session.execute(text(f"""
                        SELECT COUNT(*) as total,
                               SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) as null_count
                        FROM {table}
                        WHERE created_at >= date('now', '-30 days')
                    """))
                    row = result.fetchone()
                    if row and row[1] > 0:
                        issues.append({
                            "type": "null_values",
                            "table": table,
                            "column": col,
                            "null_count": row[1],
                            "total_count": row[0],
                            "percentage": round((row[1] / row[0] * 100) if row[0] > 0 else 0, 2),
                            "severity": "medium" if (row[1] / row[0] > 0.05) else "low"
                        })
                except:
                    pass
        
        # Check for duplicates
        if "all" in check_types or "duplicates" in check_types:
            duplicate_checks = [
                ("service_appointments", ["appointment_date", "appointment_time", "customer_name", "vehicle_vin"]),
            ]
            
            for table, cols in duplicate_checks:
                try:
                    cols_str = ", ".join(cols)
                    result = await db_session.execute(text(f"""
                        SELECT {cols_str}, COUNT(*) as count
                        FROM {table}
                        GROUP BY {cols_str}
                        HAVING COUNT(*) > 1
                        LIMIT 10
                    """))
                    duplicates = result.fetchall()
                    if duplicates:
                        issues.append({
                            "type": "duplicates",
                            "table": table,
                            "columns": cols,
                            "duplicate_count": len(duplicates),
                            "severity": "medium"
                        })
                except:
                    pass
        
        return json.dumps({
            "data_quality_report": {
                "timestamp": datetime.now().isoformat(),
                "issues_found": len(issues),
                "issues": issues,
                "summary": {
                    "high_severity": len([i for i in issues if i.get("severity") == "high"]),
                    "medium_severity": len([i for i in issues if i.get("severity") == "medium"]),
                    "low_severity": len([i for i in issues if i.get("severity") == "low"])
                }
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def generate_executive_summary(
    persona: str = "CEO",
    time_period: str = "week",
    include_visuals: bool = True
) -> str:
    """Generate personalized executive summary for different personas (CEO, COO, CFO, VP Sales).
    
    Args:
        persona: Executive persona - 'CEO', 'COO', 'CFO', 'VP_Sales'
        time_period: Time period - 'week', 'month', 'quarter'
        include_visuals: Whether to include chart configurations
    
    Returns:
        JSON string with executive summary including top wins, risks, forecast, sentiment, anomalies
    """
    from app.db.database import get_db
    from app.agents.tools import generate_sql_query
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Get data based on time period
        if time_period == "week":
            date_filter = "date('now', '-7 days')"
        elif time_period == "month":
            date_filter = "date('now', '-30 days')"
        else:
            date_filter = "date('now', '-90 days')"
        
        # Get key metrics based on persona
        summary_data = {}
        
        if persona in ["CEO", "COO", "CFO"]:
            # Revenue metrics
            revenue_query = f"""
                SELECT 
                    SUM(fni_revenue) as total_revenue,
                    COUNT(*) as transactions,
                    AVG(penetration_rate) * 100 as avg_penetration
                FROM fni_transactions
                WHERE transaction_date >= {date_filter}
            """
            result = await db_session.execute(text(revenue_query))
            revenue_data = result.fetchone()
            summary_data["revenue"] = {
                "total": float(revenue_data[0]) if revenue_data[0] else 0,
                "transactions": revenue_data[1] or 0,
                "avg_penetration": round(revenue_data[2] or 0, 2)
            }
        
        if persona in ["CEO", "COO", "VP_Sales"]:
            # Service metrics
            service_query = f"""
                SELECT 
                    COUNT(*) as appointments,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(revenue) as service_revenue
                FROM service_appointments
                WHERE appointment_date >= {date_filter}
            """
            result = await db_session.execute(text(service_query))
            service_data = result.fetchone()
            summary_data["service"] = {
                "appointments": service_data[0] or 0,
                "completed": service_data[1] or 0,
                "revenue": float(service_data[2]) if service_data[2] else 0
            }
        
        # Get top wins (best performing dealers/campaigns)
        wins_query = f"""
            SELECT d.name as dealer_name, SUM(f.fni_revenue) as revenue
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE f.transaction_date >= {date_filter}
            GROUP BY d.name
            ORDER BY revenue DESC
            LIMIT 5
        """
        result = await db_session.execute(text(wins_query))
        wins = [{"dealer": row[0], "revenue": float(row[1])} for row in result.fetchall()]
        summary_data["top_wins"] = wins
        
        # Get risks (alerts/KPI issues)
        alerts_query = f"""
            SELECT metric, current_value, change_percent, root_cause
            FROM kpi_metrics
            WHERE alert_date >= {date_filter}
            AND change_percent < -5
            ORDER BY ABS(change_percent) DESC
            LIMIT 5
        """
        result = await db_session.execute(text(alerts_query))
        risks = [{
            "metric": row[0],
            "current_value": row[1],
            "change_percent": row[2],
            "root_cause": row[3]
        } for row in result.fetchall()]
        summary_data["risks"] = risks
        
        # Generate summary text based on persona
        persona_templates = {
            "CEO": "Strategic overview focusing on overall business performance, key wins, and critical risks.",
            "COO": "Operational metrics including service efficiency, logistics performance, and plant operations.",
            "CFO": "Financial metrics including revenue, margins, and cost drivers.",
            "VP_Sales": "Sales performance, dealer metrics, and customer engagement."
        }
        
        summary_text = f"""
        {persona} Executive Summary - {time_period.capitalize()}ly Report
        
        **Overview:**
        {persona_templates.get(persona, "Comprehensive business performance summary")}
        
        **Key Metrics:**
        - Revenue: ${summary_data.get('revenue', {}).get('total', 0):,.2f}
        - Transactions: {summary_data.get('revenue', {}).get('transactions', 0):,}
        - Service Appointments: {summary_data.get('service', {}).get('appointments', 0):,}
        
        **Top Wins:**
        {chr(10).join([f"- {w['dealer']}: ${w['revenue']:,.2f}" for w in summary_data.get('top_wins', [])])}
        
        **Risks & Opportunities:**
        {chr(10).join([f"- {r['metric']}: {r['change_percent']:.1f}% change - {r['root_cause']}" for r in summary_data.get('risks', [])])}
        """
        
        return json.dumps({
            "executive_summary": {
                "persona": persona,
                "time_period": time_period,
                "generated_at": datetime.now().isoformat(),
                "summary_text": summary_text.strip(),
                "data": summary_data,
                "include_visuals": include_visuals
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def detect_anomalies(
    user_query: str,
    metric_type: Optional[str] = None,
    threshold: Optional[float] = None
) -> str:
    """Detect anomalies in sales, defects, service workload, inventory, etc.
    Uses LLM agent to intelligently determine what metrics to check and appropriate thresholds.
    
    Args:
        user_query: Natural language query (e.g., "Detect anomalies in sales", "Find unusual patterns")
        metric_type: Type of metric - 'sales', 'defects', 'service', 'inventory', 'all' (optional, inferred from query)
        threshold: Deviation threshold (0.2 = 20% deviation from normal) (optional, inferred from query)
    
    Returns:
        JSON string with detected anomalies, contextual messages, and root cause suggestions
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Use LLM to determine metric type and threshold
        llm = ChatAnthropic(
            model=settings.anthropic_model,
            temperature=0.2,
            api_key=settings.anthropic_api_key
        )
        
        try:
            schema = await get_cached_schema(db_session)
        except:
            schema = get_fallback_schema()
        
        anomaly_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an anomaly detection agent for Cox Automotive's SQLite database.

**Database Context:**
- Database: SQLite 3.x
- Schema: {schema[:1000]}...

**Your task:** Determine what metrics to check and appropriate thresholds for anomaly detection.

**Available Metric Types:**
- sales: F&I revenue, transaction counts, penetration rates
- defects: Quality issues, warranty claims
- service: Service appointments, workload, completion rates
- inventory: Stock levels, stockout risks
- all: Check all metric types

**Threshold Guidelines:**
- 0.1 (10%): Very sensitive, catches small changes
- 0.2 (20%): Standard threshold for most metrics
- 0.3 (30%): Less sensitive, only major changes

**SQLite Date Functions:**
- Use date('now', '-7 days') for last week (NOT '-1 week')
- Use date('now', '-14 days') for 2 weeks ago (NOT '-2 weeks')

Return JSON:
{{
    "metric_type": "sales" | "defects" | "service" | "inventory" | "all",
    "threshold": 0.2,
    "time_period": "7 days" | "14 days" | "30 days",
    "reasoning": "Why these settings"
}}"""),
            ("human", "User query: {query}\n\nMetric type (if provided): {metric_type}\n\nThreshold (if provided): {threshold}\n\nDetermine anomaly detection parameters:")
        ])
        
        detection_plan = await (anomaly_prompt | llm).ainvoke({
            "query": user_query,
            "metric_type": metric_type or "not specified",
            "threshold": str(threshold) if threshold else "not specified"
        })
        
        # Parse detection plan
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', detection_plan.content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                metric_type = plan.get("metric_type", metric_type or "all")
                threshold = float(plan.get("threshold", threshold or 0.2))
            else:
                metric_type = metric_type or "all"
                threshold = threshold or 0.2
        except:
            metric_type = metric_type or "all"
            threshold = threshold or 0.2
        
        anomalies = []
        
        # Sales anomalies
        if not metric_type or metric_type in ['sales', 'all']:
            sales_query = """
                SELECT 
                    d.region,
                    COUNT(*) as current_count,
                    AVG(f.fni_revenue) as current_avg_revenue
                FROM fni_transactions f
                JOIN dealers d ON f.dealer_id = d.id
                WHERE f.transaction_date >= date('now', '-7 days')
                GROUP BY d.region
            """
            result = await db_session.execute(text(sales_query))
            current_sales = {row[0]: {"count": row[1], "avg_revenue": float(row[2])} for row in result.fetchall()}
            
            # Compare with previous period
            prev_query = """
                SELECT 
                    d.region,
                    COUNT(*) as prev_count,
                    AVG(f.fni_revenue) as prev_avg_revenue
                FROM fni_transactions f
                JOIN dealers d ON f.dealer_id = d.id
                WHERE f.transaction_date >= date('now', '-14 days')
                AND f.transaction_date < date('now', '-7 days')
                GROUP BY d.region
            """
            result = await db_session.execute(text(prev_query))
            prev_sales = {row[0]: {"count": row[1], "avg_revenue": float(row[2])} for row in result.fetchall()}
            
            for region, current in current_sales.items():
                if region in prev_sales:
                    prev = prev_sales[region]
                    count_change = (current["count"] - prev["count"]) / prev["count"] if prev["count"] > 0 else 0
                    revenue_change = (current["avg_revenue"] - prev["avg_revenue"]) / prev["avg_revenue"] if prev["avg_revenue"] > 0 else 0
                    
                    if abs(count_change) > threshold or abs(revenue_change) > threshold:
                        anomalies.append({
                            "type": "sales_anomaly",
                            "metric": "F&I Revenue",
                            "region": region,
                            "current_value": current["avg_revenue"],
                            "previous_value": prev["avg_revenue"],
                            "change_percent": round(revenue_change * 100, 2),
                            "severity": "high" if abs(revenue_change) > 0.3 else "medium",
                            "contextual_message": f"F&I revenue in {region} {'increased' if revenue_change > 0 else 'decreased'} by {abs(revenue_change)*100:.1f}%",
                            "suggested_root_cause": "Check dealer performance, finance manager changes, or promotional campaigns"
                        })
        
        # Service workload anomalies
        if not metric_type or metric_type in ['service', 'all']:
            service_query = """
                SELECT 
                    DATE(appointment_date) as date,
                    COUNT(*) as appointment_count
                FROM service_appointments
                WHERE appointment_date >= date('now', '-14 days')
                GROUP BY DATE(appointment_date)
                ORDER BY date DESC
            """
            result = await db_session.execute(text(service_query))
            service_data = list(result.fetchall())
            
            if len(service_data) >= 7:
                recent_avg = sum([row[1] for row in service_data[:7]]) / 7
                previous_avg = sum([row[1] for row in service_data[7:14]]) / 7 if len(service_data) >= 14 else recent_avg
                
                change = (recent_avg - previous_avg) / previous_avg if previous_avg > 0 else 0
                if abs(change) > threshold:
                    anomalies.append({
                        "type": "service_anomaly",
                        "metric": "Service Appointments",
                        "current_avg": recent_avg,
                        "previous_avg": previous_avg,
                        "change_percent": round(change * 100, 2),
                        "severity": "medium",
                        "contextual_message": f"Service appointment volume {'increased' if change > 0 else 'decreased'} by {abs(change)*100:.1f}%",
                        "suggested_root_cause": "Check for seasonal patterns, marketing campaigns, or operational changes"
                    })
        
        return json.dumps({
            "anomaly_detection": {
                "timestamp": datetime.now().isoformat(),
                "threshold": threshold,
                "anomalies_found": len(anomalies),
                "anomalies": anomalies,
                "summary": {
                    "high_severity": len([a for a in anomalies if a.get("severity") == "high"]),
                    "medium_severity": len([a for a in anomalies if a.get("severity") == "medium"])
                }
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_model_performance(
    region: Optional[str] = None,
    time_period: str = "week"
) -> str:
    """Analyze model performance vs forecast (e.g., "Which models underperformed vs forecast in Northeast last week?").
    
    Args:
        region: Region to analyze (optional)
        time_period: Time period - 'week', 'month'
    
    Returns:
        JSON string with model performance analysis vs forecast
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # For demo purposes, we'll use vehicle make/model from service appointments as proxy
        # In production, this would use actual sales/forecast data
        
        date_filter = "date('now', '-7 days')" if time_period == "week" else "date('now', '-30 days')"
        
        query = f"""
            SELECT 
                vehicle_make,
                vehicle_model,
                COUNT(*) as service_count,
                SUM(revenue) as total_revenue,
                AVG(revenue) as avg_revenue
            FROM service_appointments
            WHERE appointment_date >= {date_filter}
        """
        
        if region:
            query += f"""
                AND dealer_id IN (
                    SELECT id FROM dealers WHERE region = '{region}'
                )
            """
        
        query += """
            GROUP BY vehicle_make, vehicle_model
            ORDER BY service_count DESC
            LIMIT 20
        """
        
        result = await db_session.execute(text(query))
        model_data = [{
            "make": row[0],
            "model": row[1],
            "service_count": row[2],
            "total_revenue": float(row[3]) if row[3] else 0,
            "avg_revenue": float(row[4]) if row[4] else 0
        } for row in result.fetchall()]
        
        # Calculate average for comparison (simplified forecast)
        avg_service_count = sum([m["service_count"] for m in model_data]) / len(model_data) if model_data else 0
        
        underperformers = [
            m for m in model_data 
            if m["service_count"] < avg_service_count * 0.8  # 20% below average
        ]
        
        return json.dumps({
            "model_performance_analysis": {
                "region": region or "All",
                "time_period": time_period,
                "analysis_date": datetime.now().isoformat(),
                "total_models": len(model_data),
                "average_service_count": round(avg_service_count, 2),
                "underperformers": underperformers,
                "all_models": model_data,
                "summary": f"Found {len(underperformers)} models performing below forecast threshold"
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_stockout_risk(
    component_type: Optional[str] = None
) -> str:
    """Analyze stockout risk for components (e.g., "What's the current stockout risk for EV batteries?").
    
    Args:
        component_type: Type of component to check (optional)
    
    Returns:
        JSON string with stockout risk analysis
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # For demo, we'll use plant downtime data to infer component shortages
        # In production, this would use actual inventory/stock data
        
        query = """
            SELECT 
                reason_detail,
                COUNT(*) as occurrence_count,
                SUM(downtime_hours) as total_downtime,
                supplier
            FROM plant_downtime
            WHERE reason_category = 'Supply'
            AND event_date >= date('now', '-30 days')
            GROUP BY reason_detail, supplier
            ORDER BY occurrence_count DESC
        """
        
        result = await db_session.execute(text(query))
        supply_issues = [{
            "component": row[0],
            "occurrence_count": row[1],
            "total_downtime": float(row[2]) if row[2] else 0,
            "supplier": row[3] or "Unknown"
        } for row in result.fetchall()]
        
        # Calculate risk levels
        high_risk = [s for s in supply_issues if s["occurrence_count"] >= 3 or s["total_downtime"] >= 10]
        medium_risk = [s for s in supply_issues if s["occurrence_count"] >= 2 or s["total_downtime"] >= 5]
        
        return json.dumps({
            "stockout_risk_analysis": {
                "analysis_date": datetime.now().isoformat(),
                "component_type": component_type or "All",
                "high_risk_items": high_risk,
                "medium_risk_items": medium_risk,
                "all_supply_issues": supply_issues,
                "summary": {
                    "high_risk_count": len(high_risk),
                    "medium_risk_count": len(medium_risk),
                    "total_issues": len(supply_issues)
                },
                "recommendations": [
                    f"Review safety stock levels for {item['component']} from {item['supplier']}"
                    for item in high_risk
                ]
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def analyze_repeat_repairs(
    component: Optional[str] = None,
    limit: int = 10
) -> str:
    """Analyze repeat repair components (e.g., "Show top 10 components causing repeat repairs").
    
    Args:
        component: Specific component to analyze (optional)
        limit: Number of top components to return
    
    Returns:
        JSON string with repeat repair analysis
    """
    from app.db.database import get_db
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Use service appointments with same VIN to identify repeat repairs
        query = """
            SELECT 
                sa1.vehicle_vin,
                sa1.service_type,
                sa1.vehicle_make,
                sa1.vehicle_model,
                COUNT(*) as repeat_count,
                MIN(sa1.appointment_date) as first_service,
                MAX(sa1.appointment_date) as last_service
            FROM service_appointments sa1
            WHERE sa1.vehicle_vin IN (
                SELECT vehicle_vin
                FROM service_appointments
                GROUP BY vehicle_vin
                HAVING COUNT(*) > 1
            )
        """
        
        if component:
            query += f" AND sa1.service_type LIKE '%{component}%'"
        
        query += f"""
            GROUP BY sa1.vehicle_vin, sa1.service_type, sa1.vehicle_make, sa1.vehicle_model
            HAVING COUNT(*) > 1
            ORDER BY repeat_count DESC
            LIMIT {limit}
        """
        
        result = await db_session.execute(text(query))
        repeat_repairs = [{
            "vin": row[0],
            "service_type": row[1],
            "make": row[2],
            "model": row[3],
            "repeat_count": row[4],
            "first_service": str(row[5]),
            "last_service": str(row[6])
        } for row in result.fetchall()]
        
        # Aggregate by service type
        service_type_counts = {}
        for repair in repeat_repairs:
            st = repair["service_type"]
            if st not in service_type_counts:
                service_type_counts[st] = {"count": 0, "vehicles": []}
            service_type_counts[st]["count"] += repair["repeat_count"]
            service_type_counts[st]["vehicles"].append(repair["vin"])
        
        top_components = sorted(
            [{"component": k, "repeat_count": v["count"], "affected_vehicles": len(set(v["vehicles"]))} 
             for k, v in service_type_counts.items()],
            key=lambda x: x["repeat_count"],
            reverse=True
        )[:limit]
        
        return json.dumps({
            "repeat_repair_analysis": {
                "analysis_date": datetime.now().isoformat(),
                "component_filter": component or "All",
                "top_components": top_components,
                "detailed_repairs": repeat_repairs,
                "summary": {
                    "total_repeat_repairs": len(repeat_repairs),
                    "unique_components": len(service_type_counts),
                    "most_common": top_components[0]["component"] if top_components else "N/A"
                }
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()


@tool
async def search_data_catalog(
    query: str,
    table_name: Optional[str] = None
) -> str:
    """Search data catalog to find datasets, schemas, and table information.
    
    Args:
        query: Natural language query (e.g., "Where can I find dealership service history?")
        table_name: Specific table to search (optional)
    
    Returns:
        JSON string with matching tables, columns, descriptions, and example data
    """
    from app.db.database import get_db
    from app.utils.schema_utils import get_database_schema
    
    db_session = None
    try:
        db_gen = get_db()
        db_session = await anext(db_gen)
        
        # Get schema
        schema = await get_database_schema(db_session)
        
        # Search for relevant tables based on query keywords
        query_lower = query.lower()
        relevant_tables = []
        
        # Table descriptions mapping
        table_descriptions = {
            "dealers": "Dealer information including name, region, state, city",
            "fni_transactions": "Finance & Insurance transactions with revenue, penetration rates, finance managers",
            "shipments": "Logistics and shipment data with carriers, routes, delays, and timestamps",
            "plants": "Manufacturing plant information",
            "plant_downtime": "Plant downtime records with reasons, categories, and suppliers",
            "marketing_campaigns": "Marketing campaign data with emails sent, opens, revenue",
            "service_appointments": "Service appointment records with customer info, vehicles, and status",
            "repair_orders": "Repair order data with status, priority, and customer information",
            "kpi_metrics": "KPI tracking metrics with alerts and root causes",
            "customers": "Customer information with loyalty tiers and service history"
        }
        
        # Match query to tables
        for table, desc in table_descriptions.items():
            if table_name and table != table_name:
                continue
            
            # Check if query keywords match table or description
            if any(keyword in query_lower for keyword in [table, desc.lower()]):
                # Get column info
                result = await db_session.execute(text(f"PRAGMA table_info({table})"))
                columns = [{"name": row[1], "type": row[2]} for row in result.fetchall()]
                
                # Get example row
                try:
                    example_result = await db_session.execute(text(f"SELECT * FROM {table} LIMIT 1"))
                    example_row = example_result.fetchone()
                    example_data = dict(zip([c["name"] for c in columns], example_row)) if example_row else {}
                except:
                    example_data = {}
                
                relevant_tables.append({
                    "table_name": table,
                    "description": desc,
                    "columns": columns,
                    "example_data": example_data,
                    "relevance_score": 1.0  # Simplified for demo
                })
        
        return json.dumps({
            "data_catalog_search": {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "tables_found": len(relevant_tables),
                "tables": relevant_tables,
                "schema_info": schema[:500] + "..." if len(schema) > 500 else schema
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if db_session:
            await db_session.close()

