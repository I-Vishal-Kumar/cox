"""Background scheduler for automated KPI monitoring."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Simple async background scheduler for KPI monitoring tasks."""

    def __init__(self):
        self.tasks = {}
        self.running = False
        self._loop_task = None

    async def start(self, session_factory):
        """Start the background scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.session_factory = session_factory
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Background scheduler started")

    async def stop(self):
        """Stop the background scheduler."""
        self.running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("Background scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        # Track last run times
        last_hourly = datetime.min
        last_daily = datetime.min

        while self.running:
            try:
                now = datetime.utcnow()

                # Hourly scan (anomaly detection)
                if (now - last_hourly) >= timedelta(hours=1):
                    await self._run_hourly_scan()
                    last_hourly = now

                # Daily scan (health score + forecasts) - run at 6 AM UTC
                if (now - last_daily) >= timedelta(days=1) or (
                    now.hour == 6 and (now - last_daily) >= timedelta(hours=12)
                ):
                    await self._run_daily_scan()
                    last_daily = now

                # Sleep for 5 minutes before checking again
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _run_hourly_scan(self):
        """Run hourly anomaly detection."""
        logger.info("Running hourly anomaly scan...")
        try:
            from app.services.kpi_monitoring_service import KPIScheduler
            scheduler = KPIScheduler(self.session_factory)
            result = await scheduler.run_scheduled_scan('hourly')
            logger.info(f"Hourly scan complete: {result.get('anomalies_detected', 0)} anomalies detected")
        except Exception as e:
            logger.error(f"Hourly scan failed: {e}")

    async def _run_daily_scan(self):
        """Run daily health score and forecast generation."""
        logger.info("Running daily KPI scan...")
        try:
            from app.services.kpi_monitoring_service import KPIScheduler
            scheduler = KPIScheduler(self.session_factory)
            result = await scheduler.run_scheduled_scan('daily')
            logger.info(f"Daily scan complete: Health score={result.get('health_score')}, "
                       f"Forecasts={result.get('forecasts_generated', 0)}")
        except Exception as e:
            logger.error(f"Daily scan failed: {e}")

    async def trigger_scan(self, scan_type: str = 'manual') -> dict:
        """Manually trigger a scan."""
        logger.info(f"Manual scan triggered: {scan_type}")
        try:
            from app.services.kpi_monitoring_service import KPIScheduler
            scheduler = KPIScheduler(self.session_factory)
            return await scheduler.run_scheduled_scan(scan_type)
        except Exception as e:
            logger.error(f"Manual scan failed: {e}")
            return {'status': 'failed', 'error': str(e)}


# Global scheduler instance
background_scheduler = BackgroundScheduler()
