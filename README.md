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
Copy-Item .env.example .env
# Edit .env with your Supabase PostgreSQL connection details and a strong secret.
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for account registration and sign-in. The Django
administration site is available at `/django-admin/`. Superusers created with
`createsuperuser` receive the Campus Admin role.

The application uses PostgreSQL, configured from `.env` (see
[`.env.example`](.env.example)). Use the Supabase session pooler connection
details supplied by your project and keep `.env` private; it is ignored by Git.
PostgreSQL connections require SSL. `DEBUG` defaults to `False`. Set
`ALLOWED_HOSTS` to the hostnames serving the app, and use a strong unique
`SECRET_KEY`. Never commit credentials or enable `DEBUG` in production.

The customer and courier dashboards currently contain UI placeholders; delivery
request creation, task acceptance, and payments are not implemented yet.
Campus Admins can verify students from the Admin dashboard.

Run the automated tests using the isolated in-memory test database:

```powershell
python manage.py test accounts --settings=campuscourier.test_settings
```
