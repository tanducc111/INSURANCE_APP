# Insurance Management System

Full-stack insurance management system with FastAPI, PostgreSQL, Next.js App Router, TypeScript, Tailwind CSS, JWT auth, RBAC, dashboards, claims, chat, appointments, and a document-grounded RAG chatbot.

## Main Features

- Authentication, JWT sessions, role-based access control
- Admin user, employee, customer, assignment, and subscription management
- Insurance package, process, and step management
- Customer incident and claim reporting
- Employee claim review and follow-up notes
- Customer-employee REST polling chat
- Appointment booking and employee appointment management
- Admin, employee, and customer dashboards
- Admin document upload and customer chatbot that answers only from uploaded company documents

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: Next.js App Router, TypeScript, Tailwind CSS, Recharts
- DevOps: Docker Compose
- RAG fallback: local keyword-vector retrieval from uploaded PDF/TXT/Markdown documents

## Environment

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Important local values:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
EMBEDDING_PROVIDER=local
RAG_MIN_SCORE=0.08
RAG_TOP_K=4
```

## Run With Docker

Rebuild after dependency changes:

```powershell
cd C:\Projects\INSURANCE_APP
docker compose down
docker compose build --no-cache api
docker compose up --build
```

In a second terminal, apply migrations and seed demo data:

```powershell
cd C:\Projects\INSURANCE_APP
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

Open:

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## Demo Accounts

The seed command is idempotent and resets these demo passwords on each run:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@insurance.local` | value of `SEED_ADMIN_PASSWORD` in `.env` |
| Employee | `employee@insurance.local` | `11111111` |
| Customer | `customer@insurance.local` | `11111111` |

With the checked-in `.env.example`, the admin password is `11111111`.

Seed also creates:

- Demo employee profile
- Demo customer profile
- Demo insurance package
- Demo customer assignment
- Demo active subscription

## Backend Local Development

```powershell
cd C:\Projects\INSURANCE_APP\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://insurance_user:insurance_password@localhost:5432/insurance_app"
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

## Frontend Local Development

```powershell
cd C:\Projects\INSURANCE_APP\web
npm install
npm run dev
```

## Database Migrations

Run migrations from the API container:

```powershell
docker compose exec api alembic upgrade head
```

Create a new migration after model changes:

```powershell
docker compose exec api alembic revision --autogenerate -m "describe change"
```

Migration phases:

- Phase 2: auth, RBAC, login history, activity logs
- Phase 3: insurance packages, processes, process steps
- Phase 4: employees, customers, assignments, follow-up notes
- Phase 5: customer subscriptions and dashboards
- Phase 6: claims and claim attachments
- Phase 7: chat rooms, chat messages, appointments
- Phase 8: RAG documents and document chunks

## Tests And Checks

Backend:

```powershell
cd C:\Projects\INSURANCE_APP
docker compose exec api pytest
docker compose exec api python -m compileall -q app alembic
```

Frontend:

```powershell
cd C:\Projects\INSURANCE_APP\web
npm install
npm run type-check
```

Docker Compose config:

```powershell
cd C:\Projects\INSURANCE_APP
docker compose --env-file .env.example config --quiet
```
