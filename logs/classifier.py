"""Local, replaceable rule classifier; never sends log content to an external service."""
from logs.models import LogEntry

RULES = [
    ("SYS_FAILURE", "CRITICAL", ("kernel panic", "out of memory", "system failure", "service unavailable"), "Critical system failure pattern"),
    ("DATABASE", "CRITICAL", ("database connection", "database unavailable", "connection refused", "sql error", "deadlock"), "Database failure pattern"),
    ("SECURITY", "CRITICAL", ("sql injection", "xss attempt", "unauthorized access", "directory traversal", "brute force", "suspicious"), "Security threat keyword"),
    ("AUTH", "WARNING", ("login failed", "authentication failed", "invalid password", "logout", "login succeeded"), "Authentication event keyword"),
    ("NETWORK", "ERROR", ("timeout", "dns failure", "network unreachable", "connection reset"), "Network failure pattern"),
    ("APP_ERROR", "ERROR", ("exception", "traceback", "internal server error", "unhandled error", "failed"), "Application error pattern"),
    ("SYS_WARNING", "WARNING", ("warning", "deprecated", "disk space", "high memory"), "System warning keyword"),
    ("ACTIVITY", "INFO", ("created", "updated", "deleted", "exported", "user action"), "User activity keyword"),
]

def classify(message, status_code=None, supplied_severity=None):
    text = (message or "").lower()
    for category, severity, words, reason in RULES:
        if any(word in text for word in words):
            return category, severity, reason, min(.98, .72 + .06 * sum(word in text for word in words))
    if status_code is not None:
        if status_code >= 500: return "APP_ERROR", "ERROR", f"HTTP {status_code} server error", .85
        if status_code in (401, 403): return "SECURITY", "WARNING", f"HTTP {status_code} access denial", .82
        if status_code >= 400: return "APP_ERROR", "WARNING", f"HTTP {status_code} client error", .78
    if supplied_severity in LogEntry.Severity.values and supplied_severity in ("CRITICAL", "ERROR", "WARNING"):
        category = {"CRITICAL":"SYS_FAILURE", "ERROR":"APP_ERROR", "WARNING":"SYS_WARNING"}[supplied_severity]
        return category, supplied_severity, "Severity supplied by source", .60
    return "GENERAL", "INFO", "No specific rule matched", .55
