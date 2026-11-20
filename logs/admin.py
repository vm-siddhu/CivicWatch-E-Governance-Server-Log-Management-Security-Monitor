from django.contrib import admin
from .models import Alert, AlertConfiguration, AuditEvent, LogEntry

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display=("timestamp","source_application","category","severity","status_code","ip_address")
    list_filter=("severity","category","source_application")
    search_fields=("message","user_id","ip_address","event_type")
    readonly_fields=("id","timestamp","original_category","original_severity","classification_reason","confidence")
@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin): list_display=("created_at","severity","state","description"); list_filter=("severity","state")
@admin.register(AuditEvent)
class AuditAdmin(admin.ModelAdmin): list_display=("created_at","actor","action","ip_address"); readonly_fields=("created_at",)
admin.site.register(AlertConfiguration)
