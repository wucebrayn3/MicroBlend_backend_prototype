from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role_target", models.CharField(blank=True, max_length=20, null=True)),
                ("title", models.CharField(max_length=150)),
                ("message", models.TextField()),
                ("category", models.CharField(default="general", max_length=50)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_read", models.BooleanField(default=False)),
                (
                    "recipient",
                    models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to="users.user"),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="DebounceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("actor_key", models.CharField(max_length=120)),
                ("action", models.CharField(max_length=80)),
                ("object_key", models.CharField(blank=True, max_length=120, null=True)),
            ],
            options={"unique_together": {("actor_key", "action", "object_key")}},
        ),
    ]
