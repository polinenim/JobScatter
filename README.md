# JobScatter AI

JobScatter AI is a Finland-focused job intelligence application for discovering early-career technology opportunities.

## Prerequisites

- Docker Desktop with Docker Compose
- Node.js 20+
- Python 3.11+

## Run with Docker

1. Copy `.env.example` to `.env`.
2. Start the services:

```powershell
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend health: http://localhost:8000/health
- PostgreSQL: localhost:5432
- n8n (local development): http://localhost:5678

Stop services with `docker compose down`. Add `-v` only when you intentionally want to delete the local database volume.
The n8n local data is stored in the `n8n_data` Docker volume.

### n8n API health workflow

Open http://localhost:5678, sign in with the local n8n owner account, and open
`JobScatter API Health Check` from the Workflows view. Select **Execute Workflow**
to run the Manual Trigger -> JobScatter API Health check. The HTTP Request node uses
`http://backend:8000/health`, which is the Compose service address from inside n8n.

## Run services locally

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

When running outside Docker, set `DATABASE_URL` to a reachable PostgreSQL instance. The backend health endpoint reports database connectivity.

## Source Registry

The source registry exposes the source configuration and operational status record through the backend API:

- `POST /sources` creates a source record.
- `GET /sources` lists registered sources.
- `GET /sources/{source_id}` retrieves one source.
- `PATCH /sources/{source_id}` updates configuration or operational status.
- `DELETE /sources/{source_id}` removes a source record.

The registry stores source configuration and operational status. Source-specific behavior belongs in the corresponding Source Adapters.

## Tests

```powershell
cd backend
pytest

cd ..\frontend
npm install
npm test
npm run build
```

## Configuration

`.env.example` documents shared local defaults. Keep secrets in `.env`; `.env` is ignored by Git. The frontend receives only `NEXT_PUBLIC_API_URL`, while database credentials remain backend-only.

## CI

GitHub Actions runs backend tests, frontend tests, and the frontend production build on pushes and pull requests. Docker Compose is the supported local integration environment.
