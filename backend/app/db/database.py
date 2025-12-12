from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    """Dependency for getting async database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Add missing columns to existing tables (migration)
        await migrate_schema(conn)


async def migrate_schema(conn):
    """Add missing columns to existing tables."""
    from sqlalchemy import text

    try:
        # Check if service_appointments table exists and add missing columns
        result = await conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='service_appointments'
        """))
        if result.fetchone():
            # Get existing columns
            result = await conn.execute(text("PRAGMA table_info(service_appointments)"))
            existing_columns = [row[1] for row in result.fetchall()]

            # Check and add missing columns to service_appointments
            columns_to_add = [
                ("estimated_duration", "TEXT"),
                ("vehicle_mileage", "TEXT"),
                ("vehicle_icon_color", "TEXT"),
                ("secondary_contact", "TEXT"),
                ("notes", "TEXT"),
                ("customer_id", "INTEGER"),
                ("created_at", "DATETIME"),
                ("updated_at", "DATETIME"),
            ]

            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        await conn.execute(text(f"ALTER TABLE service_appointments ADD COLUMN {col_name} {col_type}"))
                        print(f"✓ Added column {col_name} to service_appointments")
                    except Exception as e:
                        print(f"⚠ Could not add column {col_name}: {e}")

        # Check if customers table exists, if not it will be created by create_all
        result = await conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='customers'
        """))
        # If customers table doesn't exist, it will be created by create_all above

        # Check if kpi_alerts table exists and add missing columns if needed
        result = await conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='kpi_alerts'
        """))
        if result.fetchone():
            # Get existing columns
            result = await conn.execute(text("PRAGMA table_info(kpi_alerts)"))
            existing_columns = [row[1] for row in result.fetchall()]

            # Check and add missing columns to kpi_alerts
            columns_to_add = [
                ("investigation_notes", "TEXT"),
                ("dismissed_by", "TEXT"),
            ]

            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        await conn.execute(text(f"ALTER TABLE kpi_alerts ADD COLUMN {col_name} {col_type}"))
                        print(f"✓ Added column {col_name} to kpi_alerts")
                    except Exception as e:
                        print(f"⚠ Could not add column {col_name}: {e}")

        # New tables for KPI Monitoring will be created automatically by create_all
        # - kpi_health_scores
        # - kpi_forecasts
        # - driver_decompositions
        # - scheduled_scans
        print("✓ KPI Monitoring tables ready")

    except Exception as e:
        # Migration errors are not critical - tables might not exist yet
        print(f"⚠ Migration warning: {e}")