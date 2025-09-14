"""
Database configuration and connection management for GCP Cloud SQL PostgreSQL.
"""

import os
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from google.cloud.sql.connector import Connector
import asyncpg
from .config import get_settings

settings = get_settings()

# Create declarative base for SQLAlchemy models
Base = declarative_base()

# Metadata for schema management
metadata = MetaData()

class DatabaseManager:
    """Manages database connections for both local development and GCP Cloud SQL."""
    
    def __init__(self):
        self.connector: Optional[Connector] = None
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self._is_cloud_sql = self._detect_cloud_sql_environment()
    
    def _detect_cloud_sql_environment(self) -> bool:
        """Detect if running in GCP environment with Cloud SQL."""
        return (
            settings.GCP_PROJECT_ID is not None and 
            "cloudsql" in (settings.DATABASE_URL or "").lower()
        )
    
    async def _get_cloud_sql_connection_string(self) -> str:
        """Get Cloud SQL connection string using Cloud SQL Connector."""
        if not self.connector:
            self.connector = Connector()
        
        # Extract connection details from DATABASE_URL
        # Expected format: postgresql://user:password@/dbname?host=/cloudsql/project:region:instance
        db_url = settings.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL not configured for Cloud SQL")
        
        # Parse Cloud SQL connection string
        # Format: postgresql://user:password@/dbname?host=/cloudsql/project:region:instance
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        if "cloudsql" not in parsed.query:
            # Fallback to regular connection for local development
            return db_url
        
        # Extract Cloud SQL instance connection name
        query_params = urllib.parse.parse_qs(parsed.query)
        host_param = query_params.get('host', [None])[0]
        
        if not host_param or not host_param.startswith('/cloudsql/'):
            raise ValueError("Invalid Cloud SQL connection string format")
        
        instance_connection_name = host_param.replace('/cloudsql/', '')
        
        # Create connection using Cloud SQL Connector
        def getconn():
            conn = self.connector.connect(
                instance_connection_name,
                "asyncpg",
                user=parsed.username,
                password=parsed.password,
                db=parsed.path.lstrip('/'),
            )
            return conn
        
        # Return async engine with Cloud SQL connector
        return create_async_engine(
            "postgresql+asyncpg://",
            creator=getconn,
            echo=settings.debug
        )
    
    async def initialize_database(self):
        """Initialize database connections."""
        if self._is_cloud_sql:
            # Use Cloud SQL Connector for GCP
            self.async_engine = await self._get_cloud_sql_connection_string()
        else:
            # Use regular connection for local development
            database_url = settings.DATABASE_URL
            if not database_url:
                raise ValueError("DATABASE_URL not configured")
            
            # Convert to async URL if needed
            if database_url.startswith("postgresql://"):
                async_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            else:
                async_url = database_url
            
            self.async_engine = create_async_engine(
                async_url,
                echo=settings.debug,
                pool_pre_ping=True,
                pool_recycle=300,
            )
            
            # Also create sync engine for migrations
            self.engine = create_engine(
                database_url,
                echo=settings.debug,
                pool_pre_ping=True,
                pool_recycle=300,
            )
        
        # Create session factories
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        if self.engine:
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        if not self.AsyncSessionLocal:
            await self.initialize_database()
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_session(self):
        """Get synchronous database session for migrations."""
        if not self.SessionLocal:
            raise RuntimeError("Sync session not available. Initialize database first.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def close_connections(self):
        """Close all database connections."""
        if self.async_engine:
            await self.async_engine.dispose()
        
        if self.engine:
            self.engine.dispose()
        
        if self.connector:
            await self.connector.close_async()

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    async for session in db_manager.get_async_session():
        yield session

# Initialize database on module import
async def init_db():
    """Initialize database connections."""
    await db_manager.initialize_database()

# Cleanup function for application shutdown
async def close_db():
    """Close database connections."""
    await db_manager.close_connections()