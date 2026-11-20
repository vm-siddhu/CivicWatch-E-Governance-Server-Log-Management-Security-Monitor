from .services import record_log

class RequestLogMiddleware:
    """Capture server errors without recording request bodies or credentials."""
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code >= 500 and not request.path.startswith("/static/"):
            try:
                user = getattr(request, "user", None)
                record_log({"source_application": "django", "user_id": user.pk if user and user.is_authenticated else "", "request_url": request.path, "http_method": request.method, "event_type": "http_response", "message": f"HTTP {response.status_code} response", "status_code": response.status_code, "ip_address": request.META.get("REMOTE_ADDR")})
            except Exception: pass
        return response
