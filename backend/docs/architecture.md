# Project Kavach - Backend Architecture

## Overview

Project Kavach is an Industrial Edge AI Monitoring Platform.

The backend receives machine learning predictions from the Edge AI inference service, stores them in PostgreSQL, exposes REST APIs for dashboard consumption, and pushes real-time updates to connected clients using WebSockets.

The backend follows a layered architecture to maintain separation of concerns and scalability.

---

# High Level Architecture

```text
STM32 Sensors
      │
      ▼
Edge AI Inference Service
      │
      ▼
POST /api/v1/internal/predictions
      │
      ▼
FastAPI Backend
      │
      ├── API Layer
      ├── Service Layer
      ├── Repository Layer
      ├── WebSocket Layer
      │
      ▼
Neon PostgreSQL
      │
      ▼
React Dashboard
```

---

# Backend Layers

```text
Routes (API Layer)
        │
        ▼
Services (Business Logic)
        │
        ▼
Repositories (Database Access)
        │
        ▼
Database (PostgreSQL)
```

---

## API Layer

Location:

```text
app/api/v1/endpoints/
```

Responsibilities:

- Receive HTTP requests
- Validate request schemas
- Call service methods
- Return API responses

Examples:

- Health Endpoint
- Prediction Endpoint
- Dashboard Endpoint
- Ingestion Endpoint

The API layer should not contain business logic or database queries.

---

## Service Layer

Location:

```text
app/services/
```

Responsibilities:

- Business logic
- Data validation
- Workflow orchestration
- WebSocket event triggering

Current Services:

- PredictionService

Example Flow:

```text
Request
   │
   ▼
PredictionService
   │
   ▼
Repository
```

---

## Repository Layer

Location:

```text
app/repositories/
```

Responsibilities:

- CRUD operations
- Database queries
- Pagination
- Aggregations

Current Repository:

- PredictionRepository

Example:

```text
PredictionService
        │
        ▼
PredictionRepository
        │
        ▼
PostgreSQL
```

---

## Database Layer

Technology:

- PostgreSQL (Neon)

Current Table:

### predictions

| Field | Type |
|---------|---------|
| id | UUID |
| fault_label | String |
| confidence | Float |
| probabilities_json | JSON |
| prediction_timestamp | Timestamp |
| created_at | Timestamp |
| updated_at | Timestamp |

Purpose:

Store ML prediction history for dashboard visualization and analytics.

---

# Current Backend Flow

## Prediction Ingestion Flow

```text
Edge AI Model
      │
      ▼
POST /internal/predictions
      │
      ▼
PredictionService
      │
      ▼
PredictionRepository
      │
      ▼
PostgreSQL
      │
      ▼
WebSocket Broadcast
```

---

## Dashboard Data Flow

```text
React Dashboard
      │
      ▼
REST API Request
      │
      ▼
Prediction Endpoint
      │
      ▼
PredictionService
      │
      ▼
PredictionRepository
      │
      ▼
Database Response
      │
      ▼
Frontend
```

---

# Real-Time Communication

## WebSocket Endpoint

```text
/api/v1/ws
```

Purpose:

Provide real-time prediction updates without page refresh.

---

## Event Flow

```text
New Prediction
      │
      ▼
Database Save
      │
      ▼
PREDICTION_CREATED Event
      │
      ▼
WebSocket Broadcast
      │
      ▼
Connected React Clients
```

---

## Current Event

### PREDICTION_CREATED

```json
{
  "event": "PREDICTION_CREATED",
  "data": {
    "id": "uuid",
    "fault_label": "bearing_fault_near",
    "confidence": 0.92
  }
}
```

Frontend Usage:

- Update latest prediction card
- Update dashboard statistics
- Update charts
- Show fault notification if machine state is unhealthy

---

# Project Structure

```text
app/
│
├── api/
│   └── v1/
│       ├── endpoints/
│       └── router.py
│
├── core/
│   ├── config.py
│   ├── logging.py
│   └── exceptions.py
│
├── database/
│   ├── session.py
│   └── init_db.py
│
├── models/
│
├── repositories/
│
├── schemas/
│
├── services/
│
├── websocket/
│   ├── manager.py
│   ├── router.py
│   └── events.py
│
└── main.py
```

---

# Current Implemented Features

✅ Health Check API

✅ Prediction Ingestion API

✅ Latest Prediction API

✅ Prediction History API

✅ Dashboard Summary API

✅ Fault Distribution API

✅ PostgreSQL Persistence

✅ WebSocket Real-Time Updates

---

# Planned Features

- API Key Authentication
- Telemetry Module
- Alert Module
- Production Deployment

---

# Design Principles

- Layered Architecture
- Separation of Concerns
- Service-Oriented Business Logic
- Repository Pattern
- Real-Time Event Driven Updates
- Environment-Based Configuration
- Database Agnostic Design
- Frontend Independent APIs