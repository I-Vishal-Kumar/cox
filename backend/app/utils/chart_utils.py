"""Utility functions for chart configuration."""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class ChartConfigManager:
    """Manager for chart configurations."""
    
    def __init__(self, config_path: str = "app/config/chart_configs.json"):
        self.config_path = Path(config_path)
        self._configs: Optional[Dict] = None
        self._load_configs()
    
    def _load_configs(self):
        """Load chart configurations from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                self._configs = json.load(f)
        except FileNotFoundError:
            self._configs = {"default": {
                "type": "bar",
                "title": "Data Visualization",
                "x_axis": "category",
                "y_axis": "value"
            }}
        except json.JSONDecodeError:
            self._configs = {"default": {
                "type": "bar",
                "title": "Data Visualization",
                "x_axis": "category",
                "y_axis": "value"
            }}
    
    def get_config(
        self, 
        query_type: str, 
        chart_name: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get chart configuration for a query type.
        
        Args:
            query_type: Type of query (fni_analysis, logistics_analysis, etc.)
            chart_name: Specific chart name within the query type
            data: Optional data to help determine best chart
            
        Returns:
            Chart configuration dictionary or None
        """
        if not self._configs:
            return None
        
        # Get configs for this query type
        type_configs = self._configs.get(query_type, {})
        
        if not type_configs:
            # Return default config
            return self._configs.get("default")
        
        # If specific chart name provided, return that
        if chart_name and chart_name in type_configs:
            return type_configs[chart_name]
        
        # If data provided, try to infer best chart
        if data and len(data) > 0:
            return self._infer_best_chart(type_configs, data)
        
        # Return first available chart config for this type
        first_key = next(iter(type_configs))
        return type_configs[first_key]
    
    def _infer_best_chart(
        self, 
        type_configs: Dict[str, Any], 
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Infer the best chart configuration based on data structure.
        
        Args:
            type_configs: Available chart configs for this query type
            data: The data to visualize
            
        Returns:
            Best matching chart configuration
        """
        if not data:
            return next(iter(type_configs.values()))
        
        # Get data characteristics
        first_row = data[0]
        columns = list(first_row.keys())
        num_rows = len(data)
        
        # Check for time-based data
        time_columns = ['date', 'month', 'week', 'year', 'timestamp']
        has_time = any(col.lower() in time_columns for col in columns)
        
        # Check for categorical data
        categorical_columns = ['category', 'type', 'status', 'reason', 'name']
        has_category = any(col.lower() in categorical_columns for col in columns)
        
        # Prefer line charts for time series
        if has_time:
            for config in type_configs.values():
                if config.get('type') == 'line':
                    return config
        
        # Prefer pie/donut for categorical with few items
        if has_category and num_rows <= 10:
            for config in type_configs.values():
                if config.get('type') in ['pie', 'donut']:
                    return config
        
        # Default to first config
        return next(iter(type_configs.values()))
    
    def get_all_configs_for_type(self, query_type: str) -> Dict[str, Any]:
        """
        Get all available chart configurations for a query type.
        
        Args:
            query_type: Type of query
            
        Returns:
            Dictionary of all chart configs for this type
        """
        return self._configs.get(query_type, {})
    
    def reload_configs(self):
        """Reload configurations from file."""
        self._load_configs()


# Global instance
_chart_manager: Optional[ChartConfigManager] = None


def get_chart_manager() -> ChartConfigManager:
    """Get or create global chart configuration manager."""
    global _chart_manager
    if _chart_manager is None:
        _chart_manager = ChartConfigManager()
    return _chart_manager
