# AtomQuest: Enterprise Goal & Performance Portal
## Hackathon Architecture & System Flow Specification

**AtomQuest** is a production-grade, highly resilient Performance Management and Objective Key Result (OKR) portal designed for modern enterprises. Built with a responsive React single-page application and a robust FastAPI Python backend, AtomQuest seamlessly unites organizational goal setting, quarterly achievement check-ins, multi-tiered managerial approval workflows, and automated HR escalations into a single, lightning-fast platform.

---

## 1. High-Level Architectural Topology

AtomQuest is engineered for zero downtime, horizontal scalability, and strict data consistency. The architecture decouples synchronous REST API handling from intensive background reminder sweeps and email notifications using an ACID-guaranteed Transactional Outbox pattern.

```mermaid
graph TD
    %% Frontend Layer
    subgraph Client [Frontend SPA]
        UI[React + Vite UI<br>Tailwind CSS + Recharts + Lucide]
        TQ[TanStack Query Cache<br>staleTime: 5 mins]
        UI <-->|Component Hooks| TQ
    end

    %% API Gateway / Backend Layer
    subgraph Gateway [Backend API Pods]
        FastAPI[FastAPI Web Service<br>Uvicorn + Pydantic v2 + CORSMiddleware]
        CB[503 Circuit Breaker<br>OperationalError / PoolError Handler]
        RBAC[JWT Security & RBAC<br>Stateless Session Fallback]
        FastAPI <--> CB
        FastAPI <--> RBAC
    end

    %% Database & Persistence Layer
    subgraph Persistence [Data & Queue Infrastructure]
        PG[(PostgreSQL Primary<br>Managed Database)]
        Pool[PgBouncer / Pool<br>pool_recycle=1800]
        Redis[(Redis Broker / Cache<br>AOF + RDB Hybrid Persistence)]
    end

    %% Asynchronous Processing Cluster
    subgraph Workers [Asynchronous Processing]
        Worker[Celery Worker Pods<br>task_acks_late=True]
        Beat[Celery Beat Scheduler<br>Daily Reminders & Escalations]
        OutboxRelay[Outbox Relay Poller<br>process-outbox-events]
    end

    %% Client to API
    TQ <===>|HTTPS REST / JSON| FastAPI

    %% Backend to Infrastructure
    CB <===>|SQLAlchemy ORM| Pool
    Pool <===> PG
    RBAC <===>|Token Revocation Check| Redis

    %% Workers Interaction
    Beat -->|Publishes Daily Cron| Redis
    Redis <===>|Consumes Queues| Worker
    Worker -->|Asynchronous SMTP| Email((External SMTP / SMTP Relay))

    %% Outbox Pattern
    OutboxRelay -->|Polls Pending Outbox| PG
    OutboxRelay -->|Dispatches Reliable Messages| Worker

    classDef client fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef gateway fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef storage fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef worker fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;

    class UI,TQ client;
    class FastAPI,CB,RBAC gateway;
    class PG,Pool,Redis storage;
    class Worker,Beat,OutboxRelay worker;
```

---

## 2. Core Workflows & Data Flows

### Flow A: Goal Setting & Submission (The Transactional Outbox Pattern)
When an employee defines their quarterly OKRs, the backend dynamically validates personal weightages against shared organizational goals. Upon reaching precisely 100% personal allocation, the goal sheet is submitted. To guarantee that supervising managers are alerted even during network outages, AtomQuest records an `OutboxEvent` inside the **exact same ACID database transaction** as the sheet status update.

```mermaid
sequenceDiagram
    autonumber
    actor Emp as Employee
    participant UI as React Client
    participant API as FastAPI Web Service
    participant PG as PostgreSQL (ACID)
    participant Relay as Celery Outbox Relay
    participant SMTP as SMTP Mail Server
    actor Mgr as Supervising Manager

    Emp->>UI: Fills personal goals & weights
    UI->>API: PUT /goals/sheet/{id}
    API->>PG: Synchronize & recalculate total_weightage
    PG-->>API: Returns 100% Weightage Confirmation
    UI->>API: POST /goals/submit/{id}
    
    rect rgb(240, 253, 244)
        Note over API, PG: Guaranteed Zero-Loss ACID Transaction
        API->>PG: 1. UPDATE goal_sheets SET status = 'submitted'
        API->>PG: 2. INSERT INTO outbox_events (event_type, payload, status: 'pending')
        API->>PG: 3. COMMIT Transaction
    end

    API-->>UI: 200 OK (Sheet Locked & Submitted)
    UI->>UI: TanStack Query Invalidate & Re-render Dashboard

    loop Every 5 Minutes
        Relay->>PG: SELECT * FROM outbox_events WHERE status = 'pending'
        PG-->>Relay: Returns unnotified goal submissions
        Relay->>PG: UPDATE outbox_events SET status = 'processing'
        Relay->>SMTP: Async dispatch email to Supervising Manager
        SMTP-->>Relay: 250 Message Accepted
        Relay->>PG: UPDATE outbox_events SET status = 'completed'
    end
    SMTP->>Mgr: Delivery: "Action Required: Goal Sheet Submitted"
```

