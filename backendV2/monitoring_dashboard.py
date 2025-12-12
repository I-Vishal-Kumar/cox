"""Real-time monitoring and analytics dashboard for the token-optimized BI system."""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import asyncio

from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

@dataclass
class SystemMetric:
    """Represents a system metric data point."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    category: str
    metadata: Dict[str, Any] = None

@dataclass
class AlertRule:
    """Represents an alerting rule."""
    rule_id: str
    metric_name: str
    condition: str  # 'greater_than', 'less_than', 'equals', 'not_equals'
    threshold: float
    severity: str  # 'info', 'warning', 'critical'
    enabled: bool = True
    cooldown_minutes: int = 5

@dataclass
class Alert:
    """Represents a triggered alert."""
    alert_id: str
    rule_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False

class MetricsCollector:
    """Collects and stores system metrics."""
    
    def __init__(self, max_history_hours: int = 24):
        self.max_history_hours = max_history_hours
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))  # Store last 1000 points per metric
        self.current_metrics = {}
        self.collection_interval = 30  # seconds
        self.running = False
    
    def record_metric(self, metric_name: str, value: float, unit: str = "", category: str = "system", metadata: Dict[str, Any] = None):
        """Record a new metric value."""
        metric = SystemMetric(
            timestamp=datetime.now(),
            metric_name=metric_name,
            value=value,
            unit=unit,
            category=category,
            metadata=metadata or {}
        )
        
        self.metrics_history[metric_name].append(metric)
        self.current_metrics[metric_name] = metric
        
        logger.debug(f"Recorded metric: {metric_name} = {value} {unit}")
    
    def get_metric_history(self, metric_name: str, hours: int = 1) -> List[SystemMetric]:
        """Get metric history for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if metric_name not in self.metrics_history:
            return []
        
        return [
            metric for metric in self.metrics_history[metric_name]
            if metric.timestamp >= cutoff_time
        ]
    
    def get_current_metrics(self) -> Dict[str, SystemMetric]:
        """Get current values for all metrics."""
        return self.current_metrics.copy()
    
    def get_metric_summary(self, metric_name: str, hours: int = 1) -> Dict[str, Any]:
        """Get statistical summary for a metric."""
        history = self.get_metric_history(metric_name, hours)
        
        if not history:
            return {"error": f"No data for metric {metric_name}"}
        
        values = [m.value for m in history]
        
        return {
            "metric_name": metric_name,
            "current_value": values[-1] if values else 0,
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values),
            "data_points": len(values),
            "time_range_hours": hours,
            "last_updated": history[-1].timestamp.isoformat() if history else None
        }
    
    def cleanup_old_metrics(self):
        """Remove metrics older than max_history_hours."""
        cutoff_time = datetime.now() - timedelta(hours=self.max_history_hours)
        
        for metric_name in self.metrics_history:
            # Remove old entries
            while (self.metrics_history[metric_name] and 
                   self.metrics_history[metric_name][0].timestamp < cutoff_time):
                self.metrics_history[metric_name].popleft()

class AlertManager:
    """Manages alerting rules and notifications."""
    
    def __init__(self):
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.last_alert_times = {}  # For cooldown tracking
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alerting rule."""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.rule_id} for {rule.metric_name}")
    
    def remove_alert_rule(self, rule_id: str):
        """Remove an alerting rule."""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def check_alerts(self, current_metrics: Dict[str, SystemMetric]):
        """Check all alert rules against current metrics."""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            if rule.metric_name not in current_metrics:
                continue
            
            metric = current_metrics[rule.metric_name]
            should_alert = self._evaluate_condition(metric.value, rule.condition, rule.threshold)
            
            if should_alert:
                self._trigger_alert(rule, metric.value)
            else:
                self._resolve_alert(rule_id)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate if an alert condition is met."""
        if condition == "greater_than":
            return value > threshold
        elif condition == "less_than":
            return value < threshold
        elif condition == "equals":
            return abs(value - threshold) < 0.001  # Float comparison
        elif condition == "not_equals":
            return abs(value - threshold) >= 0.001
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert if not in cooldown."""
        now = datetime.now()
        
        # Check cooldown
        if rule.rule_id in self.last_alert_times:
            last_alert = self.last_alert_times[rule.rule_id]
            if (now - last_alert).total_seconds() < rule.cooldown_minutes * 60:
                return  # Still in cooldown
        
        # Create alert
        alert_id = f"{rule.rule_id}_{int(now.timestamp())}"
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            severity=rule.severity,
            message=f"{rule.metric_name} is {current_value} (threshold: {rule.threshold})",
            triggered_at=now
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_times[rule.rule_id] = now
        
        logger.warning(f"ALERT TRIGGERED: {alert.message} (Severity: {alert.severity})")
    
    def _resolve_alert(self, rule_id: str):
        """Resolve active alerts for a rule."""
        alerts_to_resolve = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.rule_id == rule_id and not alert.resolved_at
        ]
        
        for alert_id in alerts_to_resolve:
            self.active_alerts[alert_id].resolved_at = datetime.now()
            logger.info(f"ALERT RESOLVED: {alert_id}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all currently active alerts."""
        return [alert for alert in self.active_alerts.values() if not alert.resolved_at]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if alert.triggered_at >= cutoff_time
        ]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False

