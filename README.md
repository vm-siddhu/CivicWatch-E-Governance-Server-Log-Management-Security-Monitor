# CivicWatch · E-Governance Server Log Management & Security Monitor

CivicWatch is a centralized, role-based log management and security monitoring platform designed for public sector and institutional digital infrastructure. It provides authenticated log ingestion, privacy-preserving local content classification, automated brute-force and anomaly alerting, immutable audit trails, and an interactive real-time operational dashboard powered by WebSockets.

---

## Table of Contents
1. [Key Features](#key-features)
2. [Architecture & Request Flow](#architecture--request-flow)
3. [User Roles & Access Control (RBAC)](#user-roles--access-control-rbac)
4. [Local Setup & Quick Start](#local-setup--quick-start)
5. [Log Ingestion API Reference](#log-ingestion-api-reference)
6. [Classification & Threat Detection](#classification--threat-detection)
7. [Real-Time WebSocket Streaming](#real-time-websocket-streaming)
8. [Audit Trail & Governance](#audit-trail--governance)
9. [Management Commands](#management-commands)
10. [Environment Variables Reference](#environment-variables-reference)
11. [Production Deployment Controls](#production-deployment-controls)

---

## Key Features

- **Secure Ingest API**: Authenticated HTTP REST endpoint (`POST /api/logs/ingest/`) accepting structured JSON telemetry from connected e-governance services.
- **On-the-Fly Sanitization**: Automated regex filtering redacts passwords, tokens, API keys, and Bearer headers from log messages and query parameters prior to storage.
- **Local Heuristic & Pattern Classifier**: Classifies events across 9 departmental categories and 5 severities without transmitting sensitive civic data to external cloud APIs.
- **Automated Incident & Anomaly Alerting**: Flags `CRITICAL` events, security exploits, and repeated authentication failures (e.g. 5+ failed logins from the same IP within 10 minutes) into actionable incident alerts.
- **Live WebSocket Dashboard**: Interactive dashboard with real-time log activity feeds, severity breakdowns, category distribution charts, and unresolved incident trackers.
- **Self-Service & Admin User Onboarding**: Web UI registration (`/accounts/register/`) with automatic security group assignment, as well as Django CLI superuser provisioning.
- **Institutional Audit Trail**: Captures administrative and authentication actions (logins, log corrections, CSV exports, incident resolutions) for regulatory review.

---

## Architecture & Request Flow

### 1. External Log Ingestion Flow (`POST /api/logs/ingest/`)

```
+-----------------------------------------------------------------------------------+
|                            External Public Application                            |
|          (Student Portal, Tax Filing, Land Records, Transport Gateway)            |
+-----------------------------------------------------------------------------------+
                                          |
                                          | HTTP POST (JSON Payload + X-Log-Token)
                                          v
+-----------------------------------------------------------------------------------+
|                        CivicWatch Ingest API Endpoint                             |
|                                                                                   |
|  1. IngestPermission: Validates 'X-Log-Token' header via constant-time check      |
|  2. Serializer Validation: Validates IP, status code, URL, message length        |
|  3. Redaction Engine: Strips sensitive credentials (password, secret, Bearer)    |
|  4. Local Classifier: Derives Category, Severity, Reason, Confidence              |
|  5. Persistence: Writes to database (LogEntry) with UUID & timestamp              |
+-----------------------------------------------------------------------------------+
        |                                                 |
        | If CRITICAL / SECURITY / Auth Burst             | Async Thread
        v                                                 v
+-----------------------------+           +-----------------------------------------+
|     Alerting Engine         |           |        Channels WebSocket Layer         |
|                             |           |                                         |
| - Creates 'Alert' record    |           | - Broadcasts event to 'log_updates'     |
| - Sends SMTP email alerts   |           | - Dashboard receives live update (UI)   |
+-----------------------------+           +-----------------------------------------+
```

### 2. What an Ingestion Request Contains

| Field | Type | Required | Description |
|---|---|---|---|
| `source_application` | `string(120)` | Optional | Identifier of originating service (e.g., `student-portal`, `tax-filing`). Default: `e-governance`. |
| `event_type` | `string(100)` | Optional | High-level event category (e.g., `auth_event`, `db_query`, `http_request`). |
| `message` | `string(10000)`| **Required** | The log message or error description. |
| `status_code` | `integer` | Optional | HTTP response status (100–599) if representing a web request. |
| `ip_address` | `IPv4/IPv6` | Optional | Client or user IP address associated with the event. |
| `server_ip` | `IPv4/IPv6` | Optional | Internal server or container node IP. |
| `request_url` | `string(2048)`| Optional | HTTP request URL or path. |
| `http_method` | `string(10)` | Optional | HTTP verb (`GET`, `POST`, `PUT`, `DELETE`, etc.). |
| `user_id` | `string(120)` | Optional | Identifier of citizen or officer involved in the event. |
| `severity` | `string` | Optional | Overriding source severity (`INFO`, `WARNING`, `ERROR`, `CRITICAL`). |

### 3. What an Ingestion Response Contains

- **Status**: `HTTP 201 Created`
- **Body**:
  ```json
  {
    "id": "3c80661c-cb4f-407b-9c01-05ff76823ec3",
    "timestamp": "2026-11-20T06:47:07.900198Z",
    "category": "AUTH",
    "severity": "WARNING",
    "classification_reason": "Authentication event keyword"
  }
  ```

---

## User Roles & Access Control (RBAC)

CivicWatch enforces role-based access through Django Groups and custom permission decorators:

| Role | Target Users | Web Capabilities |
|---|---|---|
| **Monitoring Officer** | General security officers, support staff, auditors | View Overview Dashboard, search and filter Server Logs, inspect log details, and view active Alerts. (Read-only access). |
| **System Administrator** | DevOps engineers, senior administrators | All Monitoring Officer privileges, plus: correct AI/rule classifications, ingest manual logs from UI, acknowledge and resolve Alerts, view Audit Trail, and export CSV reports. |
| **Super Administrator** | Platform owners, IT directors | Full system access, Django Admin access (`/admin/`), user and group management, and global alert configuration. |

### How Users Register & Access the System
1. **Self-Service Registration**: Visit `/accounts/register/` to create an officer account. New users are assigned to the `Monitoring Officer` or `System Administrator` group and logged in immediately.
2. **Super Administrator CLI**: Run `python manage.py createsuperuser` in the terminal to initialize an administrative root user.
3. **Role Assignment in Admin**: Superusers can adjust user groups at any time in `http://127.0.0.1:8000/admin/auth/user/`.

---

## Local Setup & Quick Start

### Prerequisites
- Python 3.11 or newer
- PowerShell (Windows) or Bash (Linux / macOS)

### 1. Clone & Set Up Virtual Environment

```powershell
# Clone or navigate into the project directory
cd DjangoProject

# Create and activate Python virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

*(On Linux / macOS, use `python3 -m venv .venv && source .venv/bin/activate`)*

### 2. Configure Environment & Database

```powershell
# Apply database migrations
python manage.py migrate

# Initialize standard RBAC security groups and permissions
python manage.py setup_roles

# (Optional) Seed realistic demo server logs and alerts
python manage.py seed_demo_logs --count 25

# (Optional) Create a superuser for Django Admin
python manage.py createsuperuser
```

### 3. Run the Development Server

```powershell
python manage.py runserver
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser:
- If not logged in, you will be redirected to the secure sign-in portal.
- Click **"Register here"** (or open `/accounts/register/`) to create your officer account.

---

## Log Ingestion API Reference

### Endpoint Details
- **URL**: `/api/logs/ingest/`
- **Method**: `POST`
- **Required Header**: `X-Log-Token: <your-token>`
  > *Note: In local development (`DJANGO_DEBUG=1`), `LOG_INGEST_TOKEN` defaults to `dev-ingest-token` if not explicitly set.*

### Ingest Examples

#### Using PowerShell:
```powershell
$headers = @{
    "X-Log-Token" = "dev-ingest-token"
    "Content-Type" = "application/json"
}

$body = @{
    source_application = "student-portal"
    event_type = "auth_event"
    message = "Login failed for account student_9821 with invalid password"
    status_code = 401
    ip_address = "192.168.1.105"
    request_url = "/api/v1/auth/login"
    http_method = "POST"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/logs/ingest/" -Headers $headers -Body $body
```

#### Using cURL:
```bash
curl -X POST http://127.0.0.1:8000/api/logs/ingest/ \
  -H "X-Log-Token: dev-ingest-token" \
  -H "Content-Type: application/json" \
  -d '{
    "source_application": "tax-portal",
    "event_type": "security_alert",
    "message": "Potential SQL injection attempt detected in search query",
    "status_code": 403,
    "ip_address": "203.0.113.45",
    "request_url": "/citizen/filings?id='\'' OR 1=1--"
  }'
```

#### Using Python (`requests`):
```python
import requests

url = "http://127.0.0.1:8000/api/logs/ingest/"
headers = {
    "X-Log-Token": "dev-ingest-token",
    "Content-Type": "application/json"
}
payload = {
    "source_application": "land-records",
    "event_type": "database_error",
    "message": "Database connection pool exhausted: connection refused",
    "status_code": 500,
    "ip_address": "10.0.4.12"
}

response = requests.post(url, json=payload, headers=headers)
print(response.status_code, response.json())
```

---

## Classification & Threat Detection

CivicWatch processes every message through an offline, deterministic rule classifier (`logs/classifier.py`):

| Category Key | Category Display | Default Severity | Trigger Keywords / Patterns |
|---|---|---|---|
| `SYS_FAILURE` | Critical System Failures | `CRITICAL` | `kernel panic`, `out of memory`, `system failure`, `service unavailable` |
| `DATABASE` | Database Errors | `CRITICAL` | `database connection`, `database unavailable`, `connection refused`, `sql error`, `deadlock` |
| `SECURITY` | Security Threats | `CRITICAL` | `sql injection`, `xss attempt`, `unauthorized access`, `directory traversal`, `brute force`, `suspicious` |
| `AUTH` | Authentication Events | `WARNING` | `login failed`, `authentication failed`, `invalid password`, `login succeeded` |
| `NETWORK` | Network Issues | `ERROR` | `timeout`, `dns failure`, `network unreachable`, `connection reset` |
| `APP_ERROR` | Application Errors | `ERROR` | `exception`, `traceback`, `internal server error`, `unhandled error`, HTTP 5xx |
| `SYS_WARNING`| System Warnings | `WARNING` | `warning`, `deprecated`, `disk space`, `high memory` |
| `ACTIVITY` | User Activities | `INFO` | `created`, `updated`, `deleted`, `exported`, `user action` |
| `GENERAL` | General Information | `INFO` | Default fallback when no specific pattern matches |

### Automated Threat & Alert Conditions
1. **Critical & Security Trigger**: Any event classified with `CRITICAL` severity or `SECURITY` category automatically creates an in-app `Alert`.
2. **Brute Force Detection**: If `AUTH` failure events from the same IP and application exceed the database threshold (default: 5 events within 10 minutes), an incident alert is raised.
3. **Admin Corrections**: If an administrator corrects a classification via the UI (`POST /logs/<id>/correct/`), the original prediction and confidence score are permanently preserved alongside the corrected values, and an audit event is logged.

---

## Real-Time WebSocket Streaming

CivicWatch leverages **Django Channels** and ASGI to push live event cards to the dashboard:
- **WebSocket Route**: `ws://127.0.0.1:8000/ws/logs/`
- **Consumer**: `LogConsumer` (`logs/consumers.py`) validates user session authentication upon connection.
- **Frontend Integration**: `static/app.js` connects to the WebSocket stream and prepends new entries directly into the dashboard's "Recent Activity" table, updating the live heartbeat badge.
- **Development Default**: Uses `channels.layers.InMemoryChannelLayer`. In multi-process production deployments, configure `REDIS_URL`.

---

## Audit Trail & Governance

To ensure institutional compliance and accountability, sensitive operations are automatically recorded into the `AuditEvent` model:

- `login` & `logout`: Logged via Django authentication signals with actor and IP address.
- `failed_login`: Captures invalid login attempts and usernames.
- `user_registered`: Records newly registered officers and their assigned roles.
- `classification_corrected`: Records the administrator, the log ID, and the changes made.
- `alert_acknowledged` & `alert_resolved`: Records the handling officer and incident ID.
- `logs_exported` & `audit_report_exported`: Logs the actor and the number of rows exported to CSV.

Audit reports can be filtered by date range and exported directly to CSV from `/audit/`.

---

## Management Commands

| Command | Purpose | Example |
|---|---|---|
| `setup_roles` | Idempotently creates the baseline RBAC groups (`Super Administrator`, `System Administrator`, `Monitoring Officer`) and attaches model permissions. | `python manage.py setup_roles` |
| `seed_demo_logs` | Generates realistic synthetic e-governance log records across multiple departments, backdates timestamps, and triggers sample alerts for visualization. | `python manage.py seed_demo_logs --count 30` |
| `createsuperuser` | Creates an interactive root administrator with access to the Django administrative site (`/admin/`). | `python manage.py createsuperuser` |

---

## Environment Variables Reference

Configure these settings via your environment or `.env` file:

| Variable | Default Value | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `dev-only-change-this...` | Secret key for cryptographic signing. Must be changed in production. |
| `DJANGO_DEBUG` | `1` | Enable/disable debug mode (`1` for true, `0` for false). |
| `DJANGO_ALLOWED_HOSTS`| `localhost,127.0.0.1,testserver` | Comma-separated list of host/domain names. |
| `LOG_INGEST_TOKEN` | `dev-ingest-token` *(when DEBUG=1)* | Secret authorization token required in the `X-Log-Token` header. |
| `DB_NAME` | `""` *(uses SQLite)* | PostgreSQL database name. If omitted, uses local `db.sqlite3`. |
| `DB_USER` | `""` | PostgreSQL username. |
| `DB_PASSWORD` | `""` | PostgreSQL user password. |
| `DB_HOST` | `localhost` | PostgreSQL database host. |
| `DB_PORT` | `5432` | PostgreSQL database port. |
| `REDIS_URL` | `""` *(uses InMemoryLayer)*| Redis channel layer URL (e.g. `redis://127.0.0.1:6379/1`). Required for multi-worker WebSockets. |
| `ALERT_EMAIL_RECIPIENTS`| `""` | Comma-separated list of emails to notify on critical alerts. |
| `EMAIL_BACKEND` | `console.EmailBackend` | Django email backend (`smtp.EmailBackend` in production). |

---

## Production Deployment Controls

1. **Security Settings**:
   - Set `DJANGO_DEBUG=0` and specify strict `DJANGO_ALLOWED_HOSTS`.
   - Generate a cryptographically strong `DJANGO_SECRET_KEY` and `LOG_INGEST_TOKEN`.
   - Enforce HTTPS with `SECURE_SSL_REDIRECT = True` and secure session/CSRF cookies.
2. **Database & Cache**:
   - Use PostgreSQL (`DB_NAME`, `DB_USER`, `DB_PASSWORD`) with automated point-in-time backups.
   - Run a dedicated Redis instance (`REDIS_URL`) to support multi-process ASGI WebSocket streaming.
3. **ASGI / WSGI Web Servers**:
   - Run behind Daphne or Uvicorn behind a hardened reverse proxy (Nginx or Caddy) handling SSL termination and rate limiting.
4. **Data Retention & Privacy**:
   - Establish periodic archiving or purge policies for `LogEntry` records past statutory retention limits.
   - Institutional audit logs (`AuditEvent`) should be preserved and restricted to authorized oversight officers.
