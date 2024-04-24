# Generated by Django 4.2.2 on 2023-07-24 16:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_invoice_total_for_single_event'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invoice',
            old_name='date',
            new_name='date_created',
        ),
        migrations.RenameField(
            model_name='invoice',
            old_name='sent_date',
            new_name='dueDate',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='cc_supplement',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='crew_count',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='date_of_event',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='duration',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='extra_supplement',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='location',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='paid_invoice',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='total_for_single_event',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='travel_supplement',
        ),
        migrations.AddField(
            model_name='event',
            name='fuel_surcharge',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='paymentTerms',
            field=models.CharField(choices=[('7 days', '7 days'), ('14 days', '14 days'), ('30 days', '30 days')], default='14 days', max_length=100),
        ),
        migrations.AddField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('CURRENT', 'CURRENT'), ('EMAIL_SENT', 'EMAIL_SENT'), ('OVERDUE', 'OVERDUE'), ('PAID', 'PAID')], default='CURRENT', max_length=100),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.client'),
        ),
    ]
