from django.contrib import admin

from .models import DebounceRecord, Notification

admin.site.register(Notification)
admin.site.register(DebounceRecord)
