from django.db import migrations, models


def forward_status_mapping(apps, schema_editor):
    Order = apps.get_model("orders", "Order")

    Order.objects.filter(status="placed").update(status="pending")
    Order.objects.filter(status="payment_pending").update(status="ready", cashier_status="awaiting_payment")
    Order.objects.filter(status="paid").update(status="ready", cashier_status="paid")

    Order.objects.filter(cashier_status__in=["pending", "preparing", "ready", "cancelled", "not_required", "awaiting_verification"]).update(
        cashier_status="awaiting_payment"
    )


def backward_status_mapping(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(status="pending").update(status="placed")
    Order.objects.filter(status="waiting").update(status="placed")
    Order.objects.filter(status="ready", cashier_status="awaiting_payment").update(status="payment_pending")
    Order.objects.filter(cashier_status="awaiting_payment").update(cashier_status="pending")


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("pending", "Pending"),
                    ("waiting", "Waiting"),
                    ("preparing", "Preparing"),
                    ("ready", "Ready"),
                    ("cancelled", "Cancelled"),
                ],
                default="draft",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="cashier_status",
            field=models.CharField(
                choices=[("awaiting_payment", "Awaiting Payment"), ("paid", "Paid")],
                default="awaiting_payment",
                max_length=30,
            ),
        ),
        migrations.RunPython(forward_status_mapping, backward_status_mapping),
    ]