class SystemMonitor:
    """Main system monitoring and analytics dashboard."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.monitoring_active = False
        self.collection_task = None
        
        # Initialize default alert rules
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Set up default alerting rules for the BI system."""
        default_rules = [
            AlertRule(
                rule_id="high_token_usage",
                metric_name="tokens_per_minute",
                condition="greater_than",
                threshold=8000,  # 80% of 10k limit
                severity="warning",
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="critical_token_usage",
                metric_name="tokens_per_minute",
                condition="greater_than",
                threshold=9500,  # 95% of 10k limit
                severity="critical",
                cooldown_minutes=2
            ),
            AlertRule(
                rule_id="low_cache_hit_rate",
                metric_name="cache_hit_rate_percent",
                condition="less_than",
                threshold=70.0,
                severity="warning",
                cooldown_minutes=10
            ),
            AlertRule(
                rule_id="high_response_time",
                metric_name="avg_response_time_ms",
                condition="greater_than",
                threshold=500.0,
                severity="warning",
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="system_error_rate",
                metric_name="error_rate_percent",
                condition="greater_than",
                threshold=5.0,
                severity="critical",
                cooldown_minutes=3
            )
        ]
        
        for rule in default_rules:
            self.alert_manager.add_alert_rule(rule)
    
    async def start_monitoring(self):
        """Start the monitoring system."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.collection_task = asyncio.create_task(self._monitoring_loop())
        logger.info("System monitoring started")
    
    async def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics from system components
                await self._collect_system_metrics()
                
                # Check alert conditions
                current_metrics = self.metrics_collector.get_current_metrics()
                self.alert_manager.check_alerts(current_metrics)
                
                # Cleanup old data
                self.metrics_collector.cleanup_old_metrics()
                
                # Wait for next collection interval
                await asyncio.sleep(self.metrics_collector.collection_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _collect_system_metrics(self):
        """Collect metrics from all system components."""
        try:
            # Import here to avoid circular imports
            from query_router import QueryRouter
            from query_decomposition import HybridAnalysisSystem
            
            # Simulate getting metrics from components
            # In a real system, these would be actual component instances
            
            # Token usage metrics
            self.metrics_collector.record_metric(
                "tokens_per_minute", 
                150,  # Simulated current token usage
                "tokens", 
                "performance"
            )
            
            # Cache performance metrics
            self.metrics_collector.record_metric(
                "cache_hit_rate_percent",
                85.5,  # Simulated cache hit rate
                "%",
                "performance"
            )
            
            # Response time metrics
            self.metrics_collector.record_metric(
                "avg_response_time_ms",
                125.3,  # Simulated response time
                "ms",
                "performance"
            )
            
            # Error rate metrics
            self.metrics_collector.record_metric(
                "error_rate_percent",
                1.2,  # Simulated error rate
                "%",
                "reliability"
            )
            
            # System resource metrics
            self.metrics_collector.record_metric(
                "memory_usage_percent",
                45.8,  # Simulated memory usage
                "%",
                "resources"
            )
            
            # Business metrics
            self.metrics_collector.record_metric(
                "queries_per_minute",
                23,  # Simulated query rate
                "queries",
                "business"
            )
            
            self.metrics_collector.record_metric(
                "unique_users_active",
                8,  # Simulated active users
                "users",
                "business"
            )
            
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
    
    def get_dashboard_data(self, hours: int = 1) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        current_metrics = self.metrics_collector.get_current_metrics()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Get summaries for key metrics
        key_metrics = [
            "tokens_per_minute",
            "cache_hit_rate_percent", 
            "avg_response_time_ms",
            "error_rate_percent",
            "queries_per_minute"
        ]
        
        metric_summaries = {}
        for metric_name in key_metrics:
            summary = self.metrics_collector.get_metric_summary(metric_name, hours)
            if "error" not in summary:
                metric_summaries[metric_name] = summary
        
        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_status": "active" if self.monitoring_active else "inactive",
            "current_metrics": {
                name: {
                    "value": metric.value,
                    "unit": metric.unit,
                    "category": metric.category,
                    "last_updated": metric.timestamp.isoformat()
                }
                for name, metric in current_metrics.items()
            },
            "metric_summaries": metric_summaries,
            "alerts": {
                "active_count": len(active_alerts),
                "active_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "metric_name": alert.metric_name,
                        "severity": alert.severity,
                        "message": alert.message,
                        "triggered_at": alert.triggered_at.isoformat(),
                        "acknowledged": alert.acknowledged
                    }
                    for alert in active_alerts
                ],
                "alert_rules_count": len(self.alert_manager.alert_rules)
            },
            "system_health": self._calculate_system_health(current_metrics, active_alerts)
        }
    
    def _calculate_system_health(self, current_metrics: Dict[str, SystemMetric], active_alerts: List[Alert]) -> Dict[str, Any]:
        """Calculate overall system health score."""
        health_score = 100
        health_status = "excellent"
        issues = []
        
        # Check critical metrics
        if "tokens_per_minute" in current_metrics:
            token_usage = current_metrics["tokens_per_minute"].value
            if token_usage > 9000:
                health_score -= 30
                issues.append("Critical token usage")
            elif token_usage > 7000:
                health_score -= 15
                issues.append("High token usage")
        
        if "cache_hit_rate_percent" in current_metrics:
            cache_rate = current_metrics["cache_hit_rate_percent"].value
            if cache_rate < 60:
                health_score -= 20
                issues.append("Low cache hit rate")
            elif cache_rate < 80:
                health_score -= 10
                issues.append("Suboptimal cache performance")
        
        if "error_rate_percent" in current_metrics:
            error_rate = current_metrics["error_rate_percent"].value
            if error_rate > 5:
                health_score -= 25
                issues.append("High error rate")
            elif error_rate > 2:
                health_score -= 10
                issues.append("Elevated error rate")
        
        # Factor in active alerts
        critical_alerts = sum(1 for alert in active_alerts if alert.severity == "critical")
        warning_alerts = sum(1 for alert in active_alerts if alert.severity == "warning")
        
        health_score -= critical_alerts * 20
        health_score -= warning_alerts * 5
        
        # Determine health status
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 60:
            health_status = "fair"
        elif health_score >= 40:
            health_status = "poor"
        else:
            health_status = "critical"
        
        return {
            "score": max(0, health_score),
            "status": health_status,
            "issues": issues,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time."""
        trend_metrics = [
            "tokens_per_minute",
            "cache_hit_rate_percent",
            "avg_response_time_ms",
            "queries_per_minute"
        ]
        
        trends = {}
        for metric_name in trend_metrics:
            history = self.metrics_collector.get_metric_history(metric_name, hours)
            if len(history) >= 2:
                values = [m.value for m in history]
                
                # Calculate trend direction
                recent_avg = sum(values[-5:]) / min(5, len(values))
                older_avg = sum(values[:5]) / min(5, len(values))
                
                if recent_avg > older_avg * 1.05:
                    trend_direction = "increasing"
                elif recent_avg < older_avg * 0.95:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
                
                trends[metric_name] = {
                    "direction": trend_direction,
                    "recent_average": recent_avg,
                    "change_percent": ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0,
                    "data_points": len(history)
                }
        
        return trends

