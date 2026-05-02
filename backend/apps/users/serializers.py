from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from apps.audit_logs.services import log_user_action
from apps.orders.models import Order
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "staff_role",
            "registered_device_id",
            "is_active",
        )
        read_only_fields = ("id", "role", "staff_role", "is_active")


class UserAdminSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ("id",)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    device_id = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password",
            "device_id",
        )
        read_only_fields = ("id", "username")

    def create(self, validated_data):
        device_id = validated_data.pop("device_id", None) or None
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, registered_device_id=device_id, **validated_data)
        linked_guest_orders = 0
        if device_id:
            guest_users = User.objects.filter(is_guest=True, registered_device_id=device_id)
            guest_user_ids = list(guest_users.values_list("id", flat=True))
            if guest_user_ids:
                updated = Order.objects.filter(placed_by_id__in=guest_user_ids).update(placed_by=user)
                linked_guest_orders += updated
                guest_users.update(is_active=False, is_deleted=True)
        token, _ = Token.objects.get_or_create(user=user)
        log_user_action(user, "account.registered", {"device_id": device_id, "linked_guest_orders": linked_guest_orders})
        user.auth_token = token
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        identifier = attrs["identifier"].strip()
        password = attrs["password"]
        device_id = attrs.get("device_id") or None

        lookup = {"email": identifier} if "@" in identifier else {"phone": identifier}
        try:
            user = User.objects.get(**lookup)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid credentials.") from exc

        authenticated_user = authenticate(username=user.username, password=password)
        if not authenticated_user or not authenticated_user.is_active:
            raise serializers.ValidationError("Invalid credentials.")

        if device_id and authenticated_user.registered_device_id and authenticated_user.registered_device_id != device_id:
            raise serializers.ValidationError("This account is already bound to another mobile device.")

        attrs["user"] = authenticated_user
        attrs["device_id"] = device_id
        return attrs


class AccountUpdateSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "current_password",
            "new_password",
        )

    def validate(self, attrs):
        current_password = attrs.get("current_password")
        new_password = attrs.get("new_password")
        user = self.instance
        if new_password:
            if not current_password or not user.check_password(current_password):
                raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop("current_password", None)
        new_password = validated_data.pop("new_password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if new_password:
            instance.set_password(new_password)
        instance.full_clean()
        instance.save()
        log_user_action(instance, "account.updated", {"fields": list(validated_data.keys())})
        return instance
