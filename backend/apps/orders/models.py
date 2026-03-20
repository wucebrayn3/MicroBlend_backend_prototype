from decimal import Decimal

from django.conf import settings
from django.db import models

from common.constants import (
    ORDER_CHANNEL_CHOICES,
    ORDER_CHANNEL_CUSTOMER,
    ORDER_STATUS_CHOICES,
    ORDER_STATUS_DRAFT,
    WORKFLOW_STATUS_AWAITING_VERIFICATION,
    WORKFLOW_STATUS_CHOICES,
    WORKFLOW_STATUS_NOT_REQUIRED,
    WORKFLOW_STATUS_PENDING,
)
from common.models import BaseModel
from common.utils import generate_reference


class Order(BaseModel):
    table_session = models.ForeignKey(
        "table_sessions.TableSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    placed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    placed_by_name = models.CharField(max_length=120, blank=True, null=True)
    placed_by_role = models.CharField(max_length=30, blank=True, null=True)
    placed_for_name = models.CharField(max_length=120, blank=True, null=True)
    placed_for_contact = models.CharField(max_length=120, blank=True, null=True)
    channel = models.CharField(max_length=30, choices=ORDER_CHANNEL_CHOICES, default=ORDER_CHANNEL_CUSTOMER)
    status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_DRAFT)
    kitchen_status = models.CharField(max_length=30, choices=WORKFLOW_STATUS_CHOICES, default=WORKFLOW_STATUS_PENDING)
    bar_status = models.CharField(max_length=30, choices=WORKFLOW_STATUS_CHOICES, default=WORKFLOW_STATUS_PENDING)
    cashier_status = models.CharField(
        max_length=30,
        choices=WORKFLOW_STATUS_CHOICES,
        default=WORKFLOW_STATUS_PENDING,
    )
    is_bulk_order = models.BooleanField(default=False)
    requires_cashier_verification = models.BooleanField(default=False)
    price_alert_sent = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    receipt_number = models.CharField(max_length=40, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True)
    external_pos_reference = models.CharField(max_length=120, blank=True, null=True)
    inventory_committed = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = generate_reference("RCPT")
        super().save(*args, **kwargs)

    def refresh_totals(self, save=False):
        total = sum(item.line_total for item in self.items.all())
        self.total_amount = total
        if save:
            self.save(update_fields=["total_amount", "updated_at"])
        return total

    def station_required(self, station):
        return self.items.filter(station=station).exists()

    def initialize_station_statuses(self):
        if not self.station_required("kitchen"):
            self.kitchen_status = WORKFLOW_STATUS_NOT_REQUIRED
        if not self.station_required("bar"):
            self.bar_status = WORKFLOW_STATUS_NOT_REQUIRED
        if self.is_bulk_order:
            self.cashier_status = WORKFLOW_STATUS_AWAITING_VERIFICATION

    def __str__(self):
        return self.receipt_number or f"Order {self.pk}"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey("menu.MenuItem", on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=200)
    station = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    customization_notes = models.CharField(max_length=255, blank=True, null=True)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"


class OrderStatusLog(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=40)
    note = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.order_id} -> {self.status}"
