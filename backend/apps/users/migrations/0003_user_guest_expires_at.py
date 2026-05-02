from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_is_guest"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="guest_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
