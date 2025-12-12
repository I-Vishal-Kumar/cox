"""Database connection utilities for read-only access to existing Cox Automotive DB."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create read-only database engine
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}
)

# Session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        yield session

async def execute_read_only_query(sql_query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query safely.
    
    Args:
        sql_query: SQL query string (SELECT only)
        params: Optional query parameters
        
    Returns:
        List of result dictionaries
        
    Raises:
        ValueError: If query contains non-SELECT operations
    """
    # Safety check - only allow SELECT and PRAGMA queries
    query_upper = sql_query.strip().upper()
    if not (query_upper.startswith('SELECT') or query_upper.startswith('PRAGMA')):
        raise ValueError("Only SELECT and PRAGMA queries are allowed for read-only access")
    
    # Additional safety checks for dangerous operations (but allow PRAGMA)
    if not query_upper.startswith('PRAGMA'):
        dangerous_patterns = [
            r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', 
            r'\bDROP\b', r'\bCREATE\b', r'\bALTER\b', r'\bTRUNCATE\b'
        ]
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper):
                keyword = pattern.replace(r'\b', '').replace('\\', '')
                raise ValueError(f"Query contains dangerous keyword: {keyword}")
    
    try:
        async with async_session() as session:
            result = await session.execute(text(sql_query), params or {})
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        logger.error(f"Query: {sql_query}")
        return []

async def test_database_connection() -> bool:
    """Test database connection."""
    try:
        result = await execute_read_only_query("SELECT 1 as test")
        return len(result) > 0 and result[0]['test'] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

async def get_table_info() -> Dict[str, Any]:
    """Get information about available tables."""
    try:
        # Get table names
        tables_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
        tables = await execute_read_only_query(tables_query)
        
        table_info = {}
        for table in tables:
            table_name = table['name']
            
            # Get column information
            columns_query = f"PRAGMA table_info({table_name})"
            columns = await execute_read_only_query(columns_query)
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = await execute_read_only_query(count_query)
            row_count = count_result[0]['count'] if count_result else 0
            
            table_info[table_name] = {
                'columns': columns,
                'row_count': row_count
            }
        
        return table_info
    except Exception as e:
        logger.error(f"Failed to get table info: {e}")
        return {}

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Test database connection
        print("Testing database connection...")
        if await test_database_connection():
            print("✓ Database connection successful")
            
            # Get table information
            print("\nGetting table information...")
            table_info = await get_table_info()
            print(f"✓ Found {len(table_info)} tables:")
            for table_name, info in table_info.items():
                print(f"  - {table_name}: {info['row_count']} rows, {len(info['columns'])} columns")
        else:
            print("✗ Database connection failed")
    
    asyncio.run(main())