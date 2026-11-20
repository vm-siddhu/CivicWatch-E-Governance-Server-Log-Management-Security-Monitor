from rest_framework.permissions import BasePermission
from django.contrib.auth.decorators import login_required, user_passes_test
import secrets

class IngestPermission(BasePermission):
    def has_permission(self, request, view):
        from django.conf import settings
        expected = settings.LOG_INGEST_TOKEN
        supplied = request.headers.get("X-Log-Token", "")
        return bool(expected and secrets.compare_digest(supplied, expected))

def is_admin_user(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or
        user.groups.filter(name__in=["Admin", "Administrator", "System Administrator", "Super Administrator"]).exists()
    )

def admin_required(view):
    return user_passes_test(is_admin_user)(view)

# Keep aliases for compatibility
system_admin_required = admin_required
monitor_required = login_required
