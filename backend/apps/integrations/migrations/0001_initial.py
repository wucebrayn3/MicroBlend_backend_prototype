from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExternalSystem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120, unique=True)),
                ("system_type", models.CharField(choices=[("pos", "POS"), ("mobile", "Mobile"), ("kiosk", "Kiosk")], max_length=20)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="SyncEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(max_length=80)),
                ("aggregate_type", models.CharField(max_length=80)),
                ("aggregate_id", models.CharField(max_length=64)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("idempotency_key", models.CharField(blank=True, max_length=120, null=True, unique=True)),
                (
                    "source_system",
                    models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to="integrations.externalsystem"),
                ),
            ],
            options={"ordering": ("id",)},
        ),
    ]
