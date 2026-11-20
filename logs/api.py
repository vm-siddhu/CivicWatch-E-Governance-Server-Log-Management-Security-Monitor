from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import LogEntry
from .permissions import IngestPermission
from .services import record_log

class LogInputSerializer(serializers.Serializer):
    source_application = serializers.CharField(max_length=120, required=False)
    server_ip = serializers.IPAddressField(required=False, allow_null=True)
    user_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
    request_url = serializers.CharField(max_length=2048, required=False, allow_blank=True)
    http_method = serializers.CharField(max_length=10, required=False, allow_blank=True)
    event_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    message = serializers.CharField(max_length=10000)
    severity = serializers.ChoiceField(choices=LogEntry.Severity.choices, required=False)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    status_code = serializers.IntegerField(min_value=100, max_value=599, required=False, allow_null=True)

class IngestView(APIView):
    authentication_classes = []
    permission_classes = [IngestPermission]
    def post(self, request):
        serializer = LogInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = record_log(serializer.validated_data, request)
        return Response({"id": str(entry.id), "timestamp": entry.timestamp, "category": entry.category, "severity": entry.severity, "classification_reason": entry.classification_reason}, status=status.HTTP_201_CREATED)

