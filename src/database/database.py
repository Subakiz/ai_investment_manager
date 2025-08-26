"""
Database connection and utilities for AlphaGen Investment Platform
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator
import asyncio

from ..config.settings import config
from ..utils.logger import get_logger
from .models import Base

logger = get_logger(__name__)

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        # Synchronous engine for migrations and setup
        self.sync_engine = create_engine(
            config.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=config.LOG_LEVEL.upper() == "DEBUG"
        )
        
        # Asynchronous engine for application usage
        self.async_engine = create_async_engine(
            config.async_database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=config.LOG_LEVEL.upper() == "DEBUG"
        )
        
        # Session factories
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.sync_engine
        )
        
        self.AsyncSessionLocal = sessionmaker(
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            bind=self.async_engine
        )
    
    @contextmanager
    def get_session(self) -> Generator:
        """Get synchronous database session"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get asynchronous database session"""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async database session error: {e}")
                raise
    
    async def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.sync_engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.sync_engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    async def setup_extensions(self):
        """Setup PostgreSQL extensions (TimescaleDB, pgvector)"""
        extensions = [
            "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;",
            "CREATE EXTENSION IF NOT EXISTS vector;"
        ]
        
        try:
            async with self.async_engine.begin() as conn:
                for extension in extensions:
                    await conn.execute(text(extension))
            logger.info("Database extensions setup successfully")
        except Exception as e:
            logger.error(f"Failed to setup extensions: {e}")
            # Don't raise here as some extensions might not be available
    
    async def setup_hypertables(self):
        """Setup TimescaleDB hypertables for time-series data"""
        hypertable_queries = [
            """
            SELECT create_hypertable(
                'stock_prices', 
                'trade_date',
                if_not_exists => TRUE
            );
            """,
            """
            SELECT create_hypertable(
                'news_articles', 
                'published_at',
                if_not_exists => TRUE
            );
            """
        ]
        
        try:
            async with self.async_engine.begin() as conn:
                for query in hypertable_queries:
                    await conn.execute(text(query))
            logger.info("TimescaleDB hypertables setup successfully")
        except Exception as e:
            logger.error(f"Failed to setup hypertables: {e}")
            # Don't raise here as TimescaleDB might not be available
    
    async def close(self):
        """Close database connections"""
        await self.async_engine.dispose()
        self.sync_engine.dispose()
        logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for dependency injection
def get_db_session():
    """Dependency function for FastAPI to get database session"""
    with db_manager.get_session() as session:
        yield session

async def get_async_db_session():
    """Dependency function for FastAPI to get async database session"""
    async with db_manager.get_async_session() as session:
        yield session

async def init_database():
    """Initialize database with tables and extensions"""
    logger.info("Initializing database...")
    
    # Check connection
    if not await db_manager.check_connection():
        raise Exception("Cannot connect to database")
    
    # Setup extensions
    await db_manager.setup_extensions()
    
    # Create tables
    db_manager.create_tables()
    
    # Setup hypertables
    await db_manager.setup_hypertables()
    
    logger.info("Database initialization completed")

if __name__ == "__main__":
    # CLI tool for database initialization
    import asyncio
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "init":
                await init_database()
            elif command == "create-tables":
                db_manager.create_tables()
            elif command == "drop-tables":
                db_manager.drop_tables()
            elif command == "check":
                success = await db_manager.check_connection()
                sys.exit(0 if success else 1)
            else:
                print("Available commands: init, create-tables, drop-tables, check")
                sys.exit(1)
        else:
            print("Usage: python -m src.database.database <command>")
            print("Commands: init, create-tables, drop-tables, check")
            sys.exit(1)
    
    asyncio.run(main())