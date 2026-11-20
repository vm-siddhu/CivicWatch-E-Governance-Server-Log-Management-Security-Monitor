import uuid
from django.conf import settings
from django.db import models

class LogEntry(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        ERROR = "ERROR", "Error"
        WARNING = "WARNING", "Warning"
        INFO = "INFO", "Info"
        DEBUG = "DEBUG", "Debug"
    class Category(models.TextChoices):
        AUTH = "AUTH", "Authentication Events"
        SECURITY = "SECURITY", "Security Threats"
        APP_ERROR = "APP_ERROR", "Application Errors"
        DATABASE = "DATABASE", "Database Errors"
        NETWORK = "NETWORK", "Network Issues"
        ACTIVITY = "ACTIVITY", "User Activities"
        WARNING = "SYS_WARNING", "System Warnings"
        FAILURE = "SYS_FAILURE", "Critical System Failures"
        GENERAL = "GENERAL", "General Information"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    source_application = models.CharField(max_length=120, default="e-governance", db_index=True)
    server_ip = models.GenericIPAddressField(null=True, blank=True)
    user_id = models.CharField(max_length=120, blank=True, db_index=True)
    request_url = models.CharField(max_length=2048, blank=True)
    http_method = models.CharField(max_length=10, blank=True)
    event_type = models.CharField(max_length=100, blank=True, db_index=True)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL, db_index=True)
    original_category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    original_severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO)
    classification_reason = models.CharField(max_length=255, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    corrected_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="classification_corrections")
    corrected_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["timestamp", "severity"]), models.Index(fields=["category", "source_application"])]
    def __str__(self): return f"{self.timestamp} {self.severity} {self.message[:80]}"

class Alert(models.Model):
    class State(models.TextChoices):
        UNREAD = "UNREAD", "Unread"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"
    log = models.ForeignKey(LogEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="alerts")
    description = models.CharField(max_length=500)
    severity = models.CharField(max_length=10, choices=LogEntry.Severity.choices, default=LogEntry.Severity.ERROR)
    recommended_action = models.CharField(max_length=500, blank=True)
    state = models.CharField(max_length=15, choices=State.choices, default=State.UNREAD, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta: ordering = ["-created_at"]

class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100, db_index=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta: ordering = ["-created_at"]

class AlertConfiguration(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
