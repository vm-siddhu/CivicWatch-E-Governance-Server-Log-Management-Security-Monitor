from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from pathlib import Path

DIST_DIR = settings.BASE_DIR / "frontend" / "dist"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("logs.api_urls")),

    # Serve built React static assets
    re_path(r"^assets/(?P<path>.*)$", serve, {"document_root": str(DIST_DIR / "assets")}),

    # Catch-all route to serve React Single Page Application
    re_path(r"^.*$", serve, {"document_root": str(DIST_DIR), "path": "index.html"}, name="react-app"),
]
