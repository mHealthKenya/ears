from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import datetime, date
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class call_incident_category(models.Model):
    incident_description = models.CharField(max_length=100)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incident_category_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incident_category_created_by')

    def __str__(self):
        return self.incident_description

class unrelated_calls_category(models.Model):
    description = models.CharField(max_length=100)
    call_incident_category_id = models.ForeignKey(call_incident_category, on_delete=models.CASCADE, default=3)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unrelated_call_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unrelated_call_created_by')

    def __str__(self):
        return self.description

class incident_status(models.Model):
    status_description = models.CharField(max_length=100)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incident_type_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incident_type_created_by')

    def __str__(self):
        return self.status_description

class disease_type(models.Model):
    disease_description = models.CharField(max_length=1000)
    priority_disease = models.BooleanField(default=False)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disease_type_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disease_type_created_by')

    class Meta:
        ordering = ('disease_description',)

    def __str__(self):
        return self.disease_description

class event_type(models.Model):
    event_description = models.CharField(max_length=1000)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_type_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_type_created_by')

    def __str__(self):
        return self.event_description

class county(models.Model):
    description= models.CharField(max_length=1000)
    longitude=models.CharField(max_length=1000, default=36.8167)
    latitude=models.CharField(max_length=1000, default=-1.2833)

    def natural_key(self):
        return (self.description)

    def __str__(self):
        return self.description

    class meta:
        unique_together=(('description'),)

class sub_county(models.Model):
    county=models.ForeignKey(county,on_delete=models.CASCADE)
    subcounty=models.CharField(max_length=1000)
    longitude=models.CharField(max_length=1000, default=36.8167)
    latitude=models.CharField(max_length=1000, default=-1.2833)

    def natural_key(self):
        return (self.subcounty)

    def __str__(self):
        return self.subcounty

    class meta:
        unique_together=(('subcounty'),)

class organizational_units(models.Model):
    uid = models.CharField(max_length=50)
    organisationunitid = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50)
    parentid = models.CharField(max_length=50)
    hierarchylevel = models.IntegerField()
    latitude=models.CharField(max_length=100, default='0.0000')
    longitude=models.CharField(max_length=100, default='0.0000')

    class Meta:
       ordering = ['name']
    def __str__(self):
        return self.organisationunitid

class persons(models.Model):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{10,12}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    org_unit = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='persons_org_uit', default='2620')
    access_level = models.CharField(max_length=10, default='National')
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='persons_county', default='2620')
    sub_county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='persons_subcounty', default='2620')
    phone_number = models.CharField(validators=[phone_regex], max_length=12, blank=False, default='0700000000')

    class Meta:
        ordering = ['user']
    def __str__(self):
        return self.user.username + ' - ' + self.org_unit.name

class dhis_disease_type(models.Model):
    uid = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    priority_disease = models.BooleanField(default=False)
    infectious_disease = models.BooleanField(default=False)

    def __str__(self):
        return self.uid + ' - ' + self.name

class dhis_event_type(models.Model):
    uid = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.uid + ' - ' + self.name

class data_source(models.Model):
    source_description = models.CharField(max_length=50)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_source_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_source_created_by')

    def natural_key(self):
        return (self.source_description)

    def __str__(self):
        return self.source_description

    class meta:
        unique_together=(('source_description'),)

class reporting_region(models.Model):
    region_description = models.CharField(max_length=1000)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reporting_region_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reporting_region_created_by')

    def natural_key(self):
        return (self.region_description)

    def __str__(self):
        return self.region_description

    class meta:
        unique_together=(('region_description'),)

class accesslevel(models.Model):
    description = models.CharField(max_length=50)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_level_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_level_created_by')

class user_profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    accesslevel = models.ForeignKey(accesslevel, on_delete=models.CASCADE, blank=False)
    county = models.ForeignKey(county, on_delete=models.CASCADE, blank=True)
    subcounty = models.ForeignKey(sub_county, on_delete=models.CASCADE, blank=True)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_profile_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_profile_created_by')

    def __str__(self):
        return self.user.username + ' - ' + self.accesslevel.description

User.profile = property(lambda u: user_profile.objects.get_or_create(user=u)[0])

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
#
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()

