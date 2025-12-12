"""Scheduled job system for automated SQL dump generation."""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from dump_generator import DumpGenerator
from database import test_database_connection
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

class DumpScheduler:
    """Manages scheduled dump generation jobs."""
    
    def __init__(self):
        self.generator = DumpGenerator()
        self.is_running = False
        
    async def daily_job(self) -> Dict[str, Any]:
        """Daily job to refresh real-time analytics (runs at 2 AM)."""
        logger.info("Starting daily dump generation job...")
        
        try:
            # Test database connection first
            if not await test_database_connection():
                logger.error("Database connection failed - skipping daily job")
                return {"success": False, "error": "Database connection failed"}
            
            # Refresh specific categories that need daily updates
            daily_categories = ["sales_analytics", "kpi_monitoring", "inventory_management"]
            
            results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "job_type": "daily",
                "categories_processed": [],
                "total_files": 0,
                "errors": []
            }
            
            for category in daily_categories:
                logger.info(f"Refreshing daily category: {category}")
                category_result = await self.generator.refresh_specific_category(category)
                
                if category_result["success"]:
                    results["categories_processed"].append(category)
                    results["total_files"] += len(category_result["generated_files"])
                    logger.info(f"Daily refresh completed for {category}: {len(category_result['generated_files'])} files")
                else:
                    results["errors"].extend(category_result.get("errors", []))
                    logger.error(f"Daily refresh failed for {category}")
            
            # Log summary
            logger.info(f"Daily job completed: {results['total_files']} files generated, {len(results['errors'])} errors")
            
            # Save job log
            await self._save_job_log(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Daily job failed with exception: {e}")
            return {"success": False, "error": str(e), "job_type": "daily"}
    
    async def weekly_job(self) -> Dict[str, Any]:
        """Weekly job for executive summaries (runs Sunday at 3 AM)."""
        logger.info("Starting weekly dump generation job...")
        
        try:
            if not await test_database_connection():
                logger.error("Database connection failed - skipping weekly job")
                return {"success": False, "error": "Database connection failed"}
            
            # Refresh executive reports and warranty analysis
            weekly_categories = ["executive_reports", "warranty_analysis"]
            
            results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "job_type": "weekly",
                "categories_processed": [],
                "total_files": 0,
                "errors": []
            }
            
            for category in weekly_categories:
                logger.info(f"Refreshing weekly category: {category}")
                category_result = await self.generator.refresh_specific_category(category)
                
                if category_result["success"]:
                    results["categories_processed"].append(category)
                    results["total_files"] += len(category_result["generated_files"])
                    logger.info(f"Weekly refresh completed for {category}: {len(category_result['generated_files'])} files")
                else:
                    results["errors"].extend(category_result.get("errors", []))
                    logger.error(f"Weekly refresh failed for {category}")
            
            logger.info(f"Weekly job completed: {results['total_files']} files generated, {len(results['errors'])} errors")
            
            await self._save_job_log(results)
            return results
            
        except Exception as e:
            logger.error(f"Weekly job failed with exception: {e}")
            return {"success": False, "error": str(e), "job_type": "weekly"}
    
    async def monthly_job(self) -> Dict[str, Any]:
        """Monthly job for comprehensive analysis (runs 1st of month at 4 AM)."""
        logger.info("Starting monthly dump generation job...")
        
        try:
            if not await test_database_connection():
                logger.error("Database connection failed - skipping monthly job")
                return {"success": False, "error": "Database connection failed"}
            
            # Full regeneration of all dumps
            logger.info("Performing full dump regeneration for monthly job")
            results = await self.generator.generate_all_dumps()
            results["job_type"] = "monthly"
            
            logger.info(f"Monthly job completed: {len(results.get('generated_files', []))} files generated")
            
            await self._save_job_log(results)
            return results
            
        except Exception as e:
            logger.error(f"Monthly job failed with exception: {e}")
            return {"success": False, "error": str(e), "job_type": "monthly"}
    
    async def _save_job_log(self, results: Dict[str, Any]) -> None:
        """Save job execution log."""
        try:
            log_dir = Path(settings.logs_dir) / "job_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            job_type = results.get("job_type", "unknown")
            log_file = log_dir / f"{job_type}_job_{timestamp}.json"
            
            import json
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Job log saved: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save job log: {e}")
    
    def setup_schedule(self) -> None:
        """Set up the scheduled jobs."""
        logger.info("Setting up scheduled jobs...")
        
        # Daily job at 2 AM
        schedule.every().day.at("02:00").do(self._run_async_job, self.daily_job)
        
        # Weekly job on Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self._run_async_job, self.weekly_job)
        
        # Monthly job on 1st of month at 4 AM
        schedule.every().month.do(self._run_async_job, self.monthly_job)
        
        logger.info("Scheduled jobs configured:")
        logger.info("  - Daily: 2:00 AM (sales, KPI, inventory)")
        logger.info("  - Weekly: Sunday 3:00 AM (executive reports, warranty)")
        logger.info("  - Monthly: 1st at 4:00 AM (full regeneration)")
    
    def _run_async_job(self, job_func):
        """Wrapper to run async job functions in sync scheduler."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(job_func())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def start_scheduler(self) -> None:
        """Start the scheduler (blocking call)."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.setup_schedule()
        self.is_running = True
        
        logger.info("🕐 Dump scheduler started - waiting for scheduled jobs...")
        logger.info("Press Ctrl+C to stop the scheduler")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        finally:
            self.is_running = False
    
    def stop_scheduler(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped and cleared")
    
    async def run_job_now(self, job_type: str) -> Dict[str, Any]:
        """Run a specific job immediately (for testing)."""
        logger.info(f"Running {job_type} job immediately...")
        
        if job_type == "daily":
            return await self.daily_job()
        elif job_type == "weekly":
            return await self.weekly_job()
        elif job_type == "monthly":
            return await self.monthly_job()
        else:
            return {"success": False, "error": f"Unknown job type: {job_type}"}

# CLI interface for scheduler
async def main():
    """Main function for running scheduler or individual jobs."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SQL Dump Scheduler")
    parser.add_argument(
        "--mode", 
        choices=["start", "daily", "weekly", "monthly"],
        default="start",
        help="Scheduler mode: start (run scheduler), or run specific job"
    )
    
    args = parser.parse_args()
    scheduler = DumpScheduler()
    
    if args.mode == "start":
        # Start the scheduler (blocking)
        scheduler.start_scheduler()
    else:
        # Run specific job immediately
        result = await scheduler.run_job_now(args.mode)
        if result["success"]:
            print(f"✅ {args.mode.title()} job completed successfully")
            print(f"📊 Files generated: {result.get('total_files', 0)}")
            if result.get("errors"):
                print(f"⚠️  Errors: {len(result['errors'])}")
        else:
            print(f"❌ {args.mode.title()} job failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())