import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from logs.models import LogEntry
from logs.services import record_log
from logs.roles import ensure_roles_exist

DEMO_EVENTS = [
    {
        "source_application": "student-portal",
        "event_type": "auth_event",
        "message": "Login failed for account student_9821",
        "status_code": 401,
        "ip_address": "192.168.1.105",
        "request_url": "/api/v1/auth/login",
        "http_method": "POST"
    },
    {
        "source_application": "tax-portal",
        "event_type": "security_alert",
        "message": "Potential sql injection attempt detected in search query parameter id=' OR 1=1--",
        "status_code": 403,
        "ip_address": "203.0.113.45",
        "request_url": "/citizen/filings?id=' OR 1=1--",
        "http_method": "GET"
    },
    {
        "source_application": "land-records",
        "event_type": "database_error",
        "message": "Database connection pool exhausted: connection refused by primary replica",
        "status_code": 500,
        "ip_address": "10.0.4.12",
        "request_url": "/api/registry/mutation",
        "http_method": "POST"
    },
    {
        "source_application": "pension-service",
        "event_type": "system_failure",
        "message": "Kernel panic: out of memory while allocating worker thread for batch disbursement",
        "status_code": 503,
        "ip_address": "10.0.8.22",
        "request_url": "/jobs/disburse-monthly",
        "http_method": "POST"
    },
    {
        "source_application": "citizen-identity",
        "event_type": "user_action",
        "message": "New citizen grievance created for civic road repair",
        "status_code": 201,
        "ip_address": "49.36.12.8",
        "request_url": "/portal/grievance/new",
        "http_method": "POST"
    },
    {
        "source_application": "healthcare-registry",
        "event_type": "http_request",
        "message": "Hospital inventory updated for vaccine storage facility #402",
        "status_code": 200,
        "ip_address": "192.168.10.88",
        "request_url": "/supplies/inventory/update",
        "http_method": "PUT"
    },
    {
        "source_application": "tax-portal",
        "event_type": "system_warning",
        "message": "Disk space warning: /var/log filesystem usage exceeded 88%",
        "status_code": 200,
        "ip_address": "10.0.1.5",
        "request_url": "/internal/health",
        "http_method": "GET"
    },
    {
        "source_application": "transport-department",
        "event_type": "network_failure",
        "message": "Network unreachable: timeout connecting to national vehicle registry gateway",
        "status_code": 504,
        "ip_address": "10.0.12.99",
        "request_url": "/rc-status/verify",
        "http_method": "GET"
    },
    {
        "source_application": "student-portal",
        "event_type": "auth_event",
        "message": "Login failed for account student_9821 with invalid password",
        "status_code": 401,
        "ip_address": "192.168.1.105",
        "request_url": "/api/v1/auth/login",
        "http_method": "POST"
    },
    {
        "source_application": "student-portal",
        "event_type": "auth_event",
        "message": "Login failed for account student_9821 with invalid password",
        "status_code": 401,
        "ip_address": "192.168.1.105",
        "request_url": "/api/v1/auth/login",
        "http_method": "POST"
    },
    {
        "source_application": "student-portal",
        "event_type": "auth_event",
        "message": "Login failed for account student_9821 with invalid password",
        "status_code": 401,
        "ip_address": "192.168.1.105",
        "request_url": "/api/v1/auth/login",
        "http_method": "POST"
    },
    {
        "source_application": "student-portal",
        "event_type": "auth_event",
        "message": "Login failed for account student_9821 with invalid password - brute force suspect",
        "status_code": 401,
        "ip_address": "192.168.1.105",
        "request_url": "/api/v1/auth/login",
        "http_method": "POST"
    },
    {
        "source_application": "land-records",
        "event_type": "application_error",
        "message": "Unhandled exception in property tax assessment calculator: division by zero",
        "status_code": 500,
        "ip_address": "10.0.4.15",
        "request_url": "/assess/calculate",
        "http_method": "POST"
    }
]

class Command(BaseCommand):
    help = "Seed realistic demo e-governance server logs and alerts for dashboard visualization."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=25, help="Number of demo logs to generate")

    def handle(self, *args, **options):
        ensure_roles_exist()
        count = options["count"]
        self.stdout.write(f"Generating {count} demo e-governance log records...")

        now = timezone.now()
        created = 0
        for i in range(count):
            template = random.choice(DEMO_EVENTS)
            payload = template.copy()
            # Spread timestamps over the last 5 days
            offset_hours = random.randint(0, 120)
            offset_minutes = random.randint(0, 59)
            simulated_time = now - timedelta(hours=offset_hours, minutes=offset_minutes)
            
            entry = record_log(payload)
            # Update timestamp to backfill the timeline
            LogEntry.objects.filter(pk=entry.pk).update(timestamp=simulated_time)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully generated {created} sample server logs and triggered alerts!"))
