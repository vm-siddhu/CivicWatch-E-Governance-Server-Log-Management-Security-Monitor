from django.urls import path
from . import api

urlpatterns = [
    # Auth
    path("auth/me/", api.AuthMeAPIView.as_view(), name="api-auth-me"),
    path("auth/login/", api.AuthLoginAPIView.as_view(), name="api-auth-login"),
    path("auth/register/", api.AuthRegisterAPIView.as_view(), name="api-auth-register"),
    path("auth/logout/", api.AuthLogoutAPIView.as_view(), name="api-auth-logout"),

    # Dashboard & Stats
    path("dashboard/", api.DashboardAPIView.as_view(), name="api-dashboard"),

    # Logs
    path("logs/", api.LogListCreateAPIView.as_view(), name="api-log-list-create"),
    path("logs/export/", api.ExportLogsCSVAPIView.as_view(), name="api-log-export"),
    path("logs/<uuid:log_id>/", api.LogDetailDeleteAPIView.as_view(), name="api-log-detail-delete"),
    path("logs/ingest/", api.IngestView.as_view(), name="api-log-ingest"),

    # Notifications
    path("notifications/", api.NotificationsAPIView.as_view(), name="api-notifications"),
    path("notifications/<int:alert_id>/resolve/", api.ResolveNotificationAPIView.as_view(), name="api-notification-resolve"),

    # Settings & Demo Tools
    path("settings/", api.SettingsAPIView.as_view(), name="api-settings"),
    path("settings/seed/", api.SeedLogsAPIView.as_view(), name="api-settings-seed"),
    path("settings/clear/", api.ClearLogsAPIView.as_view(), name="api-settings-clear"),
]
