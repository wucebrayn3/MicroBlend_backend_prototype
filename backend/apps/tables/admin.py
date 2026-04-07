from django.contrib import admin
from .models import StaffPageRequest, Table, TableMergeGroup, TableScanRequest

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("identifier", "capacity", "status")
    search_fields = ("identifier",)


@admin.register(TableMergeGroup)
class TableGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "combined_capacity")
    search_fields = ("name",)


admin.site.register(TableScanRequest)
admin.site.register(StaffPageRequest)
