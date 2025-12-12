"""KPI Monitoring Service - Health Score, Forecasting, and Driver Decomposition."""

from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, and_, case
import json
import numpy as np
from app.db.models import (
    KPIMetric, KPIAlert, KPIHealthScore, KPIForecast,
    DriverDecomposition, ScheduledScan, FNITransaction,
    Shipment, PlantDowntime, Dealer
)


class KPIMonitoringService:
    """Service for automated KPI monitoring, health scores, and forecasting."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== HEALTH SCORE ====================

    async def generate_daily_health_score(self, score_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate daily KPI health score with recommendations."""
        if score_date is None:
            score_date = date.today()

        # Check if already generated for today
        existing = await self.session.execute(
            select(KPIHealthScore).where(KPIHealthScore.score_date == score_date)
        )
        existing_score = existing.scalar_one_or_none()

        # Calculate category scores
        category_scores = await self._calculate_category_scores(score_date)

        # Get KPI counts
        kpi_counts = await self._get_kpi_counts(score_date)

        # Get top risks and performers
        top_risks = await self._get_top_risks(score_date)
        top_performers = await self._get_top_performers(score_date)

        # Generate recommendations based on risks
        recommendations = await self._generate_recommendations(top_risks, category_scores)

        # Calculate overall score (weighted average)
        weights = {
            'sales': 0.25,
            'service': 0.20,
            'fni': 0.25,
            'logistics': 0.15,
            'manufacturing': 0.15
        }

        overall_score = 0
        total_weight = 0
        for category, weight in weights.items():
            score = category_scores.get(f'{category}_score')
            if score is not None:
                overall_score += score * weight
                total_weight += weight

        if total_weight > 0:
            overall_score = overall_score / total_weight * 100
        else:
            overall_score = 75  # Default if no data

        # Create or update health score record
        if existing_score:
            existing_score.overall_score = overall_score
            existing_score.sales_score = category_scores.get('sales_score')
            existing_score.service_score = category_scores.get('service_score')
            existing_score.fni_score = category_scores.get('fni_score')
            existing_score.logistics_score = category_scores.get('logistics_score')
            existing_score.manufacturing_score = category_scores.get('manufacturing_score')
            existing_score.total_kpis_monitored = kpi_counts['total']
            existing_score.kpis_on_target = kpi_counts['on_target']
            existing_score.kpis_at_risk = kpi_counts['at_risk']
            existing_score.kpis_critical = kpi_counts['critical']
            existing_score.top_risks = json.dumps(top_risks)
            existing_score.top_performers = json.dumps(top_performers)
            existing_score.recommendations = json.dumps(recommendations)
            existing_score.generated_at = datetime.utcnow()
            health_score = existing_score
        else:
            health_score = KPIHealthScore(
                score_date=score_date,
                overall_score=overall_score,
                sales_score=category_scores.get('sales_score'),
                service_score=category_scores.get('service_score'),
                fni_score=category_scores.get('fni_score'),
                logistics_score=category_scores.get('logistics_score'),
                manufacturing_score=category_scores.get('manufacturing_score'),
                total_kpis_monitored=kpi_counts['total'],
                kpis_on_target=kpi_counts['on_target'],
                kpis_at_risk=kpi_counts['at_risk'],
                kpis_critical=kpi_counts['critical'],
                top_risks=json.dumps(top_risks),
                top_performers=json.dumps(top_performers),
                recommendations=json.dumps(recommendations),
                generated_by='system'
            )
            self.session.add(health_score)

        await self.session.commit()

        return {
            'score_date': score_date.isoformat(),
            'overall_score': round(overall_score, 1),
            'category_scores': {
                'sales': category_scores.get('sales_score'),
                'service': category_scores.get('service_score'),
                'fni': category_scores.get('fni_score'),
                'logistics': category_scores.get('logistics_score'),
                'manufacturing': category_scores.get('manufacturing_score')
            },
            'kpi_counts': kpi_counts,
            'top_risks': top_risks,
            'top_performers': top_performers,
            'recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat()
        }

    async def _calculate_category_scores(self, score_date: date) -> Dict[str, float]:
        """Calculate health scores for each KPI category."""
        scores = {}

        # Sales score - based on revenue vs target
        sales_query = """
            SELECT
                AVG(CASE WHEN metric_value >= target_value THEN 100
                    WHEN metric_value >= target_value * 0.9 THEN 80
                    WHEN metric_value >= target_value * 0.8 THEN 60
                    ELSE 40 END) as score
            FROM kpi_metrics
            WHERE category = 'Sales'
            AND metric_date >= date(:score_date, '-7 days')
            AND target_value > 0
        """
        result = await self.session.execute(text(sales_query), {'score_date': score_date})
        row = result.fetchone()
        scores['sales_score'] = row[0] if row and row[0] else 75

        # Service score - based on appointment completion and satisfaction
        service_query = """
            SELECT
                AVG(CASE WHEN metric_value >= target_value THEN 100
                    WHEN metric_value >= target_value * 0.9 THEN 80
                    WHEN metric_value >= target_value * 0.8 THEN 60
                    ELSE 40 END) as score
            FROM kpi_metrics
            WHERE category = 'Service'
            AND metric_date >= date(:score_date, '-7 days')
            AND target_value > 0
        """
        result = await self.session.execute(text(service_query), {'score_date': score_date})
        row = result.fetchone()
        scores['service_score'] = row[0] if row and row[0] else 75

        # F&I score - based on revenue and penetration rates
        fni_query = """
            SELECT
                AVG(CASE WHEN f.fni_revenue >= 1500 THEN 100
                    WHEN f.fni_revenue >= 1200 THEN 80
                    WHEN f.fni_revenue >= 900 THEN 60
                    ELSE 40 END) as score
            FROM fni_transactions f
            WHERE f.transaction_date >= date(:score_date, '-7 days')
        """
        result = await self.session.execute(text(fni_query), {'score_date': score_date})
        row = result.fetchone()
        scores['fni_score'] = row[0] if row and row[0] else 75

        # Logistics score - based on on-time delivery rate
        logistics_query = """
            SELECT
                (COUNT(CASE WHEN status != 'Delayed' THEN 1 END) * 100.0 /
                 NULLIF(COUNT(*), 0)) as score
            FROM shipments
            WHERE scheduled_departure >= datetime(:score_date, '-7 days')
        """
        result = await self.session.execute(text(logistics_query), {'score_date': score_date})
        row = result.fetchone()
        scores['logistics_score'] = row[0] if row and row[0] else 75

        # Manufacturing score - based on uptime (inverse of downtime)
        manufacturing_query = """
            SELECT
                (1 - (SUM(downtime_hours) / (7 * 24.0))) * 100 as score
            FROM plant_downtime
            WHERE event_date >= date(:score_date, '-7 days')
        """
        result = await self.session.execute(text(manufacturing_query), {'score_date': score_date})
        row = result.fetchone()
        scores['manufacturing_score'] = max(0, min(100, row[0])) if row and row[0] else 85

        return scores

    async def _get_kpi_counts(self, score_date: date) -> Dict[str, int]:
        """Get counts of KPIs by status."""
        # Count from active alerts
        alert_query = select(KPIAlert).where(
            KPIAlert.status == 'active',
            KPIAlert.detected_at >= datetime.combine(score_date - timedelta(days=7), datetime.min.time())
        )
        result = await self.session.execute(alert_query)
        alerts = result.scalars().all()

        critical_count = sum(1 for a in alerts if a.severity == 'critical')
        warning_count = sum(1 for a in alerts if a.severity == 'warning')

        # Estimate total KPIs monitored
        total_kpis = 15  # Base KPI count

        return {
            'total': total_kpis,
            'on_target': max(0, total_kpis - critical_count - warning_count),
            'at_risk': warning_count,
            'critical': critical_count
        }

    async def _get_top_risks(self, score_date: date) -> List[Dict[str, Any]]:
        """Get top risk KPIs."""
        # Order by severity (critical first) then by change percent
        severity_order = case(
            (KPIAlert.severity == 'critical', 1),
            (KPIAlert.severity == 'warning', 2),
            else_=3
        )
        query = select(KPIAlert).where(
            KPIAlert.status == 'active',
            KPIAlert.severity.in_(['critical', 'warning'])
        ).order_by(
            severity_order,
            KPIAlert.change_percent.desc()
        ).limit(5)

        result = await self.session.execute(query)
        alerts = result.scalars().all()

        return [{
            'metric': alert.metric_name,
            'severity': alert.severity,
            'change_percent': alert.change_percent,
            'category': alert.category,
            'region': alert.region,
            'root_cause': alert.root_cause
        } for alert in alerts]

    async def _get_top_performers(self, score_date: date) -> List[Dict[str, Any]]:
        """Get top performing KPIs."""
        query = """
            SELECT
                metric_name,
                category,
                region,
                AVG(metric_value) as avg_value,
                AVG(target_value) as avg_target,
                ROUND((AVG(metric_value) - AVG(target_value)) / NULLIF(AVG(target_value), 0) * 100, 1) as performance
            FROM kpi_metrics
            WHERE metric_date >= date(:score_date, '-7 days')
            AND target_value > 0
            GROUP BY metric_name, category, region
            HAVING AVG(metric_value) >= AVG(target_value)
            ORDER BY performance DESC
            LIMIT 5
        """
        result = await self.session.execute(text(query), {'score_date': score_date})
        rows = result.fetchall()

        return [{
            'metric': row[0],
            'category': row[1],
            'region': row[2],
            'value': row[3],
            'target': row[4],
            'performance': f"+{row[5]}%" if row[5] else "On Target"
        } for row in rows]

    async def _generate_recommendations(
        self,
        top_risks: List[Dict],
        category_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on risks and scores."""
        recommendations = []

        # Category-based recommendations
        for category, score in category_scores.items():
            if score and score < 70:
                cat_name = category.replace('_score', '').upper()
                if 'fni' in category:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'F&I',
                        'action': 'Deploy F&I coaching resources to underperforming dealers',
                        'expected_impact': 'Improve penetration rates by 5-10%'
                    })
                elif 'logistics' in category:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'Logistics',
                        'action': 'Review carrier performance and consider backup routing',
                        'expected_impact': 'Reduce delays by 15-20%'
                    })
                elif 'manufacturing' in category:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'Manufacturing',
                        'action': 'Implement predictive maintenance on critical equipment',
                        'expected_impact': 'Reduce unplanned downtime by 25%'
                    })

        # Risk-based recommendations
        for risk in top_risks[:3]:
            if risk['severity'] == 'critical':
                if 'F&I' in str(risk.get('category', '')):
                    recommendations.append({
                        'priority': 'critical',
                        'category': risk['category'],
                        'action': f"Immediate review of {risk['metric']} - {risk.get('root_cause', 'investigate root cause')}",
                        'expected_impact': 'Prevent further revenue decline'
                    })
                elif 'Logistics' in str(risk.get('category', '')):
                    recommendations.append({
                        'priority': 'critical',
                        'category': risk['category'],
                        'action': 'Recommend checking supplier and carrier status for delays',
                        'expected_impact': 'Restore normal delivery timelines'
                    })

        # Default recommendations if none generated
        if not recommendations:
            recommendations.append({
                'priority': 'info',
                'category': 'General',
                'action': 'Continue monitoring KPIs - all metrics within acceptable ranges',
                'expected_impact': 'Maintain current performance levels'
            })

        return recommendations[:5]  # Return top 5 recommendations

    async def get_health_score_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get health score history for trending."""
        query = select(KPIHealthScore).where(
            KPIHealthScore.score_date >= date.today() - timedelta(days=days)
        ).order_by(KPIHealthScore.score_date.desc())

        result = await self.session.execute(query)
        scores = result.scalars().all()

        return [{
            'date': score.score_date.isoformat(),
            'overall_score': score.overall_score,
            'sales_score': score.sales_score,
            'service_score': score.service_score,
            'fni_score': score.fni_score,
            'logistics_score': score.logistics_score,
            'manufacturing_score': score.manufacturing_score,
            'kpis_on_target': score.kpis_on_target,
            'kpis_at_risk': score.kpis_at_risk,
            'kpis_critical': score.kpis_critical
        } for score in scores]

    # ==================== FORECASTING ====================

    async def generate_forecasts(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Generate KPI forecasts with confidence intervals."""
        forecasts_generated = []

        # Define KPIs to forecast
        kpi_configs = [
            {'metric': 'F&I Revenue', 'category': 'F&I', 'table': 'fni_transactions', 'field': 'fni_revenue'},
            {'metric': 'Service Appointments', 'category': 'Service', 'table': 'service_appointments', 'field': 'COUNT(*)'},
            {'metric': 'Shipment Delays', 'category': 'Logistics', 'table': 'shipments', 'field': 'delay_rate'},
        ]

        for config in kpi_configs:
            try:
                # Get historical data
                historical = await self._get_historical_data(config)

                if len(historical) < 7:
                    continue

                # Generate forecasts using multiple methods
                for day_offset in range(1, days_ahead + 1):
                    forecast_date = date.today() + timedelta(days=day_offset)

                    # Calculate prediction using moving average with trend
                    prediction = float(self._calculate_forecast(historical, day_offset))

                    # Calculate confidence intervals (convert numpy types to Python native)
                    std_dev = float(np.std([h['value'] for h in historical])) if historical else 0.0
                    lower_bound = float(prediction - (1.96 * std_dev))
                    upper_bound = float(prediction + (1.96 * std_dev))

                    # Determine if at risk (convert to Python bool for JSON serialization)
                    target = historical[-1].get('target', prediction * 1.1) if historical else prediction
                    at_risk = bool(prediction < target * 0.9)
                    risk_reason = f"Predicted to be {round((1 - prediction/target) * 100, 1)}% below target" if at_risk else None

                    # Check if forecast exists
                    existing = await self.session.execute(
                        select(KPIForecast).where(
                            KPIForecast.metric_name == config['metric'],
                            KPIForecast.forecast_date == forecast_date
                        )
                    )
                    existing_forecast = existing.scalar_one_or_none()

                    if existing_forecast:
                        existing_forecast.predicted_value = prediction
                        existing_forecast.lower_bound = max(0, lower_bound)
                        existing_forecast.upper_bound = upper_bound
                        existing_forecast.at_risk = at_risk
                        existing_forecast.risk_reason = risk_reason
                        existing_forecast.generated_at = datetime.utcnow()
                    else:
                        forecast = KPIForecast(
                            metric_name=config['metric'],
                            category=config['category'],
                            forecast_date=forecast_date,
                            predicted_value=prediction,
                            lower_bound=max(0, lower_bound),
                            upper_bound=upper_bound,
                            confidence_level=0.95,
                            at_risk=at_risk,
                            risk_reason=risk_reason,
                            model_used='moving_average_trend'
                        )
                        self.session.add(forecast)

                    forecasts_generated.append({
                        'metric': config['metric'],
                        'date': forecast_date.isoformat(),
                        'predicted': round(prediction, 2),
                        'at_risk': at_risk
                    })

            except Exception as e:
                print(f"Error forecasting {config['metric']}: {e}")
                continue

        await self.session.commit()

        return {
            'forecasts_generated': len(forecasts_generated),
            'forecasts': forecasts_generated,
            'generated_at': datetime.utcnow().isoformat()
        }

    async def _get_historical_data(self, config: Dict) -> List[Dict]:
        """Get historical data for forecasting."""
        if config['table'] == 'fni_transactions':
            query = """
                SELECT
                    transaction_date as date,
                    SUM(fni_revenue) as value,
                    50000 as target
                FROM fni_transactions
                WHERE transaction_date >= date('now', '-30 days')
                GROUP BY transaction_date
                ORDER BY transaction_date
            """
        elif config['table'] == 'service_appointments':
            query = """
                SELECT
                    appointment_date as date,
                    COUNT(*) as value,
                    50 as target
                FROM service_appointments
                WHERE appointment_date >= date('now', '-30 days')
                GROUP BY appointment_date
                ORDER BY appointment_date
            """
        elif config['table'] == 'shipments':
            query = """
                SELECT
                    date(scheduled_departure) as date,
                    (SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as value,
                    5 as target
                FROM shipments
                WHERE scheduled_departure >= datetime('now', '-30 days')
                GROUP BY date(scheduled_departure)
                ORDER BY date
            """
        else:
            return []

        result = await self.session.execute(text(query))
        rows = result.fetchall()
        return [{'date': row[0], 'value': row[1], 'target': row[2]} for row in rows]

    def _calculate_forecast(self, historical: List[Dict], days_ahead: int) -> float:
        """Calculate forecast using moving average with trend."""
        if not historical:
            return 0.0

        values = [h['value'] for h in historical if h['value'] is not None]
        if len(values) < 3:
            return float(values[-1]) if values else 0.0

        # Simple moving average (convert numpy to Python float)
        ma_7 = float(np.mean(values[-7:])) if len(values) >= 7 else float(np.mean(values))

        # Calculate trend
        if len(values) >= 14:
            recent_avg = float(np.mean(values[-7:]))
            older_avg = float(np.mean(values[-14:-7]))
            trend = (recent_avg - older_avg) / 7
        else:
            trend = 0.0

        # Forecast with trend
        prediction = ma_7 + (trend * days_ahead)

        return max(0.0, float(prediction))

    async def get_forecasts(
        self,
        metric_name: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get forecasts for display."""
        query = select(KPIForecast).where(
            KPIForecast.forecast_date >= date.today(),
            KPIForecast.forecast_date <= date.today() + timedelta(days=days)
        )

        if metric_name:
            query = query.where(KPIForecast.metric_name == metric_name)

        query = query.order_by(KPIForecast.metric_name, KPIForecast.forecast_date)

        result = await self.session.execute(query)
        forecasts = result.scalars().all()

        return [{
            'metric_name': f.metric_name,
            'category': f.category,
            'forecast_date': f.forecast_date.isoformat(),
            'predicted_value': f.predicted_value,
            'lower_bound': f.lower_bound,
            'upper_bound': f.upper_bound,
            'confidence_level': f.confidence_level,
            'actual_value': f.actual_value,
            'at_risk': f.at_risk,
            'risk_reason': f.risk_reason,
            'model_used': f.model_used
        } for f in forecasts]

    # ==================== DRIVER DECOMPOSITION ====================

    async def analyze_driver_decomposition(
        self,
        metric_name: str,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform driver decomposition analysis for a KPI change."""
        analysis_date = date.today()

        # Get this week vs last week data
        if 'F&I' in metric_name or 'fni' in metric_name.lower():
            decomposition = await self._decompose_fni_drivers(region)
        elif 'Logistics' in metric_name or 'Shipment' in metric_name:
            decomposition = await self._decompose_logistics_drivers()
        else:
            decomposition = await self._decompose_generic_drivers(metric_name, region)

        # Store decomposition
        existing = await self.session.execute(
            select(DriverDecomposition).where(
                DriverDecomposition.metric_name == metric_name,
                DriverDecomposition.analysis_date == analysis_date
            )
        )
        existing_decomp = existing.scalar_one_or_none()

        if existing_decomp:
            # Update existing
            for key, value in decomposition.items():
                if hasattr(existing_decomp, key):
                    setattr(existing_decomp, key, value)
        else:
            decomp = DriverDecomposition(
                analysis_date=analysis_date,
                metric_name=metric_name,
                category=decomposition.get('category', 'General'),
                region=region,
                total_change=decomposition.get('total_change', 0),
                total_change_percent=decomposition.get('total_change_percent', 0),
                price_impact=decomposition.get('price_impact'),
                volume_impact=decomposition.get('volume_impact'),
                mix_impact=decomposition.get('mix_impact'),
                regional_impact=decomposition.get('regional_impact'),
                seasonality_impact=decomposition.get('seasonality_impact'),
                other_impact=decomposition.get('other_impact'),
                price_details=json.dumps(decomposition.get('price_details', {})),
                mix_details=json.dumps(decomposition.get('mix_details', {})),
                regional_details=json.dumps(decomposition.get('regional_details', {})),
                seasonality_details=json.dumps(decomposition.get('seasonality_details', {})),
                primary_driver=decomposition.get('primary_driver'),
                insights=json.dumps(decomposition.get('insights', []))
            )
            self.session.add(decomp)

        await self.session.commit()

        return {
            'metric_name': metric_name,
            'analysis_date': analysis_date.isoformat(),
            'decomposition': decomposition
        }

    async def _decompose_fni_drivers(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Decompose F&I revenue change drivers."""
        region_filter = f"AND d.region = '{region}'" if region else ""

        # Get this week vs last week comparison
        query = f"""
            WITH weekly_data AS (
                SELECT
                    CASE WHEN f.transaction_date >= date('now', '-7 days') THEN 'this_week'
                         ELSE 'last_week' END as period,
                    SUM(f.fni_revenue) as total_revenue,
                    COUNT(*) as transaction_count,
                    AVG(f.sale_price) as avg_price,
                    AVG(f.penetration_rate) as avg_penetration,
                    SUM(CASE WHEN f.service_contract_sold THEN f.service_contract_revenue ELSE 0 END) as service_contract_rev,
                    SUM(CASE WHEN f.gap_insurance_sold THEN f.gap_insurance_revenue ELSE 0 END) as gap_rev
                FROM fni_transactions f
                JOIN dealers d ON f.dealer_id = d.id
                WHERE f.transaction_date >= date('now', '-14 days')
                {region_filter}
                GROUP BY period
            )
            SELECT * FROM weekly_data
        """

        result = await self.session.execute(text(query))
        rows = result.fetchall()

        this_week = next((dict(zip(['period', 'total_revenue', 'transaction_count', 'avg_price',
                                     'avg_penetration', 'service_contract_rev', 'gap_rev'], r))
                          for r in rows if r[0] == 'this_week'), {})
        last_week = next((dict(zip(['period', 'total_revenue', 'transaction_count', 'avg_price',
                                     'avg_penetration', 'service_contract_rev', 'gap_rev'], r))
                          for r in rows if r[0] == 'last_week'), {})

        # Calculate total change
        this_rev = this_week.get('total_revenue', 0) or 0
        last_rev = last_week.get('total_revenue', 0) or 1
        total_change = this_rev - last_rev
        total_change_pct = (total_change / last_rev) * 100 if last_rev else 0

        # Calculate driver impacts
        # Price impact = (new_price - old_price) * old_volume
        price_change = (this_week.get('avg_price', 0) or 0) - (last_week.get('avg_price', 0) or 0)
        old_volume = last_week.get('transaction_count', 0) or 0
        price_impact = price_change * old_volume * 0.05  # F&I is ~5% of sale price

        # Volume impact = (new_volume - old_volume) * old_price
        volume_change = (this_week.get('transaction_count', 0) or 0) - old_volume
        old_price = last_week.get('avg_price', 0) or 0
        volume_impact = volume_change * old_price * 0.05

        # Mix impact (service contracts vs gap insurance)
        sc_change = (this_week.get('service_contract_rev', 0) or 0) - (last_week.get('service_contract_rev', 0) or 0)
        gap_change = (this_week.get('gap_rev', 0) or 0) - (last_week.get('gap_rev', 0) or 0)
        mix_impact = sc_change * 0.4 + gap_change * 0.3  # Weighted by typical margins

        # Regional breakdown
        regional_query = f"""
            SELECT
                d.region,
                SUM(CASE WHEN f.transaction_date >= date('now', '-7 days') THEN f.fni_revenue ELSE 0 END) as this_week,
                SUM(CASE WHEN f.transaction_date < date('now', '-7 days') THEN f.fni_revenue ELSE 0 END) as last_week
            FROM fni_transactions f
            JOIN dealers d ON f.dealer_id = d.id
            WHERE f.transaction_date >= date('now', '-14 days')
            GROUP BY d.region
        """
        regional_result = await self.session.execute(text(regional_query))
        regional_data = [dict(zip(['region', 'this_week', 'last_week'], r)) for r in regional_result.fetchall()]

        regional_impact = sum(
            ((r.get('this_week', 0) or 0) - (r.get('last_week', 0) or 0)) * 0.1
            for r in regional_data
        )

        # Seasonality (simplified - compare to same period last month)
        seasonality_impact = total_change * 0.05  # Assume 5% seasonal effect

        # Other/unexplained
        explained = price_impact + volume_impact + mix_impact + regional_impact + seasonality_impact
        other_impact = total_change - explained

        # Determine primary driver
        impacts = {
            'price': abs(price_impact),
            'volume': abs(volume_impact),
            'mix': abs(mix_impact),
            'regional': abs(regional_impact),
            'seasonality': abs(seasonality_impact)
        }
        primary_driver = max(impacts, key=impacts.get)

        # Generate insights
        insights = []
        if price_impact < -1000:
            insights.append("Average sale price decreased, impacting F&I revenue per deal")
        if volume_impact < -1000:
            insights.append("Transaction volume declined, reducing total F&I opportunity")
        if mix_impact < -1000:
            insights.append("Product mix shifted away from higher-margin service contracts")
        if not insights:
            insights.append("Multiple factors contributing to change with no dominant driver")

        return {
            'category': 'F&I',
            'total_change': round(total_change, 2),
            'total_change_percent': round(total_change_pct, 1),
            'price_impact': round(price_impact, 2),
            'volume_impact': round(volume_impact, 2),
            'mix_impact': round(mix_impact, 2),
            'regional_impact': round(regional_impact, 2),
            'seasonality_impact': round(seasonality_impact, 2),
            'other_impact': round(other_impact, 2),
            'price_details': {
                'this_week_avg': this_week.get('avg_price'),
                'last_week_avg': last_week.get('avg_price'),
                'change': price_change
            },
            'mix_details': {
                'service_contract_change': sc_change,
                'gap_insurance_change': gap_change,
                'penetration_change': (this_week.get('avg_penetration', 0) or 0) - (last_week.get('avg_penetration', 0) or 0)
            },
            'regional_details': regional_data,
            'seasonality_details': {'seasonal_adjustment': seasonality_impact},
            'primary_driver': primary_driver,
            'insights': insights
        }

    async def _decompose_logistics_drivers(self) -> Dict[str, Any]:
        """Decompose logistics delay change drivers."""
        query = """
            WITH weekly_data AS (
                SELECT
                    CASE WHEN scheduled_departure >= datetime('now', '-7 days') THEN 'this_week'
                         ELSE 'last_week' END as period,
                    COUNT(*) as total_shipments,
                    SUM(CASE WHEN status = 'Delayed' THEN 1 ELSE 0 END) as delayed,
                    SUM(CASE WHEN delay_reason = 'Carrier' THEN 1 ELSE 0 END) as carrier_delays,
                    SUM(CASE WHEN delay_reason = 'Route' THEN 1 ELSE 0 END) as route_delays,
                    SUM(CASE WHEN delay_reason = 'Weather' THEN 1 ELSE 0 END) as weather_delays,
                    AVG(dwell_time_hours) as avg_dwell
                FROM shipments
                WHERE scheduled_departure >= datetime('now', '-14 days')
                GROUP BY period
            )
            SELECT * FROM weekly_data
        """

        result = await self.session.execute(text(query))
        rows = result.fetchall()

        columns = ['period', 'total_shipments', 'delayed', 'carrier_delays', 'route_delays', 'weather_delays', 'avg_dwell']
        this_week = next((dict(zip(columns, r)) for r in rows if r[0] == 'this_week'), {})
        last_week = next((dict(zip(columns, r)) for r in rows if r[0] == 'last_week'), {})

        this_delay_rate = ((this_week.get('delayed', 0) or 0) / (this_week.get('total_shipments', 1) or 1)) * 100
        last_delay_rate = ((last_week.get('delayed', 0) or 0) / (last_week.get('total_shipments', 1) or 1)) * 100

        total_change = this_delay_rate - last_delay_rate

        # Carrier impact
        carrier_change = (this_week.get('carrier_delays', 0) or 0) - (last_week.get('carrier_delays', 0) or 0)
        carrier_impact = carrier_change / (this_week.get('total_shipments', 1) or 1) * 100

        # Route impact
        route_change = (this_week.get('route_delays', 0) or 0) - (last_week.get('route_delays', 0) or 0)
        route_impact = route_change / (this_week.get('total_shipments', 1) or 1) * 100

        # Weather impact
        weather_change = (this_week.get('weather_delays', 0) or 0) - (last_week.get('weather_delays', 0) or 0)
        weather_impact = weather_change / (this_week.get('total_shipments', 1) or 1) * 100

        other_impact = total_change - carrier_impact - route_impact - weather_impact

        # Determine primary driver
        impacts = {'carrier': abs(carrier_impact), 'route': abs(route_impact), 'weather': abs(weather_impact)}
        primary_driver = max(impacts, key=impacts.get) if any(impacts.values()) else 'unknown'

        insights = []
        if carrier_impact > 2:
            insights.append("Carrier performance issues are the primary delay driver")
        if weather_impact > 2:
            insights.append("Weather conditions significantly impacting delivery times")
        if route_impact > 2:
            insights.append("Route congestion or changes contributing to delays")

        return {
            'category': 'Logistics',
            'total_change': round(total_change, 2),
            'total_change_percent': round(total_change, 1),
            'price_impact': None,
            'volume_impact': None,
            'mix_impact': round(carrier_impact, 2),  # Using mix for carrier
            'regional_impact': round(route_impact, 2),  # Using regional for route
            'seasonality_impact': round(weather_impact, 2),  # Using seasonality for weather
            'other_impact': round(other_impact, 2),
            'mix_details': {
                'carrier_delays_change': carrier_change,
                'carrier_impact_pct': carrier_impact
            },
            'regional_details': {
                'route_delays_change': route_change,
                'route_impact_pct': route_impact
            },
            'seasonality_details': {
                'weather_delays_change': weather_change,
                'weather_impact_pct': weather_impact
            },
            'primary_driver': primary_driver,
            'insights': insights if insights else ['Multiple factors contributing to delay changes']
        }

    async def _decompose_generic_drivers(self, metric_name: str, region: Optional[str]) -> Dict[str, Any]:
        """Generic driver decomposition for other metrics."""
        return {
            'category': 'General',
            'total_change': 0,
            'total_change_percent': 0,
            'price_impact': None,
            'volume_impact': None,
            'mix_impact': None,
            'regional_impact': None,
            'seasonality_impact': None,
            'other_impact': None,
            'primary_driver': 'unknown',
            'insights': ['Insufficient data for detailed driver decomposition']
        }

    async def get_decomposition(
        self,
        metric_name: str,
        analysis_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """Get stored driver decomposition."""
        if analysis_date is None:
            analysis_date = date.today()

        query = select(DriverDecomposition).where(
            DriverDecomposition.metric_name == metric_name,
            DriverDecomposition.analysis_date == analysis_date
        )
        result = await self.session.execute(query)
        decomp = result.scalar_one_or_none()

        if not decomp:
            return None

        return {
            'metric_name': decomp.metric_name,
            'analysis_date': decomp.analysis_date.isoformat(),
            'category': decomp.category,
            'total_change': decomp.total_change,
            'total_change_percent': decomp.total_change_percent,
            'drivers': {
                'price': {'impact': decomp.price_impact, 'details': json.loads(decomp.price_details or '{}')},
                'volume': {'impact': decomp.volume_impact},
                'mix': {'impact': decomp.mix_impact, 'details': json.loads(decomp.mix_details or '{}')},
                'regional': {'impact': decomp.regional_impact, 'details': json.loads(decomp.regional_details or '{}')},
                'seasonality': {'impact': decomp.seasonality_impact, 'details': json.loads(decomp.seasonality_details or '{}')},
                'other': {'impact': decomp.other_impact}
            },
            'primary_driver': decomp.primary_driver,
            'insights': json.loads(decomp.insights or '[]')
        }


# ==================== SCHEDULED SCANNING ====================

class KPIScheduler:
    """Background scheduler for automated KPI scanning."""

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.running = False

    async def run_scheduled_scan(self, scan_type: str = 'daily') -> Dict[str, Any]:
        """Run a scheduled KPI scan."""
        async with self.session_factory() as session:
            # Record scan start
            scan = ScheduledScan(
                scan_type=scan_type,
                status='running',
                scheduled_at=datetime.utcnow(),
                started_at=datetime.utcnow()
            )
            session.add(scan)
            await session.commit()

            try:
                monitoring_service = KPIMonitoringService(session)

                # 1. Detect anomalies
                from app.services.analytics_service import AnalyticsService
                analytics_service = AnalyticsService(session)
                anomaly_result = await analytics_service.detect_and_store_anomalies()

                # 2. Generate health score
                health_result = await monitoring_service.generate_daily_health_score()

                # 3. Generate forecasts
                forecast_result = await monitoring_service.generate_forecasts()

                # Update scan record
                scan.status = 'completed'
                scan.completed_at = datetime.utcnow()
                scan.anomalies_detected = anomaly_result.get('anomalies_detected', 0)
                scan.alerts_created = anomaly_result.get('alerts_stored', 0)
                scan.health_score_generated = True
                scan.forecasts_generated = forecast_result.get('forecasts_generated', 0)

                await session.commit()

                return {
                    'status': 'completed',
                    'scan_type': scan_type,
                    'anomalies_detected': scan.anomalies_detected,
                    'alerts_created': scan.alerts_created,
                    'health_score': health_result.get('overall_score'),
                    'forecasts_generated': scan.forecasts_generated,
                    'completed_at': scan.completed_at.isoformat()
                }

            except Exception as e:
                scan.status = 'failed'
                scan.completed_at = datetime.utcnow()
                scan.error_message = str(e)
                await session.commit()

                return {
                    'status': 'failed',
                    'scan_type': scan_type,
                    'error': str(e)
                }

    async def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scan history."""
        async with self.session_factory() as session:
            query = select(ScheduledScan).order_by(
                ScheduledScan.scheduled_at.desc()
            ).limit(limit)

            result = await session.execute(query)
            scans = result.scalars().all()

            return [{
                'id': s.id,
                'scan_type': s.scan_type,
                'status': s.status,
                'scheduled_at': s.scheduled_at.isoformat() if s.scheduled_at else None,
                'started_at': s.started_at.isoformat() if s.started_at else None,
                'completed_at': s.completed_at.isoformat() if s.completed_at else None,
                'anomalies_detected': s.anomalies_detected,
                'alerts_created': s.alerts_created,
                'health_score_generated': s.health_score_generated,
                'forecasts_generated': s.forecasts_generated,
                'error_message': s.error_message
            } for s in scans]
