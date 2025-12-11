"""Analytics service for data retrieval and processing."""

from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from app.db.models import (
    Dealer, FNITransaction, Shipment, Plant, PlantDowntime,
    MarketingCampaign, ServiceAppointment, KPIMetric
)


class AnalyticsService:
    """Service for retrieving and processing analytics data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_sql(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        try:
            result = await self.session.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return [{"error": str(e)}]

    async def get_invite_dashboard_data(self, dealer_id: Optional[int] = None) -> Dict[str, Any]:
        """Get data for the Invite (Marketing) dashboard."""

        # Program Summary
        program_summary_query = """
            SELECT
                COUNT(DISTINCT campaign_name) as total_programs,
                SUM(emails_sent) as total_emails,
                SUM(unique_opens) as total_opens,
                ROUND(AVG(unique_opens * 100.0 / NULLIF(emails_sent, 0)), 1) as avg_open_rate,
                SUM(ro_count) as total_ros,
                ROUND(SUM(revenue), 2) as total_revenue
            FROM marketing_campaigns
            WHERE send_date >= date('now', '-30 days')
        """
        if dealer_id:
            program_summary_query += f" AND dealer_id = {dealer_id}"

        summary_data = await self.execute_sql(program_summary_query)

        # Program Performance by Campaign
        performance_query = """
            SELECT
                campaign_name,
                campaign_type as category,
                SUM(emails_sent) as emails_sent,
                SUM(unique_opens) as unique_opens,
                ROUND(SUM(unique_opens) * 100.0 / NULLIF(SUM(emails_sent), 0), 1) as open_rate,
                SUM(ro_count) as ro_count,
                ROUND(SUM(revenue), 2) as revenue
            FROM marketing_campaigns
            WHERE send_date >= date('now', '-30 days')
            GROUP BY campaign_name, campaign_type
            ORDER BY revenue DESC
            LIMIT 20
        """
        if dealer_id:
            performance_query = performance_query.replace(
                "GROUP BY",
                f"AND dealer_id = {dealer_id} GROUP BY"
            )

        performance_data = await self.execute_sql(performance_query)

        # Monthly Trend
        monthly_query = """
            SELECT
                month,
                SUM(emails_sent) as emails_sent,
                SUM(unique_opens) as unique_opens,
                SUM(ro_count) as ro_count,
                ROUND(SUM(revenue), 2) as revenue
            FROM marketing_campaigns
            GROUP BY month
            ORDER BY send_date DESC
            LIMIT 6
        """

        monthly_data = await self.execute_sql(monthly_query)

        return {
            "program_summary": summary_data[0] if summary_data else {},
            "program_performance": performance_data,
            "monthly_metrics": monthly_data,
            "last_updated": datetime.now().isoformat()
        }

    async def get_fni_analysis(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Get F&I analysis data."""
        base_query = """
            WITH weekly_data AS (
                SELECT
                    d.name as dealer_name,
                    d.region,
                    d.dealer_code,
                    CASE
                        WHEN f.transaction_date >= date('now', '-7 days') THEN 'this_week'
                        ELSE 'last_week'
                    END as period,
                    SUM(f.fni_revenue) as total_revenue,
                    AVG(f.penetration_rate) as avg_penetration,
                    COUNT(*) as transaction_count,
                    SUM(CASE WHEN f.service_contract_sold THEN 1 ELSE 0 END) as service_contracts_sold
                FROM fni_transactions f
                JOIN dealers d ON f.dealer_id = d.id
                WHERE f.transaction_date >= date('now', '-14 days')
                {region_filter}
                GROUP BY d.id, d.name, d.region, d.dealer_code, period
            )
            SELECT
                dealer_name,
                region,
                dealer_code,
                MAX(CASE WHEN period = 'this_week' THEN total_revenue END) as this_week_revenue,
                MAX(CASE WHEN period = 'last_week' THEN total_revenue END) as last_week_revenue,
                MAX(CASE WHEN period = 'this_week' THEN avg_penetration END) as current_penetration,
                MAX(CASE WHEN period = 'last_week' THEN avg_penetration END) as previous_penetration,
                MAX(CASE WHEN period = 'this_week' THEN transaction_count END) as this_week_transactions,
                MAX(CASE WHEN period = 'last_week' THEN transaction_count END) as last_week_transactions
            FROM weekly_data
            GROUP BY dealer_name, region, dealer_code
            ORDER BY (MAX(CASE WHEN period = 'this_week' THEN total_revenue END) -
                      MAX(CASE WHEN period = 'last_week' THEN total_revenue END)) ASC
        """

        region_filter = f"AND d.region = '{region}'" if region else ""
        query = base_query.format(region_filter=region_filter)

        dealer_data = await self.execute_sql(query)

        # Get manager-level breakdown for problem dealers
        manager_query = """
            SELECT
                f.finance_manager,
                d.name as dealer_name,
                ROUND(AVG(f.penetration_rate) * 100, 1) as avg_penetration,
                COUNT(*) as transactions,
                SUM(f.fni_revenue) as total_revenue
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE f.transaction_date >= date('now', '-7 days')
            AND d.region = 'Midwest'
            GROUP BY f.finance_manager, d.name
            ORDER BY avg_penetration ASC
            LIMIT 10
        """

        manager_data = await self.execute_sql(manager_query)

        return {
            "dealer_comparison": dealer_data,
            "manager_breakdown": manager_data,
            "analysis_date": datetime.now().isoformat()
        }

    async def get_logistics_analysis(self) -> Dict[str, Any]:
        """Get logistics and shipment delay analysis."""
        # Overall delay stats
        delay_stats_query = """
            SELECT
                COUNT(*) as total_shipments,
                SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) as delayed_shipments,
                ROUND(SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as delay_rate
            FROM shipments
            WHERE scheduled_departure >= datetime('now', '-7 days')
        """

        delay_stats = await self.execute_sql(delay_stats_query)

        # Carrier breakdown
        carrier_query = """
            SELECT
                carrier,
                COUNT(*) as total_shipments,
                SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) as delayed_count,
                ROUND(AVG(dwell_time_hours), 2) as avg_dwell_time,
                ROUND(SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as delay_rate
            FROM shipments
            WHERE scheduled_departure >= datetime('now', '-7 days')
            GROUP BY carrier
            ORDER BY delayed_count DESC
        """

        carrier_data = await self.execute_sql(carrier_query)

        # Route breakdown
        route_query = """
            SELECT
                route,
                carrier,
                COUNT(*) as total_shipments,
                SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) as delayed_count,
                delay_reason
            FROM shipments
            WHERE scheduled_departure >= datetime('now', '-7 days')
            AND status = 'Delayed'
            GROUP BY route, carrier, delay_reason
            ORDER BY delayed_count DESC
            LIMIT 10
        """

        route_data = await self.execute_sql(route_query)

        # Delay reason breakdown
        reason_query = """
            SELECT
                delay_reason,
                COUNT(*) as count
            FROM shipments
            WHERE scheduled_departure >= datetime('now', '-7 days')
            AND delay_reason IS NOT NULL
            GROUP BY delay_reason
        """

        reason_data = await self.execute_sql(reason_query)

        return {
            "overall_stats": delay_stats[0] if delay_stats else {},
            "carrier_breakdown": carrier_data,
            "route_analysis": route_data,
            "delay_reasons": reason_data
        }

    async def get_plant_downtime_analysis(self) -> Dict[str, Any]:
        """Get plant downtime analysis."""
        # Plant summary
        plant_summary_query = """
            SELECT
                p.name as plant_name,
                p.plant_code,
                SUM(pd.downtime_hours) as total_downtime,
                COUNT(*) as event_count
            FROM plants p
            JOIN plant_downtime pd ON p.id = pd.plant_id
            WHERE pd.event_date >= date('now', '-7 days')
            GROUP BY p.id, p.name, p.plant_code
            ORDER BY total_downtime DESC
        """

        plant_summary = await self.execute_sql(plant_summary_query)

        # Detailed breakdown
        detail_query = """
            SELECT
                p.name as plant_name,
                pd.line_number,
                pd.downtime_hours,
                pd.reason_category,
                pd.reason_detail,
                pd.is_planned,
                pd.supplier
            FROM plants p
            JOIN plant_downtime pd ON p.id = pd.plant_id
            WHERE pd.event_date >= date('now', '-7 days')
            ORDER BY pd.downtime_hours DESC
        """

        detail_data = await self.execute_sql(detail_query)

        # Cause breakdown
        cause_query = """
            SELECT
                reason_category,
                SUM(downtime_hours) as total_hours,
                COUNT(*) as event_count
            FROM plant_downtime
            WHERE event_date >= date('now', '-7 days')
            GROUP BY reason_category
            ORDER BY total_hours DESC
        """

        cause_data = await self.execute_sql(cause_query)

        return {
            "plant_summary": plant_summary,
            "detailed_events": detail_data,
            "cause_breakdown": cause_data
        }

    async def get_kpi_metrics(
        self,
        category: Optional[str] = None,
        region: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get KPI metrics."""
        query = f"""
            SELECT
                metric_name,
                metric_date,
                ROUND(AVG(metric_value), 2) as value,
                ROUND(AVG(target_value), 2) as target,
                ROUND(AVG(variance), 2) as variance,
                category,
                region
            FROM kpi_metrics
            WHERE metric_date >= date('now', '-{days} days')
            {"AND category = '" + category + "'" if category else ""}
            {"AND region = '" + region + "'" if region else ""}
            GROUP BY metric_name, metric_date, category, region
            ORDER BY metric_date DESC, metric_name
        """

        return await self.execute_sql(query)

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current KPI alerts based on anomaly detection."""
        # Find metrics with significant variance
        alert_query = """
            SELECT
                metric_name,
                metric_date,
                metric_value as current_value,
                target_value,
                variance,
                region,
                category,
                CASE
                    WHEN ABS(variance) > 15 THEN 'critical'
                    WHEN ABS(variance) > 10 THEN 'warning'
                    ELSE 'info'
                END as severity
            FROM kpi_metrics
            WHERE metric_date >= date('now', '-7 days')
            AND ABS(variance) > 8
            ORDER BY ABS(variance) DESC
            LIMIT 10
        """

        return await self.execute_sql(alert_query)
