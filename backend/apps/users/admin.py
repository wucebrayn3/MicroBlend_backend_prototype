from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "display_name", "role", "staff_role", "email", "phone", "is_active")
    list_filter = ("role", "staff_role", "is_active", "is_deleted")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        (
            "MicroBlend",
            {
                "fields": (
                    "role",
                    "staff_role",
                    "phone",
                    "registered_device_id",
                    "is_deleted",
                )
            },
        ),
    )
