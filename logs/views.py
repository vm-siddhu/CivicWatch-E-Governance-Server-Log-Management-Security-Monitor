import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import OfficerRegistrationForm
from .models import Alert, AuditEvent, LogEntry
from .permissions import monitor_required, system_admin_required
from .services import audit, record_log

def home(request):
    """Public portal landing page presenting the CivicWatch system, architecture, and AICTE compliance."""
    base = LogEntry.objects.all()
    counts = {
        "total": base.count(),
        "critical": base.filter(severity="CRITICAL").count(),
        "security": base.filter(category="SECURITY").count(),
        "alerts": Alert.objects.exclude(state="RESOLVED").count(),
        "apps": base.values("source_application").distinct().count(),
    }
    recent = base[:6]
    return render(request, "logs/home.html", {"counts": counts, "recent": recent})

@require_POST
def simulate_log(request):
    """Interactive endpoint to simulate realistic log ingestion and immediate classification."""
    import json
    from django.http import JsonResponse
    try:
        data = json.loads(request.body) if request.body else {}
    except Exception:
        data = request.POST.dict()

    scenario = data.get("scenario", "sql_injection")
    scenarios = {
        "sql_injection": {
            "source_application": "tax-portal",
            "event_type": "security_threat",
            "message": "Potential SQL injection detected in parameter id=' OR 1=1--",
            "status_code": 403,
            "ip_address": "203.0.113.88",
            "request_url": "/citizen/filings?id=' OR 1=1--",
            "http_method": "GET"
        },
        "brute_force": {
            "source_application": "student-portal",
            "event_type": "auth_event",
            "message": "Login failed for account student_9821 with invalid password",
            "status_code": 401,
            "ip_address": "192.168.1.105",
            "request_url": "/api/v1/auth/login",
            "http_method": "POST"
        },
        "db_timeout": {
            "source_application": "land-records",
            "event_type": "database_error",
            "message": "Database connection pool exhausted: connection refused by primary replica",
            "status_code": 500,
            "ip_address": "10.0.4.12",
            "request_url": "/api/registry/mutation",
            "http_method": "POST"
        },
        "system_crash": {
            "source_application": "pension-service",
            "event_type": "system_failure",
            "message": "Kernel panic: out of memory while allocating worker thread for batch run",
            "status_code": 503,
            "ip_address": "10.0.8.22",
            "request_url": "/jobs/disburse-monthly",
            "http_method": "POST"
        },
        "normal_activity": {
            "source_application": "citizen-identity",
            "event_type": "user_action",
            "message": "New citizen grievance submitted for road repair in ward #4",
            "status_code": 201,
            "ip_address": "49.36.12.8",
            "request_url": "/portal/grievance/new",
            "http_method": "POST"
        }
    }
    payload = scenarios.get(scenario, scenarios["sql_injection"])
    entry = record_log(payload, request)
    alert_created = Alert.objects.filter(log=entry).exists()

    return JsonResponse({
        "success": True,
        "id": str(entry.id),
        "source_application": entry.source_application,
        "message": entry.message,
        "category": entry.get_category_display(),
        "severity": entry.severity,
        "confidence": f"{round(entry.confidence * 100)}%" if entry.confidence else "Standard",
        "reason": entry.classification_reason,
        "alert_triggered": alert_created,
        "timestamp": entry.timestamp.strftime("%b %d, %H:%M:%S")
    })

