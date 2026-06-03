# Insurance Management System

Insurance Management System is a full-stack insurance operations platform for three user roles: Admin, Employee, and Customer. It supports insurance package management, customer and employee management, care assignments, subscriptions, claim reports, claim evidence uploads, appointments, customer-employee chat, dashboards, and a Graph RAG AI assistant powered by internal company documents.

The project is designed as a modern SaaS-style insurance management system with clear RBAC, realistic demo data, a Vietnamese end-user interface, and a maintainable full-stack architecture.

## Main Features

### Admin

- Manage users, roles, and account status.
- Manage employees and customers.
- Assign customers to employees.
- Manage insurance packages and insurance processes.
- Manage customer insurance subscriptions.
- View and manage claim reports.
- View uploaded claim evidence.
- Manage appointments.
- Manage AI documents for Graph RAG.
- View dashboards and operational statistics.
- Review login history and activity logs.

### Employee

- View assigned customers.
- View subscriptions of assigned customers.
- Review and update assigned claim reports.
- View customer-uploaded evidence such as images and PDFs.
- Chat with assigned customers.
- Manage customer appointments.
- Add follow-up notes.
- View productivity-focused dashboard metrics.

### Customer

- View personal profile.
- View own insurance subscriptions.
- Report incidents and create claim reports.
- Upload claim evidence such as accident photos, hospital invoices, repair receipts, and PDFs.
- Track claim status.
- Chat with assigned employee.
- Book appointments.
- Ask the AI insurance assistant questions based on internal company documents.

## Tech Stack

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, Recharts, Lucide React
- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL
- Authentication: JWT, Role-Based Access Control
- AI: Gemini API, Graph RAG, PDF ingestion, local retrieval fallback
- DevOps: Docker Compose

## Project Architecture

```text
INSURANCE_APP/
+-- api/
|   +-- app/
|   |   +-- api/routers/        # FastAPI routers
|   |   +-- core/               # configuration, security, auth dependencies
|   |   +-- db/                 # database session and seed data
|   |   +-- models/             # SQLAlchemy models
|   |   +-- repositories/       # database query layer
|   |   +-- schemas/            # Pydantic schemas
|   |   +-- services/           # business logic
|   |   +-- utils/              # shared helpers
|   +-- alembic/                # database migrations
|   +-- uploads/                # local development upload storage
+-- web/
|   +-- app/                    # Next.js routes
|   +-- components/             # reusable UI components
|   +-- hooks/                  # auth and role hooks
|   +-- lib/                    # formatters, labels, auth storage
|   +-- services/               # API clients
|   +-- types/                  # TypeScript types
+-- docs/                       # demo documents and PDF samples
+-- docker-compose.yml
+-- README.md
```

## System Modules

- Auth/RBAC: login, JWT, ADMIN/EMPLOYEE/CUSTOMER role permissions.
- Insurance management: insurance packages, insurance processes, and process steps.
- Customer and employee management: employee records, customer records, assignments, follow-up notes.
- Subscriptions: customer insurance policies, policy status, payment status.
- Claims: incident reports, claim review workflow, employee review notes.
- Claim attachments: local image/PDF upload and preview for claim evidence.
- Chat: customer-employee chat using REST polling.
- Appointments: customer booking, employee review, admin overview.
- Dashboards: role-specific operational metrics.
- Graph RAG chatbot: AI assistant that answers only from uploaded internal documents.
- Audit: login history and activity logs.

## Setup

Create the environment file:

```powershell
cd C:\Projects\INSURANCE_APP
Copy-Item .env.example .env
```

Start the full stack:

```powershell
docker compose up --build
```

In a second terminal, run migrations and seed demo data:

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed --reseed
```

Access the application:

- Web app: http://localhost:3000
- API health check: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

## Demo Accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@insurance.local` | `11111111` |
| Employee | `nhanvien001@insurance.local` | `11111111` |
| Customer | `customer001@customer.insurance.local` | `11111111` |

## Useful Commands

Run backend tests:

```powershell
docker compose exec api pytest
```

Validate Docker Compose configuration:

```powershell
docker compose --env-file .env.example config --quiet
```

Run the frontend locally:

```powershell
cd C:\Projects\INSURANCE_APP\web
npm install
npm run dev
```

Run TypeScript checks:

```powershell
cd C:\Projects\INSURANCE_APP\web
npm run type-check
```

Clean demo data while keeping the admin account:

```powershell
docker compose exec api python -m app.db.seed --clean
```

Clean and recreate all demo data:

```powershell
docker compose exec api python -m app.db.seed --reseed
```

## Environment Variables

