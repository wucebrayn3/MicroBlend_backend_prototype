from django.db.models import Q
from rest_framework import mixins, viewsets

from common.permissions import IsAuthenticatedAndActive

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        user = self.request.user
        role_targets = {user.role}
        if user.staff_role:
            role_targets.add(user.staff_role)
        if user.role == "staff":
            role_targets.add("staff")
        return Notification.objects.filter(Q(recipient=user) | Q(role_target__in=role_targets)).order_by("-created_at")
