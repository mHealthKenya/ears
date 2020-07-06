# Generated by Django 3.0.6 on 2020-06-29 08:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('veoc', '0088_auto_20200627_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='quarantine_contacts',
            name='driver_image',
            field=models.ImageField(null=True, upload_to='Truker_Image/'),
        ),
        migrations.AlterField(
            model_name='discharged_quarantine',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 512114)),
        ),
        migrations.AlterField(
            model_name='home_based_care',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 511117)),
        ),
        migrations.AlterField(
            model_name='quarantine_contacts',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 505133)),
        ),
        migrations.AlterField(
            model_name='quarantine_contacts',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 505133)),
        ),
        migrations.AlterField(
            model_name='quarantine_follow_up',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 506130)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 511117)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='date_lab_confirmation',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 510119)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='date_specimen_collected',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 510119)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='date_specimen_taken_lab',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 510119)),
        ),
        migrations.AlterField(
            model_name='truck_quarantine_lab',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 29, 11, 41, 43, 511117)),
        ),
    ]
