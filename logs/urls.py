from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("logs/", views.log_list, name="logs"),
    path("logs/add/", views.add_log, name="add-log"),
    path("logs/<uuid:log_id>/", views.log_detail, name="log-detail"),
    path("logs/<uuid:log_id>/delete/", views.delete_log, name="delete-log"),
    path("logs/export/", views.export_logs, name="export-logs"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:alert_id>/resolve/", views.resolve_notification, name="resolve-notification"),
    path("settings/", views.settings_view, name="settings"),
    path("settings/seed/", views.seed_logs_view, name="seed-logs"),
    path("settings/clear/", views.clear_logs_view, name="clear-logs"),
    # Compatibility aliases
    path("alerts/", views.notifications_view, name="alerts"),
    path("alerts/<int:alert_id>/update/", views.resolve_notification, name="alert-update"),
]
