from .services import record_log
from django.http import HttpResponse

class RequestLogMiddleware:
    """Capture server errors without recording request bodies or credentials."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code >= 500 and not request.path.startswith("/static/"):
            try:
                user = getattr(request, "user", None)
                record_log({
                    "source_application": "django",
                    "user_id": user.pk if user and user.is_authenticated else "",
                    "request_url": request.path,
                    "http_method": request.method,
                    "event_type": "http_response",
                    "message": f"HTTP {response.status_code} response",
                    "status_code": response.status_code,
                    "ip_address": request.META.get("REMOTE_ADDR")
                })
            except Exception:
                pass
        return response

class CorsMiddleware:
    """Lightweight CORS middleware for React development."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)

        if request.path.startswith("/api/"):
            origin = request.headers.get("Origin", "")
            if origin:
                response["Access-Control-Allow-Origin"] = origin
            else:
                response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken, Authorization, X-Log-Token, X-Requested-With"

        return response
