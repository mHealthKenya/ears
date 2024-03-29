# Generated by Django 2.0 on 2020-08-01 06:56

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('veoc', '0108_auto_20200801_0951'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='airline_quarantine',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='airline_quarantine',
            name='patient_contacts',
        ),
        migrations.RemoveField(
            model_name='airline_quarantine',
            name='updated_by',
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='api_access_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 991304)),
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 991304)),
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='date_tested',
            field=models.DateField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 991304)),
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 991304)),
        ),
        migrations.AlterField(
            model_name='discharged_quarantine',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 994612)),
        ),
        migrations.AlterField(
            model_name='home_based_care',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 994612)),
        ),
        migrations.AlterField(
            model_name='quarantine_contacts',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 987275)),
        ),
        migrations.AlterField(
            model_name='quarantine_contacts',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 987275)),
        ),
        migrations.AlterField(
            model_name='quarantine_follow_up',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 988270)),
        ),
        migrations.AlterField(
            model_name='quarantine_revisit',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 991304)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 993328)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='date_lab_confirmation',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 993328)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='date_specimen_collected',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 993328)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='onset_of_symptoms',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 993328)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 1, 9, 56, 16, 993328)),
        ),
        migrations.DeleteModel(
            name='airline_quarantine',
        ),
    ]
