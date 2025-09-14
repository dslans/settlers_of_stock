# Settlers of Stock

A conversational stock research application that provides intelligent analysis by combining fundamental and technical trading approaches.

## Project Structure

```
settlers-of-stock/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models
│   │   └── services/       # Business logic services
│   ├── tests/              # Backend tests
│   ├── main.py             # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend Docker configuration
├── frontend/               # React TypeScript frontend
│   ├── public/             # Static assets
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile          # Frontend Docker configuration
├── docker-compose.yml      # Local development environment
└── README.md              # This file
```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (for containerized development)

### Option 1: Docker Development (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd settlers-of-stock
   ```

2. Start the development environment:
   ```bash
   docker-compose up --build
   ```

3. Access the applications:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

5. Start the backend server:
   ```bash
   python main.py
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## Environment Configuration

### Backend Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `GCP_PROJECT_ID`: Google Cloud Project ID
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `NEWS_API_KEY`: News API key
- `SECRET_KEY`: JWT secret key

### Frontend Environment Variables

Create `frontend/.env.local` for local development:

```
REACT_APP_API_URL=http://localhost:8000
```

## Available Scripts

### Backend

- `python main.py` - Start the FastAPI server
- `pytest` - Run tests
- `alembic upgrade head` - Run database migrations

### Frontend

- `npm start` - Start development server
- `npm test` - Run tests
- `npm run build` - Build for production
- `npm run lint` - Run ESLint

## API Documentation

When the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and serialization
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **Celery** - Background job processing

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Material-UI** - Component library
- **React Query** - Data fetching and caching
- **Chart.js** - Financial charts

### External Services
- **Google Cloud Platform** - Cloud infrastructure
- **yfinance** - Market data
- **Alpha Vantage** - Financial data API
- **NewsAPI** - Financial news
- **Vertex AI** - Natural language processing

## Development Guidelines

1. Follow TypeScript strict mode for frontend development
2. Use Pydantic models for all API data validation
3. Write tests for all business logic
4. Use conventional commits for version control
5. Follow the established project structure

## Next Steps

After setting up the development environment:

1. Implement core data models (Task 2)
2. Set up basic FastAPI endpoints (Task 3)
3. Create basic React chat interface (Task 4)
4. Integrate market data sources (Task 5)

For detailed implementation tasks, see `.kiro/specs/settlers-of-stock/tasks.md`.