---
name: insurance-management-system
description: Build a full-stack insurance company management system with admin, employees, customers, insurance packages, claims, dashboards, role permissions, RAG chatbot from company PDFs, chat, and appointments.
---

# Role

Act as a senior full-stack engineer building an insurance management system.

# Default Stack

Frontend:
- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts

Backend:
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- JWT authentication
- Role-based authorization

AI:
- RAG chatbot from company PDF/Wiki documents
- The chatbot must answer only from provided company knowledge

DevOps:
- Docker
- Docker Compose
- .env.example
- README

# Users

Roles:
- ADMIN
- EMPLOYEE
- CUSTOMER

# Main Features

Admin:
- Manage users
- Create employee/customer accounts
- Reset passwords
- Manage roles and permissions
- View login history and activity logs
- Manage insurance packages
- Manage insurance workflows
- View dashboards and statistics

Employee:
- View assigned customers
- Track customer care
- Review incident/claim reports
- Chat with customers
- Manage appointments
- Add follow-up notes

Customer:
- View profile
- View registered insurance packages
- Report incidents/claims
- Chat with assigned employee
- Book appointments
- Ask chatbot

# Core Modules

- Authentication and authorization
- Insurance package management
- Insurance workflow/process management
- Customer management
- Employee management
- Customer assignment
- Customer insurance subscriptions
- Incident/claim reports
- Chat system
- Appointment scheduling
- Admin dashboard
- Employee dashboard
- Customer dashboard
- RAG chatbot from company PDFs
- Login history
- Activity logs

# Backend Architecture

Use clean architecture:

api/
├── routers/
├── services/
├── repositories/
├── models/
├── schemas/
├── core/
├── db/
└── utils/

Rules:
- Routers only handle HTTP layer
- Services contain business logic
- Repositories handle database queries
- Schemas handle validation
- Models define database tables
- Core contains config, security, auth
- Use dependency injection
- Use centralized error handling
- Protect APIs by role

# Frontend Architecture

web/
├── app/
├── components/
├── features/
├── hooks/
├── lib/
├── services/
├── types/
└── store/

Rules:
- Use reusable components
- Use dashboard layout by role
- Add loading states
- Add error states
- Add empty states
- Use responsive design
- Keep API calls in services

# Database Tables

Create models for:
- users
- employees
- customers
- insurance_packages
- insurance_processes
- process_steps
- customer_insurance_subscriptions
- claims
- claim_attachments
- customer_assignments
- follow_up_notes
- chat_rooms
- chat_messages
- appointments
- login_history
- activity_logs
- documents
- document_chunks

# API Standards

Always:
- Use RESTful endpoints
- Add pagination for list APIs
- Add search/filter/sort where needed
- Validate inputs
- Return proper HTTP status codes
- Protect endpoints by role
- Add clear error messages

# RAG Chatbot Rules

The chatbot must:
- Answer only from uploaded company PDF/Wiki documents
- Politely refuse if the answer is outside company knowledge
- Support PDF upload and ingestion
- Chunk documents
- Store embeddings
- Retrieve relevant chunks
- Generate answer using retrieved context only

# Development Rules

When implementing:
1. Inspect current structure first.
2. Reuse existing patterns.
3. Avoid unrelated rewrites.
4. Make small safe changes.
5. Explain changed files.
6. Provide commands to run/test.