---

### Flow B: Managerial Review, Inline Editing & Approval
Managers access their approval queue containing all direct reports' submitted sheets. Managers can perform inline modifications to target metrics and weights or return sheets for revisions with check-in comments. Once approved, the sheet is permanently locked, and an immutable audit log is generated.

```mermaid
sequenceDiagram
    autonumber
    actor Mgr as Supervising Manager
    participant UI as Manager Dashboard
    participant API as Approvals Router
    participant PG as PostgreSQL Database
    participant Audit as Immutable Audit Table

    Mgr->>UI: Navigates to Team Approvals Queue
    UI->>API: GET /approvals/queue
    API->>PG: Bulk ORM Query: sheets WHERE manager_id = mgr.id
    PG-->>API: Returns submitted goal sheets
    API-->>UI: Serialized GoalSheetResponse list
    Mgr->>UI: Clicks "Inline Edit" on Goal #2 weightage (e.g. 30% -> 40%)
    UI->>API: PUT /approvals/sheet/{sid}/goal/{gid} (InlineEditRequest)
    API->>PG: Update goal target / weight & recalculate sheet
    PG-->>API: Confirmed
    API-->>UI: Updated Goal structure
    Mgr->>UI: Clicks "Approve Goal Sheet"
    API->>PG: UPDATE sheet SET status='approved', is_locked=true
    API->>Audit: INSERT INTO audit_logs (action: 'goal_sheet.approved', old/new state)
    API->>PG: INSERT INTO outbox_events ('notify_goal_approved')
    PG-->>API: COMMIT
    API-->>UI: Approved Confirmation Envelope
```

---

### Flow C: Quarterly Check-ins & Automated Scoring Engine
Throughout the performance cycle, employees submit quarterly check-ins for active goals. The backend actuals engine evaluates numerical target values or timeline completion dates to calculate standardized achievement scores.

```mermaid
sequenceDiagram
    autonumber
    actor Emp as Employee
    participant UI as My Check-ins View
    participant API as Checkins Router
    participant Engine as Score Calculation Engine
    participant PG as Database

    Emp->>UI: Opens current quarter check-in (e.g. Q2)
    UI->>API: GET /checkins/sheet/{id}/quarter/q2
    API->>PG: Eager join goals + achievements
    PG-->>API: Returns active goals and previous check-in milestones
    API-->>UI: Serialized CheckinSheetResponse
    Emp->>UI: Enters actual sales ($85,000) & narrative update
    UI->>API: POST /checkins/goal/{gid}/quarter/q2 (CheckinCreate)
    API->>Engine: Evaluate actual ($85k) vs target ($100k)
    Engine-->>API: Computes score rating (85.0%)
    API->>PG: INSERT INTO goal_achievements (score: 85.0, status: 'completed')
    PG-->>API: COMMIT
    API-->>UI: Updated achievement score
```

---

### Flow D: Automated Reminders & Hierarchical Escalations
To ensure organizational alignment without manual HR chasing, a daily Celery cron worker evaluates active milestone windows and configurable escalation thresholds (e.g., goals unsubmitted after 7 days, check-ins uncompleted after 14 days).

```mermaid
sequenceDiagram
    autonumber
    participant Beat as Celery Beat Scheduler
    participant Worker as Celery Worker Pod
    participant PG as Database & Rules Table
    participant Cache as Redis / Local Memory Lock
    participant SMTP as SMTP Relay

    Note over Beat: 09:00 AM Daily UTC
    Beat->>Worker: Dispatch run_escalations() task
    Worker->>PG: SELECT * FROM escalation_rules WHERE is_active = true
    PG-->>Worker: Rules (e.g. 'checkin_not_done' > 14 days)
    Worker->>PG: Bulk map active employees and managers
    PG-->>Worker: Employee & Manager hierarchy dictionaries
    
    loop For each overdue employee
        Worker->>Cache: _acquire_lock("escalate:checkin:emp:102:q2", ttl=259200)
        alt Redis is Online
            Cache-->>Worker: Lock Acquired in Redis (returns True)
        else Redis is Offline / Unreachable
            Cache-->>Worker: Logs warning, acquires lock in local in-memory dict (returns True)
        end

        Worker->>SMTP: Dispatch Employee Warning Email
        Worker->>SMTP: Dispatch Supervising Manager Alert Email
        Worker->>SMTP: Dispatch HR Department Escalation Notice
    end
```

---

## 3. Key Technical Innovations & Hackathon Showpieces

