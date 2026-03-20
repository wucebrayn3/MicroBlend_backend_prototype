from django.contrib import admin

from .models import CostSimulation, GeneratedReport

admin.site.register(GeneratedReport)
admin.site.register(CostSimulation)
