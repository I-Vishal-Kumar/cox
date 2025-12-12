#!/usr/bin/env python3
"""Test script for the dump scheduler."""

import asyncio
from scheduler import DumpScheduler

async def test_jobs():
    """Test all scheduler jobs."""
    scheduler = DumpScheduler()
    
    print("🧪 Testing scheduler jobs...")
    
    # Test daily job
    print("\n📅 Testing daily job...")
    daily_result = await scheduler.run_job_now("daily")
    if daily_result["success"]:
        print(f"✅ Daily job: {daily_result['total_files']} files generated")
    else:
        print(f"❌ Daily job failed: {daily_result.get('error')}")
    
    # Test weekly job
    print("\n📅 Testing weekly job...")
    weekly_result = await scheduler.run_job_now("weekly")
    if weekly_result["success"]:
        print(f"✅ Weekly job: {weekly_result['total_files']} files generated")
    else:
        print(f"❌ Weekly job failed: {weekly_result.get('error')}")
    
    # Test monthly job
    print("\n📅 Testing monthly job...")
    monthly_result = await scheduler.run_job_now("monthly")
    if monthly_result["success"]:
        print(f"✅ Monthly job: {len(monthly_result.get('generated_files', []))} files generated")
    else:
        print(f"❌ Monthly job failed: {monthly_result.get('error')}")
    
    print("\n🎉 Scheduler testing completed!")

if __name__ == "__main__":
    asyncio.run(test_jobs())