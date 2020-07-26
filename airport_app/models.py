from django.db import models
from veoc.models import quarantine_contacts
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import datetime, date
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class airline_quarantine(models.Model):
    patient_contacts = models.ForeignKey(quarantine_contacts, on_delete=models.DO_NOTHING, related_name='airline_contact')
    airline = models.CharField(max_length=100, blank=True)
    flight_number = models.CharField(max_length=200, blank=True)
    seat_number = models.CharField(max_length=200, blank=True)
    destination_city = models.CharField(max_length=200, blank=True)
    travel_history = models.CharField(max_length=200, blank=True)
    residence = models.CharField(max_length=200, blank=True)
    postal_address = models.CharField(max_length=200, blank=True)
    estate = models.CharField(max_length=200, blank=True)
    cough = models.BooleanField(default=True)
    breathing_difficulty = models.BooleanField(default=True)
    fever = models.BooleanField(default=True)
    chills = models.BooleanField(default=True)
    temperature = models.FloatField(max_length=200, blank=True, default='0.0')
    measured_temperature = models.FloatField(max_length=200, blank=True, default='0.0')
    arrival_airport_code = models.CharField(max_length=200, blank=True)
    released = models.BooleanField(default=True)
    risk_assessment_referal = models.BooleanField(default=True)
    designated_hospital_refferal = models.BooleanField(default=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=datetime.now())
    updated_at = models.DateTimeField(default=datetime.now())
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='airline_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='airline_created_by')

    def _str_(self):
        return self.patient_contacts.first_name + ' - ' + self.airline + ' - ' + self.flight_number