class call_log(models.Model):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{10,12}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    call_category = models.ForeignKey(call_incident_category, on_delete=models.CASCADE)
    call_category_incident = models.IntegerField(default=0, blank=False)
    incident_status = models.ForeignKey(incident_status, on_delete=models.CASCADE, default=0)
    reporting_region = models.ForeignKey(reporting_region, on_delete=models.CASCADE, default=0)
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='call_log_county', default='2620')
    subcounty = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='call_log_subcounty', default='2620')
    ward = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='call_log_ward', default='2620')
    location = models.CharField(max_length=100, blank=True)
    caller_name = models.CharField(max_length=100, blank=True)
    caller_number = models.CharField(validators=[phone_regex], max_length=12, blank=False)
    date_reported = models.DateTimeField(default=datetime.now)
    call_description = models.TextField(max_length=500)
    action_taken = models.TextField(max_length=500, blank=True)
    significant = models.BooleanField(default=False)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_log_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_log_created_by')

    class Meta:
       ordering = ['-created_at']
    def __str__(self):
        return self.call_category.incident_description + ' - ' + self.county.name

class event(models.Model):
    CASE_CHOICES = [(1,'Open'),(2,'Closed')]

    event_type = models.ForeignKey(dhis_event_type, on_delete=models.CASCADE, related_name='events_types')
    data_source = models.ForeignKey(data_source, on_delete=models.CASCADE)
    incident_status = models.ForeignKey(incident_status, on_delete=models.CASCADE, default=0)
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='event_county', default='2620')
    subcounty = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='event_subcounty', default='2620')
    ward = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='event_ward', default='2620')
    reporting_region = models.ForeignKey(reporting_region, on_delete=models.CASCADE)
    date_reported = models.DateTimeField(default=datetime.now)
    cases = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    remarks = models.TextField(max_length=500)
    action_taken = models.TextField(max_length=500, default='None')
    significant_event = models.BooleanField(default=False)
    case_status = models.CharField(choices=[(1,'Open'),(2,'Closed')],default=1, blank=False, max_length=10)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_created_by')

    class Meta:
       ordering = ['-created_at']

    def __str__(self):
       return str(self.created_at) + ' - ' +self.event_type.name

class disease(models.Model):
    CASE_CHOICES = [(1,'Open'),(2,'Closed')]

    disease_type = models.ForeignKey(dhis_disease_type, on_delete=models.CASCADE, related_name='disease_types')
    data_source = models.ForeignKey(data_source, on_delete=models.CASCADE)
    incident_status = models.ForeignKey(incident_status, on_delete=models.CASCADE, default=0)
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='disease_county', default='2620')
    subcounty = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='disease_subcounty', default='2620')
    ward = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='disease_ward', default='2620')
    reporting_region = models.ForeignKey(reporting_region, on_delete=models.CASCADE)
    date_reported = models.DateTimeField(default=datetime.now)
    cases = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    remarks = models.TextField(max_length=500)
    action_taken = models.TextField(max_length=500, default='None')
    significant = models.BooleanField(default=False)
    case_status = models.CharField(choices=[(1,'Open'),(2,'Closed')],default=1, blank=False, max_length=10)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disease_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disease_created_by')

    class Meta:
       ordering = ['-created_at']
    def __str__(self):
        return self.disease_type.name

class infectious_disease(models.Model):

    disease_type = models.ForeignKey(dhis_disease_type, on_delete=models.CASCADE, related_name='infectious_disease_types')
    data_source = models.ForeignKey(data_source, on_delete=models.CASCADE)
    incident_status = models.ForeignKey(incident_status, on_delete=models.CASCADE, default=0)
    reporting_region = models.ForeignKey(reporting_region, on_delete=models.CASCADE)
    date_reported = models.DateTimeField(default=datetime.now)
    remarks = models.TextField(max_length=500)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infectious_disease_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infectious_disease_created_by')

    class Meta:
       ordering = ['-created_at']
    def __str__(self):
        return self.disease_type.name

