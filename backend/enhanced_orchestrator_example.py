# Enhanced Orchestrator with Structured Data Support

class LangChainAnalyticsOrchestrator:
    
    async def process_query(self, query: str, db_session=None, session_id=None, conversation_history=None) -> Dict[str, Any]:
        """Enhanced process_query with structured data support"""
        
        result = {
            "query": query,
            "query_type": demo_scenario or "general",
            "sql_query": None,
            "data": None,                    # Raw database results
            "analysis": None,               # Human-readable analysis
            "structured_data": None,        # ✅ NEW: Structured analysis data
            "recommendations": [],
            "chart_config": None,
            "metadata": {                   # ✅ NEW: Enhanced metadata
                "processing_time": None,
                "tokens_used": None,
                "confidence_score": None
            }
        }
        
        # ... existing logic ...
        
        # After getting agent response, extract structured data
        if result["analysis"]:
            result["structured_data"] = self._extract_structured_data(
                result["analysis"], 
                result["data"], 
                result["query_type"]
            )
        
        return result
    
    def _extract_structured_data(self, analysis_text: str, raw_data: List[Dict], query_type: str) -> Dict[str, Any]:
        """Extract structured data from analysis and raw results"""
        
        if query_type == "fni_midwest":
            return self._structure_fni_data(analysis_text, raw_data)
        elif query_type == "logistics_delays":
            return self._structure_logistics_data(analysis_text, raw_data)
        elif query_type == "plant_downtime":
            return self._structure_plant_data(analysis_text, raw_data)
        else:
            return self._structure_generic_data(analysis_text, raw_data)
    
    def _structure_fni_data(self, analysis: str, data: List[Dict]) -> Dict[str, Any]:
        """Structure F&I analysis data"""
        if not data:
            return {}
        
        # Calculate key metrics from raw data
        total_current = sum(row.get('this_week_revenue', 0) for row in data)
        total_previous = sum(row.get('last_week_revenue', 0) for row in data)
        
        return {
            "summary": {
                "total_revenue_change": {
                    "amount": total_current - total_previous,
                    "percentage": ((total_current - total_previous) / total_previous * 100) if total_previous > 0 else 0
                },
                "dealers_analyzed": len(data),
                "period": "week_over_week"
            },
            "dealer_performance": {
                "declining": [
                    {
                        "name": row["dealer_name"],
                        "code": row["dealer_code"],
                        "revenue_change_pct": row["change_pct"],
                        "penetration_change": row["current_penetration"] - row["previous_penetration"]
                    }
                    for row in data if row.get("change_pct", 0) < 0
                ],
                "improving": [
                    {
                        "name": row["dealer_name"],
                        "code": row["dealer_code"],
                        "revenue_change_pct": row["change_pct"],
                        "penetration_change": row["current_penetration"] - row["previous_penetration"]
                    }
                    for row in data if row.get("change_pct", 0) > 0
                ]
            },
            "risk_assessment": {
                "high_risk_dealers": [row["dealer_code"] for row in data if row.get("change_pct", 0) < -40],
                "medium_risk_dealers": [row["dealer_code"] for row in data if -40 <= row.get("change_pct", 0) < -20],
                "low_risk_dealers": [row["dealer_code"] for row in data if -20 <= row.get("change_pct", 0) < 0]
            },
            "penetration_analysis": {
                "avg_current": sum(row.get('current_penetration', 0) for row in data) / len(data),
                "avg_previous": sum(row.get('previous_penetration', 0) for row in data) / len(data),
                "biggest_drops": sorted(data, key=lambda x: x.get('current_penetration', 0) - x.get('previous_penetration', 0))[:3]
            }
        }