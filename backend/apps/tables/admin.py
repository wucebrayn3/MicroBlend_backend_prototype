from django.contrib import admin
from .models import Table
# Register your models here.

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "capacity", "status")
    # list_filter = ("is_available",)
    search_fields = ("number",)