class facilities(models.Model):
    facility_name=models.CharField(max_length=100)
    facility_level=models.CharField(max_length=10)
    facility_type=models.CharField(max_length=10, default='Private')
    mfl_code=models.CharField(max_length=10)
    county = models.ForeignKey(county, on_delete=models.CASCADE)
    subcounty = models.ForeignKey(sub_county, on_delete=models.CASCADE)
    latitude=models.CharField(max_length=100, default='0.0000')
    longitude=models.CharField(max_length=100, default='0.0000')

    def __str__(self):
        return self.facility_name

class idsr_diseases(models.Model):
    uid = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.uid + ' - ' + self.name

class idsr_reported_incidents(models.Model):
    category_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.category_id + ' - ' + self.name

class idsr_weekly_facility_report(models.Model):
    idsr_disease_id = models.ForeignKey(idsr_diseases, on_delete=models.CASCADE, default='1')
    idsr_incident_id = models.ForeignKey(idsr_reported_incidents, on_delete=models.CASCADE, default='1')
    org_unit_id = models.ForeignKey(organizational_units, on_delete=models.CASCADE, default='1')
    period = models.CharField(max_length=100, default='000000')
    data_value = models.FloatField(max_length=50)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateTimeField(default=datetime.now)

class dhis_disease_data_elements(models.Model):
    uid = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.uid + ' - ' + self.name

class dhis_reported_diseases(models.Model):
    program = models.CharField(max_length=50, default='Jt6SPO0bjKB')
    org_unit_id = models.ForeignKey(organizational_units, on_delete=models.CASCADE)
    disease_type = models.ForeignKey(dhis_disease_type, on_delete=models.CASCADE, related_name='dhis2_disease_types')
    eventDate = models.DateField(default=date.today)
    period = models.CharField(max_length=20, default='000000')
    status = models.CharField(max_length=50, default='COMPLETED')
    stored_by = models.CharField(max_length=10, default='eoc_user')

    def __str__(self):
        return self.org_unit_uid.uid + ' - ' + self.name

class dhis_disease_data_values(models.Model):
    dhis_reported_disease_id = models.ForeignKey(dhis_reported_diseases, on_delete=models.CASCADE)
    data_element_id = models.ForeignKey(dhis_disease_data_elements, on_delete=models.CASCADE)
    data_value = models.CharField(max_length=50)
    sent_status = models.CharField(max_length=2, default=0)

    def __str__(self):
        return self.dhis_reported_disease_id.disease_type.name + ' - ' + self.data_value

class dhis_event_data_elements(models.Model):
    uid = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.uid + ' - ' + self.name

class dhis_reported_events(models.Model):
    program = models.CharField(max_length=50, default='hH7eq688OJT')
    org_unit_id = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='dhis2_events_types')
    event_type = models.ForeignKey(dhis_event_type, on_delete=models.CASCADE)
    eventDate = models.DateField(default=date.today)
    period = models.CharField(max_length=20)
    status = models.CharField(max_length=50, default='COMPLETED')
    stored_by = models.CharField(max_length=10, default='eoc_user')

    def __str__(self):
        return self.org_unit_uid.uid + ' - ' + self.name

class dhis_event_data_values(models.Model):
    dhis_reported_event_id = models.ForeignKey(dhis_reported_events, on_delete=models.CASCADE)
    data_element_id = models.ForeignKey(dhis_event_data_elements, on_delete=models.CASCADE)
    data_value = models.CharField(max_length=50)
    sent_status = models.CharField(max_length=2, default=0)

    def __str__(self):
        return self.data_element_uid.name + ' - ' + self.data_value

class idsr_weekly_national_report(models.Model):
    idsr_disease_id = models.ForeignKey(idsr_diseases, on_delete=models.CASCADE, default='1')
    idsr_incident_id = models.ForeignKey(idsr_reported_incidents, on_delete=models.CASCADE, default='1')
    org_unit_id = models.ForeignKey(organizational_units, on_delete=models.CASCADE)
    period = models.CharField(max_length=100, default='000000')
    data_value = models.FloatField(max_length=50)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateTimeField(default=datetime.now)

