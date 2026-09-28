# Project Kavach API Contract (V1)

**Version:** v1

**Base URL**

```
/api/v1
```

---

# Authentication

> Not implemented yet.

Future implementation:

```http
X-API-KEY: <your-api-key>
```

---

# Health Module

## GET /health

### Purpose

Check backend availability and status.

### Response

```json
{
  "success": true,
  "message": "Backend is healthy",
  "data": {
    "status": "UP",
    "version": "1.0.0"
  }
}
```

---

# Prediction Module

## POST /internal/predictions

### Purpose

Receive ML prediction from the Edge AI inference service.

### Request Body

```json
{
  "fault_label": "bearing_fault_near",
  "confidence": 0.92,
  "probabilities_json": {
    "healthy": 0.08,
    "bearing_fault_near": 0.92
  }
}
```

### Response

```json
{
  "success": true,
  "message": "Prediction ingested successfully",
  "data": {}
}
```

---

## GET /predictions/latest

### Purpose

Fetch the latest machine prediction.

### Response

```json
{
  "success": true,
  "message": "Latest prediction fetched",
  "data": {
    "id": "uuid",
    "fault_label": "bearing_fault_near",
    "confidence": 0.92,
    "probabilities_json": {},
    "prediction_timestamp": "2026-09-28T13:40:43Z",
    "created_at": "2026-09-28T19:10:46Z"
  }
}
```

---

## GET /predictions

### Purpose

Retrieve prediction history.

### Query Parameters

| Parameter | Type | Description |
|------------|--------|-------------|
| page | integer | Page number |
| size | integer | Records per page |
| fault_label | string | Filter by fault label |

### Response

```json
{
  "success": true,
  "data": {
    "total": 100,
    "page": 1,
    "size": 20,
    "items": []
  }
}
```

---

# Dashboard Module

## GET /dashboard/summary

### Purpose

Provide KPI statistics for the dashboard.

### Response

```json
{
  "total_predictions": 100,
  "healthy_count": 80,
  "fault_count": 20,
  "average_confidence": 0.91,
  "latest_prediction": {}
}
```

---

## GET /dashboard/fault-distribution

### Purpose

Provide fault distribution data for charts.

### Response

```json
{
  "healthy": 80,
  "bearing_fault_near": 20
}
```

---

# Real-Time Updates

## WebSocket Endpoint

```text
ws://<host>/api/v1/ws
```

### Purpose

Push real-time prediction updates to connected frontend clients.

The frontend should maintain a single persistent WebSocket connection.

---

## Event: PREDICTION_CREATED

### Payload

```json
{
  "event": "PREDICTION_CREATED",
  "data": {
    "id": "uuid",
    "fault_label": "bearing_fault_near",
    "confidence": 0.92,
    "probabilities_json": {
      "healthy": 0.08,
      "bearing_fault_near": 0.92
    },
    "prediction_timestamp": "2026-09-28T13:40:43Z",
    "created_at": "2026-09-28T19:10:46Z"
  }
}
```

### Frontend Usage

- Update latest prediction card
- Update dashboard statistics
- Refresh fault distribution chart
- Display warning notification when fault_label != "healthy"

---

# Standard Success Response

```json
{
  "success": true,
  "message": "Request completed successfully",
  "data": {}
}
```

---

# Standard Error Response

```json
{
  "success": false,
  "message": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

---

# HTTP Status Codes

| Code | Meaning |
|--------|----------|
| 200 | Success |
| 201 | Resource Created |
| 400 | Bad Request |
| 404 | Resource Not Found |
| 500 | Internal Server Error |

---

# Current Scope (V1)

### Implemented

- Health Check API
- Prediction Ingestion API
- Prediction History API
- Latest Prediction API
- Dashboard Summary API
- Fault Distribution API
- WebSocket Real-Time Updates
- PostgreSQL Persistence

### Planned

- API Key Authentication
- Telemetry Module
- Alert Module

### Out of Scope (V1)

- Recommendation Workflow
- Security Events
- Alert Resolution System
- Multi-User Roles & Permissions