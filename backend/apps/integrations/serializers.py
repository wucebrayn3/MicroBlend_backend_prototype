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
