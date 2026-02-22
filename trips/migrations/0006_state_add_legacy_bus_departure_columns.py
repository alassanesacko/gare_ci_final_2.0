from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trips", "0005_state_add_legacy_trip_columns"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="bus",
                    name="name",
                    field=models.CharField(blank=True, default="", max_length=100),
                ),
                migrations.AddField(
                    model_name="bus",
                    name="capacity",
                    field=models.PositiveIntegerField(default=0),
                ),
                migrations.AddField(
                    model_name="departure",
                    name="date",
                    field=models.DateField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="departure",
                    name="time",
                    field=models.TimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="departure",
                    name="is_active",
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]