### 1. Enterprise Resiliency & Self-Healing Architecture
- **Zero-Crash Database Reconnection**: The database connection engine is configured with `pool_pre_ping=True` and `pool_recycle=1800`. If cloud load balancers or database failovers drop TCP sockets, stale connections are automatically discarded before executing queries.
- **503 Graceful Degradation Circuit Breaker**: If the managed PostgreSQL instance undergoes automated maintenance or failover, custom exception handlers (`OperationalError`, `PoolError`) immediately intercept failures and return HTTP 503 `Service Temporarily Unavailable` with `Retry-After: 30` headers. The frontend TanStack Query client intercepts this, displays an unobtrusive "Reconnecting" banner, and allows users to continue browsing cached data without UI freezing or 500 error screens.
- **Stateless Authentication Fallback**: Redis is utilized for high-speed JWT token revocation blacklisting. If Redis goes offline, `try...except` wrappers catch cache exceptions and seamlessly fallback to stateless cryptographic verification of short-lived JWT signatures, keeping user sessions active without interruption.

### 2. Guaranteed Zero-Loss Asynchronous Queue (Transactional Outbox)
Standard background task queues (`background_tasks.add_task` or direct Celery dispatching) lose data if the worker process crashes or the server restarts immediately after an API call. AtomQuest solves this enterprise challenge by implementing the **Transactional Outbox Pattern**:
- Every critical state change (goal submission, approval, or return) inserts an `OutboxEvent` record into PostgreSQL within the **exact same ACID transaction**.
- If Celery or Redis is offline at the moment of submission, the message remains safely persisted in PostgreSQL.
- A periodic Celery beat poller sweeps pending outbox events every 5 minutes and successfully delivers all queued emails once worker nodes recover.
- Worker tasks utilize late acknowledgements (`task_acks_late=True`) so that if a worker pod is forcibly restarted mid-execution, Redis re-queues the unacknowledged job for another healthy node.

### 3. Extreme Performance Optimization
- **N+1 ORM Query Elimination**: In standard ORM applications, looping through 1,000 employees and querying each manager or goal sheet individually creates severe database bottlenecks during background jobs. AtomQuest's services and Celery reminders utilize upfront bulk SQLAlchemy queries (`User.id.in_()`), eager loading (`joinedload`), and in-memory dictionary mapping (`sheet_map`, `mgr_map`), collapsing thousands of sequential queries into exactly 3 to 4 bulk queries per scheduled job.
- **TanStack Query SPA Optimization**: All frontend dashboard views utilize TanStack React Query with a uniform 5-minute `staleTime`. This eliminates duplicate REST fetching on component re-renders or tab switches, resulting in instantaneous page navigation.

### 4. Rigorous Security & Immutable Audit Trails
- **Cryptographic Security**: Password hashing utilizes `bcrypt` via `passlib`, and API authentication is secured via dual-token (Access + Refresh) JWT architecture with server-side blacklist capability.
- **Role-Based Access Control (RBAC)**: Custom dependency injectors (`require_roles("manager", "admin")`) enforce strict organizational boundaries, ensuring managers can only approve or view goal sheets of their direct reports.
- **Comprehensive Audit Log**: The database maintains an immutable `audit_logs` table. Every modification to a goal sheet or target metric records the exact user UUID, action string, precise timestamp, and JSONB snapshots of the `old_value` and `new_value`, providing perfect compliance and traceability.

---

## 4. Entity-Relationship Schema Summary

```
┌────────────────────────────────────────┐
│               USERS                    │
├────────────────────────────────────────┤
│ id (UUID, PK)                          │
│ email (String, Unique)                 │
│ hashed_password (String)               │
│ full_name (String)                     │
│ role (Enum: employee, manager, admin)  │
│ department_id (FK -> departments)      │
│ manager_id (FK -> users.id)            │
└───────────────────┬────────────────────┘
                    │ 1:M
                    ▼
┌────────────────────────────────────────┐
│             GOAL_SHEETS                │
├────────────────────────────────────────┤
│ id (UUID, PK)                          │
│ employee_id (FK -> users.id)           │
│ cycle_id (FK -> cycles.id)             │
│ status (Enum: draft, submitted...)     │
│ total_weightage (Decimal)              │
│ is_locked (Boolean)                    │
└───────────────────┬────────────────────┘
                    │ 1:M
                    ▼
┌────────────────────────────────────────┐
│                 GOALS                  │
├────────────────────────────────────────┤
│ id (UUID, PK)                          │
│ goal_sheet_id (FK -> goal_sheets.id)   │
│ title, description (String, Text)      │
│ weightage (Decimal)                    │
│ target_value (Decimal)                 │
│ uom_type (Enum: currency, timeline...) │
└───────────────────┬────────────────────┘
                    │ 1:M
                    ▼
┌────────────────────────────────────────┐
│          GOAL_ACHIEVEMENTS             │
├────────────────────────────────────────┤
│ id (UUID, PK)                          │
│ goal_id (FK -> goals.id)               │
│ quarter (Enum: q1, q2, q3, q4)         │
│ actual_value (Decimal)                 │
│ score (Decimal)                        │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│             OUTBOX_EVENTS              │
├────────────────────────────────────────┤
│ id (UUID, PK)                          │
│ event_type (String: notify_submitted...)│
│ payload (JSONB)                        │
│ status (String: pending, completed...) │
│ created_at (DateTime, Indexed)         │
└────────────────────────────────────────┘
```
