# Kavach frontend

React operator dashboard for the Kavach FastAPI backend. This folder is self-contained; it does not modify `backend/` or `EdgeAI/`.

## Run locally

1. Start the backend on port `8000`.
2. From this directory:

```bash
npm install
npm run dev
```

The Vite dev server (port `5173`) proxies `/api` and WebSocket traffic to `http://localhost:8000`.

Optional: copy `.env.example` to `.env` and set `API_BASE_URL` if you want to call the backend without the proxy.

## Screens

- **Overview** — dashboard summary, latest prediction, fault distribution, prediction stats
- **Predictions** — paginated history with `fault_label` filter
- **Alerts** — filters, acknowledge, resolve, and alert detail
- **System** — health check and latest stored prediction

Live updates come from `ws://<host>/api/v1/ws` (`PREDICTION_CREATED`, `alert`, `alert_updated`).
