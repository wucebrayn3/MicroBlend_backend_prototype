from django.contrib import admin
from .models import StaffPageRequest, Table, TableMergeGroup, TableScanRequest

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("identifier", "capacity", "status")
    search_fields = ("identifier",)


admin.site.register(TableMergeGroup)
admin.site.register(TableScanRequest)
admin.site.register(StaffPageRequest)
