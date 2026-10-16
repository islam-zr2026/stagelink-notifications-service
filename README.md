# STAGELINK: Notifications & Communication service

Django REST Framework microservice that stores in-app notifications, shows each user only their own, tracks read state and accepts trusted internal requests. See `service.md` for the full plan.

## Prerequisites
- Python 3.11+
- PostgreSQL with an empty database named `notifications_db`

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit SECRET_KEY and DB_PASSWORD
python manage.py makemigrations api
python manage.py migrate
python manage.py runserver
```

Check it works: open http://127.0.0.1:8000/api/health/ → `{"status": "ok", "service": "notifications"}`.

## Tests
```bash
python manage.py test
```

## Naming conventions
See `project.md` section 7.1 (snake_case, PascalCase, UPPER_SNAKE_CASE, `_private`).
