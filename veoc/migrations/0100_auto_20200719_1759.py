# Generated by Django 3.0.6 on 2020-07-19 14:59

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('veoc', '0099_auto_20200718_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='covid_results',
            name='api_access_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 956633)),
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 956633)),
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='date_tested',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 956633)),
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='result',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='covid_results',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 956633)),
        ),
        migrations.AlterField(
            model_name='discharged_quarantine',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 958628)),
        ),
        migrations.AlterField(
            model_name='home_based_care',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 958628)),
        ),
        migrations.AlterField(
            model_name='quarantine_contacts',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 952684)),
        ),
        migrations.AlterField(
            model_name='quarantine_contacts',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 952684)),
        ),
        migrations.AlterField(
            model_name='quarantine_follow_up',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 953682)),
        ),
        migrations.AlterField(
            model_name='quarantine_revisit',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 955636)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 957632)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='date_lab_confirmation',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 957632)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='date_specimen_collected',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 957632)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='onset_of_symptoms',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 957632)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 19, 17, 59, 7, 957632)),
        ),
    ]
