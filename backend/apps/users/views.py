from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import log_user_action
from apps.orders.models import Order
from apps.users.models import User
from apps.users.services import get_or_create_guest_user
from apps.users.serializers import (
    AccountUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserAdminSerializer,
    UserSerializer,
)
from common.permissions import IsAdmin, IsAuthenticatedAndActive
from uuid import uuid4


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "token": user.auth_token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        device_id = serializer.validated_data["device_id"]
        if device_id and not user.registered_device_id:
            user.registered_device_id = device_id
            user.save(update_fields=["registered_device_id", "updated_at"])

        token, _ = Token.objects.get_or_create(user=user)
        log_user_action(user, "account.logged_in", {"device_id": device_id})
        return Response({"token": token.key, "user": UserSerializer(user).data})


class GuestSessionStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        guest_key = (request.query_params.get("guest_key") or "").strip()
        if not guest_key:
            return Response({"detail": "guest_key is required."}, status=status.HTTP_400_BAD_REQUEST)

        guest = User.objects.filter(registered_device_id=guest_key, is_guest=True).order_by("-id").first()
        if not guest:
            return Response(
                {
                    "guest_key": guest_key,
                    "has_active_guest_access": False,
                    "expires_at": None,
                    "seconds_remaining": 0,
                }
            )

        now = timezone.now()
        is_expired = not guest.is_active or (guest.guest_expires_at is not None and guest.guest_expires_at <= now)
        seconds_remaining = 0
        if guest.guest_expires_at and not is_expired:
            seconds_remaining = max(int((guest.guest_expires_at - now).total_seconds()), 0)

        return Response(
            {
                "guest_key": guest_key,
                "guest_user_id": guest.id,
                "has_active_guest_access": not is_expired,
                "expires_at": guest.guest_expires_at,
                "seconds_remaining": seconds_remaining,
            }
        )


class GuestStartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        guest_key = uuid4().hex
        guest_name = request.data.get("guest_name")
        guest_user = get_or_create_guest_user(guest_key=guest_key, guest_name=guest_name)
        now = timezone.now()
        seconds_remaining = 0
        if guest_user.guest_expires_at:
            seconds_remaining = max(int((guest_user.guest_expires_at - now).total_seconds()), 0)
        return Response(
            {
                "guest_key": guest_key,
                "guest_user_id": guest_user.id,
                "expires_at": guest_user.guest_expires_at,
                "seconds_remaining": seconds_remaining,
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        log_user_action(request.user, "account.logged_out")
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = AccountUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    def delete(self, request):
        request.user.is_active = False
        request.user.is_deleted = True
        request.user.save(update_fields=["is_active", "is_deleted", "updated_at"])
        Token.objects.filter(user=request.user).delete()
        log_user_action(request.user, "account.deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyHistoryView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request):
        logs = AuditLog.objects.filter(actor=request.user).order_by("-created_at")[:100]
        action_logs = [
            {
                "id": log.id,
                "action": log.action,
                "actor_role": log.actor_role,
                "metadata": log.metadata,
                "created_at": log.created_at,
            }
            for log in logs
        ]
        contact_values = [value for value in [request.user.email, request.user.phone] if value]
        guest_orders = []
        linked_guest_orders = (
            Order.objects.filter(placed_by=request.user, channel="guest").order_by("-created_at").distinct()[:100]
        )
        for order in linked_guest_orders:
            guest_orders.append(
                {
                    "id": order.id,
                    "receipt_number": order.receipt_number,
                    "status": order.status,
                    "total_amount": order.total_amount,
                    "placed_for_contact": order.placed_for_contact,
                    "created_at": order.created_at,
                }
            )
        if contact_values:
            matched_orders = (
                Order.objects.filter(placed_by__is_guest=True, channel="guest", placed_for_contact__in=contact_values)
                .order_by("-created_at")
                .distinct()[:100]
            )
            existing_ids = {entry["id"] for entry in guest_orders}
            for order in matched_orders:
                if order.id in existing_ids:
                    continue
                guest_orders.append(
                    {
                        "id": order.id,
                        "receipt_number": order.receipt_number,
                        "status": order.status,
                        "total_amount": order.total_amount,
                        "placed_for_contact": order.placed_for_contact,
                        "created_at": order.created_at,
                    }
                )

        return Response(
            {
                "action_logs": action_logs,
                "guest_orders_matched_after_registration": guest_orders,
            }
        )


class UserAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        log_user_action(request.user, "admin.account.deactivated", {"target_user_id": user.id})
        return Response(self.get_serializer(user).data)
