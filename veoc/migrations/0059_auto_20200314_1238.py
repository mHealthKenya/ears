# Generated by Django 2.0 on 2020-03-14 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('veoc', '0058_remove_quarantine_follow_up_test_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quarantine_follow_up',
            name='cough',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='quarantine_follow_up',
            name='difficulty_breathing',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='quarantine_follow_up',
            name='fever',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='quarantine_follow_up',
            name='thermal_gun',
            field=models.CharField(max_length=20),
        ),
    ]