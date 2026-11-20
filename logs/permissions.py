from rest_framework.permissions import BasePermission
from django.contrib.auth.decorators import user_passes_test
import secrets

class IngestPermission(BasePermission):
    def has_permission(self, request, view):
        from django.conf import settings
        expected = settings.LOG_INGEST_TOKEN
        supplied = request.headers.get("X-Log-Token", "")
        return bool(expected and secrets.compare_digest(supplied, expected))

def system_admin_required(view):
    return user_passes_test(lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name__in=["Super Administrator", "System Administrator"]).exists()))(view)

def monitor_required(view):
    return user_passes_test(lambda u: u.is_authenticated and (u.is_superuser or u.groups.filter(name__in=["Super Administrator", "System Administrator", "Monitoring Officer"]).exists()))(view)
