# CampusCourier

CampusCourier is a Django starter for a campus delivery network with Student
Customer, Student Courier, and Campus Admin roles. Public registration creates
unverified student accounts; admins can review accounts in the dashboard or
manage verification in Django admin.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for account registration and sign-in. The Django
administration site is available at `/django-admin/`. Superusers created with
`createsuperuser` receive the Campus Admin role.

SQLite is configured by default so the project runs locally without external
services. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS`
through the environment before deploying. Do not use the development secret or
`DEBUG=true` in production.

The customer and courier dashboards currently contain UI placeholders; delivery
request creation, task acceptance, payments, and verification workflows are
not implemented yet.
