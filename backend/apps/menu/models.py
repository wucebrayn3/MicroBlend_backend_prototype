from django.db import models
from common.models import BaseModel

class Category(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class MenuItem(BaseModel):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name