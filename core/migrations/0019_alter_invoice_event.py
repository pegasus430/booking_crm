# Generated by Django 4.2.2 on 2023-07-24 18:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_event_cc_required'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.event'),
        ),
    ]
