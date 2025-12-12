"""Frontend integration system for serving chart data and handling client-side interactions."""

import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

from chart_generator import ChartDataGenerator
from query_router import QueryRouter
from response_cache import ResponseCache
from fast_server import FastFileServer, ResponseOptimizer
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class FrontendIntegration:
    """Handles frontend integration for chart data and client-side interactions."""
    
    def __init__(self):
        self.chart_generator = ChartDataGenerator()
        self.query_router = QueryRouter()
        self.response_cache = ResponseCache()
        self.file_server = FastFileServer()
        self.response_optimizer = ResponseOptimizer()
        
    async def process_frontend_query(self, query: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query from the frontend and return chart-ready response.
        
        Args:
            query: User's natural language query
            options: Frontend options (chart preferences, filters, etc.)
            
        Returns:
            Complete response with data, charts, and metadata
        """
        try:
            # Check cache first
            cached_response = await self.response_cache.get_cached_response(query, options)
            if cached_response:
                logger.info(f"Cache hit for frontend query: '{query}'")
                return cached_response
            
            # Get base response from query router
            response = self.query_router.process_query(query, options)
            
            if not response.get("success"):
                error_response = self._format_error_response(response, query)
                # Cache error responses briefly to avoid repeated processing
                await self.response_cache.cache_response(query, error_response, options, ttl_hours=1)
                return error_response
            
            # Extract data and metadata
            data = response.get("data", [])
            match_info = response.get("match_info", {})
            metadata = response.get("metadata", {})
            
            # Apply frontend options
            if options:
                data = self._apply_frontend_filters(data, options.get("filters", {}))
            
            # Generate chart configurations
            chart_configs = self._generate_frontend_charts(
                data=data,
                category=match_info.get("category", ""),
                query_name=match_info.get("query_name", ""),
                options=options
            )
            
            # Format response for frontend
            frontend_response = {
                "success": True,
                "query": query,
                "data": {
                    "raw": data,
                    "processed": self._process_data_for_frontend(data),
                    "summary": self._generate_data_summary(data)
                },
                "charts": chart_configs,
                "metadata": {
                    **metadata,
                    "data_points": len(data),
                    "chart_count": len(chart_configs),
                    "interactive_features": self._get_interactive_features(data),
                    "export_options": ["csv", "json", "png", "pdf"]
                },
                "match_info": match_info,
                "ui_suggestions": self._generate_ui_suggestions(data, match_info)
            }
            
            # Optimize response for frontend
            optimized_response = self.response_optimizer.optimize_response(frontend_response)
            
            # Cache the optimized response
            await self.response_cache.cache_response(query, optimized_response, options, ttl_hours=24)
            
            logger.info(f"Frontend query processed: '{query}' -> {len(data)} data points, {len(chart_configs)} charts")
            return optimized_response
            
        except Exception as e:
            logger.error(f"Frontend query processing failed: {e}")
            return self._format_error_response({"error": str(e)}, query)
    
    def _format_error_response(self, error_response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format error response for frontend consumption."""
        return {
            "success": False,
            "query": query,
            "error": error_response.get("error", "Unknown error"),
            "suggestions": error_response.get("suggestions", []),
            "data": {"raw": [], "processed": [], "summary": {}},
            "charts": [],
            "metadata": {
                "data_points": 0,
                "chart_count": 0,
                "response_time_ms": error_response.get("metadata", {}).get("response_time_ms", 0)
            }
        }
    
    def _apply_frontend_filters(self, data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply frontend filters to data."""
        if not filters or not data:
            return data
        
        filtered_data = data
        
        for field, filter_value in filters.items():
            if field in data[0]:  # Check if field exists
                if isinstance(filter_value, list):
                    # Multiple values filter
                    filtered_data = [row for row in filtered_data if row.get(field) in filter_value]
                elif isinstance(filter_value, dict):
                    # Range filter
                    min_val = filter_value.get("min")
                    max_val = filter_value.get("max")
                    
                    if min_val is not None:
                        filtered_data = [row for row in filtered_data if row.get(field, 0) >= min_val]
                    if max_val is not None:
                        filtered_data = [row for row in filtered_data if row.get(field, 0) <= max_val]
                else:
                    # Exact match filter
                    filtered_data = [row for row in filtered_data if row.get(field) == filter_value]
        
        logger.info(f"Applied filters: {len(data)} -> {len(filtered_data)} rows")
        return filtered_data
    
    def _generate_frontend_charts(
        self, 
        data: List[Dict], 
        category: str, 
        query_name: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate chart configurations optimized for frontend rendering."""
        if not data:
            return []
        
        charts = []
        
        # Get chart preferences from options
        preferred_types = options.get("chart_types", ["auto"]) if options else ["auto"]
        
        for chart_type in preferred_types:
            # Generate chart config
            config = self.chart_generator.generate_chart_config(
                data=data,
                chart_type=chart_type,
                title=self._generate_chart_title(query_name, category),
                category=category,
                query_name=query_name
            )
            
            if config:
                # Add frontend-specific enhancements
                enhanced_config = self._enhance_chart_for_frontend(config, data, options)
                
                charts.append({
                    "id": f"{query_name}_{chart_type}_{len(charts)}",
                    "type": config["type"],
                    "config": enhanced_config,
                    "recommended": chart_type == "auto",
                    "responsive": True,
                    "interactive": True
                })
        
        # If no charts generated, create a default one
        if not charts:
            default_config = self.chart_generator.generate_chart_config(
                data=data,
                chart_type="bar",
                title=self._generate_chart_title(query_name, category),
                category=category
            )
            
            if default_config:
                charts.append({
                    "id": f"{query_name}_default",
                    "type": "bar",
                    "config": default_config,
                    "recommended": True,
                    "responsive": True,
                    "interactive": True
                })
        
        return charts
    
    def _enhance_chart_for_frontend(
        self, 
        config: Dict[str, Any], 
        data: List[Dict], 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enhance chart configuration with frontend-specific features."""
        enhanced = config.copy()
        
        # Add responsive design options
        enhanced["options"]["responsive"] = True
        enhanced["options"]["maintainAspectRatio"] = False
        
        # Add animation options
        enhanced["options"]["animation"] = {
            "duration": 1000,
            "easing": "easeInOutQuart"
        }
        
        # Enhanced tooltips
        enhanced["options"]["plugins"]["tooltip"] = {
            "enabled": True,
            "mode": "index",
            "intersect": False,
            "backgroundColor": "rgba(0, 0, 0, 0.8)",
            "titleColor": "white",
            "bodyColor": "white",
            "borderColor": "rgba(255, 255, 255, 0.1)",
            "borderWidth": 1
        }
        
        # Add data labels for better readability
        enhanced["options"]["plugins"]["datalabels"] = {
            "display": len(data) <= 10,  # Only show labels for small datasets
            "color": "black",
            "font": {"weight": "bold"}
        }
        
        # Add zoom and pan capabilities
        enhanced["options"]["plugins"]["zoom"] = {
            "zoom": {
                "wheel": {"enabled": True},
                "pinch": {"enabled": True},
                "mode": "x"
            },
            "pan": {
                "enabled": True,
                "mode": "x"
            }
        }
        
        # Add export options
        enhanced["options"]["plugins"]["export"] = {
            "enabled": True,
            "formats": ["png", "pdf", "svg"]
        }
        
        return enhanced
    
    def _process_data_for_frontend(self, data: List[Dict]) -> List[Dict]:
        """Process raw data for optimal frontend consumption."""
        if not data:
            return []
        
        processed = []
        
        for row in data:
            processed_row = {}
            
            for key, value in row.items():
                # Format values for display
                if isinstance(value, float):
                    # Round floats to 2 decimal places
                    processed_row[key] = round(value, 2)
                elif isinstance(value, str):
                    # Capitalize string values
                    processed_row[key] = value.title() if len(value) < 50 else value
                else:
                    processed_row[key] = value
                
                # Add formatted display versions
                if isinstance(value, (int, float)) and "amount" in key.lower() or "revenue" in key.lower():
                    processed_row[f"{key}_formatted"] = self._format_currency(value)
                elif isinstance(value, (int, float)) and "percent" in key.lower():
                    processed_row[f"{key}_formatted"] = f"{value:.1f}%"
            
            processed.append(processed_row)
        
        return processed
    
    def _generate_data_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics for the data."""
        if not data:
            return {}
        
        summary = {
            "total_rows": len(data),
            "columns": list(data[0].keys()),
            "numeric_columns": [],
            "statistics": {}
        }
        
        # Identify numeric columns and calculate statistics
        for key in data[0].keys():
            values = [row.get(key) for row in data if isinstance(row.get(key), (int, float))]
            
            if values:
                summary["numeric_columns"].append(key)
                summary["statistics"][key] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "total": sum(values) if "count" in key.lower() or "amount" in key.lower() else None
                }
        
        return summary
    
    def _get_interactive_features(self, data: List[Dict]) -> List[str]:
        """Get available interactive features based on data structure."""
        features = ["tooltip", "legend_toggle"]
        
        if len(data) > 1:
            features.extend(["zoom", "pan", "filter"])
        
        if len(data) <= 20:
            features.append("data_labels")
        
        # Check for drill-down possibilities
        sample = data[0] if data else {}
        if any(key in sample for key in ["region", "category", "dealer_id"]):
            features.append("drill_down")
        
        return features
    
    def _generate_ui_suggestions(self, data: List[Dict], match_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI suggestions for better user experience."""
        suggestions = {
            "filters": [],
            "chart_types": [],
            "drill_down": [],
            "related_queries": []
        }
        
        if not data:
            return suggestions
        
        sample = data[0]
        
        # Suggest filters based on categorical fields
        for key, value in sample.items():
            if isinstance(value, str) and key not in ["id", "description"]:
                unique_values = list(set(row.get(key) for row in data))
                if 2 <= len(unique_values) <= 10:
                    suggestions["filters"].append({
                        "field": key,
                        "type": "select",
                        "options": unique_values
                    })
        
        # Suggest chart types based on data structure
        category = match_info.get("category", "")
        if category == "sales_analytics":
            suggestions["chart_types"] = ["bar", "line", "area"]
        elif category == "kpi_monitoring":
            suggestions["chart_types"] = ["horizontalBar", "gauge", "line"]
        else:
            suggestions["chart_types"] = ["bar", "pie", "line"]
        
        # Suggest drill-down options
        if "region" in sample:
            suggestions["drill_down"].append("View by individual dealers in region")
        if "category" in sample:
            suggestions["drill_down"].append("Break down by subcategory")
        
        # Suggest related queries
        suggestions["related_queries"] = [
            "Show trends over time",
            "Compare with previous period",
            "Break down by different dimension"
        ]
        
        return suggestions
    
    def _generate_chart_title(self, query_name: str, category: str) -> str:
        """Generate appropriate chart title."""
        # Convert query name to readable title
        title = query_name.replace("_", " ").title()
        
        # Add category context if helpful
        category_names = {
            "sales_analytics": "Sales Analytics",
            "kpi_monitoring": "KPI Monitoring",
            "inventory_management": "Inventory Management",
            "warranty_analysis": "Warranty Analysis",
            "executive_reports": "Executive Reports"
        }
        
        category_title = category_names.get(category, category.replace("_", " ").title())
        
        return f"{title} - {category_title}"
    
    def _format_currency(self, value: Union[int, float]) -> str:
        """Format numeric value as currency."""
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value / 1_000:.1f}K"
        else:
            return f"${value:.2f}"
    
    def get_chart_export_data(self, chart_id: str, format: str = "png") -> Dict[str, Any]:
        """Get chart data for export in specified format."""
        # This would typically interface with the frontend chart library
        # For now, return metadata about export capabilities
        
        return {
            "chart_id": chart_id,
            "export_format": format,
            "available_formats": ["png", "pdf", "svg", "csv", "json"],
            "export_url": f"/api/charts/{chart_id}/export/{format}",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_system_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities for frontend configuration."""
        return {
            "supported_chart_types": self.chart_generator.supported_chart_types,
            "color_palettes": list(self.chart_generator.color_palettes.keys()),
            "interactive_features": [
                "zoom", "pan", "tooltip", "legend_toggle", 
                "data_labels", "drill_down", "filter", "export"
            ],
            "export_formats": ["png", "pdf", "svg", "csv", "json"],
            "max_data_points": 1000,
            "response_time_target_ms": settings.max_response_time_ms
        }

# Test functions
def test_frontend_integration():
    """Test the frontend integration system."""
    integration = FrontendIntegration()
    
    print("🧪 Testing Frontend Integration System")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "What were the top selling models in the Northeast last week?",
        "Show me KPI health scores",
        "Give me inventory stock levels by plant"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        # Test basic processing
        response = integration.process_frontend_query(query)
        
        if response["success"]:
            print(f"✅ Success:")
            print(f"   Data points: {response['metadata']['data_points']}")
            print(f"   Charts: {response['metadata']['chart_count']}")
            print(f"   Interactive features: {len(response['metadata']['interactive_features'])}")
            print(f"   Response time: {response['metadata']['response_time_ms']:.1f}ms")
        else:
            print(f"❌ Failed: {response['error']}")
        
        # Test with options
        options = {
            "chart_types": ["bar", "pie"],
            "filters": {"region": "Northeast"}
        }
        
        response_with_options = integration.process_frontend_query(query, options)
        if response_with_options["success"]:
            print(f"📊 With options: {len(response_with_options['charts'])} charts generated")
    
    # Test system capabilities
    print(f"\n🔧 System Capabilities:")
    capabilities = integration.get_system_capabilities()
    print(f"   Chart types: {len(capabilities['supported_chart_types'])}")
    print(f"   Interactive features: {len(capabilities['interactive_features'])}")
    print(f"   Export formats: {capabilities['export_formats']}")

if __name__ == "__main__":
    test_frontend_integration()