class v_dhis_national_data_view(models.Model):
    id = models.BigIntegerField(primary_key=True)
    period = models.CharField(max_length=100)
    idsr_disease_id = models.ForeignKey(idsr_diseases, on_delete=models.DO_NOTHING)
    idsr_incident_id = models.ForeignKey(idsr_reported_incidents, on_delete=models.DO_NOTHING)
    data_value = models.FloatField(max_length=50)

    class Meta:
        managed = False
        db_table = 'v_dhis_national_data_view'

class v_dhis_national_report_data_view(models.Model):
    id = models.BigIntegerField(primary_key=True)
    period = models.CharField(max_length=100)
    idsr_disease_id = models.ForeignKey(idsr_diseases, on_delete=models.DO_NOTHING)
    # idsr_incident_id = models.ForeignKey(idsr_reported_incidents, on_delete=models.DO_NOTHING)
    cases = models.FloatField(max_length=50)
    deaths = models.FloatField(max_length=50)

    class Meta:
        managed = False
        db_table = 'v_dhis_national_report_data_view'

class standard_case_definitions(models.Model):
    code = models.CharField(max_length=20)
    condition = models.ForeignKey(dhis_disease_type, null=True, on_delete=models.SET_NULL, related_name='std_case_disease_types', default='1')
    incubation_period = models.CharField(max_length=50)
    suspected_standard_case_def = models.CharField(max_length=1000)
    confirmed_standard_case_def = models.CharField(max_length=1000)
    signs_and_symptoms = models.CharField(max_length=1000)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='std_case_updated_by')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='std_case_created_by')

    class Meta:
       ordering = ['-code']
    def __str__(self):
        return str(self.condition)

# class moh_linelisting(models.Model):
#     names = models.CharField(max_length=100)
#     patient_statud = models.CharField(max_length=20)
#     county = models.CharField(max_length=20)
#     subcounty = models.CharField(max_length=20)
#     location = models.CharField(max_length=20)
#     sublocation = models.CharField(max_length=20)
#     village = models.CharField(max_length=20)
#     ward = models.CharField(max_length=20)
#     facility = models.CharField(max_length=20)
#     sex = models.CharField(max_length=20)
#     age = models.IntegerField(max_length=20)
#     date_seen = models.DateField(max_length=20)
#     date_onset = models.CharField(max_length=20)
#     epi_week = models.CharField(max_length=20)
#     doses_of_vaccine = models.IntegerField(max_length=20)
#     lab_test = models.CharField(max_length=20)
#     speciment_taken = models.CharField(max_length=20)
#     speciment_date = models.IntegerField(max_length=20)
#     speciment_type = models.CharField(max_length=20)
#     lab_results = models.CharField(max_length=20)
#     rdt = models.CharField(max_length=20)
#     culture = models.CharField(max_length=20)
#     outcome = models.CharField(max_length=20)
#     comments = models.CharField(max_length=100)
#     next_of_kin = models.IntegerField(max_length=20)

class police_post(models.Model):
    police_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,12}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    police_post_code=models.CharField(max_length=50)
    police_post_name=models.CharField(max_length=50)
    ocs_names = models.CharField(max_length=50)
    ocs_phone = models.CharField(validators=[police_phone_regex], max_length=12, blank=False)
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='post_county')
    subcounty = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='post_subcounty')
    ward = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='post_ward')
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_created_by')

    def __str__(self):
        return self.police_post_name

class referral_labs(models.Model):
    tech_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,12}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    lab_referral_code=models.CharField(max_length=10)
    lab_referral_name=models.CharField(max_length=20)
    lead_lab_tech_name=models.CharField(max_length=20)
    lead_lab_tech_phone = models.CharField(validators=[tech_phone_regex], max_length=12, blank=False)
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='refferal_county')
    subcounty = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='refferal_subcounty')
    ward = models.ForeignKey(organizational_units, on_delete=models.CASCADE)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refferal_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refferal_created_by')

    def __str__(self):
        return self.referal_name

class designation(models.Model):
    designation_description = models.CharField(max_length=500)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designation_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designation_created_by')

    def __str__(self):
        return self.designation_description

class contact_type(models.Model):
    contact_description = models.CharField(max_length=500)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_type_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_type_created_by')

    def natural_key(self):
        return (self.contact_description)

    def __str__(self):
        return self.contact_description

    class meta:
        unique_together=(('contact_description'),)

