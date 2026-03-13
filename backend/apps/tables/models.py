from django.db import models
from common.models import BaseModel
# Create your models here.

class Table(BaseModel):

    number = models.IntegerField(unique=True)
    capacity = models.IntegerField()

    STATUS_CHOICES = (
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("reserved", "Reserved"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")

    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Table {self.number} - {self.status}"