Do not commit real secret values to the repository.

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string for the backend |
| `SECRET_KEY` | JWT signing secret |
| `JWT_ALGORITHM` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes |
| `SEED_ADMIN_EMAIL` | Admin email used by the seed script |
| `SEED_ADMIN_PASSWORD` | Admin password used by the seed script |
| `GEMINI_API_KEY` | Gemini API key |
| `GEMINI_MODEL` | Gemini model, default `gemini-1.5-flash` |
| `AI_PROVIDER` | AI provider, currently configured for `gemini` with local fallback |
| `RAG_TOP_K` | Number of top document chunks for retrieval fallback |
| `RAG_MIN_SCORE` | Minimum similarity score for considering a chunk relevant |
| `RAG_MAX_CHUNKS_PER_DOCUMENT` | Maximum chunks processed per document, default `80` |
| `RAG_ENTITY_EXTRACTION_BATCH_SIZE` | Number of chunks processed per entity extraction batch |
| `RAG_PROCESSING_MODE` | Document processing mode, default `background` |
| `DOCUMENT_UPLOAD_DIR` | Local storage directory for uploaded PDF/TXT/Markdown documents |
| `CLAIM_UPLOAD_DIR` | Local storage directory for claim evidence uploads |
| `CLAIM_UPLOAD_MAX_BYTES` | Maximum claim attachment size per file |

## Graph RAG Chatbot

The AI assistant is designed to answer customer questions only from uploaded internal company documents. It must not answer from general model knowledge.

Document ingestion flow:

1. Admin uploads a PDF, TXT, or Markdown document in the AI Documents page.
2. The API stores the file, creates a document record, and returns immediately to avoid upload timeout.
3. FastAPI BackgroundTasks processes the document in the background with one of these statuses: `uploaded`, `processing`, `completed`, or `failed`.
4. The backend extracts text and page count from the document.
5. The system chunks the document while preserving headings, numbered sections, bullet lists, and table-like blocks.
6. Duplicate chunks are skipped.
7. Graph RAG ingestion extracts entities and relationships from chunks.
8. Document chunks, entities, relationships, and ingestion metrics are stored in PostgreSQL.
9. The chatbot retrieves only documents with `processing_status = completed`.
10. The customer asks a question in the AI assistant page.
11. The system classifies the query before retrieval.
12. Retrieval uses chunk similarity, matched entities, and graph relationships.
13. Gemini receives only the retrieved company-document context.
14. If the context is insufficient, the chatbot refuses politely.

Unsupported or low-confidence questions return:

```text
Xin lỗi, tôi chỉ có thể trả lời các câu hỏi liên quan đến tài liệu bảo hiểm nội bộ đã được công ty tải lên. Vui lòng đặt câu hỏi về quyền lợi bảo hiểm, hợp đồng, hồ sơ bồi thường hoặc quy trình xử lý.
```

Questions outside uploaded company knowledge return:

```text
Xin lỗi, thông tin này chưa có trong tài liệu nội bộ của công ty. Vui lòng liên hệ nhân viên phụ trách để được hỗ trợ thêm.
```

If `GEMINI_API_KEY` is not configured, the system still uses a safe local fallback for demo retrieval, but answer quality will be simpler.

## Graph RAG Query Understanding

Before retrieval, customer questions are classified as:

- `insurance_knowledge`
- `claim_process`
- `contract_information`
- `appointment_support`
- `unsupported`

The retrieval service calculates:

- `entity_match_score`
- `relationship_match_score`
- `chunk_similarity_score`
- final confidence score from `0.0` to `1.0`

If confidence is below `0.55`, Gemini is not called and the assistant returns the unsupported-scope response.

Current retrieval limits:

- Top chunks: `3`
- Top relationships: `10`

## Claim Attachment Flow

Customers can upload claim evidence when reporting an incident, including:

- Hospital invoices
- Accident photos
- Repair receipts
- Garage invoices
- Discharge papers or related medical documents

Upload rules:

- Supported formats: JPG, PNG, WEBP, PDF
- Maximum file size: 5MB per file
- Local development storage: `api/uploads/claims/`
- Employees and admins can view uploaded evidence in the claim review screen.
- Customers can delete attachments only while the claim is still pending or needs more documents.

## Demo Data

The `--reseed` command creates realistic Vietnamese demo data:

- 15 employees
- 80 customers
- 12 insurance packages
- Insurance processes and process steps
- 120 insurance subscriptions
- 60 claim reports
- 40 appointments
- Demo chat rooms and messages
- Customer follow-up notes
- Login history and activity logs
- RAG documents and document chunks

## Manual Smoke Test

1. Log in as a customer.
2. Open the incident report page.
3. Select an insurance subscription.
4. Enter incident information.
5. Upload one image and one PDF.
6. Submit the claim.
7. Open the claim detail page and verify attachment previews.
8. Log in as an employee.
9. Open the claim review page.
10. Select the claim and verify the customer evidence.
11. Open the AI insurance assistant and ask a question related to uploaded internal documents.

## Screenshots

Coming soon.

## Roadmap

- WebSocket-based real-time chat.
- Cloud upload storage with S3 or Cloudinary.
- Email notifications for appointments, claims, and subscriptions.
- Advanced analytics dashboards.
- Production deployment with Nginx and HTTPS.
- pgvector for stronger semantic retrieval.
- Advanced audit logs and report exports.

## Security Notes

- Do not commit `.env`.
- Do not commit user-uploaded files.
- Change `SECRET_KEY` before production deployment.
- Do not use demo passwords in production.
- Configure CORS for production domains.

## License / Author

Author: **Pham Tan Duc**
