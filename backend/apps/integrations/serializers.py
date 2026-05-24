from rest_framework import serializers

from .models import ExternalSystem, SyncEvent


class ExternalSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalSystem
        fields = "__all__"


class SyncEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncEvent
        fields = "__all__"


class SyncEventAckSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["delivered", "failed"])
    error = serializers.CharField(required=False, allow_blank=True, max_length=255)
