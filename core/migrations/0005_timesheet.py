# Generated by Django 4.2.2 on 2023-07-04 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_sms"),
    ]

    operations = [
        migrations.CreateModel(
            name="Timesheet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(default="", max_length=100)),
                ("job_date", models.DateField(blank=True, default=None)),
                ("start_time", models.TimeField(blank=True, default=None)),
                ("quoted_hours", models.IntegerField()),
                ("worked_hours", models.IntegerField(null=True)),
                (
                    "cc_supplement",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
                ),
                (
                    "travel_supplement",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
                ),
                (
                    "extra_supplement",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
                ),
                (
                    "totals",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
                ),
                (
                    "total_pay",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
                ),
                ("paid", models.BooleanField(default=False)),
                (
                    "event",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.event",
                    ),
                ),
                (
                    "worker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.worker"
                    ),
                ),
            ],
        ),
    ]