# 🎯 JobScatter

<div align="center">

**Multi-Source Job Discovery & Matching Platform**

A Finland-focused application for collecting technology job listings and matching them against candidate profiles.

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)
[![Node](https://img.shields.io/badge/Node-20+-green)](https://nodejs.org/)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Workflow](#workflow)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
  - [Docker Setup](#docker-setup)
  - [Local Development](#local-development)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Development](#development)
- [Contributing](#contributing)

---

## Overview

JobScatter is a job aggregation and matching platform that:

- 🔍 **Collects** job listings from supported job-board sources
- 🤖 **Matches** listings against candidate profiles
- 📄 **Extracts** text from uploaded PDF CVs
- 📥 **Exports** matching results as a PDF report

### Key Features

- Source registry and ingestion for supported job boards
- Candidate-profile-based job search and filtering
- PDF CV text extraction and matching-report export
- Docker Compose setup for the frontend, API, database, and n8n

---

## 📐 Architecture

JobScatter consists of a Next.js frontend, a FastAPI backend, and a PostgreSQL database. An n8n service is included in Docker Compose for optional workflow automation.

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                       │
│              (Frontend - React/Next.js)              │
│                 :3000 (Development)                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│                Backend API Layer                    │
│         (Backend - FastAPI/Uvicorn)                │
│                 :8000                              │
│  ┌────────────────────────────────────────────┐   │
│  │                API routing                 │   │
│  └────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
┌───────▼───┐ ┌───▼──────┐ ┌─▼──────────┐
│   Core    │ │  Source  │ │ Automation │
│  Services │ │ Adapters │ │  (n8n)     │
├───────────┤ ├──────────┤ ├────────────┤
│ • Search  │ │ • Parser │ │ • Triggers │
│ • Jobs    │ │ • Sync   │ │ • HTTP     │
│ • Sources │ │ • Adapter│ │  Requests  │
│           │ │  Pattern │ │            │
└───────────┘ └──────────┘ └────────────┘
        │          │          │
        └──────────┼──────────┘
                   │
    ┌──────────────┴──────────────┐
    │      Data Layer             │
    │  (PostgreSQL Database)      │
    │  :5432 in container         │
    └─────────────────────────────┘
```

### Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Frontend** | User interface & interactions | React/Next.js, TypeScript, CSS |
| **Backend API** | Job search, ingestion, CV extraction, and source management | FastAPI, Python 3.11+ |
| **Database** | Persistent job, candidate, and source data | PostgreSQL with pgvector |
| **n8n** | Optional workflow automation; workflows are configured in n8n | n8n, HTTP requests |
| **Source Adapters** | Fetch and normalize Greenhouse, Lever, Ashby, and Jobly listings | Python modules |

---

## 🔄 Workflow

### Job Aggregation Workflow

```
1. A client requests a fetch-and-search operation.
2. The backend runs ingestion for enabled, supported sources.
3. Adapters normalize listings and the backend stores them in PostgreSQL.
4. The backend matches stored listings against the requested candidate profile.
5. The frontend displays results; clients can also request a PDF report.
```

### Source Registry Workflow

```
┌─────────────────────────────────────────┐
│      Source Configuration Lifecycle     │
└─────────────────────────────────────────┘

POST /sources
  └─► Create source configuration
      (source type, access method, endpoint metadata, configuration)

GET /sources
  └─► List all registered sources
      (Config & operational status)

GET /sources/{source_id}
  └─► Retrieve single source details
      (Metadata, last sync, error logs)

PATCH /sources/{source_id}
  └─► Update config or operational status
      (Enable/disable or update source metadata)

DELETE /sources/{source_id}
  └─► Delete the source registration
```

### CI/CD Workflow

```
Push or pull request → backend tests + frontend tests + frontend build

Successful CI run on master → publish available Docker images to GHCR
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (async web framework)
- **Runtime**: Python 3.11+
- **Database**: PostgreSQL (relational data)
- **Database access**: psycopg (PostgreSQL driver)
- **Validation**: Pydantic (data validation)
- **Server**: Uvicorn (ASGI server)

### Frontend
- **Framework**: React / Next.js
- **Language**: TypeScript
- **Styling**: CSS
- **Runtime**: Node.js 20+
- **Package Manager**: npm

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Workflow Engine**: n8n (automation)
- **CI/CD**: GitHub Actions
- **Environment**: Local development and Docker Compose

### Development Tools
- **Testing**: pytest (backend), Vitest (frontend)
- **CI checks**: Backend tests, frontend tests, and frontend production build
- **Version Control**: Git

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** with Docker Compose
- **Node.js** 20+
- **Python** 3.11+
- **Git**

### Docker Setup

The fastest way to get started with all services running together:

1. **Clone the repository**
   ```bash
   git clone https://github.com/polinenim/JobScatter.git
   cd JobScatter
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration if needed
   ```

3. **Start all services**
   ```bash
   docker compose up --build
   ```

4. **Access services**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs (Swagger UI)
   - Health Check: http://localhost:8000/health
   - PostgreSQL: localhost:5433 (container port 5432)
   - n8n Workflows: http://localhost:5678

5. **Stop services**
   ```bash
   docker compose down
   ```
   
   To also remove the database volume:
   ```bash
   docker compose down -v
   ```

#### n8n Workflow Testing

To verify the backend health through n8n:

1. Open http://localhost:5678
2. On first visit, complete n8n's owner-account setup; then sign in.
3. Create a workflow with a **Manual Trigger** node and an **HTTP Request** node.
4. Configure the HTTP Request node to send a `GET` request to `http://backend:8000/health`.
5. Execute the workflow. The backend is reachable by the service name `backend` from the n8n container.

> **Note**: n8n workflows and local data are stored in the `n8n_data` Docker volume and persist between restarts. No JobScatter workflow is preloaded.

---

### Local Development

Run services individually on your machine for development:

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy ..\.env.example .env  # Windows
# or
cp ../.env.example .env  # macOS/Linux

# The example DATABASE_URL uses the Docker Compose hostname. For local
# development, set it to the address of your PostgreSQL server (see below).

# Run server with auto-reload
uvicorn app.main:app --reload --port 8000
```

**Backend will be available at**: http://localhost:8000

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend will be available at**: http://localhost:3000

#### Database Configuration

When running services locally (not in Docker):

1. Ensure PostgreSQL is running on your system
2. Set the `DATABASE_URL` environment variable:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/jobscatter
   ```
   If you use the PostgreSQL service from Docker Compose, its default host port is `5433`; use `localhost:5433` rather than the container-only hostname `db`.

3. The backend health endpoint will report database connectivity:
   ```bash
   curl http://localhost:8000/health
   ```

---

## 📚 API Documentation

### Auto-Generated Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Source Management Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/sources` | Create a new source configuration |
| `GET` | `/sources` | List all registered sources |
| `GET` | `/sources/{source_id}` | Get specific source details |
| `PATCH` | `/sources/{source_id}` | Update source config or status |
| `DELETE` | `/sources/{source_id}` | Remove a source registration |
| `POST` | `/ingestion/sources/{source_id}/run` | Run ingestion for an enabled, supported source |
| `GET` | `/jobs` | List and filter stored jobs |
| `POST` | `/search` | Match stored jobs to a candidate profile |
| `POST` | `/fetch` | Ingest enabled sources, then search for matching jobs |
| `POST` | `/search/pdf` | Download matching results as a PDF |
| `POST` | `/candidates/cv/extract` | Extract text from a PDF CV |

### Health & Status

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | System health check (includes DB connection) |
| `GET /` | API name and basic status |

### Example: Create a Source

```bash
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "Example Greenhouse Board",
    "source_type": "greenhouse",
    "access_method": "public_api",
    "configuration": {"board_token": "example-board"}
  }'
```

The `board_token` is required by the Greenhouse adapter. Other source types have their own configuration requirements.

---

## ⚙️ Configuration

### Environment Variables

All configuration is managed through `.env` files:

**`.env.example`** contains defaults for local development:
- `DATABASE_URL`: PostgreSQL connection string
- `NEXT_PUBLIC_API_URL`: Frontend API endpoint
- `BACKEND_PORT`, `FRONTEND_PORT`, `POSTGRES_PORT`, `N8N_PORT`: Published host ports
- `JOBSCATTER_CANDIDATE_ID`: Candidate profile ID exposed to the frontend

**Production Secrets**:
- Keep actual secrets in `.env` (Git-ignored)
- `NEXT_PUBLIC_API_URL` and `JOBSCATTER_CANDIDATE_ID` are exposed to the frontend; do not put secrets in frontend variables
- Source configuration is stored by the backend
- Use `.env.production` for production deployments

### Database Configuration

- **Default**: PostgreSQL in Docker, published on `localhost:5433` (container port `5432`)
- **Custom**: Set `DATABASE_URL` for external databases
- **Local Dev**: Set `DATABASE_URL` to the address and credentials of your local database

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run a specific test file
pytest tests/test_source_registry.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Install dependencies
npm install

# Run tests
npm test

# Build for production
npm run build

# Test build locally
npm run build && npm start
```

### All Tests (Docker)

```bash
# In the root directory
docker compose run backend pytest
docker compose run frontend npm test
docker compose run frontend npm run build
```

---

## 👨‍💻 Development

### Project Structure

```
JobScatter/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── *_api.py        # API routers
│   │   ├── *_repository.py # PostgreSQL access
│   │   └── *_adapter.py    # Source adapters
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Backend configuration
│
├── frontend/               # Next.js application
│   ├── app/               # Next.js App Router pages and layout
│   ├── app/globals.css    # Global styles
│   ├── package.json       # Node dependencies
│   └── .env.local         # Frontend configuration
│
├── docker-compose.yml     # Service orchestration
├── .env.example           # Environment template
└── README.md              # This file
```

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test locally
   ```bash
   # Backend: Run pytest
   cd backend && pytest
   
   # Frontend: Run tests
   cd frontend && npm test
   ```

3. **Commit with descriptive messages**
   ```bash
   git commit -m "feat: add job matching algorithm"
   ```

4. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Standards

- **Python**: PEP 8 compliant, type hints required
- **TypeScript**: Strict mode
- **Commits**: Conventional Commits format
- **Tests**: Add tests for new behavior

---

## 🔄 CI/CD Pipeline

GitHub Actions runs CI on pushes and pull requests:

1. ✅ **Backend Tests**: Run pytest suite
2. ✅ **Frontend Tests**: Run npm test
3. ✅ **Frontend Build**: Verify the production build

After a successful CI run on `master`, the CD workflow builds and publishes backend and frontend images to GitHub Container Registry when their Dockerfiles are present. It does not deploy the application.

---

## 📞 Support & Contributing

### Issues & Bugs

Found a bug? Please [create an issue](https://github.com/polinenim/JobScatter/issues) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details

### Feature Requests

Have an idea? [Start a discussion](https://github.com/polinenim/JobScatter/discussions) or open an issue with the `enhancement` label.

### Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**polinenim**  
- GitHub: [@polinenim](https://github.com/polinenim)


<!-- CI/CD demo: testing the GitHub Actions pipeline. -->