class country(models.Model):
    phone_code = models.IntegerField(blank=False)
    name = models.CharField(max_length=50)
    iso = models.CharField(max_length=50)
    iso3 = models.CharField(max_length=50)

class contact(models.Model):
    person_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,12}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    designation = models.ForeignKey(designation, on_delete=models.CASCADE, blank=True)
    phone_number = models.CharField(validators=[person_phone_regex], max_length=12, blank=False)
    email_address = models.EmailField(max_length=20, blank=True)
    type_of_contact = models.ForeignKey(contact_type, on_delete=models.CASCADE, blank=True)
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='contact_county')
    subcounty = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='contact_subcounty')
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_created_by')

    def __str__(self):
        return self.county.description + ' - ' + self.contact_type.description

class translation_languages(models.Model):
    language_name = models.CharField(max_length=20)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='language_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='language_created_by')

    def __str__(self):
        return self.language_name

class translation_messages(models.Model):
    language = models.ForeignKey(translation_languages, on_delete=models.CASCADE, blank=False)
    massage = models.CharField(max_length=200)
    message_description = models.CharField(max_length=50)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='massage_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='massage_created_by')

    def __str__(self):
        return self.language_name

class quarantine_sites(models.Model):
    person_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    site_name = models.CharField(max_length=500)
    team_lead_names = models.CharField(max_length=500)
    team_lead_phone = models.CharField(validators=[person_phone_regex], max_length=15, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quarantine_sites_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quarantine_sites_created_by')

    def natural_key(self):
        return (self.site_name)

    def __str__(self):
        return self.site_name

    class meta:
        unique_together=(('site_name'),)

class quarantine_contacts(models.Model):
    person_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    contact_uuid = models.CharField(max_length=50, blank=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    sex = models.CharField(max_length=50)
    dob = models.DateField(default=date.today)
    passport_number = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(validators=[person_phone_regex], max_length=255, blank=False)
    email_address = models.EmailField(max_length=20, blank=True)
    origin_country = models.CharField(max_length=50,default='KENYA')
    county = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='quarantine_county', blank=True)
    nationality = models.CharField(max_length=50, default='KENYA')
    subcounty = models.ForeignKey(organizational_units, on_delete=models.CASCADE, related_name='quarantine_subcounty', blank=True)
    ward = models.ForeignKey(organizational_units, on_delete=models.CASCADE, blank=True, related_name='quarantine_ward', default='2620')
    place_of_diagnosis = models.CharField(max_length=50, blank=True)
    drugs = models.CharField(max_length=50, blank=True)
    nok = models.CharField(max_length=50, blank=True)
    nok_phone_num = models.CharField(validators=[person_phone_regex], max_length=255, blank=True)
    cormobidity = models.CharField(max_length=50, blank=True)
    place_of_diagnosis = models.CharField(max_length=50, blank=True)
    quarantine_site = models.ForeignKey(quarantine_sites, on_delete=models.DO_NOTHING, related_name='quarantine_site', default=1)
    date_of_contact = models.DateField(default=date.today)
    contact_state = models.CharField(max_length=50, blank=True)
    physical_address = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=50, blank=True)
    communication_language = models.ForeignKey(translation_languages, on_delete=models.DO_NOTHING, related_name='quarantine_language', default='1')
    created_at = models.DateTimeField(default=datetime.now())
    updated_at = models.DateTimeField(default=datetime.now())
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quarantine_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quarantine_created_by')

    def __str__(self):
        return self.first_name + ' - ' + self.phone_number

    @property
    def age(self):
        return int((datetime.now().date() - self.dob).days / 365.25)

class quarantine_follow_up(models.Model):
    patient_contacts = models.ForeignKey(quarantine_contacts, on_delete=models.DO_NOTHING, related_name='followup_contact')
    self_quarantine = models.BooleanField(default=False)
    thermal_gun = models.CharField(max_length=20)
    body_temperature = models.FloatField(blank=False)
    fever = models.CharField(max_length=20)
    cough = models.CharField(max_length=20)
    difficulty_breathing = models.CharField(max_length=20)
    follow_up_day = models.IntegerField(blank=False)
    comment = models.CharField(max_length=160, blank=True)
    sms_status = models.CharField(max_length=10, default="No")
    lat = models.FloatField(default=0.0000)
    lng = models.FloatField(default=0.0000)
    created_at = models.DateTimeField(default=datetime.now())

