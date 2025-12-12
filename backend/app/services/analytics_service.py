"""Analytics service for data retrieval and processing."""

from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, case
import json
from app.db.models import (
    Dealer, FNITransaction, Shipment, Plant, PlantDowntime,
    MarketingCampaign, ServiceAppointment, KPIMetric, RepairOrder, Customer, KPIAlert
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

        # Monthly Trend - Get last 6 months ordered by month name
        monthly_query = """
            SELECT
                month,
                SUM(emails_sent) as emails_sent,
                SUM(unique_opens) as unique_opens,
                SUM(ro_count) as ro_count,
                ROUND(SUM(revenue), 2) as revenue
            FROM marketing_campaigns
            WHERE send_date >= date('now', '-180 days')
            GROUP BY month
            ORDER BY 
                CASE month
                    WHEN 'Jan' THEN 1
                    WHEN 'Feb' THEN 2
                    WHEN 'Mar' THEN 3
                    WHEN 'Apr' THEN 4
                    WHEN 'May' THEN 5
                    WHEN 'Jun' THEN 6
                    WHEN 'Jul' THEN 7
                    WHEN 'Aug' THEN 8
                    WHEN 'Sep' THEN 9
                    WHEN 'Oct' THEN 10
                    WHEN 'Nov' THEN 11
                    WHEN 'Dec' THEN 12
                    ELSE 99
                END DESC
            LIMIT 6
        """

        monthly_data = await self.execute_sql(monthly_query)

        # Channel Performance Breakdown (Email, SMS, Direct Mail)
        channel_query = """
            SELECT
                category,
                SUM(emails_sent) as total_sent,
                SUM(unique_opens) as total_opens,
                ROUND(SUM(unique_opens) * 100.0 / NULLIF(SUM(emails_sent), 0), 1) as open_rate,
                SUM(ro_count) as ro_count,
                ROUND(SUM(revenue), 2) as revenue
            FROM marketing_campaigns
            WHERE send_date >= date('now', '-30 days')
            GROUP BY category
        """
        if dealer_id:
            channel_query += f" AND dealer_id = {dealer_id}"
        
        channel_data = await self.execute_sql(channel_query)
        
        # Transform channel data to a dictionary for easy lookup
        channel_performance = {}
        for channel in channel_data:
            cat = channel.get('category', '').lower()
            if 'email' in cat:
                channel_performance['email'] = {
                    'open_rate': channel.get('open_rate', 0),
                    'total_sent': channel.get('total_sent', 0),
                    'total_opens': channel.get('total_opens', 0),
                    'ro_count': channel.get('ro_count', 0),
                    'revenue': channel.get('revenue', 0),
                }
            elif 'sms' in cat or 'text' in cat:
                channel_performance['sms'] = {
                    'open_rate': channel.get('open_rate', 0),
                    'total_sent': channel.get('total_sent', 0),
                    'total_opens': channel.get('total_opens', 0),
                    'ro_count': channel.get('ro_count', 0),
                    'revenue': channel.get('revenue', 0),
                }
            elif 'mail' in cat or 'direct' in cat:
                channel_performance['direct_mail'] = {
                    'open_rate': channel.get('open_rate', 0),
                    'total_sent': channel.get('total_sent', 0),
                    'total_opens': channel.get('total_opens', 0),
                    'ro_count': channel.get('ro_count', 0),
                    'revenue': channel.get('revenue', 0),
                }

        return {
            "program_summary": summary_data[0] if summary_data else {},
            "program_performance": performance_data,
            "monthly_metrics": monthly_data,
            "channel_performance": channel_performance,
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

        # Dwell time comparison (this week vs last week by carrier)
        dwell_time_comparison_query = """
            WITH carrier_dwell AS (
                SELECT
                    carrier,
                    CASE
                        WHEN scheduled_departure >= datetime('now', '-7 days') THEN 'this_week'
                        WHEN scheduled_departure >= datetime('now', '-14 days') AND scheduled_departure < datetime('now', '-7 days') THEN 'last_week'
                    END as period,
                    ROUND(AVG(dwell_time_hours), 2) as avg_dwell_time
                FROM shipments
                WHERE scheduled_departure >= datetime('now', '-14 days')
                AND dwell_time_hours IS NOT NULL
                GROUP BY carrier, period
            )
            SELECT
                carrier,
                MAX(CASE WHEN period = 'this_week' THEN avg_dwell_time END) as this_week_dwell,
                MAX(CASE WHEN period = 'last_week' THEN avg_dwell_time END) as last_week_dwell
            FROM carrier_dwell
            WHERE carrier IS NOT NULL
            GROUP BY carrier
            HAVING this_week_dwell IS NOT NULL AND last_week_dwell IS NOT NULL
            ORDER BY carrier
            LIMIT 10
        """
        
        dwell_comparison_raw = await self.execute_sql(dwell_time_comparison_query)
        
        # Transform to frontend format
        dwell_time_comparison = []
        if dwell_comparison_raw:
            # Get unique carriers
            carriers = list(set([row['carrier'] for row in dwell_comparison_raw]))
            
            # Build comparison data
            last_week_data = {row['carrier']: row['last_week_dwell'] for row in dwell_comparison_raw}
            this_week_data = {row['carrier']: row['this_week_dwell'] for row in dwell_comparison_raw}
            
            # Create period-based structure
            last_week_row = {'period': 'Last Week'}
            this_week_row = {'period': 'This Week'}
            
            for carrier in carriers:
                if carrier in last_week_data:
                    last_week_row[carrier] = last_week_data[carrier]
                if carrier in this_week_data:
                    this_week_row[carrier] = this_week_data[carrier]
            
            if last_week_row.get('period') and len(last_week_row) > 1:
                dwell_time_comparison = [last_week_row, this_week_row]

        return {
            "overall_stats": delay_stats[0] if delay_stats else {},
            "carrier_breakdown": carrier_data,
            "route_analysis": route_data,
            "delay_reasons": reason_data,
            "dwell_time_comparison": dwell_time_comparison
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
                p.plant_code,
                pd.line_number,
                pd.downtime_hours,
                pd.reason_category,
                pd.reason_detail,
                pd.is_planned,
                pd.supplier,
                pd.event_date
            FROM plants p
            JOIN plant_downtime pd ON p.id = pd.plant_id
            WHERE pd.event_date >= date('now', '-7 days')
            ORDER BY pd.downtime_hours DESC
        """

        detail_data = await self.execute_sql(detail_query)

        # Calculate unplanned downtime per plant
        unplanned_query = """
            SELECT
                p.plant_code,
                SUM(CASE WHEN pd.is_planned = 0 THEN pd.downtime_hours ELSE 0 END) as unplanned
            FROM plants p
            JOIN plant_downtime pd ON p.id = pd.plant_id
            WHERE pd.event_date >= date('now', '-7 days')
            GROUP BY p.plant_code
        """
        unplanned_data = await self.execute_sql(unplanned_query)
        unplanned_map = {row['plant_code']: row['unplanned'] for row in unplanned_data}

        # Add event count and unplanned to plant summary
        for plant in plant_summary:
            plant['events'] = len([d for d in detail_data if d.get('plant_code') == plant.get('plant_code')])
            plant['unplanned'] = unplanned_map.get(plant.get('plant_code'), 0)

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
            "downtime_details": detail_data,
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
        """Get current KPI alerts from stored KPIAlert table."""
        severity_order = case(
            (KPIAlert.severity == 'critical', 1),
            (KPIAlert.severity == 'warning', 2),
            else_=3
        )
        query = select(KPIAlert).where(
            KPIAlert.status == 'active'
        ).order_by(
            severity_order,
            KPIAlert.detected_at.desc()
        ).limit(50)
        
        result = await self.session.execute(query)
        alerts = result.scalars().all()
        
        return [{
            'id': alert.alert_id,
            'metric_name': alert.metric_name,
            'timestamp': alert.detected_at.isoformat() if alert.detected_at else datetime.now().isoformat(),
            'current_value': alert.current_value,
            'previous_value': alert.previous_value,
            'change_percent': alert.change_percent,
            'severity': alert.severity,
            'message': alert.message,
            'region': alert.region or 'All',
            'category': alert.category or 'General',
            'root_cause': alert.root_cause,
        } for alert in alerts]

    async def detect_and_store_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies using direct database queries and store them in KPIAlert table."""
        import uuid
        from sqlalchemy import text

        anomaly_list = []

        try:
            # Direct anomaly detection using SQL queries (more reliable than LLM tool)

            # 1. Detect F&I Revenue anomalies by region
            fni_query = """
                SELECT
                    d.region,
                    AVG(CASE WHEN f.transaction_date >= date('now', '-7 days') THEN f.fni_revenue END) as current_avg,
                    AVG(CASE WHEN f.transaction_date >= date('now', '-14 days') AND f.transaction_date < date('now', '-7 days') THEN f.fni_revenue END) as prev_avg,
                    COUNT(CASE WHEN f.transaction_date >= date('now', '-7 days') THEN 1 END) as current_count
                FROM fni_transactions f
                JOIN dealers d ON f.dealer_id = d.id
                WHERE f.transaction_date >= date('now', '-14 days')
                GROUP BY d.region
                HAVING current_avg IS NOT NULL AND prev_avg IS NOT NULL
            """
            result = await self.session.execute(text(fni_query))
            for row in result.fetchall():
                region, current_avg, prev_avg, count = row
                if prev_avg and prev_avg > 0:
                    change_pct = ((current_avg - prev_avg) / prev_avg) * 100
                    if abs(change_pct) >= 10:  # 10% threshold
                        anomaly_list.append({
                            'type': 'sales_anomaly',
                            'metric': f'F&I Revenue',
                            'region': region,
                            'current_value': float(current_avg),
                            'previous_value': float(prev_avg),
                            'change_percent': round(change_pct, 2),
                            'severity': 'high' if abs(change_pct) >= 20 else 'medium',
                            'contextual_message': f"F&I revenue in {region} {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.1f}%",
                            'suggested_root_cause': f"Review dealer performance in {region}. Check finance manager metrics and promotional campaigns."
                        })

            # 2. Detect Service Appointment volume changes
            service_query = """
                SELECT
                    AVG(CASE WHEN appointment_date >= date('now', '-7 days') THEN daily_count END) as current_avg,
                    AVG(CASE WHEN appointment_date >= date('now', '-14 days') AND appointment_date < date('now', '-7 days') THEN daily_count END) as prev_avg
                FROM (
                    SELECT DATE(appointment_date) as appointment_date, COUNT(*) as daily_count
                    FROM service_appointments
                    WHERE appointment_date >= date('now', '-14 days')
                    GROUP BY DATE(appointment_date)
                )
            """
            result = await self.session.execute(text(service_query))
            row = result.fetchone()
            if row and row[0] and row[1]:
                current_avg, prev_avg = float(row[0]), float(row[1])
                if prev_avg > 0:
                    change_pct = ((current_avg - prev_avg) / prev_avg) * 100
                    if abs(change_pct) >= 15:
                        anomaly_list.append({
                            'type': 'service_anomaly',
                            'metric': 'Service Appointments',
                            'region': 'All',
                            'current_value': current_avg,
                            'previous_value': prev_avg,
                            'change_percent': round(change_pct, 2),
                            'severity': 'medium',
                            'contextual_message': f"Service appointment volume {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.1f}%",
                            'suggested_root_cause': 'Check for seasonal patterns, marketing campaigns, or operational changes affecting service demand.'
                        })

            # 3. Detect Shipment delay anomalies
            shipment_query = """
                SELECT
                    AVG(CASE WHEN scheduled_departure >= datetime('now', '-7 days') THEN
                        CASE WHEN status = 'Delayed' THEN 1.0 ELSE 0.0 END
                    END) * 100 as current_delay_rate,
                    AVG(CASE WHEN scheduled_departure >= datetime('now', '-14 days') AND scheduled_departure < datetime('now', '-7 days') THEN
                        CASE WHEN status = 'Delayed' THEN 1.0 ELSE 0.0 END
                    END) * 100 as prev_delay_rate
                FROM shipments
                WHERE scheduled_departure >= datetime('now', '-14 days')
            """
            result = await self.session.execute(text(shipment_query))
            row = result.fetchone()
            if row and row[0] is not None and row[1] is not None:
                current_rate, prev_rate = float(row[0]), float(row[1])
                if prev_rate > 0:
                    change_pct = ((current_rate - prev_rate) / prev_rate) * 100
                    if abs(change_pct) >= 25 or current_rate > 15:  # Significant change or high absolute rate
                        anomaly_list.append({
                            'type': 'logistics_anomaly',
                            'metric': 'Shipment Delay Rate',
                            'region': 'All',
                            'current_value': current_rate,
                            'previous_value': prev_rate,
                            'change_percent': round(change_pct, 2),
                            'severity': 'high' if current_rate > 20 else 'medium',
                            'contextual_message': f"Shipment delay rate is {current_rate:.1f}% (was {prev_rate:.1f}%)",
                            'suggested_root_cause': 'Review carrier performance, check for supply chain disruptions or capacity issues.'
                        })

            # 4. Detect Plant Downtime anomalies
            downtime_query = """
                SELECT
                    p.name,
                    SUM(CASE WHEN pd.event_date >= date('now', '-7 days') THEN pd.downtime_hours ELSE 0 END) as current_downtime,
                    SUM(CASE WHEN pd.event_date >= date('now', '-14 days') AND pd.event_date < date('now', '-7 days') THEN pd.downtime_hours ELSE 0 END) as prev_downtime
                FROM plants p
                LEFT JOIN plant_downtime pd ON p.id = pd.plant_id
                WHERE pd.event_date >= date('now', '-14 days')
                GROUP BY p.id, p.name
                HAVING current_downtime > 0 OR prev_downtime > 0
            """
            result = await self.session.execute(text(downtime_query))
            for row in result.fetchall():
                plant_name, current_downtime, prev_downtime = row
                current_downtime = float(current_downtime or 0)
                prev_downtime = float(prev_downtime or 0)
                if prev_downtime > 0:
                    change_pct = ((current_downtime - prev_downtime) / prev_downtime) * 100
                    if change_pct >= 50 or current_downtime > 10:  # 50% increase or > 10 hours
                        anomaly_list.append({
                            'type': 'manufacturing_anomaly',
                            'metric': f'Plant Downtime - {plant_name}',
                            'region': 'Manufacturing',
                            'current_value': current_downtime,
                            'previous_value': prev_downtime,
                            'change_percent': round(change_pct, 2),
                            'severity': 'high' if current_downtime > 15 else 'medium',
                            'contextual_message': f"{plant_name} downtime: {current_downtime:.1f} hours this week vs {prev_downtime:.1f} hours last week",
                            'suggested_root_cause': f"Equipment maintenance may be needed at {plant_name}. Check maintenance logs and equipment status."
                        })

        except Exception as e:
            # Log error but continue - we'll still return what we found
            print(f"Error during anomaly detection: {e}")
        stored_count = 0
        
        for idx, anomaly in enumerate(anomaly_list):
            # Generate unique alert_id with timestamp and UUID to ensure uniqueness
            unique_suffix = uuid.uuid4().hex[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            alert_id = f"{anomaly.get('type', 'unknown')}_{anomaly.get('metric', 'unknown')}_{anomaly.get('region', 'all')}_{timestamp}_{unique_suffix}"
            
            # Check if alert already exists (by metric, region, and similar values)
            # We'll check for alerts with same metric and region in last hour to avoid duplicates
            metric_name = anomaly.get('metric', 'Unknown Metric')
            region = anomaly.get('region') or 'All'
            existing_query = select(KPIAlert).where(
                KPIAlert.metric_name == metric_name,
                KPIAlert.region == region,
                KPIAlert.status == 'active',
                KPIAlert.detected_at >= datetime.now() - timedelta(hours=1)
            )
            existing_result = await self.session.execute(existing_query)
            if existing_result.scalar_one_or_none():
                continue  # Skip if similar alert exists in last hour
            
            # Determine severity
            severity = anomaly.get('severity', 'medium')
            if severity == 'high':
                severity = 'critical'
            elif severity == 'medium':
                severity = 'warning'
            else:
                severity = 'info'
            
            # Get values
            current_val = anomaly.get('current_value') or anomaly.get('current_avg', 0)
            previous_val = anomaly.get('previous_value') or anomaly.get('previous_avg')
            change_pct = anomaly.get('change_percent', 0)
            
            # Create alert
            alert = KPIAlert(
                alert_id=alert_id,
                metric_name=anomaly.get('metric', 'Unknown Metric'),
                current_value=float(current_val) if current_val else 0.0,
                previous_value=float(previous_val) if previous_val else None,
                change_percent=float(change_pct) if change_pct else 0.0,
                severity=severity,
                message=anomaly.get('contextual_message', 'Anomaly detected'),
                root_cause=anomaly.get('suggested_root_cause'),
                region=anomaly.get('region') or 'All',
                category=self._infer_category(anomaly.get('metric', '')),
                status='active',
                detected_at=datetime.now()
            )
            
            self.session.add(alert)
            stored_count += 1
        
        await self.session.commit()
        
        return {
            'anomalies_detected': len(anomaly_list),
            'alerts_stored': stored_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def _infer_category(self, metric_name: str) -> str:
        """Infer category from metric name."""
        metric_lower = metric_name.lower()
        if 'f&i' in metric_lower or 'finance' in metric_lower or 'revenue' in metric_lower:
            return 'F&I'
        elif 'service' in metric_lower or 'appointment' in metric_lower:
            return 'Service'
        elif 'shipment' in metric_lower or 'carrier' in metric_lower or 'logistics' in metric_lower:
            return 'Logistics'
        elif 'sales' in metric_lower:
            return 'Sales'
        elif 'marketing' in metric_lower or 'campaign' in metric_lower:
            return 'Marketing'
        return 'General'
    
    async def dismiss_alert(self, alert_id: str, dismissed_by: str = "system") -> bool:
        """Dismiss an alert by setting status to dismissed."""
        query = select(KPIAlert).where(
            KPIAlert.alert_id == alert_id,
            KPIAlert.status == 'active'
        )
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.status = 'dismissed'
            alert.dismissed_at = datetime.now()
            alert.dismissed_by = dismissed_by
            await self.session.commit()
            return True
        return False
    
    async def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific alert by ID for investigation."""
        query = select(KPIAlert).where(KPIAlert.alert_id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            return {
                'id': alert.alert_id,
                'metric_name': alert.metric_name,
                'timestamp': alert.detected_at.isoformat() if alert.detected_at else None,
                'current_value': alert.current_value,
                'previous_value': alert.previous_value,
                'change_percent': alert.change_percent,
                'severity': alert.severity,
                'message': alert.message,
                'region': alert.region,
                'category': alert.category,
                'root_cause': alert.root_cause,
                'status': alert.status,
                'investigation_notes': alert.investigation_notes,
            }
        return None

    async def get_data_catalog(self) -> Dict[str, Any]:
        """Get data catalog information - tables, columns, row counts, regions, categories."""
        from app.utils.schema_utils import get_database_schema
        
        # Get all table names
        tables_query = text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        result = await self.session.execute(tables_query)
        table_names = [row[0] for row in result.fetchall()]
        
        tables = []
        table_descriptions = {
            'dealers': 'Dealer information including location and region',
            'fni_transactions': 'Finance & Insurance transaction records',
            'shipments': 'Vehicle shipment and logistics data',
            'plants': 'Manufacturing plant information',
            'plant_downtime': 'Manufacturing plant downtime events',
            'marketing_campaigns': 'Marketing campaign performance (Invite)',
            'service_appointments': 'Service appointment records with customer information',
            'kpi_metrics': 'Daily KPI metric values and targets',
            'kpi_alerts': 'Stored KPI alerts and anomalies',
            'customers': 'Customer information for personalized experience',
            'repair_orders': 'Repair order (RO) data for inspection dashboard',
        }
        
        for table_name in table_names:
            # Get column information
            columns_query = text(f"PRAGMA table_info({table_name})")
            columns_result = await self.session.execute(columns_query)
            columns_data = columns_result.fetchall()
            columns = [col[1] for col in columns_data]  # col[1] is column name
            
            # Get row count
            count_query = text(f"SELECT COUNT(*) FROM {table_name}")
            count_result = await self.session.execute(count_query)
            row_count = count_result.scalar() or 0
            
            tables.append({
                'name': table_name,
                'description': table_descriptions.get(table_name, f'{table_name} table'),
                'columns': columns,
                'row_count': f'~{row_count:,}' if row_count > 0 else '0'
            })
        
        # Get unique regions from dealers table
        regions_query = text("SELECT DISTINCT region FROM dealers WHERE region IS NOT NULL ORDER BY region")
        regions_result = await self.session.execute(regions_query)
        regions = [row[0] for row in regions_result.fetchall()] or ['Midwest', 'Northeast', 'Southeast', 'West']
        
        # Get unique KPI categories from kpi_metrics table
        categories_query = text("SELECT DISTINCT category FROM kpi_metrics WHERE category IS NOT NULL ORDER BY category")
        categories_result = await self.session.execute(categories_query)
        kpi_categories = [row[0] for row in categories_result.fetchall()] or ['Sales', 'Service', 'F&I', 'Marketing', 'Logistics']
        
        return {
            'tables': tables,
            'regions': regions,
            'kpi_categories': kpi_categories
        }

    async def get_repair_orders(
        self,
        ro_type: Optional[str] = None,
        shop_type: Optional[str] = None,
        waiter: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get repair orders with optional filtering."""
        query = """
            SELECT
                ro.id,
                ro.ro_number as ro,
                ro.priority as p,
                ro.tag,
                ro.promised_time as promised,
                ro.promised_date,
                ro.indicator as e,
                ro.customer_name as customer,
                ro.advisor_id as adv,
                ro.technician_id as tech,
                ro.metric_time as mt,
                CASE 
                    WHEN ro.process_time_days = 0 THEN ''
                    ELSE ro.process_time_days || 'd'
                END as pt,
                ro.status,
                ro.ro_type,
                ro.shop_type,
                ro.waiter,
                ro.is_overdue,
                ro.is_urgent
            FROM repair_orders ro
            WHERE 1=1
        """
        
        if ro_type and ro_type != 'All':
            query += f" AND ro.ro_type = '{ro_type}'"
        if shop_type and shop_type != 'All':
            query += f" AND ro.shop_type = '{shop_type}'"
        if waiter and waiter != 'All':
            query += f" AND ro.waiter = '{waiter}'"
        if search:
            query += f" AND (ro.ro_number LIKE '%{search}%' OR ro.customer_name LIKE '%{search}%')"
        
        query += " ORDER BY ro.priority, ro.promised_date DESC, ro.ro_number"
        
        return await self.execute_sql(query)

    async def get_service_appointments(
        self,
        appointment_date: Optional[date] = None,
        advisor: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get service appointments for Engage page with customer information."""
        if appointment_date is None:
            appointment_date = date.today()
        
        # First, check which columns and tables exist
        try:
            columns_check = await self.session.execute(text("PRAGMA table_info(service_appointments)"))
            existing_columns = {row[1]: row[2] for row in columns_check.fetchall()}
        except:
            existing_columns = {}
        
        # Check if customers table exists
        try:
            table_check = await self.session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='customers'
            """))
            customers_table_exists = table_check.fetchone() is not None
        except:
            customers_table_exists = False
        
        # Build query with customer join - only select columns that exist
        # Core required columns
        select_fields = [
            "sa.id",
            "sa.appointment_date",
            "sa.appointment_time",
            "sa.service_type",
            "sa.vehicle_vin",
            "sa.vehicle_year",
            "sa.vehicle_make",
            "sa.vehicle_model",
            "sa.customer_name",
            "sa.advisor",
            "sa.status",
        ]
        
        # Optional columns (only if they exist)
        optional_fields = [
            ("sa.estimated_duration", "estimated_duration"),
            ("sa.vehicle_mileage", "vehicle_mileage"),
            ("sa.vehicle_icon_color", "vehicle_icon_color"),
            ("sa.secondary_contact", "secondary_contact"),
            ("sa.ro_number", "ro_number"),
            ("sa.code", "code"),
            ("sa.notes", "notes"),
        ]
        
        for field, col_name in optional_fields:
            if col_name in existing_columns:
                select_fields.append(field)
            else:
                # Add NULL as placeholder for missing columns
                select_fields.append(f"NULL as {col_name}")
        
        # Customer fields (only if customers table exists)
        if customers_table_exists:
            select_fields.extend([
                "c.id as customer_id",
                "c.phone",
                "c.email",
                "c.loyalty_tier",
                "c.preferred_services",
                "c.service_history_count",
                "c.last_visit_date"
            ])
            join_clause = "LEFT JOIN customers c ON sa.customer_id = c.id"
        else:
            # Add NULL placeholders if customers table doesn't exist
            select_fields.extend([
                "NULL as customer_id",
                "NULL as phone",
                "NULL as email",
                "NULL as loyalty_tier",
                "NULL as preferred_services",
                "NULL as service_history_count",
                "NULL as last_visit_date"
            ])
            join_clause = ""
        
        query = f"""
            SELECT 
                {', '.join(select_fields)}
            FROM service_appointments sa
            {join_clause}
            WHERE sa.appointment_date = :appointment_date
        """
        
        params = {"appointment_date": appointment_date}
        
        if advisor and advisor != 'All':
            query += " AND sa.advisor = :advisor"
            params["advisor"] = advisor
        
        if status and status != 'All':
            query += " AND sa.status = :status"
            params["status"] = status
        
        if search:
            query += " AND (sa.customer_name LIKE :search OR sa.vehicle_vin LIKE :search OR sa.vehicle_make LIKE :search OR sa.vehicle_model LIKE :search OR sa.ro_number LIKE :search)"
            params["search"] = f"%{search}%"
        
        query += " ORDER BY sa.appointment_time"
        
        result = await self.session.execute(text(query), params)
        rows = result.fetchall()
        columns = result.keys()
        
        appointments = []
        for row in rows:
            apt_dict = dict(zip(columns, row))
            # Parse preferred_services JSON if present
            if apt_dict.get('preferred_services'):
                try:
                    apt_dict['preferred_services'] = json.loads(apt_dict['preferred_services'])
                except:
                    apt_dict['preferred_services'] = []
            else:
                apt_dict['preferred_services'] = []
            appointments.append(apt_dict)
        
        return appointments

    async def check_in_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """Check in a service appointment."""
        query = text("""
            UPDATE service_appointments
            SET status = 'checked_in',
                updated_at = :updated_at
            WHERE id = :appointment_id
            RETURNING id, status
        """)
        
        result = await self.session.execute(
            query,
            {"appointment_id": appointment_id, "updated_at": datetime.utcnow()}
        )
        await self.session.commit()
        
        row = result.fetchone()
        if row:
            return {"id": row[0], "status": row[1], "success": True}
        return {"success": False, "message": "Appointment not found"}

    async def get_appointment_needs_action_count(self, appointment_date: Optional[date] = None) -> int:
        """Get count of appointments that need action (not_arrived, overdue, etc.)."""
        if appointment_date is None:
            appointment_date = date.today()
        
        query = text("""
            SELECT COUNT(*) as count
            FROM service_appointments
            WHERE appointment_date = :appointment_date
            AND status = 'not_arrived'
        """)
        
        result = await self.session.execute(query, {"appointment_date": appointment_date})
        row = result.fetchone()
        return row[0] if row else 0
