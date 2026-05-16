# AtomQuest Goal Portal

A comprehensive Goal Setting & Tracking Portal built for corporate goal management with role-based access control, quarterly check-ins, and real-time analytics.

## Quick Start

```bash
docker compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/api/v1/health

## Demo Credentials

| Role     | Email                   | Password    |
|----------|-------------------------|-------------|
| Admin    | admin@atomquest.com     | Admin@123   |
| Manager  | manager@atomquest.com   | Manager@123 |
| Employee | alice@atomquest.com     | Alice@123   |
| Employee | bob@atomquest.com       | Bob@123     |

## Architecture

```

┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Frontend  │────▶│   Backend   │────▶│  PostgreSQL  │
│  React/Vite │     │   FastAPI   │     │    (DB)      │
│  Port 3000  │     │  Port 8000  │     │  Port 5432   │
└─────────────┘     └──────┬──────┘     └──────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis    │
                    │  Port 6379  │
                    └──────┬──────┘
                           │
               ┌───────────┴───────────┐
               │                       │
        ┌──────┴──────┐     ┌─────────┴────────┐
        │   Celery    │     │   Celery Beat    │
        │   Worker    │     │   (Scheduler)    │
        └─────────────┘     └──────────────────┘

```

## Tech Stack

- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Queue**: Celery
- **Container**: Docker Compose

## Features

### Employee

- Create up to 8 goals per cycle with weightage validation (must total 100%)
- Submit goal sheets for manager approval
- Quarterly check-ins with score computation
- View manager feedback

### Manager

- Approval queue for direct reports' goal sheets
- Inline editing of goals during review
- Approve or return sheets with comments
- Team check-in monitoring

### Admin

- Cycle management (create, activate fiscal year cycles)
- Organization-wide completion dashboard
- Achievement reports with CSV/Excel export
- Audit log with filtering
- Shared goal management
- Escalation rule configuration

## Score Engine

| UoM Type | Formula | Example |
|----------|---------|---------|
| Min (Higher is Better) | min(actual/target, 1.0) | Target: 100, Actual: 80 → 0.80 |
| Max (Lower is Better) | min(target/actual, 1.0) | Target: 5, Actual: 3 → 1.00 |
| Timeline | 1.0 if on/before target date, 0.5 if late | — |
| Zero | 1.0 if actual == 0 | Target: 0, Actual: 0 → 1.00 |

## Development

### Backend only

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

See `.env.example` for all configuration options.
