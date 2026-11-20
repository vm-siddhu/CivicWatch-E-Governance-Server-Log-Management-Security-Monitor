from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logs/", views.log_list, name="logs"),
    path("logs/export/", views.export_logs, name="export-logs"),
    path("logs/manual/", views.manual_log, name="manual-log"),
    path("logs/<uuid:log_id>/", views.log_detail, name="log-detail"),
    path("logs/<uuid:log_id>/correct/", views.log_correct, name="log-correct"),
    path("alerts/", views.alert_list, name="alerts"),
    path("alerts/<int:alert_id>/update/", views.alert_update, name="alert-update"),
    path("audit/", views.audit_report, name="audit-report"),
    path("simulate-log/", views.simulate_log, name="simulate-log"),
]
