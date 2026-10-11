# 🎯 JobScatter

<div align="center">

**Multi-Source Job Intelligence & Matching Platform**

A Finland-focused job intelligence application for discovering early-career technology opportunities through intelligent aggregation and matching.

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

JobScatter is an intelligent job aggregation and matching platform that:

- 🔍 **Aggregates** job listings from multiple sources
- 🤖 **Intelligently matches** opportunities with candidates
- 📊 **Provides analytics** on job market trends
- 🔄 **Maintains real-time** data synchronization
- 🛡️ **Ensures data integrity** across distributed sources

### Key Features

- Multi-source job aggregation with real-time updates
- Advanced job matching algorithms
- Comprehensive API for source management
- Scalable architecture with containerized deployment
- Health monitoring and workflow automation

---

## 📐 Architecture

JobScatter follows a microservices architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                       │
│              (Frontend - React/Next.js)              │
│                 :3000 (Development)                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│              API Gateway Layer                      │
│         (Backend - FastAPI/Uvicorn)                │
│                 :8000                              │
│  ┌────────────────────────────────────────────┐   │
│  │  Authentication │ Authorization │ Routing  │   │
│  └────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
┌───────▼───┐ ┌───▼──────┐ ┌─▼──────────┐
│   Core    │ │  Source  │ │ Automation │
│  Services │ │ Adapters │ │  (n8n)     │
├───────────┤ ├──────────┤ ├────────────┤
│ • Jobs    │ │ • Parser │ │ • Webhooks │
│ • Matches │ │ • Sync   │ │ • Health   │
│ • Metrics │ │ • Adapter│ │  Checks    │
│ • Sources │ │  Pattern │ │ • Triggers │
└───────────┘ └──────────┘ └────────────┘
        │          │          │
        └──────────┼──────────┘
                   │
    ┌──────────────┴──────────────┐
    │      Data Layer             │
    │  (PostgreSQL Database)      │
    │    :5432                    │
    └─────────────────────────────┘
```

### Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Frontend** | User interface & interactions | React/Next.js, TypeScript, CSS |
| **Backend API** | Core business logic & routing | FastAPI, Python 3.11+ |
| **Database** | Persistent data storage | PostgreSQL |
| **n8n Workflow** | Automation & event orchestration | n8n, HTTP requests |
| **Source Adapters** | Multi-source aggregation | Custom Python modules |

### Data Flow

```
External Job Sources
        │
        ▼
┌────────────────────────────┐
│  Source Adapters           │
│  (Parse & Transform)       │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  n8n Workflows             │
│  (Orchestration)           │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Backend API               │
│  (Validation & Storage)    │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  PostgreSQL Database       │
│  (Persistence)             │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Frontend Application      │
│  (Presentation)            │
└────────────────────────────┘
```

---

## 🔄 Workflow

### Job Aggregation Workflow

```
1. Data Collection
   ├─ Trigger: Scheduled (n8n) or Webhook
   ├─ Action: Connect to source APIs
   └─ Output: Raw job listings

2. Data Transformation
   ├─ Adapter: Source-specific parser
   ├─ Process: Normalize & validate
   └─ Output: Standardized job objects

3. Data Enrichment
   ├─ Categorization: Job level, company, location
   ├─ Analysis: Required skills, market trends
   └─ Output: Enhanced job metadata

4. Storage & Indexing
   ├─ Database: Insert/update in PostgreSQL
   ├─ Indexing: Enable fast search
   └─ Output: Persistent, queryable records

5. Notification & Sync
   ├─ Trigger: New jobs alert
   ├─ Matching: Candidate fit analysis
   └─ Output: User notifications & recommendations
```

### Source Registry Workflow

```
┌─────────────────────────────────────────┐
│      Source Configuration Lifecycle     │
└─────────────────────────────────────────┘

POST /sources
  └─► Create source configuration
      (API endpoint, auth, update frequency)

