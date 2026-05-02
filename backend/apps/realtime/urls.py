from django.urls import path

from apps.realtime.views import RealtimeEventListView, RealtimeStreamView

urlpatterns = [
    path("realtime/events/", RealtimeEventListView.as_view(), name="realtime-events"),
    path("realtime/stream/", RealtimeStreamView.as_view(), name="realtime-stream"),
]
