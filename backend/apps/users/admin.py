from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserAdminCreationForm
    form = UserAdminChangeForm
    model = User
    list_display = ("id", "username", "display_name", "role", "staff_role", "is_guest", "email", "phone", "is_active")
    list_filter = ("role", "staff_role", "is_guest", "is_active", "is_deleted")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    ordering = ("id",)
    fieldsets = UserAdmin.fieldsets + (
        (
            "MicroBlend",
            {
                "fields": (
                    "role",
                    "staff_role",
                    "phone",
                    "registered_device_id",
                    "is_guest",
                    "guest_expires_at",
                    "is_deleted",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "role",
                    "staff_role",
                    "registered_device_id",
                    "is_guest",
                    "guest_expires_at",
                    "is_active",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
