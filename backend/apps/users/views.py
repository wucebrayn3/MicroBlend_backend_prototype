from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import log_user_action
from apps.users.models import User
from apps.users.serializers import (
    AccountUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserAdminSerializer,
    UserSerializer,
)
from common.permissions import IsAdmin, IsAuthenticatedAndActive


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
        data = [
            {
                "id": log.id,
                "action": log.action,
                "actor_role": log.actor_role,
                "metadata": log.metadata,
                "created_at": log.created_at,
            }
            for log in logs
        ]
        return Response(data)


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
