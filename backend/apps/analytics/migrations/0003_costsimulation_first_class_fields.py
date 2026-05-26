from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="costsimulation",
            name="menu_price_delta",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="costsimulation",
            name="monthly_salary_delta",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="costsimulation",
            name="staff_delta",
            field=models.IntegerField(default=0),
        ),
    ]
