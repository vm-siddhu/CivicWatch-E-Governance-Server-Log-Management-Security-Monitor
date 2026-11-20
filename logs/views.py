import csv
import sys
from datetime import timedelta
import django
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import LogEntryForm, SimpleRegistrationForm
from .models import Alert, AlertConfiguration, AuditEvent, LogEntry
from .permissions import admin_required, is_admin_user
from .services import audit, record_log

def register(request):
    """User registration view with Admin and User roles."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SimpleRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            role_title = "Administrator" if user.is_staff else "Regular User"
            audit("user_registered", request, {"username": user.username, "role": role_title}, actor=user)
            messages.success(request, f"Welcome to CivicWatch, {user.username}! Signed in as {role_title}.")
            return redirect("dashboard")
    else:
        form = SimpleRegistrationForm()

    return render(request, "registration/register.html", {"form": form})

@login_required
def dashboard(request):
    """Main dashboard displaying log statistics, recent activity, and notifications."""
    now = timezone.now()
    since = now - timedelta(days=7)
    base = LogEntry.objects.all()

    counts = {
        "total": base.count(),
        "info": base.filter(severity="INFO").count(),
        "warnings": base.filter(severity="WARNING").count(),
        "errors": base.filter(severity__in=["ERROR", "CRITICAL"]).count(),
        "critical": base.filter(severity="CRITICAL").count(),
        "notifications": Alert.objects.exclude(state="RESOLVED").count(),
    }

    # Daily trend data for the last 7 days
    daily = list(
        base.filter(timestamp__gte=since)
        .extra(select={"day": "date(timestamp)"})
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    # Severity distribution
    severity_data = list(
        base.values("severity")
        .annotate(total=Count("id"))
        .order_by("severity")
    )

    recent_logs = base[:8]
    recent_alerts = Alert.objects.exclude(state="RESOLVED")[:5]

    return render(request, "logs/dashboard.html", {
        "counts": counts,
        "recent_logs": recent_logs,
        "recent_alerts": recent_alerts,
        "daily": daily,
        "severity_data": severity_data,
        "is_admin": is_admin_user(request.user),
    })

@login_required
def log_list(request):
    """Search and filter server logs with pagination."""
    qs = LogEntry.objects.all()

    # Search query
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(message__icontains=q) | Q(source_application__icontains=q) | Q(ip_address__icontains=q))

    # Level filter
    level = request.GET.get("level", "").strip()
    if level in LogEntry.Severity.values:
        qs = qs.filter(severity=level)

    # Date filters
    date_from = request.GET.get("from", "").strip()
    if date_from:
        try:
            qs = qs.filter(timestamp__date__gte=date_from)
        except Exception:
            pass

    date_to = request.GET.get("to", "").strip()
    if date_to:
        try:
            qs = qs.filter(timestamp__date__lte=date_to)
        except Exception:
            pass

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    severities = [
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]

    return render(request, "logs/log_list.html", {
        "page": page,
        "severities": severities,
        "q": q,
        "selected_level": level,
        "date_from": date_from,
        "date_to": date_to,
        "is_admin": is_admin_user(request.user),
    })

@login_required
def add_log(request):
    """Form to manually add a new server log entry with automatic classification."""
    if request.method == "POST":
        form = LogEntryForm(request.POST)
        if form.is_valid():
            app_choice = form.cleaned_data["source_application"]
            if app_choice == "Other" and form.cleaned_data.get("custom_application"):
                app_name = form.cleaned_data["custom_application"].strip()
            else:
                app_name = app_choice

            chosen_severity = form.cleaned_data["severity"]
            supplied_severity = None if chosen_severity == "AUTO" else chosen_severity

            entry = record_log({
                "source_application": app_name,
                "message": form.cleaned_data["message"],
                "severity": supplied_severity,
                "ip_address": form.cleaned_data.get("ip_address") or None,
                "status_code": form.cleaned_data.get("status_code") or None,
                "user_id": str(request.user.id),
                "event_type": "manual_entry"
            }, request)

            messages.success(
                request,
                f"Log recorded successfully! Automatically classified as {entry.severity} ({entry.get_category_display()})."
            )
            return redirect("logs")
    else:
        form = LogEntryForm()

    return render(request, "logs/add_log.html", {"form": form})

@login_required
def log_detail(request, log_id):
    """Inspect full details of a specific log entry."""
    entry = get_object_or_404(LogEntry, pk=log_id)
    return render(request, "logs/log_detail.html", {
        "entry": entry,
        "is_admin": is_admin_user(request.user),
    })

@admin_required
@require_POST
def delete_log(request, log_id):
    """Admin-only deletion of a log entry."""
    entry = get_object_or_404(LogEntry, pk=log_id)
    entry.delete()
    messages.success(request, "Log entry deleted.")
    return redirect("logs")

@login_required
def notifications_view(request):
    """View active and resolved system incident notifications."""
    status_filter = request.GET.get("status", "unresolved")

    if status_filter == "resolved":
        alerts = Alert.objects.filter(state="RESOLVED")
    elif status_filter == "all":
        alerts = Alert.objects.all()
    else:
        status_filter = "unresolved"
        alerts = Alert.objects.exclude(state="RESOLVED")

    return render(request, "logs/notifications.html", {
        "alerts": alerts,
        "status_filter": status_filter,
        "unresolved_count": Alert.objects.exclude(state="RESOLVED").count(),
        "is_admin": is_admin_user(request.user),
    })

@login_required
@require_POST
def resolve_notification(request, alert_id):
    """Mark a notification/alert as resolved."""
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.state = "RESOLVED"
    alert.handled_by = request.user
    alert.save(update_fields=["state", "handled_by", "updated_at"])
    messages.success(request, "Notification marked as resolved.")
    return redirect("notifications")

@login_required
def settings_view(request):
    """Settings and system information page."""
    threshold_key = "auth_failure_threshold"

    if request.method == "POST" and is_admin_user(request.user):
        new_val = request.POST.get("auth_threshold", "").strip()
        if new_val.isdigit() and int(new_val) >= 2:
            conf, _ = AlertConfiguration.objects.get_or_create(key=threshold_key)
            conf.value = new_val
            conf.save()
            messages.success(request, f"Failed authentication alert threshold updated to {new_val}.")
            return redirect("settings")

    try:
        current_threshold = AlertConfiguration.objects.get(key=threshold_key).value
    except AlertConfiguration.DoesNotExist:
        current_threshold = "5"

    sys_info = {
        "django_version": django.get_version(),
        "python_version": sys.version.split()[0],
        "database": "SQLite (db.sqlite3)",
        "total_users": User.objects.count(),
        "total_logs": LogEntry.objects.count(),
        "total_alerts": Alert.objects.count(),
    }

    return render(request, "logs/settings.html", {
        "sys_info": sys_info,
        "current_threshold": current_threshold,
        "is_admin": is_admin_user(request.user),
    })

@login_required
@require_POST
def seed_logs_view(request):
    """Quickly generate demo server logs to demonstrate dashboard functionality."""
    sample_logs = [
        {"app": "Student Portal", "msg": "Student semester fee payment completed successfully", "sev": "INFO", "status": 200, "ip": "192.168.1.15"},
        {"app": "Student Portal", "msg": "Login failed for account roll_9021 with invalid password", "sev": "WARNING", "status": 401, "ip": "192.168.1.55"},
        {"app": "Auth Service", "msg": "Multiple consecutive failed login attempts detected", "sev": "WARNING", "status": 401, "ip": "192.168.1.55"},
        {"app": "Database Server", "msg": "Database connection pool timeout: connection refused by master node", "sev": "CRITICAL", "status": 500, "ip": "10.0.1.10"},
        {"app": "Fee Gateway", "msg": "Payment gateway API timeout while verifying transaction checksum", "sev": "ERROR", "status": 504, "ip": "10.0.2.22"},
        {"app": "Exam System", "msg": "Midterm hall ticket downloaded for candidate #482", "sev": "INFO", "status": 200, "ip": "192.168.2.14"},
        {"app": "Library System", "msg": "Book return catalog entry updated for accession #9102", "sev": "INFO", "status": 200, "ip": "192.168.3.11"},
        {"app": "Student Portal", "msg": "Unhandled exception: division by zero in grade calculator", "sev": "ERROR", "status": 500, "ip": "10.0.1.18"},
        {"app": "Database Server", "msg": "Disk space warning: filesystem usage reached 87%", "sev": "WARNING", "status": 200, "ip": "10.0.1.10"},
        {"app": "Auth Service", "msg": "Potential brute force authentication attempt on admin user", "sev": "CRITICAL", "status": 403, "ip": "203.0.113.88"},
    ]

    for item in sample_logs:
        record_log({
            "source_application": item["app"],
            "message": item["msg"],
            "severity": item["sev"],
            "status_code": item["status"],
            "ip_address": item["ip"],
            "event_type": "demo_seed"
        })

    messages.success(request, f"Generated {len(sample_logs)} sample demo logs across different levels.")
    return redirect("dashboard")

@admin_required
@require_POST
def clear_logs_view(request):
    """Admin-only action to reset all logs and notifications."""
    LogEntry.objects.all().delete()
    Alert.objects.all().delete()
    messages.success(request, "All logs and notifications have been cleared.")
    return redirect("dashboard")

@login_required
def export_logs(request):
    """Export current log view to CSV."""
    qs = LogEntry.objects.all()

    if request.GET.get("level"):
        qs = qs.filter(severity=request.GET["level"])
    if request.GET.get("q"):
        qs = qs.filter(Q(message__icontains=request.GET["q"]) | Q(source_application__icontains=request.GET["q"]))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="server-logs.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Timestamp", "Application", "Level", "Category", "Status Code", "IP Address", "Message"])

    for e in qs.iterator():
        writer.writerow([
            str(e.id),
            e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            e.source_application,
            e.severity,
            e.category,
            e.status_code or "",
            e.ip_address or "",
            e.message
        ])

    return response
