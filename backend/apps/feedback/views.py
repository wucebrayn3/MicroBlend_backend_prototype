from rest_framework import viewsets

from common.permissions import IsAuthenticatedAndActive, IsStaffOrAdmin

from .models import FeedbackEntry
from .serializers import FeedbackEntrySerializer


class FeedbackEntryViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackEntrySerializer

    def get_permissions(self):
        if self.action in {"create", "list", "retrieve"}:
            return [IsAuthenticatedAndActive()]
        return [IsStaffOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.role in {"admin", "staff"}:
            return FeedbackEntry.objects.select_related("submitted_by", "order").all()
        return FeedbackEntry.objects.select_related("submitted_by", "order").filter(submitted_by=user)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
