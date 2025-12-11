"""
Result formatter tool for extracting clean JSON data from tool responses.

This tool is used to format dashboard tool responses into clean JSON
that can be directly consumed by frontend applications.
"""

from typing import Any, Dict
from langchain_core.tools import tool
import json
import re


@tool
def format_dashboard_result(
    tool_name: str,
    raw_result: str
) -> str:
    """Extract and format clean JSON from dashboard tool results.
    
    Use this tool when you need to return clean JSON data to the frontend.
    It extracts the JSON content from tool responses and returns it in a
    clean, parseable format.
    
    Args:
        tool_name: Name of the tool that generated the result
                  (e.g., "get_weekly_fni_trends", "get_enhanced_kpi_data")
        raw_result: The raw result string from the tool
        
    Returns:
        Clean JSON string that can be directly parsed by frontend
    """
    try:
        # Try to parse as JSON directly
        parsed = json.loads(raw_result)
        
        # Return formatted JSON
        return json.dumps({
            "success": True,
            "tool": tool_name,
            "data": parsed,
            "format": "json"
        }, indent=2)
        
    except json.JSONDecodeError:
        # If not valid JSON, try to extract JSON from the string
        # Look for JSON array or object patterns
        json_match = re.search(r'(\[.*\]|\{.*\})', raw_result, re.DOTALL)
        
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                return json.dumps({
                    "success": True,
                    "tool": tool_name,
                    "data": parsed,
                    "format": "json"
                }, indent=2)
            except:
                pass
        
        # If extraction failed, return the raw result with metadata
        return json.dumps({
            "success": False,
            "tool": tool_name,
            "data": raw_result,
            "format": "text",
            "error": "Could not parse as JSON"
        }, indent=2)


@tool
def format_result_as_json(context: str) -> str:
    """Format the previous tool result as clean JSON for frontend consumption.
    
    Use this tool AFTER calling a dashboard tool (like get_weekly_fni_trends,
    get_enhanced_kpi_data, etc.) when the user specifically asks for JSON format
    or when integrating with frontend applications.
    
    This tool will automatically extract the JSON data from the previous tool's
    response and return it in a clean, parseable format.
    
    Args:
        context: Brief description of what data is being formatted
                (e.g., "weekly trends data", "KPI comparison")
        
    Returns:
        Instruction to return the clean JSON data
    """
    return json.dumps({
        "instruction": "return_clean_json",
        "context": context,
        "message": "Please return only the JSON data from the previous tool call, without any additional text or formatting."
    })
