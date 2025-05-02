from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def create_hypertable(db: AsyncSession, table_name: str, time_column: str, chunk_time_interval: str = '7 days'):
    """
    Create a hypertable from an existing table.
    
    Args:
        db: AsyncSession - Database session
        table_name: str - Name of the table to convert to hypertable
        time_column: str - Name of the timestamp column to use as time dimension
        chunk_time_interval: str - Time interval for chunks (e.g., '7 days')
    """
    query = f"""
    SELECT create_hypertable('{table_name}', '{time_column}', 
                            if_not_exists => TRUE, 
                            chunk_time_interval => INTERVAL '{chunk_time_interval}');
    """
    await db.execute(text(query))
    await db.commit()

async def add_compression_policy(db: AsyncSession, table_name: str, time_column: str, older_than: str = '30 days'):
    """
    Add a compression policy to a hypertable.
    
    Args:
        db: AsyncSession - Database session
        table_name: str - Name of the hypertable
        time_column: str - Name of the timestamp column
        older_than: str - Age threshold for compression (e.g., '30 days')
    """
    # First enable compression on the table
    enable_query = f"""
    ALTER TABLE {table_name} SET (
        timescaledb.compress,
        timescaledb.compress_segmentby = 'session_id'
    );
    """
    await db.execute(text(enable_query))
    
    # Then add the compression policy
    policy_query = f"""
    SELECT add_compression_policy('{table_name}', INTERVAL '{older_than}');
    """
    await db.execute(text(policy_query))
    await db.commit()

async def create_continuous_aggregate(db: AsyncSession, view_name: str, query: str, refresh_interval: str = '1 hour'):
    """
    Create a continuous aggregate view.
    
    Args:
        db: AsyncSession - Database session
        view_name: str - Name of the continuous aggregate view
        query: str - SELECT query defining the view
        refresh_interval: str - How often to refresh the view (e.g., '1 hour')
    """
    create_query = f"""
    CREATE MATERIALIZED VIEW {view_name}
    WITH (timescaledb.continuous) AS
    {query};
    """
    await db.execute(text(create_query))
    
    # Add refresh policy
    policy_query = f"""
    SELECT add_continuous_aggregate_policy('{view_name}',
        start_offset => INTERVAL '2 days',
        end_offset => INTERVAL '1 hour',
        schedule_interval => INTERVAL '{refresh_interval}');
    """
    await db.execute(text(policy_query))
    await db.commit()

async def add_retention_policy(db: AsyncSession, table_name: str, older_than: str = '365 days'):
    """
    Add a data retention policy to a hypertable.
    
    Args:
        db: AsyncSession - Database session
        table_name: str - Name of the hypertable
        older_than: str - Age threshold for data removal (e.g., '365 days')
    """
    query = f"""
    SELECT add_retention_policy('{table_name}', INTERVAL '{older_than}');
    """
    await db.execute(text(query))
    await db.commit()

async def create_index(db: AsyncSession, table_name: str, column_name: str, index_type: str = 'btree'):
    """
    Create an index on a hypertable.
    
    Args:
        db: AsyncSession - Database session
        table_name: str - Name of the hypertable
        column_name: str - Name of the column to index
        index_type: str - Type of index (btree, hash, gist, etc.)
    """
    index_name = f"idx_{table_name}_{column_name}"
    query = f"""
    CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} USING {index_type} ({column_name});
    """
    await db.execute(text(query))
    await db.commit()
