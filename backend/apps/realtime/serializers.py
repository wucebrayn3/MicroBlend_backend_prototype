from rest_framework import serializers

from apps.realtime.models import RealtimeEvent


class RealtimeEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealtimeEvent
        fields = ("id", "event_type", "payload", "role_target", "user", "created_at")
