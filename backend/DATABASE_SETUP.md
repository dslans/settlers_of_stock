# Database Setup Documentation

## Overview

This document describes the GCP Cloud SQL database setup for the Settlers of Stock application.

## Components Implemented

### 1. Database Configuration (`app/core/database.py`)

- **DatabaseManager**: Manages both local development and GCP Cloud SQL connections
- **Cloud SQL Support**: Uses Google Cloud SQL Connector for secure connections
- **Async Support**: Full async/await support with SQLAlchemy 2.0
- **Connection Pooling**: Configured with appropriate pool settings
- **Environment Detection**: Automatically detects Cloud SQL vs local development

### 2. Database Models

#### User Model (`app/models/user.py`)
- User authentication and profile management
- JSON preferences storage
- Relationships to watchlists, alerts, and chat sessions

#### Watchlist Models (`app/models/watchlist.py`)
- `Watchlist`: User's stock collections
- `WatchlistItem`: Individual stocks in watchlists
- Support for notes, target prices, and position tracking

#### Alert Models (`app/models/alert.py`)
- `Alert`: Price and condition-based notifications
- `AlertTrigger`: Historical record of triggered alerts
- Multiple alert types (price, technical, news, etc.)
- Configurable notification methods

#### Chat Models (`app/models/chat.py`)
- `ChatSession`: Conversation organization
- `ChatMessage`: Individual messages with metadata
- `ChatContext`: Persistent context storage
- Support for analysis tracking and token counting

### 3. Database Migrations (`alembic/`)

- **Alembic Configuration**: Set up for both local and Cloud SQL
- **Initial Migration**: Creates all tables with proper relationships
- **Environment Variables**: Configurable database URLs

### 4. Environment Configuration

#### Local Development
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/settlers_of_stock
```

#### GCP Cloud SQL
```bash
DATABASE_URL=postgresql://user:password@/settlers_of_stock?host=/cloudsql/project:region:instance
GCP_PROJECT_ID=your-gcp-project-id
```

### 5. Testing Setup

- **Test Database**: SQLite-based testing with aiosqlite
- **Async Tests**: Proper async test configuration with pytest-asyncio
- **Model Testing**: Comprehensive tests for all models and relationships
- **Integration Tests**: Database connection and transaction testing

## Dependencies Installed

```bash
# Core database dependencies
sqlalchemy==2.0.43
psycopg2-binary==2.9.10
alembic==1.16.5
asyncpg==0.30.0
greenlet==3.2.4

# GCP Cloud SQL
cloud-sql-python-connector==1.18.4

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
aiosqlite==0.21.0
```

## Usage Examples

### Initialize Database Connection
```python
from app.core.database import db_manager, get_db

# Initialize database
await db_manager.initialize_database()

# Use in FastAPI dependency
async def get_user(db: AsyncSession = Depends(get_db)):
    # Database operations here
    pass
```

### Create Database Tables
```bash
# Run migrations
cd backend
alembic upgrade head
```

### Run Tests
```bash
# Run database tests
cd backend
python -m pytest tests/test_database_simple.py -v
```

## Database Schema

The database includes the following main tables:

1. **users** - User accounts and preferences
2. **watchlists** - User's stock collections
3. **watchlist_items** - Individual stocks in watchlists
4. **alerts** - Price and condition alerts
5. **alert_triggers** - Alert execution history
6. **chat_sessions** - Conversation sessions
7. **chat_messages** - Individual chat messages
8. **chat_contexts** - Persistent conversation context

All tables include proper foreign key relationships, indexes, and timestamps.

## Security Features

- **Connection Security**: Uses Cloud SQL Connector for encrypted connections
- **Environment Variables**: Sensitive data stored in environment variables
- **Connection Pooling**: Prevents connection exhaustion
- **Transaction Management**: Proper rollback on errors

## Performance Considerations

- **Async Operations**: Non-blocking database operations
- **Connection Pooling**: Efficient connection reuse
- **Indexes**: Proper indexing on frequently queried columns
- **Lazy Loading**: Efficient relationship loading

## Next Steps

1. Set up actual GCP Cloud SQL instance
2. Configure production environment variables
3. Run migrations on production database
4. Set up monitoring and logging
5. Implement backup and recovery procedures