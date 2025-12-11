# Dedicated Structured Data Processing Tool

from typing import Dict, Any, List
from langchain_core.tools import tool
import pandas as pd

@tool
def process_sql_results_to_structured_data(
    sql_query: str,
    sql_results: List[Dict[str, Any]],
    expected_format: str,
    analysis_context: str
) -> Dict[str, Any]:
    """
    Convert SQL query results into structured data formats.
    
    This is a deterministic function that processes database results
    into predefined structured formats based on the query type.
    
    Args:
        sql_query: The SQL query that generated the results
        sql_results: Raw database results
        expected_format: Target format (e.g., "fni_analysis", "logistics_summary")
        analysis_context: Context about what analysis is needed
        
    Returns:
        Structured data in the requested format
    """
    
    if expected_format == "fni_analysis":
        return _process_fni_data(sql_results)
    elif expected_format == "logistics_summary":
        return _process_logistics_data(sql_results)
    elif expected_format == "plant_downtime":
        return _process_plant_data(sql_results)
    else:
        return _process_generic_data(sql_results)

def _process_fni_data(results: List[Dict]) -> Dict[str, Any]:
    """Process F&I revenue data into structured format"""
    if not results:
        return {"error": "No data available"}
    
    # Calculate aggregated metrics
    total_current = sum(row.get('this_week_revenue', 0) for row in results)
    total_previous = sum(row.get('last_week_revenue', 0) for row in results)
    
    declining_dealers = [
        row for row in results 
        if row.get('change_pct', 0) < 0
    ]
    
    improving_dealers = [
        row for row in results 
        if row.get('change_pct', 0) > 0
    ]
    
    return {
        "summary_metrics": {
            "total_current_revenue": total_current,
            "total_previous_revenue": total_previous,
            "total_change_amount": total_current - total_previous,
            "total_change_percentage": ((total_current - total_previous) / total_previous * 100) if total_previous > 0 else 0,
            "dealers_analyzed": len(results),
            "dealers_declining": len(declining_dealers),
            "dealers_improving": len(improving_dealers)
        },
        "top_declining_dealers": sorted(
            declining_dealers, 
            key=lambda x: x.get('change_pct', 0)
        )[:3],
        "top_improving_dealers": sorted(
            improving_dealers, 
            key=lambda x: x.get('change_pct', 0), 
            reverse=True
        )[:3],
        "penetration_analysis": {
            "avg_current_penetration": sum(row.get('current_penetration', 0) for row in results) / len(results),
            "avg_previous_penetration": sum(row.get('previous_penetration', 0) for row in results) / len(results),
            "penetration_change": "calculated_change"
        },
        "risk_categories": {
            "high_risk": [row for row in results if row.get('change_pct', 0) < -40],
            "medium_risk": [row for row in results if -40 <= row.get('change_pct', 0) < -20],
            "low_risk": [row for row in results if -20 <= row.get('change_pct', 0) < 0]
        }
    }

def _process_logistics_data(results: List[Dict]) -> Dict[str, Any]:
    """Process logistics delay data into structured format"""
    if not results:
        return {"error": "No data available"}
    
    # Group by delay reason
    delay_reasons = {}
    for row in results:
        reason = row.get('delay_reason', 'Unknown')
        if reason not in delay_reasons:
            delay_reasons[reason] = {
                "count": 0,
                "total_shipments": 0,
                "avg_dwell_time": 0,
                "carriers": set()
            }
        
        delay_reasons[reason]["count"] += row.get('delayed_count', 0)
        delay_reasons[reason]["total_shipments"] += row.get('total_shipments', 0)
        delay_reasons[reason]["carriers"].add(row.get('carrier', ''))
    
    return {
        "delay_attribution": {
            reason: {
                "delayed_shipments": data["count"],
                "total_shipments": data["total_shipments"],
                "delay_rate": (data["count"] / data["total_shipments"] * 100) if data["total_shipments"] > 0 else 0,
                "affected_carriers": list(data["carriers"])
            }
            for reason, data in delay_reasons.items()
        },
        "carrier_performance": _analyze_carrier_performance(results),
        "route_analysis": _analyze_route_performance(results),
        "summary_metrics": {
            "total_delayed_shipments": sum(row.get('delayed_count', 0) for row in results),
            "total_shipments": sum(row.get('total_shipments', 0) for row in results),
            "overall_delay_rate": "calculated_rate",
            "avg_dwell_time": sum(row.get('avg_dwell_time', 0) for row in results) / len(results)
        }
    }

def _analyze_carrier_performance(results: List[Dict]) -> Dict[str, Any]:
    """Analyze carrier-specific performance"""
    carriers = {}
    for row in results:
        carrier = row.get('carrier', 'Unknown')
        if carrier not in carriers:
            carriers[carrier] = {
                "total_shipments": 0,
                "delayed_shipments": 0,
                "routes": set()
            }
        
        carriers[carrier]["total_shipments"] += row.get('total_shipments', 0)
        carriers[carrier]["delayed_shipments"] += row.get('delayed_count', 0)
        carriers[carrier]["routes"].add(row.get('route', ''))
    
    return {
        carrier: {
            "delay_rate": (data["delayed_shipments"] / data["total_shipments"] * 100) if data["total_shipments"] > 0 else 0,
            "total_shipments": data["total_shipments"],
            "delayed_shipments": data["delayed_shipments"],
            "routes_served": list(data["routes"])
        }
        for carrier, data in carriers.items()
    }

def _analyze_route_performance(results: List[Dict]) -> Dict[str, Any]:
    """Analyze route-specific performance"""
    routes = {}
    for row in results:
        route = row.get('route', 'Unknown')
        if route not in routes:
            routes[route] = {
                "total_shipments": 0,
                "delayed_shipments": 0,
                "carriers": set()
            }
        
        routes[route]["total_shipments"] += row.get('total_shipments', 0)
        routes[route]["delayed_shipments"] += row.get('delayed_count', 0)
        routes[route]["carriers"].add(row.get('carrier', ''))
    
    return {
        route: {
            "delay_rate": (data["delayed_shipments"] / data["total_shipments"] * 100) if data["total_shipments"] > 0 else 0,
            "total_shipments": data["total_shipments"],
            "delayed_shipments": data["delayed_shipments"],
            "carriers_used": list(data["carriers"])
        }
        for route, data in routes.items()
    }

def _process_generic_data(results: List[Dict]) -> Dict[str, Any]:
    """Process generic data into basic structured format"""
    if not results:
        return {"error": "No data available"}
    
    return {
        "record_count": len(results),
        "columns": list(results[0].keys()) if results else [],
        "sample_data": results[:5],  # First 5 records
        "data_types": {
            col: type(results[0][col]).__name__ 
            for col in results[0].keys()
        } if results else {}
    }