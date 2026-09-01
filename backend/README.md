# Insurance Claim Support System - FastAPI Backend

FastAPI backend foundation for the Multi-Agent Insurance Claim Support System.

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   └── health.py    # Health check endpoint
│   │   │   └── router.py        # API v1 Router aggregator
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & Environment loading
│   │   ├── database.py          # Async SQLAlchemy engine & session getter
│   │   ├── logging.py           # Structured logging configuration
│   │   └── exceptions.py        # Centralized HTTP exception handlers
│   ├── models/                  # SQLAlchemy ORM model base
│   │   └── base.py
│   ├── schemas/                 # Pydantic Request/Response DTOs
│   │   └── health.py
│   ├── services/                # Business logic services
│   └── main.py                  # FastAPI application entrypoint
├── tests/
│   ├── conftest.py              # Pytest fixtures & async DB override
│   └── test_health.py           # API integration tests
├── .env.example                 # Environment variable template
├── .env                         # Active configuration file
├── pyproject.toml               # Project metadata & build spec
├── requirements.txt             # Python dependencies
└── README.md                    # Setup & operation documentation
```

---

## Backend Modules Explanation

* `app/main.py`: Entry point for FastAPI. Initializes lifespan events, CORS middleware, global exception handlers, and includes `/api/v1` routes.
* `app/core/config.py`: Uses `pydantic-settings` to load configuration from `.env` with validation for CORS origins and database connection parameters.
* `app/core/database.py`: Sets up SQLAlchemy 2.0 async engine and session factory (`AsyncSessionLocal`), providing `get_db()` dependency for API controllers.
* `app/core/logging.py`: Configures structured console logging with custom formatters and log levels.
* `app/core/exceptions.py`: Catches HTTP, Validation (422), and Server (500) exceptions to return standardized JSON error envelopes.
* `app/api/v1/endpoints/health.py`: Health check controller that tests database connection (`SELECT 1`) and returns system metadata.
* `app/schemas/health.py`: Pydantic models supporting automatic camelCase alias conversion for seamless integration with the Next.js frontend.

---

## Setup & Local Execution

### 1. Create Python Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure PostgreSQL Database

Option A: Local PostgreSQL Service
Create PostgreSQL database:
```sql
CREATE DATABASE insurance_claims_db;
CREATE USER postgres WITH PASSWORD 'postgres_password';
GRANT ALL PRIVILEGES ON DATABASE insurance_claims_db TO postgres;
```

Option B: Docker PostgreSQL Instance
```bash
docker run -d --name insurance_pg -p 5432:5432 -e POSTGRES_DB=insurance_claims_db -e POSTGRES_PASSWORD=postgres_password postgres:16
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and adjust settings as needed:
```bash
cp .env.example .env
```

Ensure `DATABASE_URL` matches your PostgreSQL connection string:
```env
DATABASE_URL="postgresql+asyncpg://postgres:postgres_password@localhost:5432/insurance_claims_db"
```

---

## Starting the FastAPI Server

Run development server with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access Interactive Documentation:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* Health Endpoint: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## Running Tests

Execute test suite using `pytest`:

```bash
pytest
```