def register(request):
    """Handle new officer / administrator account registration."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = OfficerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role_name = form.cleaned_data.get("role", "Monitoring Officer")
            auth_login(request, user)
            audit("user_registered", request, {"username": user.username, "role": role_name}, actor=user)
            messages.success(request, f"Registration successful. Welcome, {user.get_full_name() or user.username}! You are signed in as {role_name}.")
            return redirect("dashboard")
    else:
        form = OfficerRegistrationForm()

    return render(request, "registration/register.html", {"form": form})

@monitor_required
def dashboard(request):
    now = timezone.now(); since = now - timedelta(days=7); base = LogEntry.objects.all()
    counts = {"total": base.count(), "critical": base.filter(severity="CRITICAL").count(), "errors": base.filter(severity="ERROR").count(), "warnings": base.filter(severity="WARNING").count(), "security": base.filter(category="SECURITY").count(), "alerts": Alert.objects.exclude(state="RESOLVED").count()}
    daily = list(base.filter(timestamp__gte=since).extra(select={"day": "date(timestamp)"}).values("day").annotate(total=Count("id")).order_by("day"))
    severity_data = list(base.values("severity").annotate(total=Count("id")).order_by("severity"))
    category_data = list(base.values("category").annotate(total=Count("id")).order_by("category"))
    applications = list(base.values("source_application").annotate(total=Count("id")).order_by("-total")[:8])
    errors = list(base.filter(timestamp__gte=since, severity__in=["ERROR", "CRITICAL"]).extra(select={"day": "date(timestamp)"}).values("day").annotate(total=Count("id")).order_by("day"))
    return render(request, "logs/dashboard.html", {"counts": counts, "recent": base[:12], "severity_data": severity_data, "category_data": category_data, "applications": applications, "daily": daily, "errors": errors, "alerts": Alert.objects.exclude(state="RESOLVED")[:5]})

@monitor_required
def log_list(request):
    qs = LogEntry.objects.all()
    mapping = {"severity":"severity", "category":"category", "app":"source_application__icontains", "user_id":"user_id__icontains", "ip":"ip_address__icontains", "status":"status_code", "event":"event_type__icontains", "from":"timestamp__date__gte", "to":"timestamp__date__lte"}
    for key, field in mapping.items():
        value = request.GET.get(key)
        if value:
            try: qs = qs.filter(**{field:value})
            except (ValueError, TypeError): pass
    if request.GET.get("q"): qs = qs.filter(Q(message__icontains=request.GET["q"]) | Q(request_url__icontains=request.GET["q"]))
    sort = request.GET.get("sort", "-timestamp")
    if sort.lstrip("-") in {"timestamp", "severity", "category", "source_application", "status_code"}: qs = qs.order_by(sort)
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    return render(request, "logs/log_list.html", {"page":page, "severities":LogEntry.Severity.choices, "categories":LogEntry.Category.choices})

@monitor_required
def log_detail(request, log_id): return render(request, "logs/log_detail.html", {"entry":get_object_or_404(LogEntry, pk=log_id), "categories":LogEntry.Category.choices, "severities":LogEntry.Severity.choices})

@system_admin_required
@require_POST
def log_correct(request, log_id):
    entry = get_object_or_404(LogEntry, pk=log_id); category = request.POST.get("category"); severity = request.POST.get("severity")
    if category in LogEntry.Category.values and severity in LogEntry.Severity.values:
        entry.category, entry.severity, entry.corrected_by, entry.corrected_at = category, severity, request.user, timezone.now(); entry.save(update_fields=["category", "severity", "corrected_by", "corrected_at"])
        audit("classification_corrected", request, {"log_id":str(entry.id), "category":category, "severity":severity}); messages.success(request, "Classification corrected.")
    return redirect("log-detail", log_id=log_id)

@monitor_required
def export_logs(request):
    qs = LogEntry.objects.all()
    if request.GET.get("severity"): qs = qs.filter(severity=request.GET["severity"])
    if request.GET.get("category"): qs = qs.filter(category=request.GET["category"])
    if request.GET.get("q"): qs = qs.filter(message__icontains=request.GET["q"])
    response = HttpResponse(content_type="text/csv"); response["Content-Disposition"]='attachment; filename="server-logs.csv"'; writer=csv.writer(response)
    writer.writerow(["ID","Timestamp","Application","User","IP","Event","Severity","Category","Status","Message"])
    for e in qs.iterator(): writer.writerow([e.id,e.timestamp.isoformat(),e.source_application,e.user_id,e.ip_address or "",e.event_type,e.severity,e.category,e.status_code or "",e.message])
    audit("logs_exported", request, {"count":qs.count()}); return response

@monitor_required
def alert_list(request): return render(request, "logs/alerts.html", {"alerts":Alert.objects.select_related("log","handled_by")})

@system_admin_required
@require_POST
def alert_update(request, alert_id):
    alert=get_object_or_404(Alert, pk=alert_id); state=request.POST.get("state")
    if state in Alert.State.values:
        alert.state, alert.handled_by=state,request.user; alert.save(update_fields=["state","handled_by","updated_at"]); audit("alert_"+state.lower(),request,{"alert_id":alert.pk})
    return redirect("alerts")

@system_admin_required
def audit_report(request):
    qs=AuditEvent.objects.select_related("actor")
    if request.GET.get("from"): qs=qs.filter(created_at__date__gte=request.GET["from"])
    if request.GET.get("to"): qs=qs.filter(created_at__date__lte=request.GET["to"])
    if request.GET.get("csv")=="1":
        response=HttpResponse(content_type="text/csv"); response["Content-Disposition"]='attachment; filename="audit-report.csv"'; w=csv.writer(response); w.writerow(["Time","Actor","Action","Details","IP"])
        for e in qs.iterator(): w.writerow([e.created_at.isoformat(),e.actor or "system",e.action,e.details,e.ip_address or ""])
        audit("audit_report_exported",request); return response
    return render(request,"logs/audit.html",{"events":qs[:500]})

@system_admin_required
@require_POST
def manual_log(request):
    if request.POST.get("message", "").strip():
        entry=record_log({"source_application":request.POST.get("source_application","manual-entry"),"event_type":request.POST.get("event_type","manual"),"message":request.POST["message"],"user_id":request.user.pk})
        audit("manual_log_created",request,{"log_id":str(entry.id)})
    return redirect("logs")
