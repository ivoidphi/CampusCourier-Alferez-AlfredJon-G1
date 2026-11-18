# CampusCourier

CampusCourier is a peer-to-peer campus delivery web application built with Django and PostgreSQL. It enables verified students to request item pickups and deliveries across campus buildings while fellow student couriers accept and fulfill those requests.

## Core Features

### Role-Based Access & Dashboards
- **Student Customer (`/dashboard/customer/`):** Displays real-time **Active Requests** and **Completed Deliveries** counts, the latest five delivery requests, and quick actions to create or manage requests.
- **Student Courier (`/dashboard/courier/`):** Displays **Open Campus Jobs**, **Active Deliveries**, and **Completed Deliveries** counts alongside active claimed deliveries with one-click status updates.
- **Admin (`/dashboard/admin/` & `/django-admin/`):** Verifies registered student accounts and manages users and delivery records.

### Delivery Request & Fulfillment Workflow
- **Customers** can create delivery requests (item description, pickup location, drop-off location, delivery fee, and optional notes), view request details, and edit or delete requests while their status is **Pending**.
- **Couriers** can browse open **Pending** requests from other users (`/deliveries/available/`), claim jobs, and progress deliveries through **Accepted → In Transit → Delivered**.
- **Server-Side Validation:** Enforces positive delivery fees, distinct pickup and drop-off locations, role-based permissions, and valid state transitions.

### Key Routes
- `/` — Role-based dashboard redirect
- `/accounts/register/` & `/accounts/login/` — Student registration and authentication
- `/deliveries/` — User delivery requests and claimed deliveries
- `/deliveries/create/` — Post a new delivery request (Customers)
- `/deliveries/available/` — Browse open campus delivery jobs (Couriers)
- `/django-admin/` — Django administration panel

## Tech Stack
- **Backend:** Python 3.10+, Django
- **Database:** PostgreSQL (Supabase with SSL required)
- **Frontend:** Django Templates, HTML5, CSS3

## Local Setup (Windows PowerShell)

1. **Clone the repository and navigate to the project folder:**
   ```powershell
   git clone https://github.com/ivoidphi/CampusCourier-Alferez-AlfredJon-G1.git
   cd CampusCourier-Alferez-AlfredJon-G1
   ```

2. **Create and activate a virtual environment, then install dependencies:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in your `SECRET_KEY` and PostgreSQL credentials (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`). Keep `.env` private and never commit it to Git.

4. **Apply database migrations and create an admin user:**
   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```powershell
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser. Keep using `127.0.0.1` consistently when submitting forms to avoid stale CSRF cookies.

## Test Accounts

| Role | Username | Password |
| :--- | :--- | :--- |
| **Student Customer** | `StudentCustomer` | `ProjectDevelopment2` |
| **Student Courier** | `StudentCourier` | `ProjectDevelopment2` |
| **Admin** | `Superman` | `123` |

## Running Tests

Run the automated test suite using the project's isolated test database configuration:

```powershell
python manage.py test --settings=campuscourier.test_settings
```