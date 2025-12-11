import asyncio
from app.db.database import get_db
from sqlalchemy import text

async def test_connection():
    """Test database connection"""
    db_gen = get_db()
    db_session = await anext(db_gen)
    
    try:
        # Test query
        result = await db_session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"Database connection successful! Test result: {row}")
        
        # Try to query kpi_metrics table
        result = await db_session.execute(text("SELECT * FROM kpi_metrics LIMIT 1"))
        rows = result.fetchall()
        if rows:
            print(f"kpi_metrics table exists with {len(rows)} row(s)")
            columns = result.keys()
            print(f"Columns: {list(columns)}")
        else:
            print("kpi_metrics table exists but is empty")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        await db_session.close()
        print("Connection closed")

if __name__ == "__main__":
    asyncio.run(test_connection())