class weighbridge_sites(models.Model):
    person_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    weighbridge_name = models.CharField(max_length=50)
    weighbridge_location = models.CharField(max_length=50)
    team_lead_names = models.CharField(max_length=500)
    team_lead_phone = models.CharField(validators=[person_phone_regex], max_length=15, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='weighbridge_sites_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='weighbridge_sites_created_by')

    def natural_key(self):
        return (self.weighbridge_name)

    def __str__(self):
        return self.weighbridge_name

    class meta:
        unique_together=(('weighbridge_name'),)

class border_points(models.Model):
    person_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    border_name = models.CharField(max_length=50)
    border_location = models.CharField(max_length=50)
    team_lead_names = models.CharField(max_length=500)
    team_lead_phone = models.CharField(validators=[person_phone_regex], max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='border_points_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='border_points_created_by')

    def natural_key(self):
        return (self.border_name)

    def __str__(self):
        return self.border_name

    class meta:
        unique_together=(('border_name'),)

class truck_quarantine_contacts(models.Model):
    person_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    patient_contacts = models.ForeignKey(quarantine_contacts, on_delete=models.DO_NOTHING, related_name='truck_quarantine_contact')
    street = models.CharField(max_length=50, blank=True)
    village = models.CharField(max_length=50, blank=True)
    vehicle_registration = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=50, blank=True)
    company_phone = models.CharField(validators=[person_phone_regex], max_length=255, blank=False)
    company_physical_address = models.CharField(max_length=50, blank=True)
    company_street = models.CharField(max_length=50, blank=True)
    company_building = models.CharField(max_length=50, blank=True)
    weighbridge_facility = models.ForeignKey(weighbridge_sites, on_delete=models.DO_NOTHING, related_name='weighbridge_contact_facility', blank=False)
    border_point = models.ForeignKey(border_points, on_delete=models.DO_NOTHING, related_name='border_contact_facility', blank=False)
    cough = models.BooleanField(default=True)
    breathing_difficulty = models.BooleanField(default=True)
    fever = models.BooleanField(default=True)
    temperature = models.FloatField(max_length=20, blank=True, default='0.0')
    sample_taken = models.BooleanField(default=True)
    action_taken = models.CharField(max_length=100, blank=True)
    hotel = models.CharField(max_length=50, blank=True)
    hotel_phone = models.CharField(validators=[person_phone_regex], max_length=255, blank=False)
    hotel_town = models.CharField(max_length=50, blank=True)
    date_check_in = models.DateField(default=date.today)
    date_check_out = models.DateField(default=date.today)

    def __str__(self):
        return self.patient_contacts.first_name + ' - ' + self.vehicle_registration

class truck_quarantine_lab(models.Model):
    patient_contacts = models.ForeignKey(quarantine_contacts, on_delete=models.DO_NOTHING, related_name='truck_lab_contact')
    test_sample_uuid = models.CharField(max_length=50, blank=True)
    covid_test_done = models.BooleanField(default=False)
    specimen_taken = models.BooleanField(default=False)
    reason_speciment_not_taken = models.CharField(max_length=255, blank=True)
    date_specimen_collected = models.DateTimeField(default=datetime.now())
    specimen_type = models.CharField(max_length=50, blank=True)
    other_specimen_type = models.CharField(max_length=50, blank=True)
    viral_respiratory_illness = models.BooleanField(default=False)
    respiratory_illness_results = models.CharField(max_length=50, blank=True)
    date_specimen_taken_lab = models.DateTimeField(default=datetime.now())
    name_of_lab = models.CharField(max_length=50, blank=True)
    assay_used = models.CharField(max_length=50, blank=True)
    sequencing_done = models.CharField(max_length=50, blank=True)
    lab_results = models.CharField(max_length=50, blank=True)
    date_lab_confirmation = models.DateTimeField(default=datetime.now())
    source = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=datetime.now())
    updated_at = models.DateTimeField(default=datetime.now())
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='truck_lab_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='truck_lab_created_by')

    def __str__(self):
        return self.patient_contacts.first_name + ' - ' + self.specimen_type


