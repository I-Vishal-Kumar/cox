"""SQL dump generation system for pre-computed business intelligence responses."""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from database import execute_read_only_query, test_database_connection
from sql_queries import SQLQueryTemplates
from config import settings, ensure_directories

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class DumpGenerator:
    """Generates and manages SQL-based data dumps for fast query responses."""
    
    def __init__(self):
        self.templates = SQLQueryTemplates()
        ensure_directories()
    
    async def generate_all_dumps(self) -> Dict[str, Any]:
        """Generate all SQL dumps and save to files."""
        logger.info("Starting SQL dump generation...")
        
        # Test database connection first
        if not await test_database_connection():
            logger.error("Database connection failed - cannot generate dumps")
            return {"success": False, "error": "Database connection failed"}
        
        results = {
            "success": True,
            "generated_files": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        all_queries = self.templates.get_all_queries()
        
        for category, queries in all_queries.items():
            logger.info(f"Generating dumps for category: {category}")
            
            for query_name, query_info in queries.items():
                try:
                    # Execute SQL query
                    data = await execute_read_only_query(query_info["sql"])
                    
                    # Create dump entry
                    dump_entry = {
                        "query_name": query_name,
                        "category": category,
                        "description": query_info["description"],
                        "keywords": query_info["keywords"],
                        "sql_query": query_info["sql"],
                        "data": data,
                        "metadata": {
                            "generated_at": datetime.now().isoformat(),
                            "row_count": len(data),
                            "data_size_kb": len(json.dumps(data).encode('utf-8')) / 1024
                        },
                        "chart_config": self._generate_chart_config(category, query_name, data)
                    }
                    
                    # Save to file
                    file_path = self._get_dump_file_path(category, query_name)
                    await self._save_dump_to_file(dump_entry, file_path)
                    
                    results["generated_files"].append(str(file_path))
                    logger.info(f"Generated dump: {query_name} ({len(data)} rows)")
                    
                except Exception as e:
                    error_msg = f"Failed to generate dump for {query_name}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
        
        # Generate summary file
        await self._generate_summary_file(results)
        
        logger.info(f"Dump generation complete. Generated {len(results['generated_files'])} files with {len(results['errors'])} errors")
        return results
    
    def _get_dump_file_path(self, category: str, query_name: str) -> Path:
        """Get file path for a dump file."""
        return Path(settings.dumps_dir) / category / f"{query_name}.json"
    
    async def _save_dump_to_file(self, dump_entry: Dict[str, Any], file_path: Path) -> None:
        """Save dump entry to JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dump_entry, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_chart_config(self, category: str, query_name: str, data: List[Dict]) -> Optional[Dict[str, Any]]:
        """Generate chart configuration based on data structure."""
        if not data:
            return None
        
        # Determine chart type based on category and data structure
        chart_config = {
            "type": "bar",  # Default
            "title": f"{query_name.replace('_', ' ').title()}",
            "responsive": True,
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"{query_name.replace('_', ' ').title()}"
                    }
                }
            }
        }
        
        # Category-specific chart configurations
        if category == "sales_analytics":
            if "region" in data[0] and "total_revenue" in data[0]:
                chart_config.update({
                    "type": "bar",
                    "data": {
                        "labels": [row.get("region", "") for row in data[:10]],
                        "datasets": [{
                            "label": "Revenue",
                            "data": [row.get("total_revenue", 0) for row in data[:10]],
                            "backgroundColor": "rgba(54, 162, 235, 0.6)"
                        }]
                    }
                })
        
        elif category == "kpi_monitoring":
            if "metric_name" in data[0] and "variance_percent" in data[0]:
                chart_config.update({
                    "type": "horizontalBar",
                    "data": {
                        "labels": [row.get("metric_name", "") for row in data[:10]],
                        "datasets": [{
                            "label": "Variance %",
                            "data": [row.get("variance_percent", 0) for row in data[:10]],
                            "backgroundColor": [
                                "rgba(255, 99, 132, 0.6)" if abs(row.get("variance_percent", 0)) > 15 
                                else "rgba(255, 206, 86, 0.6)" if abs(row.get("variance_percent", 0)) > 5
                                else "rgba(75, 192, 192, 0.6)"
                                for row in data[:10]
                            ]
                        }]
                    }
                })
        
        elif category == "warranty_analysis":
            if "claim_count" in data[0]:
                chart_config.update({
                    "type": "pie",
                    "data": {
                        "labels": [row.get("model_name", row.get("component_name", "")) for row in data[:8]],
                        "datasets": [{
                            "data": [row.get("claim_count", 0) for row in data[:8]],
                            "backgroundColor": [
                                f"hsl({i * 45}, 70%, 60%)" for i in range(len(data[:8]))
                            ]
                        }]
                    }
                })
        
        return chart_config
    
    async def _generate_summary_file(self, results: Dict[str, Any]) -> None:
        """Generate summary file with dump generation results."""
        summary_path = Path(settings.dumps_dir) / "generation_summary.json"
        
        summary = {
            "last_generation": results["timestamp"],
            "total_files": len(results["generated_files"]),
            "total_errors": len(results["errors"]),
            "files": results["generated_files"],
            "errors": results["errors"],
            "categories": {}
        }
        
        # Count files by category
        for file_path in results["generated_files"]:
            category = Path(file_path).parent.name
            if category not in summary["categories"]:
                summary["categories"][category] = 0
            summary["categories"][category] += 1
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated summary file: {summary_path}")
    
    async def refresh_specific_category(self, category: str) -> Dict[str, Any]:
        """Refresh dumps for a specific category only."""
        logger.info(f"Refreshing dumps for category: {category}")
        
        all_queries = self.templates.get_all_queries()
        if category not in all_queries:
            return {"success": False, "error": f"Category '{category}' not found"}
        
        results = {
            "success": True,
            "generated_files": [],
            "errors": [],
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        
        queries = all_queries[category]
        for query_name, query_info in queries.items():
            try:
                data = await execute_read_only_query(query_info["sql"])
                
                dump_entry = {
                    "query_name": query_name,
                    "category": category,
                    "description": query_info["description"],
                    "keywords": query_info["keywords"],
                    "sql_query": query_info["sql"],
                    "data": data,
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "row_count": len(data),
                        "data_size_kb": len(json.dumps(data).encode('utf-8')) / 1024
                    },
                    "chart_config": self._generate_chart_config(category, query_name, data)
                }
                
                file_path = self._get_dump_file_path(category, query_name)
                await self._save_dump_to_file(dump_entry, file_path)
                
                results["generated_files"].append(str(file_path))
                logger.info(f"Refreshed dump: {query_name} ({len(data)} rows)")
                
            except Exception as e:
                error_msg = f"Failed to refresh dump for {query_name}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results

async def main():
    """Main function for testing dump generation."""
    generator = DumpGenerator()
    
    print("🔄 Generating SQL dumps...")
    results = await generator.generate_all_dumps()
    
    if results["success"]:
        print(f"✅ Successfully generated {len(results['generated_files'])} dump files")
        if results["errors"]:
            print(f"⚠️  {len(results['errors'])} errors occurred:")
            for error in results["errors"]:
                print(f"   - {error}")
    else:
        print(f"❌ Dump generation failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())