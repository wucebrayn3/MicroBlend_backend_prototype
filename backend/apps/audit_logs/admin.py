from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "actor", "actor_role", "target_type", "target_id", "created_at")
    list_filter = ("action", "actor_role", "target_type")
    search_fields = ("action", "target_id", "target_label", "actor__username", "actor__email")
