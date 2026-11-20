# CivicWatch · Server Log Management System (React + Django)

A modern, functional server log management system built with a **React** frontend and a **Django REST Framework** backend. Developed as a college assignment project to demonstrate real-time event logging, automated content-based classification, instant notifications for critical incidents, search and filtering, visual dashboards, and role-based access control.

---

## Architecture Overview

- **Frontend**: **React 18 Single Page Application (SPA)** built with Vite.
  - Minimal, modern dashboard UI.
  - Sidebar navigation: **Dashboard**, **All Logs**, **Notifications**, and **Settings**.
  - Interactive SVG charts (7-day activity trend line and log level distribution).
  - Status badges for log severity (`INFO`, `WARNING`, `ERROR`, `CRITICAL`).
  - Search, level filter, date filter, CSV export, and log inspection modals.
- **Backend**: **Django 6 & Django REST Framework**.
  - Full RESTful API for auth, dashboard telemetry, logs, notifications, and settings.
  - Automated content-based classifier (`logs/classifier.py`) analyzing keywords in log messages.
  - Lightweight CORS middleware for local Vite development.
  - Django serves the production-built React SPA directly at `http://127.0.0.1:8000/`.

---

## Project Structure

```
DjangoProject/
├── frontend/             # React SPA (Vite + React 18)
│   ├── src/
│   │   ├── App.jsx       # Main React application (Dashboard, Logs, Notifications, Settings)
│   │   ├── main.jsx      # React DOM entry point
│   │   └── index.css     # Clean, modern dashboard styles
│   ├── dist/             # Production build served directly by Django
│   ├── index.html        # HTML template
│   ├── vite.config.js    # Vite configuration & /api proxy to Django
│   └── package.json
├── config/               # Django project settings
│   ├── settings.py       # Middleware, database, templates, CORS configuration
│   ├── urls.py           # Root routes (serves API and React SPA)
│   └── asgi.py
├── logs/                 # Main Django backend app
│   ├── api.py            # REST API endpoints (Auth, Dashboard, Logs, Notifications, Settings)
│   ├── api_urls.py       # REST API routing (/api/...)
│   ├── models.py         # LogEntry, Alert, and Configuration models
│   ├── classifier.py     # Local keyword and status code classification engine
│   ├── services.py       # Sanitization, threshold alerts, and persistence
│   ├── middleware.py     # Error capture & CORS middleware
│   └── roles.py          # RBAC group initializer
└── manage.py
```

---

## How to Run the Project Locally

### 1. Prerequisites
- Python 3.11 or newer
- Node.js (v18+) and npm *(only needed if you want to rebuild the React frontend)*

---

### Option A: Standard One-Command Run (Recommended)
The React frontend is already pre-built inside `frontend/dist/`. Django serves it directly on `http://127.0.0.1:8000/` without needing a separate Node process!

```powershell
# 1. Activate virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install Python requirements
pip install -r requirements.txt

# 3. Apply database migrations & set up roles
python manage.py migrate
python manage.py setup_roles

# 4. Start the Django server
python manage.py runserver
```

Now open **`http://127.0.0.1:8000/`** in your browser. You will see the React application!

---

### Option B: Frontend Development Mode (with Vite HMR)
If you want to edit React code with instant Hot Module Reloading:

**Terminal 1 (Django Backend):**
```powershell
python manage.py runserver
```

**Terminal 2 (React Vite Dev Server):**
```powershell
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173/`** in your browser. Vite automatically proxies all `/api` requests to Django at `http://127.0.0.1:8000`.

To re-build the frontend for production:
```powershell
npm run build --prefix frontend
```

---

## How to Demonstrate the Project

1. **Sign In or Register**:
   - Click **"Sign In"** or **"Register"** in the topbar.
   - Choose between **Regular User** (view dashboard and search logs) or **Administrator** (manage logs, delete entries, resolve notifications, and clear database).
   - Once submitted, you are signed in and the top bar displays your user profile and role badge.

2. **Dashboard**:
   - Inspect the 4 Stat Cards: **Total Logs**, **Info Logs**, **Warnings**, and **Errors & Critical**.
   - Review the **7-Day Log Activity Trend** line chart and the **Log Level Distribution** bar chart.
   - View the latest classified logs and unresolved alerts.

3. **Add a New Log (Content-Based Classification)**:
   - Click **"＋ Add Log"** in the topbar.
   - Select an application (e.g. *Student Portal* or *Database Server*).
   - Enter a message such as:
     - `Database connection timeout: pool exhausted` $\rightarrow$ classified as **CRITICAL** / **ERROR**.
     - `Login failed for account roll_9021 with invalid password` $\rightarrow$ classified as **WARNING**.
     - `Semester fee payment completed successfully` $\rightarrow$ classified as **INFO**.
   - Leave Log Level on **"⚡ Auto-classify based on content"**.
   - Click **Record & Classify Log**. Notice the success toast showing the assigned level!

4. **All Logs Explorer**:
   - Click **"All Logs"** in the sidebar.
   - Search by keyword (e.g. `timeout`, `Student`, `192.168`).
   - Filter by log level (`ALL`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
   - Filter by date range.
   - Click **"Inspect"** on any row to open the modal showing full metadata, sanitized message, and classification reason.
   - Click **"↓ Export CSV"** to download the filtered table.
   - As an Administrator, click **"Delete"** to remove any entry.

5. **Incident Notifications**:
   - Click **"Notifications"** in the sidebar (note the badge counter for unresolved alerts).
   - Review active incidents generated by critical errors or brute-force attempts.
   - Click **"✓ Mark as Resolved"** to update an alert's status.

6. **Settings & Demo Tools**:
   - Click **"Settings"** in the sidebar.
   - Click **"Generate 10 Sample Logs"** to instantly populate the database with realistic demo records across all levels.
   - As an Administrator, update the failed login attempt threshold or click **"Clear All Logs & Alerts"** to reset the demo.
