# Generated by Django 4.2.2 on 2023-07-18 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_event_job_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='total_for_single_event',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]
