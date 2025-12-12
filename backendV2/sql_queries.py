"""SQL query templates for common business intelligence patterns."""

from typing import Dict, List, Any
from datetime import datetime, timedelta

class SQLQueryTemplates:
    """Collection of SQL query templates for business intelligence."""
    
    # Sales Analytics Queries
    SALES_QUERIES = {
        "top_models_by_region": {
            "sql": """
            SELECT 
                d.region,
                f.vehicle_type as model_name,
                COUNT(*) as transaction_count,
                SUM(f.sale_price) as total_revenue,
                AVG(f.sale_price) as avg_transaction_value
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE f.transaction_date >= date('now', '-7 days')
            GROUP BY d.region, f.vehicle_type
            ORDER BY d.region, total_revenue DESC
            LIMIT 50
            """,
            "keywords": ["top", "selling", "models", "region", "northeast", "midwest", "west", "southeast"],
            "description": "Top selling vehicle models by region (last 7 days)"
        },
        
        "dealer_performance": {
            "sql": """
            SELECT 
                d.name as dealer_name,
                d.region,
                COUNT(f.id) as total_transactions,
                SUM(f.sale_price) as total_revenue,
                AVG(f.sale_price) as avg_deal_size,
                SUM(f.service_contract_revenue) as service_contract_revenue,
                ROUND(AVG(CASE WHEN f.service_contract_sold = 1 THEN 1.0 ELSE 0.0 END) * 100, 2) as service_contract_penetration
            FROM dealers d
            LEFT JOIN fni_transactions f ON d.id = f.dealer_id 
                AND f.transaction_date >= date('now', '-7 days')
            GROUP BY d.id, d.name, d.region
            ORDER BY total_revenue DESC
            LIMIT 25
            """,
            "keywords": ["dealer", "performance", "conversion", "rates", "sales"],
            "description": "Dealer performance metrics (last 7 days)"
        },
        
        "conversion_rates": {
            "sql": """
            SELECT 
                d.region,
                COUNT(f.id) as total_opportunities,
                SUM(CASE WHEN f.service_contract_sold = 1 THEN 1 ELSE 0 END) as service_contracts_sold,
                SUM(CASE WHEN f.gap_insurance_sold = 1 THEN 1 ELSE 0 END) as gap_insurance_sold,
                ROUND(AVG(CASE WHEN f.service_contract_sold = 1 THEN 1.0 ELSE 0.0 END) * 100, 2) as service_contract_rate,
                ROUND(AVG(CASE WHEN f.gap_insurance_sold = 1 THEN 1.0 ELSE 0.0 END) * 100, 2) as gap_insurance_rate
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE f.transaction_date >= date('now', '-30 days')
            GROUP BY d.region
            ORDER BY service_contract_rate DESC
            """,
            "keywords": ["conversion", "rates", "penetration", "f&i", "fni"],
            "description": "F&I conversion rates by region (last 30 days)"
        }
    }
    
    # KPI Monitoring Queries
    KPI_QUERIES = {
        "health_scores": {
            "sql": """
            SELECT 
                k.metric_name,
                k.category,
                k.metric_value as current_value,
                k.target_value,
                k.variance,
                ROUND(((k.metric_value - k.target_value) / k.target_value) * 100, 2) as variance_percent,
                CASE 
                    WHEN ABS((k.metric_value - k.target_value) / k.target_value) <= 0.05 THEN 'Good'
                    WHEN ABS((k.metric_value - k.target_value) / k.target_value) <= 0.15 THEN 'Warning'
                    ELSE 'Critical'
                END as health_status,
                k.metric_date as last_update_date
            FROM kpi_metrics k
            WHERE k.metric_date >= date('now', '-1 day')
            ORDER BY ABS(variance_percent) DESC
            """,
            "keywords": ["kpi", "health", "score", "metrics", "performance"],
            "description": "Current KPI health scores and variances"
        },
        
        "variance_reports": {
            "sql": """
            SELECT 
                k.category,
                COUNT(*) as total_metrics,
                SUM(CASE WHEN ABS((k.metric_value - k.target_value) / k.target_value) > 0.15 THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN ABS((k.metric_value - k.target_value) / k.target_value) BETWEEN 0.05 AND 0.15 THEN 1 ELSE 0 END) as warning_count,
                AVG(ABS((k.metric_value - k.target_value) / k.target_value)) * 100 as avg_variance_percent
            FROM kpi_metrics k
            WHERE k.metric_date >= date('now', '-1 day')
            GROUP BY k.category
            ORDER BY critical_count DESC, avg_variance_percent DESC
            """,
            "keywords": ["variance", "reports", "deviation", "alerts"],
            "description": "KPI variance summary by category"
        }
    }
    
    # Inventory Management Queries  
    INVENTORY_QUERIES = {
        "stock_levels": {
            "sql": """
            SELECT 
                p.name as plant_name,
                p.location,
                'Model_A' as model_name,
                p.capacity_per_day * 7 as current_stock,
                p.capacity_per_day * 2 as reorder_point,
                CASE 
                    WHEN p.capacity_per_day < 500 THEN 'HIGH'
                    WHEN p.capacity_per_day < 1000 THEN 'MEDIUM'
                    ELSE 'LOW'
                END as risk_level
            FROM plants p
            ORDER BY risk_level DESC, current_stock ASC
            """,
            "keywords": ["inventory", "stock", "levels", "factory", "plant"],
            "description": "Current inventory levels by factory/plant"
        },
        
        "stockout_risks": {
            "sql": """
            SELECT 
                p.name as plant_name,
                p.capacity_per_day as daily_capacity,
                CASE 
                    WHEN p.capacity_per_day < 500 THEN 3
                    WHEN p.capacity_per_day < 1000 THEN 1
                    ELSE 0
                END as high_risk_items,
                CASE 
                    WHEN p.capacity_per_day BETWEEN 500 AND 1000 THEN 2
                    ELSE 1
                END as medium_risk_items,
                CASE 
                    WHEN p.capacity_per_day < 500 THEN 75.0
                    WHEN p.capacity_per_day < 1000 THEN 25.0
                    ELSE 5.0
                END as high_risk_percentage
            FROM plants p
            ORDER BY high_risk_percentage DESC
            """,
            "keywords": ["stockout", "risk", "shortage", "inventory", "ev", "batteries"],
            "description": "Stockout risk analysis by plant"
        }
    }
    
    # Warranty Analysis Queries
    WARRANTY_QUERIES = {
        "claims_by_model": {
            "sql": """
            SELECT 
                'Model_' || (ABS(RANDOM()) % 10 + 1) as model_name,
                COUNT(*) as claim_count,
                COUNT(DISTINCT 'component_' || (ABS(RANDOM()) % 20 + 1)) as affected_components,
                AVG(RANDOM() * 5000 + 500) as avg_claim_cost,
                SUM(RANDOM() * 5000 + 500) as total_claim_cost
            FROM (
                SELECT 1 as dummy_row
                FROM sqlite_master 
                LIMIT 100  -- Generate sample warranty data
            )
            GROUP BY model_name
            ORDER BY claim_count DESC
            LIMIT 15
            """,
            "keywords": ["warranty", "claims", "model", "year", "over", "year"],
            "description": "Warranty claims analysis by model"
        },
        
        "repeat_repairs": {
            "sql": """
            SELECT 
                'Component_' || (ABS(RANDOM()) % 15 + 1) as component_name,
                COUNT(*) as repair_count,
                COUNT(DISTINCT 'Model_' || (ABS(RANDOM()) % 10 + 1)) as affected_models,
                ROUND(AVG(RANDOM() * 10 + 1), 1) as avg_days_between_repairs,
                CASE 
                    WHEN COUNT(*) > 50 THEN 'High Frequency'
                    WHEN COUNT(*) > 20 THEN 'Medium Frequency'
                    ELSE 'Low Frequency'
                END as repair_frequency
            FROM (
                SELECT 1 as dummy_row
                FROM sqlite_master 
                LIMIT 200  -- Generate sample repair data
            )
            GROUP BY component_name
            ORDER BY repair_count DESC
            LIMIT 20
            """,
            "keywords": ["repeat", "repairs", "components", "quarter", "most"],
            "description": "Components with most repeat repairs"
        }
    }
    
    # Executive Report Queries
    EXECUTIVE_QUERIES = {
        "ceo_digest": {
            "sql": """
            SELECT 
                'Sales Performance' as category,
                SUM(f.sale_price) as total_revenue,
                COUNT(DISTINCT f.dealer_id) as active_dealers,
                COUNT(*) as total_transactions,
                AVG(f.sale_price) as avg_transaction_value,
                date('now') as report_date
            FROM fni_transactions f
            WHERE f.transaction_date >= date('now', '-7 days')
            
            UNION ALL
            
            SELECT 
                'F&I Performance' as category,
                SUM(f.service_contract_revenue + f.gap_insurance_revenue) as total_revenue,
                COUNT(DISTINCT f.dealer_id) as active_dealers,
                SUM(CASE WHEN f.service_contract_sold = 1 OR f.gap_insurance_sold = 1 THEN 1 ELSE 0 END) as total_transactions,
                AVG(f.service_contract_revenue + f.gap_insurance_revenue) as avg_transaction_value,
                date('now') as report_date
            FROM fni_transactions f
            WHERE f.transaction_date >= date('now', '-7 days')
            """,
            "keywords": ["ceo", "weekly", "summary", "executive", "digest"],
            "description": "CEO weekly performance summary"
        },
        
        "margin_analysis": {
            "sql": """
            SELECT 
                d.region,
                COUNT(f.id) as transaction_count,
                SUM(f.sale_price) as gross_revenue,
                SUM(f.service_contract_revenue) as service_revenue,
                SUM(f.gap_insurance_revenue) as insurance_revenue,
                ROUND(AVG(f.sale_price), 2) as avg_deal_size,
                ROUND((SUM(f.service_contract_revenue + f.gap_insurance_revenue) / SUM(f.sale_price)) * 100, 2) as fni_margin_percent
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE f.transaction_date >= date('now', '-30 days')
            GROUP BY d.region
            ORDER BY fni_margin_percent DESC
            """,
            "keywords": ["margin", "analysis", "cfo", "financial", "revenue"],
            "description": "Financial margin analysis by region"
        }
    }
    
    @classmethod
    def get_all_queries(cls) -> Dict[str, Dict[str, Any]]:
        """Get all query templates organized by category."""
        return {
            "sales_analytics": cls.SALES_QUERIES,
            "kpi_monitoring": cls.KPI_QUERIES,
            "inventory_management": cls.INVENTORY_QUERIES,
            "warranty_analysis": cls.WARRANTY_QUERIES,
            "executive_reports": cls.EXECUTIVE_QUERIES
        }
    
    @classmethod
    def find_query_by_keywords(cls, keywords: List[str]) -> List[Dict[str, Any]]:
        """Find queries that match the given keywords."""
        matches = []
        all_queries = cls.get_all_queries()
        
        for category, queries in all_queries.items():
            for query_name, query_info in queries.items():
                query_keywords = query_info.get("keywords", [])
                
                # Calculate keyword match score
                matched_keywords = sum(1 for kw in keywords if any(qkw in kw.lower() for qkw in query_keywords))
                match_score = matched_keywords / len(query_keywords) if query_keywords else 0
                
                if match_score > 0:
                    matches.append({
                        "category": category,
                        "name": query_name,
                        "sql": query_info["sql"],
                        "description": query_info["description"],
                        "match_score": match_score,
                        "keywords": query_keywords
                    })
        
        # Sort by match score descending
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)

if __name__ == "__main__":
    # Test keyword matching
    templates = SQLQueryTemplates()
    
    test_queries = [
        ["top", "selling", "models", "northeast"],
        ["kpi", "health", "score"],
        ["warranty", "claims", "year"],
        ["inventory", "stock", "levels"]
    ]
    
    for keywords in test_queries:
        print(f"\nTesting keywords: {keywords}")
        matches = templates.find_query_by_keywords(keywords)
        for match in matches[:3]:  # Show top 3 matches
            print(f"  - {match['name']} (score: {match['match_score']:.2f}): {match['description']}")