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

In a second terminal, apply migrations and seed the first admin:

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

Open:

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

Default local admin from `.env.example`:

- Email: `admin@insurance.local`
- Password: `ChangeMe123!`

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
docker compose exec api alembic upgrade head
```

Phase 3 adds the insurance package, process, and process step tables through the latest Alembic migration.
Phase 4 adds employee, customer, assignment, and follow-up note tables through the latest Alembic migration.
Phase 5 adds customer insurance subscriptions and dashboard statistics through the latest Alembic migration. The web app now depends on Recharts for dashboard charts, so run `npm install` in `web/` after pulling these changes.
Phase 6 adds incident and claim report tables, role-protected claim APIs, and claim dashboard statistics through the latest Alembic migration.
Phase 7 adds customer-employee chat rooms, chat messages, appointments, and role-protected REST polling APIs through the latest Alembic migration.
Phase 8 adds uploaded company documents, document chunks, PDF/TXT/Markdown ingestion, local retrieval fallback, and a customer chatbot that only answers from uploaded company documents.

Create a new migration after model changes:

```powershell
docker compose exec api alembic revision --autogenerate -m "describe change"
```
