# Insurance Management System

Full-stack foundation for the insurance management system.

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- DevOps: Docker Compose

## Run With Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## Backend Local Development

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://insurance_user:insurance_password@localhost:5432/insurance_app"
uvicorn app.main:app --reload
```

## Frontend Local Development

```powershell
cd web
npm install
npm run dev
```

## Database Migrations

Run migrations from the API container:

```powershell
docker compose exec api alembic revision --autogenerate -m "initial foundation"
docker compose exec api alembic upgrade head
```

No business tables are included in Phase 1, so the first generated migration may be empty until domain models are added.