class watcher_team_leads(models.Model):
    team_lead=models.ForeignKey(contact, on_delete=models.CASCADE, blank=False)
    team_name=models.CharField(max_length=20)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_created_by')

    def __str__(self):
        return self.team_name

class watcher_teams(models.Model):
    team_lead=models.ForeignKey(watcher_team_leads, on_delete=models.CASCADE, blank=False)
    team_member=models.ForeignKey(contact, on_delete = models.CASCADE, blank=False)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watcher_team_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watcher_team_created_by')

    def __str__(self):
        return self.team_lead.team_name

    class meta:
        unique_together=(('team_member'),)

class watchers_shifts(models.Model):
    team = models.ForeignKey(watcher_team_leads, on_delete=models.CASCADE, blank=False)
    week_no = models.IntegerField(default=0)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(default=date.today)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watcher_shift_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watcher_shift_created_by')

    def __str__(self):
        return self.team

class eoc_events_calendar(models.Model):
    event_name = models.CharField(max_length=50)
    event_description = models.CharField(max_length=200)
    time = models.TimeField()
    start_date = models.DateTimeField(default=datetime.now)
    end_date = models.DateTimeField(default=datetime.now)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_created_by')

    def __str__(self):
        return self.event_name + ' - ' + self.event_description

class eoc_status(models.Model):
    status_description = models.CharField(max_length=500)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.status_description

class repository_categories(models.Model):
    category_name=models.CharField(max_length=50)
    description=models.CharField(max_length=100)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_created_by')

    def __str__(self):
        return self.description

class document_repository(models.Model):
    category=models.ForeignKey(repository_categories, on_delete=models.CASCADE, related_name='document_category')
    description=models.CharField(max_length=500)
    author=models.CharField(max_length=50)
    myfile=models.FileField(upload_to='Documents')
    public_document = models.BooleanField(default=False)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_created_by')


    def __str__(self):
        return self.description

class staff_contact(models.Model):
    person_phone_regex = RegexValidator(regex=r'^\+?1?\d{10,12}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    designation = models.ForeignKey(designation, on_delete=models.CASCADE, related_name='contact_staff_designation')
    phone_number = models.CharField(validators=[person_phone_regex], max_length=12, blank=False)
    email_address = models.EmailField(max_length=20, blank=True)
    team_lead = models.BooleanField(default=False)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_staff_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_staff_created_by')

    def __str__(self):
        return self.first_name + ' - ' + self.email_address

class watcher_schedule(models.Model):

    watcher_details = models.ForeignKey(staff_contact, on_delete=models.CASCADE, related_name='watcher_details')
    week_no = models.IntegerField(default=0)
    from_date = models.CharField(max_length=500,default="")
    to_date = models.CharField(max_length=500,default="")
    deleted = models.CharField(max_length=20,default="N")
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedule_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedule_created_by')

    def __str__(self):
        return self.watcher_details.first_name

    class meta:
        unique_together=(('watcher_details'),)

class system_modules(models.Model):
    module_name = models.CharField(max_length=30)
    module_description = models.TextField(max_length=500)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_created_by')

class feedback(models.Model):
    module_type = models.ForeignKey(system_modules, on_delete=models.CASCADE, default=0)
    challenge = models.TextField(max_length=1000)
    recommendation = models.TextField(max_length=1000)
    challange_addressed = models.BooleanField(default=False)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_created_by')

    class Meta:
       ordering = ['-created_at']
    def __str__(self):
        return self.module_type.module_name

class general_feedback(models.Model):
    challenge = models.TextField(max_length=1000)
    challange_addressed = models.BooleanField(default=False)
    created_at = models.DateField(default=date.today)
    updated_at = models.DateField(default=date.today)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gen_feedback_updated_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gen_feedback_created_by')

    class Meta:
       ordering = ['-created_at']
    def __str__(self):
        return self.challenge
