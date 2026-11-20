from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Alert, AuditEvent, LogEntry
from .classifier import classify

def record_log(data, request=None):
    message = str(data.get("message", ""))[:10000]
    # Strip likely credential values and query-string secrets before persistence.
    import re
    message = re.sub(r"(?i)(password|token|secret|authorization)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", message)
    message = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", message)
    url = str(data.get("request_url", ""))[:2048]
    url = re.sub(r"(?i)(password|token|secret|key)=[^&]+", r"\1=[REDACTED]", url)
    status = data.get("status_code")
    category, severity, reason, confidence = classify(message, status, data.get("severity"))
    entry = LogEntry.objects.create(source_application=str(data.get("source_application", "e-governance"))[:120], server_ip=data.get("server_ip"), user_id=str(data.get("user_id", ""))[:120], request_url=url,
        http_method=str(data.get("http_method", ""))[:10], event_type=str(data.get("event_type", ""))[:100], message=message, severity=severity, ip_address=data.get("ip_address"), status_code=status,
        category=category, original_category=category, original_severity=severity, classification_reason=reason, confidence=confidence)
    try: threshold = max(2, int(AlertConfigurationValue("auth_failure_threshold", 5)))
    except (TypeError, ValueError): threshold = 5
    auth_burst = category == "AUTH" and "fail" in message.lower() and LogEntry.objects.filter(category="AUTH", message__icontains="fail", timestamp__gte=timezone.now()-timedelta(minutes=10), ip_address=entry.ip_address, source_application=entry.source_application).count() >= threshold
    auth_alert_exists = auth_burst and Alert.objects.filter(log__category="AUTH", log__ip_address=entry.ip_address, log__source_application=entry.source_application, created_at__gte=timezone.now()-timedelta(minutes=10)).exists()
    trigger = severity == "CRITICAL" or category == "SECURITY" or (auth_burst and not auth_alert_exists)
    if trigger:
        Alert.objects.create(log=entry, description=message[:500], severity=severity, recommended_action="Review the event and related activity; contain access if unauthorized.")
        recipients = [email.strip() for email in __import__("os").environ.get("ALERT_EMAIL_RECIPIENTS", "").split(",") if email.strip()]
        if recipients:
            try: send_mail(f"{severity} server event", f"{message}\nSource: {entry.source_application}\nLog: {entry.id}", settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
            except Exception: pass
    def _broadcast_live_update():
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            layer = get_channel_layer()
            if layer:
                async_to_sync(layer.group_send)("log_updates", {
                    "type": "log.event",
                    "data": {
                        "id": str(entry.id),
                        "severity": entry.severity,
                        "category": entry.category,
                        "source_application": entry.source_application,
                        "message": entry.message[:200]
                    }
                })
        except Exception:
            pass

    import threading
    threading.Thread(target=_broadcast_live_update, daemon=True).start()
    return entry

def AlertConfigurationValue(key, default):
    from .models import AlertConfiguration
    try: return AlertConfiguration.objects.get(key=key).value
    except AlertConfiguration.DoesNotExist: return default

def audit(action, request=None, details=None, actor=None):
    return AuditEvent.objects.create(actor=actor or getattr(request, "user", None) if getattr(getattr(request, "user", None), "is_authenticated", False) else actor, action=action, details=details or {}, ip_address=request.META.get("REMOTE_ADDR") if request else None)
