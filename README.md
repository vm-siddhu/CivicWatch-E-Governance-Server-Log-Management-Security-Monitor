# CivicWatch · Server Log Management System

A clean, functional Django web application for server log management, automated content classification, and incident alerting. Developed as a college project to demonstrate practical server monitoring, log ingestion, search and filtering, and role-based access control.

---

## Key Features

1. **Simple Dashboard Overview**: Displays basic statistics (Total Logs, Info, Warnings, and Errors) alongside 7-day activity and log level distribution charts.
2. **Add & Store New Logs**: Easy web form to submit application events with optional parameters (IP address, status code).
3. **Automated Content Classification**: Analyzes message keywords (`error`, `failed`, `timeout`, `warning`, `login`, etc.) and automatically classifies logs into `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
4. **Critical Error Highlighting**: Visual red badges and row highlights for immediate issue visibility.
5. **Incident Notifications**: Important events (such as repeated failed logins or server crashes) automatically generate notifications that can be reviewed and marked as resolved.
6. **Search & Multi-Filtering**: Search logs by keyword or application, filter by log level (`INFO`, `WARNING`, `ERROR`, `CRITICAL`), or filter by date range.
7. **Role-Based Access Control**:
   - **Regular User**: View dashboard, search logs, add new logs, and view notifications.
   - **Administrator**: Full access to delete logs, resolve notifications, configure alert thresholds, and export CSV reports.
8. **Demo & Testing Tools**: Built-in button in Settings to seed realistic sample logs with mixed levels for live demonstrations.

---

## Project Structure

```
DjangoProject/
├── config/              # Django project settings and root URLs
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
├── logs/                # Main application
│   ├── models.py        # LogEntry, Alert (Notifications), and Configuration models
│   ├── views.py         # Dashboard, All Logs, Add Log, Notifications, and Settings
│   ├── forms.py         # Registration and Log Entry forms
│   ├── classifier.py    # Local keyword and status code classification engine
│   ├── services.py      # Sanitization, threat detection, and storage
│   ├── permissions.py   # Admin and user access decorators
│   └── urls.py          # App routes
├── templates/
│   ├── base.html        # Clean minimal layout with responsive sidebar
│   ├── logs/
│   │   ├── dashboard.html      # Overview, stat cards, charts, and recent activity
│   │   ├── log_list.html       # All logs table with search, filter, and pagination
│   │   ├── add_log.html        # Simple form to record new server events
│   │   ├── log_detail.html     # Detailed log inspection card
│   │   ├── notifications.html  # Incident notifications and resolution
│   │   └── settings.html       # System diagnostic info and demo utilities
│   └── registration/
│       ├── login.html          # Clean sign in form
│       └── register.html       # Account registration with Admin / User role selection
├── static/              # CSS stylesheets and Chart.js integration
│   └── app.css
└── manage.py
```

---

## How to Run the Project Locally

### 1. Prerequisites
- Python 3.11 or newer

### 2. Setup Virtual Environment & Dependencies
```powershell
# Open terminal in project folder
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Initialize Database & Roles
```powershell
# Run database migrations
python manage.py migrate

# Initialize standard role groups
python manage.py setup_roles

# (Optional) Create superuser admin
python manage.py createsuperuser
```

### 4. Start the Development Server
```powershell
python manage.py runserver
```

Open **`http://127.0.0.1:8000/`** in your browser.

---

## How to Use & Demonstrate

1. **Sign In or Register**:
   - Open `http://127.0.0.1:8000/accounts/register/`.
   - Register a user with the **Administrator** or **Regular User** role.
   - You will be automatically signed in and redirected to the **Dashboard**.

2. **Dashboard**:
   - Inspect the four stat cards (**Total Logs**, **Information**, **Warnings**, **Errors**).
   - View the doughnut chart showing log level breakdown and the 7-day activity line chart.
   - Review recent logs and unresolved notifications.

3. **Add a New Log**:
   - Click **"＋ Add Log"** in the topbar or sidebar.
   - Select an application (e.g. *Student Portal* or *Database Server*).
   - Enter a message (e.g. `Database connection pool timeout: connection refused`).
   - Leave Log Level on **Auto-classify** (or pick a level manually).
   - Click **Record and Classify Log**. The system classifies the event as `CRITICAL` or `ERROR` and redirects you to the log explorer.

4. **Search and Filter**:
   - Go to **All Logs** in the sidebar.
   - Type a keyword in the search bar or select a log level (`ERROR`, `WARNING`, `INFO`).
   - Use the date pickers to filter logs by date.
   - Click **Export CSV** to download a spreadsheet report of the filtered logs.

5. **Notifications**:
   - Open **Notifications** in the sidebar.
   - Review active system alerts generated by critical events.
   - Click **Mark as Resolved** to clear an alert.

6. **Settings & Demo Utilities**:
   - Go to **Settings** in the sidebar.
   - Click **"Generate Sample Demo Logs"** to quickly populate the database with 10 realistic logs for your presentation.
   - Administrators can also change the failed login attempt threshold or click **"Clear All Logs"** to reset the demo.

---

## Log Ingestion REST API (Optional)

Connected external applications can also push logs programmatically via HTTP:

- **Endpoint**: `POST /api/logs/ingest/`
- **Header**: `X-Log-Token: dev-ingest-token`
- **Content-Type**: `application/json`

Example in PowerShell:
```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/logs/ingest/" -Headers @{"X-Log-Token"="dev-ingest-token"} -ContentType "application/json" -Body '{"source_application":"Student Portal","message":"Student fees payment completed successfully","status_code":200}'
```