GET /sources
  └─► List all registered sources
      (Config & operational status)

GET /sources/{source_id}
  └─► Retrieve single source details
      (Metadata, last sync, error logs)

PATCH /sources/{source_id}
  └─► Update config or operational status
      (Pause, resume, adjust frequency)

DELETE /sources/{source_id}
  └─► Remove source registration
      (Clean up & archive history)
```

### CI/CD Workflow

```
Git Push / Pull Request
        │
        ▼
GitHub Actions Trigger
        │
    ┌───┴───┐
    │       │
    ▼       ▼
Backend   Frontend
Tests     Tests
    │       │
    ├───┬───┤
    │   │   │
    ▼   ▼   ▼
 Lint Lint Build
    │   │   │
    └───┴───┘
        │
        ▼
Deploy (if main)
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (async web framework)
- **Runtime**: Python 3.11+
- **Database**: PostgreSQL (relational data)
- **ORM**: SQLAlchemy (database abstraction)
- **Validation**: Pydantic (data validation)
- **Server**: Uvicorn (ASGI server)

### Frontend
- **Framework**: React / Next.js
- **Language**: TypeScript
- **Styling**: CSS
- **Runtime**: Node.js 20+
- **Package Manager**: npm/pnpm

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Workflow Engine**: n8n (automation)
- **CI/CD**: GitHub Actions
- **Environment**: Local dev & production ready

### Development Tools
- **Testing**: pytest (backend), Jest (frontend)
- **Linting**: Configured per language
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
   - PostgreSQL: localhost:5432
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
2. Sign in with the local n8n owner account
3. Navigate to **Workflows** and select `JobScatter API Health Check`
4. Click **Execute Workflow**
5. The workflow will run: Manual Trigger → HTTP Request to `http://backend:8000/health`

> **Note**: n8n local data is stored in the `n8n_data` Docker volume and persists between restarts.

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

### Health & Status

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | System health check (includes DB connection) |
| `GET /status` | Detailed service status |

### Example: Create a Source

```bash
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LinkedIn Jobs",
    "source_type": "linkedin",
    "api_endpoint": "https://api.linkedin.com/jobs",
    "config": {"location": "Finland"}
  }'
```

---

## ⚙️ Configuration

### Environment Variables

All configuration is managed through `.env` files:

**`.env.example`** contains defaults for local development:
- `DATABASE_URL`: PostgreSQL connection string
- `NEXT_PUBLIC_API_URL`: Frontend API endpoint
- `BACKEND_PORT`: Backend server port
- `N8N_ADMIN_EMAIL`: n8n admin account
- Source API credentials and endpoints

**Production Secrets**:
- Keep actual secrets in `.env` (Git-ignored)
- Frontend receives only `NEXT_PUBLIC_API_URL`
- All other credentials stay backend-only
- Use `.env.production` for production deployments

### Database Configuration

- **Default**: PostgreSQL in Docker (localhost:5432)
- **Custom**: Set `DATABASE_URL` for external databases
- **Local Dev**: Required for running backend outside Docker

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_sources.py

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
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── adapters/       # Source adapters
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Backend configuration
│
├── frontend/               # Next.js application
│   ├── pages/             # Page components
│   ├── components/        # Reusable components
│   ├── lib/               # Utilities & helpers
│   ├── styles/            # CSS modules
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
- **TypeScript**: Strict mode, ESLint configured
- **Commits**: Conventional Commits format
- **Tests**: Minimum 80% coverage for new code

---

## 🔄 CI/CD Pipeline

GitHub Actions automatically runs on pushes and pull requests:

1. ✅ **Backend Tests**: Run pytest suite
2. ✅ **Frontend Tests**: Run npm test
3. ✅ **Linting**: Code quality checks
4. ✅ **Build**: Production build verification
5. 🚀 **Deploy**: Automatic deploy to production (on main branch)

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


