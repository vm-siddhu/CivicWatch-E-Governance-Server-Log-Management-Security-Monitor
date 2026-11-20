import csv
import sys
from datetime import timedelta
import django
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Alert, AlertConfiguration, AuditEvent, LogEntry
from .permissions import IngestPermission, is_admin_user
from .roles import ensure_roles_exist
from .services import audit, record_log

def serialize_log(entry):
    return {
        "id": str(entry.id),
        "timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "source_application": entry.source_application,
        "message": entry.message,
        "severity": entry.severity,
        "category": entry.category,
        "category_display": entry.get_category_display(),
        "ip_address": entry.ip_address or "",
        "status_code": entry.status_code,
        "confidence": round(entry.confidence * 100) if entry.confidence else None,
        "classification_reason": entry.classification_reason or ""
    }

def serialize_alert(alert):
    return {
        "id": alert.id,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "severity": alert.severity,
        "description": alert.description,
        "recommended_action": alert.recommended_action or "",
        "state": alert.state,
        "log_id": str(alert.log.id) if alert.log else None,
        "source_application": alert.log.source_application if alert.log else "System",
        "handled_by": alert.handled_by.username if alert.handled_by else None,
    }

# --- Auth APIs ---
class AuthMeAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                "authenticated": True,
                "user": {
                    "username": request.user.username,
                    "email": request.user.email,
                    "is_admin": is_admin_user(request.user),
                    "role": "Admin" if is_admin_user(request.user) else "User"
                }
            })
        return Response({"authenticated": False, "user": None})

class AuthLoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return Response({
                "success": True,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "is_admin": is_admin_user(user),
                    "role": "Admin" if is_admin_user(user) else "User"
                }
            })
        return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

class AuthRegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")
        role = request.data.get("role", "User")
        is_admin = role == "Admin"

        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 8:
            return Response({"error": "Password must be at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username__iexact=username).exists():
            return Response({"error": "This username is already taken."}, status=status.HTTP_400_BAD_REQUEST)

        ensure_roles_exist()
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=is_admin
        )
        group_name = "System Administrator" if is_admin else "Monitoring Officer"
        group = Group.objects.filter(name=group_name).first()
        if group:
            user.groups.add(group)

        auth_login(request, user)
        return Response({
            "success": True,
            "user": {
                "username": user.username,
                "email": user.email,
                "is_admin": is_admin_user(user),
                "role": "Admin" if is_admin else "User"
            }
        }, status=status.HTTP_201_CREATED)

class AuthLogoutAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        auth_logout(request)
        return Response({"success": True})

# --- Dashboard API ---
class DashboardAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
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

        daily = list(
            base.filter(timestamp__gte=since)
            .extra(select={"day": "date(timestamp)"})
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )

        severity_data = list(
            base.values("severity")
            .annotate(total=Count("id"))
            .order_by("severity")
        )

        recent_logs = [serialize_log(l) for l in base[:8]]
        recent_alerts = [serialize_alert(a) for a in Alert.objects.exclude(state="RESOLVED")[:5]]

        return Response({
            "counts": counts,
            "daily": daily,
            "severity_data": severity_data,
            "recent_logs": recent_logs,
            "recent_alerts": recent_alerts
        })

# --- Log Management APIs ---
class LogListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = LogEntry.objects.all()

        q = request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(message__icontains=q) | Q(source_application__icontains=q) | Q(ip_address__icontains=q))

        level = request.GET.get("level", "").strip()
        if level in LogEntry.Severity.values:
            qs = qs.filter(severity=level)

        date_from = request.GET.get("from", "").strip()
        if date_from:
            try: qs = qs.filter(timestamp__date__gte=date_from)
            except Exception: pass

        date_to = request.GET.get("to", "").strip()
        if date_to:
            try: qs = qs.filter(timestamp__date__lte=date_to)
            except Exception: pass

        page_size = min(int(request.GET.get("page_size", 20)), 100)
        paginator = Paginator(qs, page_size)
        page_num = int(request.GET.get("page", 1))
        page = paginator.get_page(page_num)

        return Response({
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "current_page": page.number,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
            "results": [serialize_log(e) for e in page]
        })

    def post(self, request):
        data = request.data
        msg = data.get("message", "").strip()
        if not msg:
            return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

        app_name = data.get("source_application", "Student Portal").strip() or "Student Portal"
        severity = data.get("severity")
        if severity == "AUTO" or not severity:
            severity = None

        entry = record_log({
            "source_application": app_name,
            "message": msg,
            "severity": severity,
            "ip_address": data.get("ip_address") or None,
            "status_code": data.get("status_code") or None,
            "user_id": str(request.user.id) if request.user.is_authenticated else "",
            "event_type": "manual_entry"
        }, request)

        return Response(serialize_log(entry), status=status.HTTP_201_CREATED)

class LogDetailDeleteAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, log_id):
        try:
            entry = LogEntry.objects.get(pk=log_id)
            return Response(serialize_log(entry))
        except LogEntry.DoesNotExist:
            return Response({"error": "Log not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, log_id):
        try:
            entry = LogEntry.objects.get(pk=log_id)
            entry.delete()
            return Response({"success": True, "message": "Log deleted."})
        except LogEntry.DoesNotExist:
            return Response({"error": "Log not found."}, status=status.HTTP_404_NOT_FOUND)

# --- Notifications API ---
class NotificationsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        status_filter = request.GET.get("status", "unresolved")
        if status_filter == "resolved":
            alerts = Alert.objects.filter(state="RESOLVED")
        elif status_filter == "all":
            alerts = Alert.objects.all()
        else:
            alerts = Alert.objects.exclude(state="RESOLVED")

        unresolved_count = Alert.objects.exclude(state="RESOLVED").count()
        return Response({
            "unresolved_count": unresolved_count,
            "results": [serialize_alert(a) for a in alerts]
        })

class ResolveNotificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, alert_id):
        try:
            alert = Alert.objects.get(pk=alert_id)
            alert.state = "RESOLVED"
            if request.user.is_authenticated:
                alert.handled_by = request.user
            alert.save(update_fields=["state", "handled_by", "updated_at"])
            return Response({"success": True, "alert": serialize_alert(alert)})
        except Alert.DoesNotExist:
            return Response({"error": "Alert not found."}, status=status.HTTP_404_NOT_FOUND)

# --- Settings & Demo APIs ---
class SettingsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        threshold_key = "auth_failure_threshold"
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
        return Response({
            "sys_info": sys_info,
            "current_threshold": current_threshold
        })

    def post(self, request):
        # Update threshold
        new_val = str(request.data.get("auth_threshold", "")).strip()
        if new_val.isdigit() and int(new_val) >= 2:
            conf, _ = AlertConfiguration.objects.get_or_create(key="auth_failure_threshold")
            conf.value = new_val
            conf.save()
            return Response({"success": True, "current_threshold": new_val})
        return Response({"error": "Invalid threshold value. Must be >= 2."}, status=status.HTTP_400_BAD_REQUEST)

class SeedLogsAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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
        created = []
        for item in sample_logs:
            entry = record_log({
                "source_application": item["app"],
                "message": item["msg"],
                "severity": item["sev"],
                "status_code": item["status"],
                "ip_address": item["ip"],
                "event_type": "demo_seed"
            })
            created.append(serialize_log(entry))
        return Response({"success": True, "count": len(created), "sample": created})

class ClearLogsAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        count_logs = LogEntry.objects.count()
        count_alerts = Alert.objects.count()
        LogEntry.objects.all().delete()
        Alert.objects.all().delete()
        return Response({"success": True, "deleted_logs": count_logs, "deleted_alerts": count_alerts})

class ExportLogsCSVAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
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
                str(e.id), e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                e.source_application, e.severity, e.category,
                e.status_code or "", e.ip_address or "", e.message
            ])
        return response

# Legacy / Programmatic Ingest endpoint
class IngestView(APIView):
    authentication_classes = []
    permission_classes = [IngestPermission]

    def post(self, request):
        data = request.data
        msg = data.get("message", "").strip()
        if not msg:
            return Response({"error": "Message required."}, status=status.HTTP_400_BAD_REQUEST)
        entry = record_log({
            "source_application": data.get("source_application", "e-governance"),
            "server_ip": data.get("server_ip"),
            "user_id": str(data.get("user_id", "")),
            "request_url": str(data.get("request_url", "")),
            "http_method": str(data.get("http_method", "")),
            "event_type": str(data.get("event_type", "")),
            "message": msg,
            "severity": data.get("severity"),
            "ip_address": data.get("ip_address"),
            "status_code": data.get("status_code"),
        }, request)
        return Response({
            "id": str(entry.id),
            "timestamp": entry.timestamp,
            "category": entry.category,
            "severity": entry.severity,
            "classification_reason": entry.classification_reason
        }, status=status.HTTP_201_CREATED)
