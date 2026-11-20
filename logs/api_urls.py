from django.urls import path
from .api import IngestView

urlpatterns = [path("logs/ingest/", IngestView.as_view(), name="log-ingest")]
