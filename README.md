# MiseOps

Restaurant work orders and kitchen handoffs, from prep to sign-off.

## What is this project used for?

MiseOps helps a restaurant manager organize kitchen preparation, station tasks and service handoffs. Each work order has an owner, quantity, due time, priority and instructions. Teams can see what is queued, being prepared, ready for inspection or closed, instead of tracking work across verbal instructions and scattered messages.

This is a restaurant jobwork application, not a recruitment portal, billing/POS system or food delivery marketplace.

## Features

- Create validated work orders and assign stations and staff.
- Search work and filter by status; export visible records to CSV.
- Enforce Queued → Preparing → Ready → Closed on the server.
- Staff-only authentication and timestamped activity history.
- PostgreSQL storage, database constraints and transactional row locking during transitions.
- Responsive React interface with a separate browser-local preview mode.

## Stack and structure

Python / Django 5.2 / PostgreSQL / React / Vite.

`backend/operations/models.py`: orders and audit events. `api.py`: authentication, validation and transitions. `frontend/src/`: React interface. `docs/`: compiled public preview.

## Run with PostgreSQL

Requires Python 3.11+, Node 20.19+ or 22.12+, Docker Compose (or an existing PostgreSQL server).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PGPASSWORD='choose-a-local-development-password'
docker compose up -d
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver
```

On Windows activate `.venv\Scripts\activate`, and set environment variables with PowerShell (`$env:PGPASSWORD = '...'`). A superuser is a staff user; for other accounts explicitly set `is_staff=True` before using the workspace.

In a second terminal:

```bash
cd frontend
npm ci
VITE_API_MODE=server npm run dev
```

On PowerShell: `$env:VITE_API_MODE='server'; npm run dev`. Open the Vite localhost URL and connect with your staff username and password. Credentials stay in component memory; they are not saved to browser storage. Vite proxies `/api` to Django on port 8000.

Database settings: `PGDATABASE` (default `miseops`), `PGUSER` (default `miseops`), `PGPASSWORD`, `PGHOST`, `PGPORT`, `PGSSLMODE` (default `prefer`, use `require` for a managed TLS database). Set `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and optionally `DJANGO_DEBUG=1` for local diagnostics. Bind PostgreSQL only to localhost for local development.

## Public preview

The `docs/` build runs independently in a browser. It starts with fictional work orders and saves edits in the visitor's local storage. It does not run Django, PostgreSQL or server authentication, and does not represent a client deployment. Open the About dialog for the same provenance note. No customer data or real restaurant integration is included.

To rebuild the browser-local version: unset `VITE_API_MODE`, then `cd frontend && npm ci && npm run build`. A production server build must use `VITE_API_MODE=server npm run build` and be served with `/api` behind the same HTTPS origin.

## API

- `GET /api/orders/` — list, optional `q` and `status`.
- `POST /api/orders/` — create with title, station, assignee, positive integer quantity and timezone-aware due timestamp.
- `POST /api/orders/{id}/transition/` — body `{"status":"preparing"}` (next allowed state only).
- `GET /api/export/` — CSV, optional filters.

All endpoints require HTTP Basic authentication for an active staff account. Use HTTPS outside localhost. This initial scope is one restaurant; every staff account can see all work orders. No tenant isolation or separate station permissions are claimed.

## Validation

```bash
python backend/manage.py test operations
cd frontend && npm ci && npm run build
```

The four backend tests cover access control, invalid quantities, transition rejection, audit history and formula-safe CSV. They passed with the isolated SQLite test override (`TEST_SQLITE=1`). The PostgreSQL integration workflow in `.github/workflows/postgresql.yml` starts PostgreSQL 17, applies migrations and runs the API suite plus PostgreSQL-specific tests for persistence, constraints and concurrent transitions. The CI check result records whether that integration has passed. A local PostgreSQL service is not available in the build container.

Before production: use a secret from your environment, HTTPS, a production WSGI/ASGI server, backup policies, rate limiting and monitored logs. The development server is for local use.
