from django.contrib import admin

from .models import ExternalSystem, SyncEvent

admin.site.register(ExternalSystem)
admin.site.register(SyncEvent)
