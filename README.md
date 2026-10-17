# STAGELINK: Notifications & Communication service

Django REST Framework microservice that stores in-app notifications, shows each user only their own, tracks read state, and accepts trusted internal requests from other services.

Related documents: `project.md` (whole system), `service.md` (this service's plan), `api_contract.md` (how other services and the frontend use this API).

## Requirements
- Python 3.11 or newer
- PostgreSQL (an empty database named `notifications_db`)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env  (then edit .env)
python manage.py migrate
python manage.py runserver
```

Check it works: open http://127.0.0.1:8000/api/health/ → `{"status": "ok", "service": "notifications"}`.

## Environment variables (`.env`, never committed)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key. Generate one: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `True` for development, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated host names |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | This service's own PostgreSQL database |
| `JWT_ALGORITHM` | `HS256` (shared secret) or `RS256` (public key). Must match Identity & Profiles |
| `JWT_SIGNING_KEY` | HS256: shared secret. RS256: public key in PEM, newlines written as `\n` |
| `JWT_USER_ID_CLAIM`, `JWT_ROLE_CLAIM` | Token claim names (defaults `user_id`, `role`) |
| `INTERNAL_SERVICE_TOKEN` | Secret sent by other services in `X-Service-Token`. Empty = internal endpoint closed |
| `DEV_AUTH_ENABLED` | Development shortcut: trust the `X-User-Id` header. Defaults to the value of `DEBUG`. **Must be off in production** |

## API

Interactive documentation (Swagger UI): http://127.0.0.1:8000/api/docs/ · raw schema: `/api/schema/`.

| Method | URL | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health/` | none | Health check |
| GET | `/api/notifications/` | user JWT | My notifications, newest first, paginated (`?unread=true`, `?page=2`) |
| GET | `/api/notifications/unread-count/` | user JWT | `{"unread_count": N}` |
| PATCH | `/api/notifications/{id}/read/` | user JWT | Mark one notification as read (idempotent) |
| POST | `/api/notifications/read-all/` | user JWT | Mark all my notifications as read |
| POST | `/api/internal/notifications/` | `X-Service-Token` | Create a notification (service to service, deduplicated) |

Details and examples for other services: `api_contract.md`.

## Docker
```bash
cp .env.example .env               # then edit it (DB_PASSWORD is required)
docker compose up --build
```
This starts the service and its own PostgreSQL. The API is then at http://localhost:8004 (docs: http://localhost:8004/api/docs/). Migrations run automatically at start.

Notes:
- Add the service host name to `ALLOWED_HOSTS` in `.env` (for example `localhost,127.0.0.1,notifications`) so other containers can call it.
- In production set `DEBUG=False` (this also turns off the development-only `X-User-Id` shortcut), use strong values for `SECRET_KEY` and `INTERNAL_SERVICE_TOKEN`, and put the real `JWT_*` values from Identity & Profiles.
- The team's shared compose file needs an equivalent `notifications` service with its own database and these environment variables.

## Tests
```bash
python manage.py test
```
Tests use a temporary PostgreSQL test database (the PostgreSQL user needs permission to create databases).

## Project structure
```
config/              settings, root URLs, WSGI/ASGI
api/
  models.py          Notification model
  serializers.py     user view and internal create validation
  views.py           endpoints
  authentication.py  JWT validation (+ development-only header stub)
  permissions.py     service-token permission
  schema.py          OpenAPI descriptions of the auth classes
  tests/             automated tests
```

## Rules
- One database per service; other services' IDs are plain fields, never foreign keys.
- Naming conventions: see `project.md` section 7.1.
- Secrets only in environment variables; `.env` is never committed.
