from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import AuditEvent

@receiver(user_logged_in)
def login_audit(sender, request, user, **kwargs): AuditEvent.objects.create(actor=user, action="login", ip_address=request.META.get("REMOTE_ADDR"))
@receiver(user_logged_out)
def logout_audit(sender, request, user, **kwargs): AuditEvent.objects.create(actor=user, action="logout" if user else "logout", ip_address=request.META.get("REMOTE_ADDR"))
@receiver(user_login_failed)
def failed_login(sender, credentials, request, **kwargs): AuditEvent.objects.create(action="failed_login", details={"username": str(credentials.get("username", ""))[:150]}, ip_address=request.META.get("REMOTE_ADDR") if request else None)