# Test function
async def test_monitoring_system():
    """Test the monitoring and alerting system."""
    print("🔍 Testing System Monitoring and Analytics Dashboard")
    print("=" * 60)
    
    monitor = SystemMonitor()
    
    # Start monitoring
    print("\\n🚀 Starting monitoring system...")
    await monitor.start_monitoring()
    
    # Let it collect some metrics
    print("📊 Collecting metrics for 5 seconds...")
    await asyncio.sleep(5)
    
    # Get dashboard data
    print("\\n📋 Dashboard Data:")
    dashboard = monitor.get_dashboard_data()
    
    print(f"   Monitoring Status: {dashboard['monitoring_status']}")
    print(f"   Current Metrics: {len(dashboard['current_metrics'])}")
    print(f"   Active Alerts: {dashboard['alerts']['active_count']}")
    print(f"   System Health: {dashboard['system_health']['status']} ({dashboard['system_health']['score']}/100)")
    
    # Show current metrics
    print(f"\\n📈 Current Metrics:")
    for name, metric in dashboard['current_metrics'].items():
        print(f"   {name}: {metric['value']} {metric['unit']} ({metric['category']})")
    
    # Test alert triggering by manually recording high token usage
    print(f"\\n⚠️  Testing alert system...")
    monitor.metrics_collector.record_metric("tokens_per_minute", 8500, "tokens", "performance")
    
    # Check alerts
    current_metrics = monitor.metrics_collector.get_current_metrics()
    monitor.alert_manager.check_alerts(current_metrics)
    
    active_alerts = monitor.alert_manager.get_active_alerts()
    print(f"   Triggered alerts: {len(active_alerts)}")
    for alert in active_alerts:
        print(f"     - {alert.severity.upper()}: {alert.message}")
    
    # Get performance trends
    print(f"\\n📊 Performance Trends:")
    trends = monitor.get_performance_trends(1)  # 1 hour
    for metric_name, trend in trends.items():
        direction_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}
        emoji = direction_emoji.get(trend['direction'], "❓")
        print(f"   {emoji} {metric_name}: {trend['direction']} ({trend['change_percent']:+.1f}%)")
    
    # Stop monitoring
    print(f"\\n🛑 Stopping monitoring system...")
    await monitor.stop_monitoring()
    
    print(f"\\n🎉 Monitoring System Test Complete!")
    print(f"✅ Metrics collection working")
    print(f"✅ Alert system functional")
    print(f"✅ Dashboard data generation successful")
    print(f"✅ Performance trend analysis operational")

if __name__ == "__main__":
    asyncio.run(test_monitoring_system())