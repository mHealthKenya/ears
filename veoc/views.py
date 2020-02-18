from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login as login_auth, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.template import RequestContext, loader
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
import csv, io
from django.conf import settings
from django.core.serializers import serialize
from django.http import HttpResponse
from django.db import transaction
from django.db.models import *
from veoc.models import *
from veoc.forms import *
from django.views.decorators.csrf import *
from . import forms
from rest_framework import viewsets
from veoc.serializer import *
from veoc.tasks import pull_dhis_idsr_data
from datetime import date, timedelta, datetime
from collections import Counter
from django import template
import time
import json
from itertools import chain
from operator import attrgetter

register = template.Library()

# Create your views here.
contacts = contact_type.objects.all()

class DiseaseView(viewsets.ModelViewSet):
    queryset = disease.objects.all()
    serializer_class = DiseaseSerializer

class EventView(viewsets.ModelViewSet):
    queryset = event.objects.all()
    serializer_class = EventSerializer

class disease_type_view(viewsets.ModelViewSet):
    queryset = dhis_disease_type.objects.all()
    serializer_class = DiseaseTypesSerializer

class event_type_view(viewsets.ModelViewSet):
    queryset = dhis_event_type.objects.all()
    serializer_class = DiseaseTypesSerializer

class data_source_view(viewsets.ModelViewSet):
    queryset = data_source.objects.all()
    serializer_class = DataSourceSerializer

class reporting_region_view(viewsets.ModelViewSet):
    queryset = reporting_region.objects.all()
    serializer_class = ReportingRegionSerializer

class incident_status_view(viewsets.ModelViewSet):
    queryset = incident_status.objects.all()
    serializer_class = IncidentStatusSerializer

class organizational_unit_view(viewsets.ModelViewSet):
    queryset = organizational_units.objects.all()
    serializer_class = OrganizationalUnitsSerializer

def not_in_manager_group(user):
    if user:
        return user.groups.filter(name='National Managers').count() == 0
    return False

def login(request):
    global next

    if request.method == "POST":
        user_name = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=user_name, password=password)

        if user is not None:
            if user.is_active:
                login_auth(request, user)
                #get the person org unit to redirect to the correct Dashboard
                u = User.objects.get(username=user_name)
                user_access_level = u.persons.access_level

                print(user_access_level)

                #Get access level to determine what dashboard to loads
                if user_access_level == 'National' :
                    print('inside National dashboard')
                    next = '/dashboard/'
                    print(next)

                elif user_access_level == 'County':
                    print('inside county dashboard')
                    next = '/county_dashboard/'
                    print(next)
                else:
                    print('inside subcounty dashboard')
                    next = '/subcounty_dashboard/'
                    print(next)

                # messages.info(request, 'Login successfully!')
                return HttpResponseRedirect(next)
            else:
                # messages.info(request, 'Username or Password NOT matching!')
                return HttpResponse("Inactive user.")
        else:
            # messages.error(request, 'User Not Registered!')
            return HttpResponseRedirect(settings.LOGIN_URL)
    else:
        return render(request, 'veoc/login.html')

def logout(request):

    return HttpResponseRedirect(settings.LOGIN_URL)

def access_dashboard(request):
    #get the person org unit to redirect to the correct Dashboard
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level

    print(user_access_level)

    #Get access level to determine what dashboard to loads
    if user_access_level == 'National' :
        print('inside National dashboard')
        next = '/dashboard/'
        print(next)

    elif user_access_level == 'County':
        print('inside county dashboard')
        next = '/county_dashboard/'
        print(next)

    else:
        print('inside subcounty dashboard')
        next = '/subcounty_dashboard/'
        print(next)

    messages.info(request, 'Your password was updated successfully!')
    return HttpResponseRedirect(next)

def user_register(request):

    if request.method == 'POST':
        first_name = request.POST.get('first_name','')
        last_name = request.POST.get('last_name','')
        user_name = request.POST.get('user_name','')
        email = request.POST.get('email','')
        phone_no = request.POST.get('phone_no','')
        access_level = request.POST.get('access_level','')
        org_unit = request.POST.get('org_unit','')
        sub_cnty = request.POST.get('subcounty','')
        user_group = request.POST.get('usergroup','')
        super_user = request.POST.get('user_status','')

        # Getting users group id
        # group_name = Group.objects.get(name=user_group)
        # print(group_name.id)

        # if user is National user, default county and subcounty id to the
        # national id (Kenya id)
        if org_unit == '':
            org_unit = 18
        if sub_cnty == '':
            sub_cnty = 18

        user = User.objects.create_user(username= user_name, email=email, password=email, first_name=first_name,
                last_name=last_name, is_superuser=super_user, is_staff="t", is_active="t")

        user.save()
        user_id = user.pk
        userObject = User.objects.get(pk = user_id)
        # userGroupObject = Group.objects.get(pk = group_name.id)
        orgunitObject = organizational_units.objects.get(organisationunitid = org_unit)
        subcntyObject = organizational_units.objects.get(organisationunitid = sub_cnty)
        # print(user_id)

        #save user groups tables
        # create_usergroup(userObject, userGroupObject)
        # user_grps = User_groups.objects.create()

        #save the user in persons tables
        user_person = persons.objects.create(user=userObject, org_unit=orgunitObject, phone_number=phone_no,
            access_level=access_level, county=orgunitObject, sub_county=subcntyObject)

    users_count = User.objects.all().count()
    users = User.objects.all()
    org_units = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    user_groups = Group.objects.all()

    values = {'users_count': users_count, 'users':users, 'org_units': org_units, 'user_groups':user_groups}

    return render(request, 'veoc/users.html', values)

@csrf_exempt
def dashboard(request):

    _dcall_logs = disease.objects.all().filter(data_source = 1).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(data_source = 1).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    marquee_call_log = []#an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []#an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []#an array that collects all confirmed diseases and maps them to the marquee

    #checks if dictionary has values for the past 7 days
    if len(_dcall_logs) == 0:
        marquee_call_log.append("None reported")
    else:
        for _dlogs in _dcall_logs:
            marquee_call_log.append(_dlogs)

    if len(_ecall_logs) == 0:
        marquee_call_log.append("")
    else:
        for _elogs in _ecall_logs:
            marquee_call_log.append(_elogs)

    if len(_events) == 0:
        marquee_events.append("None reported")
    else:
        for _eve in _events:
            marquee_events.append(_eve)

    if len(_disease) == 0:
        marquee_disease.append("None reported")
    else:
        for _dis in _disease:
            marquee_disease.append(_dis)

    #Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(incident_status = 1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(call_category=1).filter(incident_status=2).filter(date_reported__gte = date.today()- timedelta(days=1)).order_by("-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(call_category=1).filter(incident_status=1).order_by("-date_reported").count()
    # print(rum_disease_call_log_count)

    #Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(incident_status = 1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(incident_status = 3).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(call_category=2).filter(incident_status=2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(call_category=2).filter(incident_status=1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count=conf_event_count+conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()

    #changed call logs button
    disease_related_calls = call_log.objects.filter(call_category=1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(call_category=2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(date_reported__gte = date.today()- timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(date_reported__gte = date.today()- timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    #Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease = True)
    disease_report_stat= {}
    thirty_days_stat= {}
    for d_type in disease_types:
       diseases_count = disease.objects.all().filter(disease_type_id=d_type.id).count()
       thirty_days_disease_count = disease.objects.all().filter(disease_type_id=d_type.id).filter(date_reported__gte = date.today()- timedelta(days=30)).count()
       if thirty_days_disease_count > 0:
        disease_report_stat[d_type.name] = diseases_count
        thirty_days_stat[d_type.name] = thirty_days_disease_count

    #picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    #ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat= {}
    events_thirty_days_stat= {}
    for e_type in event_types:
       events_count = event.objects.all().filter(event_type_id=e_type.id).count()
       events_thirty_days_disease_count = event.objects.all().filter(event_type_id=e_type.id).filter(date_reported__gte = date.today()- timedelta(days=30)).count()
       if events_thirty_days_disease_count > 0:
        events_report_stat[e_type.name] = events_count
        events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    #picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))

    #Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}#variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(county_id = cnty.id).filter(date_reported__gte = date.today()- timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid = cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(subcounty_id = subcnty.id).filter(county_id = cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name':cnty.name, 'id':cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)

    #pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(disease_type_id = crt_tpye.id).filter(date_reported__gte = date.today()- timedelta(days=30)).values('disease_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        cases.append(disease_descriptions)

    #pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(event_type_id = crt_tpye.id).filter(date_reported__gte = date.today()- timedelta(days=30)).values('event_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        event_cases.append(event_descriptions)

    #line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        # dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id = crt_tpye.id).values('idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period', 'data_value').distinct()
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id = crt_tpye.id).values('idsr_disease_id__name', 'org_unit_id_id__name', 'period', 'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    #pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    #pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active = False)

    template = loader.get_template('veoc/dashboard.html')
    context = RequestContext(request,{
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'd_count': disease.objects.filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls' : disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported"),
        'disease_vals':disease.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat,
        'disease_reported_dash_vals':disease_reported_dash_vals,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))

def county_dashboard(request):

    #get the person org unit to dislay county on the Dashboard
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_county_id = u.persons.county_id

    #get county names
    county_object = organizational_units.objects.get(pk = user_county_id)
    county_name = county_object.name

    # print(county_name)
    # print(user_county_id)

    _dcall_logs = disease.objects.all().filter(county = user_county_id).filter(data_source = 1).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(county = user_county_id).filter(data_source = 1).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(county = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(county = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    marquee_call_log = []#an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []#an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []#an array that collects all confirmed diseases and maps them to the marquee

    #checks if dictionary has values for the past 7 days
    if len(_dcall_logs) == 0:
        marquee_call_log.append("None reported")
    else:
        for _dlogs in _dcall_logs:
            marquee_call_log.append(_dlogs)

    if len(_ecall_logs) == 0:
        marquee_call_log.append("")
    else:
        for _elogs in _ecall_logs:
            marquee_call_log.append(_elogs)

    if len(_events) == 0:
        marquee_events.append("None reported")
    else:
        for _eve in _events:
            marquee_events.append(_eve)

    if len(_disease) == 0:
        marquee_disease.append("None reported")
    else:
        for _dis in _disease:
            marquee_disease.append(_dis)


    #Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(county = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(county = user_county_id).filter(incident_status = 1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(county = user_county_id).filter(call_category=1).filter(incident_status=2).filter(date_reported__gte = date.today()- timedelta(days=1)).order_by("-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(county = user_county_id).filter(call_category=1).filter(incident_status=1).order_by("-date_reported").count()
    # print(rum_disease_call_log_count)

    #Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(county = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(county = user_county_id).filter(incident_status = 1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(county = user_county_id).filter(incident_status = 3).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(county = user_county_id).filter(call_category=2).filter(incident_status=2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(county = user_county_id).filter(call_category=2).filter(incident_status=1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count=conf_event_count+conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(county = user_county_id).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()

    #changed call logs button
    disease_related_calls = call_log.objects.filter(county = user_county_id).filter(call_category=1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(county = user_county_id).filter(call_category=2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(county = user_county_id).filter(date_reported__gte = date.today()- timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(county = user_county_id).filter(date_reported__gte = date.today()- timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    #Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease = True)
    disease_report_stat= {}
    thirty_days_stat= {}
    for d_type in disease_types:
       diseases_count = disease.objects.all().filter(county = user_county_id).filter(disease_type_id=d_type.id).count()
       thirty_days_disease_count = disease.objects.all().filter(county = user_county_id).filter(disease_type_id=d_type.id).filter(date_reported__gte = date.today()- timedelta(days=30)).count()
       if thirty_days_disease_count > 0:
        disease_report_stat[d_type.name] = diseases_count
        thirty_days_stat[d_type.name] = thirty_days_disease_count

    #picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    #ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat= {}
    events_thirty_days_stat= {}
    for e_type in event_types:
       events_count = event.objects.all().filter(county = user_county_id).filter(event_type_id=e_type.id).count()
       events_thirty_days_disease_count = event.objects.all().filter(county = user_county_id).filter(event_type_id=e_type.id).filter(date_reported__gte = date.today()- timedelta(days=30)).count()
       if events_thirty_days_disease_count > 0:
        events_report_stat[e_type.name] = events_count
        events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    #picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))

    #Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}#variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(county = user_county_id).filter(county_id = cnty.id).filter(date_reported__gte = date.today()- timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid = cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(county = user_county_id).filter(subcounty_id = subcnty.id).filter(county_id = cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name':cnty.name, 'id':cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)

    #pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(county = user_county_id).filter(disease_type_id = crt_tpye.id).filter(date_reported__gte = date.today()- timedelta(days=30)).values('disease_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        cases.append(disease_descriptions)

    #pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(county = user_county_id).filter(event_type_id = crt_tpye.id).filter(date_reported__gte = date.today()- timedelta(days=30)).values('event_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        event_cases.append(event_descriptions)

    #line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id = crt_tpye.id).values('idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period', 'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    #pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    #pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active = False)

    template = loader.get_template('veoc/county_dashboard.html')
    context = RequestContext(request,{
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'd_count': disease.objects.filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls' : disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported"),
        'disease_vals':disease.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat,
        'disease_reported_dash_vals':disease_reported_dash_vals,
        'county_name':county_name,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))

def subcounty_dashboard(request):

    #get the person org unit to dislay subcounty on the Dashboard
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_county_id = u.persons.sub_county_id

    #get county names
    county_object = organizational_units.objects.get(pk = user_county_id)
    sub_county_name = county_object.name

    # print(user_county_id)
    # print(sub_county_name)

    _dcall_logs = disease.objects.all().filter(subcounty = user_county_id).filter(data_source = 1).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(subcounty = user_county_id).filter(data_source = 1).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(subcounty = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(subcounty = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=7)).order_by("-date_reported")
    marquee_call_log = []#an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []#an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []#an array that collects all confirmed diseases and maps them to the marquee

    #checks if dictionary has values for the past 7 days
    if len(_dcall_logs) == 0:
        marquee_call_log.append("None reported")
    else:
        for _dlogs in _dcall_logs:
            marquee_call_log.append(_dlogs)

    if len(_ecall_logs) == 0:
        marquee_call_log.append("")
    else:
        for _elogs in _ecall_logs:
            marquee_call_log.append(_elogs)

    if len(_events) == 0:
        marquee_events.append("None reported")
    else:
        for _eve in _events:
            marquee_events.append(_eve)

    if len(_disease) == 0:
        marquee_disease.append("None reported")
    else:
        for _dis in _disease:
            marquee_disease.append(_dis)


    #Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(subcounty = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(subcounty = user_county_id).filter(incident_status = 1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(subcounty = user_county_id).filter(call_category=1).filter(incident_status=2).filter(date_reported__gte = date.today()- timedelta(days=1)).order_by("-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(subcounty = user_county_id).filter(call_category=1).filter(incident_status=1).order_by("-date_reported").count()
    # print(rum_disease_call_log_count)

    #Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(subcounty = user_county_id).filter(incident_status = 2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(subcounty = user_county_id).filter(incident_status = 1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(subcounty = user_county_id).filter(incident_status = 3).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(subcounty = user_county_id).filter(call_category=2).filter(incident_status=2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(subcounty = user_county_id).filter(call_category=2).filter(incident_status=1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count=conf_event_count+conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(subcounty = user_county_id).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()

    #changed call logs button
    disease_related_calls = call_log.objects.filter(subcounty = user_county_id).filter(call_category=1).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(subcounty = user_county_id).filter(call_category=2).filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(subcounty = user_county_id).filter(date_reported__gte = date.today()- timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(subcounty = user_county_id).filter(date_reported__gte = date.today()- timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    #Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease = True)
    disease_report_stat= {}
    thirty_days_stat= {}
    for d_type in disease_types:
       diseases_count = disease.objects.all().filter(subcounty = user_county_id).filter(disease_type_id=d_type.id).count()
       thirty_days_disease_count = disease.objects.all().filter(subcounty = user_county_id).filter(disease_type_id=d_type.id).filter(date_reported__gte = date.today()- timedelta(days=30)).count()
       if thirty_days_disease_count > 0:
        disease_report_stat[d_type.name] = diseases_count
        thirty_days_stat[d_type.name] = thirty_days_disease_count

    #picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    #ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat= {}
    events_thirty_days_stat= {}
    for e_type in event_types:
       events_count = event.objects.all().filter(subcounty = user_county_id).filter(event_type_id=e_type.id).count()
       events_thirty_days_disease_count = event.objects.all().filter(subcounty = user_county_id).filter(event_type_id=e_type.id).filter(date_reported__gte = date.today()- timedelta(days=30)).count()
       if events_thirty_days_disease_count > 0:
        events_report_stat[e_type.name] = events_count
        events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    #picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))

    #Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}#variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(subcounty = user_county_id).filter(county_id = cnty.id).filter(date_reported__gte = date.today()- timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid = cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(subcounty = user_county_id).filter(subcounty_id = subcnty.id).filter(county_id = cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name':cnty.name, 'id':cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)

    #pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(subcounty = user_county_id).filter(disease_type_id = crt_tpye.id).filter(date_reported__gte = date.today()- timedelta(days=30)).values('disease_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        cases.append(disease_descriptions)

    #pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(subcounty = user_county_id).filter(event_type_id = crt_tpye.id).filter(date_reported__gte = date.today()- timedelta(days=30)).values('event_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        event_cases.append(event_descriptions)

    #line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id = crt_tpye.id).values('idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period', 'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    #pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    #pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active = False)

    template = loader.get_template('veoc/subcounty_dashboard.html')
    context = RequestContext(request,{
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'd_count': disease.objects.filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls' : disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported"),
        'disease_vals':disease.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte = date.today()- timedelta(days=30)).order_by("-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat,
        'sub_county_name':sub_county_name,
        'disease_reported_dash_vals':disease_reported_dash_vals,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))

def call_register(request):

    if request.method == 'POST':
        callcategory = request.POST.get('callCategory','')
        diseasetype = request.POST.get('diseaseType','')
        eventtype = request.POST.get('eventType','')
        unrelated_incident = request.POST.get('incidentType','')
        callername = request.POST.get('callerName','')
        callernumber = request.POST.get('callerNumber','')
        region = request.POST.get('region','')
        locatn = request.POST.get('location','')
        cnty = request.POST.get('county','')
        sub_cnty = request.POST.get('subcounty','')
        ward = request.POST.get('ward','')
        status = request.POST.get('status','')
        datereported = request.POST.get('dateReported','')
        descriptn = request.POST.get('description','')
        actiontaken = request.POST.get('actionTaken','')
        significant = request.POST.get('callSignificant','')

        # check significant eventType
        significant_events = ""
        if significant == 'on' :
            significant_events = "t"
        else:
            significant_events = "f"

        #Check call_category_incident
        call_inc_category = ""
        callcategoryObject = ""
        if not diseasetype:
            print("category incident not diseasetype")
            if not eventtype:
                print("category incident not eventtype")
                if not unrelated_incident:
                    print("category incident not unrelated_incident")
                else:
                    # call_inc_category = unrelated_incident
                    unrelatedObject = unrelated_calls_category.objects.get(description = unrelated_incident)
                    call_inc_category = unrelatedObject.id
                    print("category urelated incident: ")
                    print("call_inc_category: ")
                    # print(call_inc_category)

                    #getting objects of foreignKeys
                    #checks if county data is chosen
                    callcategoryObject = call_incident_category.objects.get(incident_description = callcategory)
                    countyObject = organizational_units.objects.get(organisationunitid = 18)
                    subcountyObject = organizational_units.objects.get(organisationunitid = 18)
                    wardObject = organizational_units.objects.get(organisationunitid = 18)
                    regionObject = reporting_region.objects.get(region_description = 'Kenya')
                    incidentObject = incident_status.objects.get(status_description = 'Rumour')

            else:
                # call_inc_category = eventtype
                eventObject = dhis_event_type.objects.get(name = eventtype)
                call_inc_category = eventObject.id
                print("category event type: ")
                print("call_inc_category: ")
                # print(call_inc_category)

                #getting objects of foreignKeys
                #checks if county data is chosen
                if cnty == "":
                    callcategoryObject = call_incident_category.objects.get(incident_description = callcategory)
                    countyObject = organizational_units.objects.get(organisationunitid = 18)
                    subcountyObject = organizational_units.objects.get(organisationunitid = 18)
                    wardObject = organizational_units.objects.get(organisationunitid = 18)
                    regionObject = reporting_region.objects.get(region_description = region)
                    incidentObject = incident_status.objects.get(status_description = status)

                else :
                    callcategoryObject = call_incident_category.objects.get(incident_description = callcategory)
                    countyObject = organizational_units.objects.get(organisationunitid = cnty)
                    subcountyObject = organizational_units.objects.get(organisationunitid = sub_cnty)
                    wardObject = organizational_units.objects.get(organisationunitid = ward)
                    regionObject = reporting_region.objects.get(region_description = region)
                    incidentObject = incident_status.objects.get(status_description = status)
        else:
            # call_inc_category = diseasetype
            diseaseObject = dhis_disease_type.objects.get(name = diseasetype)
            call_inc_category = diseaseObject.id
            print("category disease type: ")
            print("call_inc_category: ")
            # print(call_inc_category)

            #getting objects of foreignKeys
            #checks if county data is chosen
            if cnty == "":
                callcategoryObject = call_incident_category.objects.get(incident_description = callcategory)
                countyObject = organizational_units.objects.get(organisationunitid = 18)
                subcountyObject = organizational_units.objects.get(organisationunitid = 18)
                wardObject = organizational_units.objects.get(organisationunitid = 18)
                regionObject = reporting_region.objects.get(region_description = region)
                incidentObject = incident_status.objects.get(status_description = status)

            else :
                callcategoryObject = call_incident_category.objects.get(incident_description = callcategory)
                countyObject = organizational_units.objects.get(name = cnty)
                subcountyObject = organizational_units.objects.get(name = sub_cnty)
                wardObject = organizational_units.objects.get(organisationunitid = ward)
                regionObject = reporting_region.objects.get(region_description = region)
                incidentObject = incident_status.objects.get(status_description = status)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        # print(current_user)
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        call_log.objects.create(call_category=callcategoryObject, call_category_incident=call_inc_category, incident_status=incidentObject,
        reporting_region=regionObject, county=countyObject, subcounty=subcountyObject, ward=wardObject, location=locatn, caller_name=callername,
        caller_number=callernumber, date_reported=datereported, call_description=descriptn, action_taken=actiontaken,
        significant=significant_events, updated_at=current_date, created_by=userObject, updated_by=userObject   , created_at=current_date)

        # call_category = call_incident_category.objects.all().order_by('id')
        # unrelated_calls = unrelated_calls_category.objects.all().order_by('id')
        # regions = reporting_region.objects.all()
        # status = incident_status.objects.all()
        # call_county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        # # call_county = county.objects.all().order_by('description')
        # diseases = dhis_disease_type.objects.all().order_by('name')
        # events = dhis_event_type.objects.all().order_by('name')
        # day = time.strftime("%Y-%m-%d")
        #
        # data = {'call_category':call_category, 'unrelated_calls':unrelated_calls, 'regions':regions, 'incident_status':status,
        # 'county':call_county, 'diseases':diseases, 'events':events, 'day':day}
        #
        # return render('veoc/call_register_form.html', data)

    call_category = call_incident_category.objects.all().order_by('id')
    unrelated_calls = unrelated_calls_category.objects.all().order_by('id')
    regions = reporting_region.objects.all()
    status = incident_status.objects.all()
    call_county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # call_county = county.objects.all().order_by('description')
    diseases = dhis_disease_type.objects.all().order_by('name')
    events = dhis_event_type.objects.all().order_by('name')
    day = time.strftime("%Y-%m-%d")

    data = {'call_category':call_category, 'unrelated_calls':unrelated_calls, 'regions':regions, 'incident_status':status,
    'county':call_county, 'diseases':diseases, 'events':events, 'day':day}

    return render(request, 'veoc/call_register_form.html', data)

def get_county(request):
    if request.method == "POST":
        counties = organizational_units.objects.filter(hierarchylevel = 2)

        serialized=serialize('json',counties)
        obj_list=json.loads(serialized)

        print(obj_list)
        print(json.dumps(obj_list))

        return HttpResponse(json.dumps(obj_list),content_type="application/json")

def get_subcounty(request):
    obj_list = None
    if request.method == "POST":
        mycounty = request.POST.get('county','')
        print(mycounty)
        county_parent_id = organizational_units.objects.get(name = mycounty)
        sub_counties = organizational_units.objects.filter(parentid = county_parent_id)

        serialized=serialize('json',sub_counties)
        obj_list=json.loads(serialized)

        return HttpResponse(json.dumps(obj_list),content_type="application/json")

def usersubcounty(request):
    obj_list = None
    if request.method == "POST":
        org_id = request.POST.get('county','')
        print(org_id)
        county_parent_id = organizational_units.objects.get(organisationunitid = org_id)
        sub_counties = organizational_units.objects.filter(parentid = county_parent_id)

        serialized=serialize('json',sub_counties)
        obj_list=json.loads(serialized)

        return HttpResponse(json.dumps(obj_list),content_type="application/json")

def get_group(request):
    obj_list = None
    if request.method == "POST":
        _name = request.POST.get('name','')

        print(_name)
        group_name = Group.objects.all()
        print(group_name)
        _group = group_name.filter(name__icontains=_name)

        print(_group)
        serialized=serialize('json',_group)
        obj_list=json.loads(serialized)
        print(obj_list)

        return HttpResponse(json.dumps(obj_list),content_type="application/json")

def get_ward(request):
    if request.method == "POST":
        mysubcounty = request.POST.get('subcounty','')

        subcounty_parent_id = organizational_units.objects.get(name = mysubcounty)
        wards = organizational_units.objects.filter(parentid = subcounty_parent_id)

        serialized=serialize('json',wards)
        obj_list=json.loads(serialized)

        return HttpResponse(json.dumps(obj_list),content_type="application/json")

def call_report(request):
    # check if there is an edit on an entry and save
    if request.method == 'POST':
        id = request.POST.get('id','')
        incident_stat = request.POST.get('status_name','')
        descrp = request.POST.get('description_name','')
        action = request.POST.get('action_taken','')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        call_log.objects.filter(pk=id).update(incident_status=incident_stat, call_description=descrp,
                        action_taken=action, updated_by=userObject, updated_at=current_date)

    call_count = call_log.objects.exclude(call_category = 3).count()
    call_incidents = call_incident_category.objects.all()
    call_status_desr = incident_status.objects.all()
    call_logs = call_log.objects.exclude(call_category = 3)
    day_from = time.strftime("%Y-%m-%d")
    day_to = time.strftime("%Y-%m-%d")

    call_cat_incident = []
    for calls in call_logs:
        _call_category = calls.call_category.id
        # print(_call_category)
        if _call_category == 1:
            calls_disease = calls.call_category_incident
            # print(calls_disease)
            call_cat_disease = dhis_disease_type.objects.filter(id = calls_disease).values_list('name', flat=True).first()
            # print(call_cat_disease)
            call_cat_incident.append(call_cat_disease)
        elif _call_category == 2:
            call_event = calls.call_category_incident
            # print(call_event)
            call_cat_event = dhis_event_type.objects.filter(id = call_event).values_list('name', flat=True).first()
            # print(call_cat_event)
            call_cat_incident.append(call_cat_event)
        else:
            print('Call category not in DB')

    # print(call_cat_incident)
    my_list_data = zip(call_logs, call_cat_incident)

    values = {'call_logs': my_list_data, 'contact_type_vals':contacts, 'call_count': call_count, 'success':"",
    'call_incidents':call_incidents, 'status_descriptions':call_status_desr}

    return render(request, 'veoc/call_report.html', values)

def filter_call_report(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from','')
        date_to = request.POST.get('date_to','')

        call_count = call_log.objects.exclude(call_category = 3).filter(date_reported__range=[date_from, date_to]).count()
        call_incidents = call_incident_category.objects.all()
        call_status_desr = incident_status.objects.all()
        call_logs = call_log.objects.exclude(call_category = 3).filter(date_reported__range=[date_from, date_to])
        day_from = date_from
        day_to = date_to

        call_cat_incident = []
        for calls in call_logs:
            _call_category = calls.call_category.id
            if _call_category == 1:
                calls_disease = calls.call_category_incident
                call_cat_disease = dhis_disease_type.objects.filter(id = calls_disease).values_list('name', flat=True).first()
                call_cat_incident.append(call_cat_disease)
            elif _call_category == 2:
                call_event = calls.call_category_incident
                call_cat_event = dhis_event_type.objects.filter(id = call_event).values_list('name', flat=True).first()
                call_cat_incident.append(call_cat_event)
            else:
                print('Call category not in DB')

        my_list_data = zip(call_logs, call_cat_incident)

        values = {'call_logs': my_list_data, 'contact_type_vals':contacts, 'call_count': call_count, 'success':"",
        'call_incidents':call_incidents, 'status_descriptions':call_status_desr, 'day_from':day_from, 'day_to': day_to}

        return render(request, 'veoc/call_report.html', values)

def disease_register(request):

    if request.method == 'POST':
        diseasetype = request.POST.get('diseaseType','')
        datasource = request.POST.get('dataSource','')
        region = request.POST.get('region','')
        cnty = request.POST.get('county','')
        sub_cnty = request.POST.get('subcounty','')
        ward = request.POST.get('ward','')
        status = request.POST.get('status','')
        datereported = request.POST.get('dateReported','')
        cases = request.POST.get('cases','')
        deaths = request.POST.get('deaths','')
        descriptn = request.POST.get('description','')
        actiontaken = request.POST.get('actionTaken','')
        significant = request.POST.get('callSignificant','')

        # check significant eventType
        significant_events = ""
        if significant == 'on' :
            significant_events = "t"
        else:
            significant_events = "f"

            # checks if data values for county exists, if not, selected region not Kenya
            # NB : organizational_unit 18 is Kenya in the database
        if region == "Kenya" :
            countyObject = organizational_units.objects.get(name = cnty)
            subcountyObject = organizational_units.objects.get(name = sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid = ward)
        else :
            countyObject = organizational_units.objects.get(organisationunitid = 18)
            subcountyObject = organizational_units.objects.get(organisationunitid = 18)
            wardObject = organizational_units.objects.get(organisationunitid = 18)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk = current_user.id)
        diseaseObject = dhis_disease_type.objects.get(name = diseasetype)
        datasourceObject = data_source.objects.get(source_description = datasource)
        regionObject = reporting_region.objects.get(region_description = region)
        incidentObject = incident_status.objects.get(status_description = status)

        #saving values to databse
        disease.objects.create(disease_type=diseaseObject, incident_status=incidentObject, county=countyObject, subcounty=subcountyObject,data_source=datasourceObject,
        ward=wardObject, reporting_region=regionObject, date_reported=datereported, cases=cases, deaths=deaths,remarks=descriptn, action_taken=actiontaken,
        significant=significant_events, updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

        # check if the incident is within kenya to save in DHIS2
        if region == "Kenya" :
            #check if the reported case is confirmed to save in dhis2 data tables
            if status == 'Confirmed':
                #saving data into dhis2 data dataTables
                rep_disease = dhis_disease_data_elements.objects.filter(name__contains=diseasetype).values_list('id', flat=True).order_by('id')

                r_disease = ''
                #pulling the data value from the object
                for rep in rep_disease:
                    r_disease = rep

                #check if there is a data element that is in disease type before saving
                if rep_disease :
                    print('saving into dhis data tables')
                    #create current week/year number
                    dt = datetime.now()
                    wk_val = dt.isocalendar()[1]
                    yr_val = dt.replace(year = dt.year)
                    final_year = yr_val.year
                    weeknum = str(final_year) + str(wk_val)
                    print(weeknum)
                    #save into dhis reported disease
                    dhis_reported_diseases.objects.create(org_unit_id=wardObject, program='Jt6SPO0bjKB', disease_type=diseaseObject, eventDate=current_date, stored_by='eoc_user', period=weeknum, status='COMPLETED')
                    #get latest key of data just entered to save into data values
                    disease_id = dhis_reported_diseases.objects.order_by('-id')[0]
                    disease_pk = disease_id.id
                    #get object of the reported disease to store into data values
                    rep_eve_Object = dhis_reported_diseases.objects.get(pk = disease_pk)
                    #get object of the data element to store into data values
                    red_object1 = dhis_disease_data_elements.objects.get(id=r_disease)
                    red_object2 = dhis_disease_data_elements.objects.get(id=30)
                    #save the data valus objects
                    dhis_disease_data_values.objects.create(dhis_reported_disease_id = rep_eve_Object, data_element_id = red_object1, data_value = cases)
                    dhis_disease_data_values.objects.create(dhis_reported_disease_id = rep_eve_Object, data_element_id = red_object2, data_value = diseasetype)
                else:
                    print('no associated disease element on disease types - not saved in dhis2 data elements')
            else:
                print('unconfirmed incident - not saved in dhis2 data elements')
        else:
            print('global incident case - not saved in dhis2 data elements')

    regions = reporting_region.objects.all()
    status = incident_status.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    diseases = dhis_disease_type.objects.all().order_by('name')
    datasource = data_source.objects.all().order_by('source_description')
    day = time.strftime("%Y-%m-%d")

    data = {'diseases':diseases, 'datasource':datasource, 'regions':regions, 'incident_status':status, 'county':county, 'day':day}

    return render(request, 'veoc/disease_form.html', data)

@login_required
def disease_view(request, id = None):
    instance = get_object_or_404(disease, id = id)

    context = {
        "disease_instance":instance,
    }
    return render(request, "veoc/disease_view.html",context)

@login_required
def event_view(request, id = None):
    instance = get_object_or_404(event, id = id)

    context = {
        "event_instance":instance,
    }
    return render(request, "veoc/event_view.html",context)

@login_required
def call_log_view(request, id = None):
    instance = get_object_or_404(call_log, id = id)

    context = {
        "call_log_instance":instance,
    }
    return render(request, "veoc/call_log_view.html",context)

def event_register(request):

    if request.method == 'POST':
        eventtype = request.POST.get('eventType','')
        datasource = request.POST.get('dataSource','')
        region = request.POST.get('region','')
        cnty = request.POST.get('county','')
        sub_cnty = request.POST.get('subcounty','')
        ward = request.POST.get('ward','')
        status = request.POST.get('status','')
        datereported = request.POST.get('dateReported','')
        cases = request.POST.get('cases','')
        deaths = request.POST.get('deaths','')
        descriptn = request.POST.get('description','')
        actiontaken = request.POST.get('actionTaken','')
        significant = request.POST.get('callSignificant','')

        # check significant eventType
        significant_events = ""
        if significant == 'on' :
            significant_events = "t"
        else:
            significant_events = "f"

        if region == "Kenya" :
            countyObject = organizational_units.objects.get(name = cnty)
            subcountyObject = organizational_units.objects.get(name = sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid = ward)
        else :
            countyObject = organizational_units.objects.get(organisationunitid = 18)
            subcountyObject = organizational_units.objects.get(organisationunitid = 18)
            wardObject = organizational_units.objects.get(organisationunitid = 18)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk = current_user.id)
        eventObject = dhis_event_type.objects.get(name = eventtype)
        datasourceObject = data_source.objects.get(source_description = datasource)
        regionObject = reporting_region.objects.get(region_description = region)
        incidentObject = incident_status.objects.get(status_description = status)

        #saving values to databse
        event.objects.create(event_type=eventObject, incident_status=incidentObject, county=countyObject, subcounty=subcountyObject,data_source=datasourceObject,
        ward=wardObject, reporting_region=regionObject, date_reported=datereported, cases=cases, deaths=deaths,remarks=descriptn, action_taken=actiontaken,
        significant_event=significant_events, updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

        # check if the incident is within kenya to save in DHIS2
        if region == "Kenya" :
            #check if the reported case is confirmed to save in dhis2 data tables
            if status == 'Confirmed':
                #create current week/year number
                dt = datetime.now()
                wk_val = dt.isocalendar()[1]
                yr_val = dt.replace(year = dt.year)
                final_year = yr_val.year
                weeknum = str(final_year) + str(wk_val)
                print(weeknum)
                #saving data into dhis2 data dataTables
                dhis_reported_events.objects.create(org_unit_id=wardObject, program='hH7eq688OJT', event_type=eventObject, eventDate=current_date, stored_by='eoc_user', period=weeknum, status='COMPLETED')
                #get latest key of data just entered
                event_id = dhis_reported_events.objects.order_by('-id')[0]
                event_pk = event_id.id
                rep_eve_Object = dhis_reported_events.objects.get(pk = event_pk)
                dataElementObject1 = dhis_event_data_elements.objects.get(pk = '1')
                dataElementObject2 = dhis_event_data_elements.objects.get(pk = '2')
                dataElementObject3 = dhis_event_data_elements.objects.get(pk = '3')
                print(dataElementObject3)

                dhis_event_data_values.objects.create(dhis_reported_event_id = rep_eve_Object, data_element_id = dataElementObject1, data_value = cases)
                dhis_event_data_values.objects.create(dhis_reported_event_id = rep_eve_Object, data_element_id = dataElementObject2, data_value = deaths)
                dhis_event_data_values.objects.create(dhis_reported_event_id = rep_eve_Object, data_element_id = dataElementObject3, data_value = eventtype)
            else:
                print('unconfirmed incident - not saved in dhis2 data elements')
        else:
            print('global incident case - not saved in dhis2 data elements')

    regions = reporting_region.objects.all()
    status = incident_status.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    events = dhis_event_type.objects.all().order_by('name')
    datasource = data_source.objects.all().order_by('source_description')
    day = time.strftime("%Y-%m-%d")

    data = {'events':events, 'datasource':datasource, 'regions':regions, 'incident_status':status, 'county':county, 'day':day}

    return render(request, 'veoc/events_form.html', data)

def feedback_create(request):

    if request.method == 'POST':
        module_type=request.POST.get('module_type','')
        date_created=request.POST.get('date_created','')
        challenge=request.POST.get('challenge','')
        recommendation=request.POST.get('recommendation','')

        cur_user=request.user.username
        usert=User.objects.get(username=cur_user)

        day = time.strftime("%Y-%m-%d")

        insertdata = Feedback(user=usert,module_type=module_type,date_created=date_created,challenge=challenge,recommendation=recommendation)
        insertdata.save()
        success="Feedback submitted successfully"

        return render(request,"veoc/feedback_form.html",{"success":success,'day':day})

    else:
        success=""
        day = time.strftime("%Y-%m-%d")

        return render(request,"veoc/feedback_form.html",{"success":success,'day':day})

def feedback_report(request):
    return render(request, 'veoc/feedback_report.html')

def unrelated_call_report(request):
    # check if there is an edit on an entry and save
    if request.method == 'POST':
        id = request.POST.get('id','')
        incident_stat = request.POST.get('status_name','')
        descrp = request.POST.get('description_name','')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        call_log.objects.filter(pk=id).update(incident_status=incident_stat, call_description=descrp,
                        updated_by=userObject, updated_at=current_date)

    call_count = call_log.objects.all().filter(call_category = 3).count()
    call_incidents = call_incident_category.objects.all()
    call_unrelated = unrelated_calls_category.objects.all()
    call_status_desr = incident_status.objects.all()
    call_logs = call_log.objects.all().filter(call_category = 3)

    call_cat_incident = []
    for calls in call_logs:
        _call_category = calls.call_category.id
        if _call_category == 3:
            calls_disease = calls.call_category_incident
            call_cat_disease = unrelated_calls_category.objects.filter(id = calls_disease).values_list('description', flat=True).first()
            call_cat_incident.append(call_cat_disease)
        else:
            print('Call category not in DB')

    my_list_data = zip(call_logs, call_cat_incident)

    values = {'call_logs': my_list_data, 'contact_type_vals':contacts, 'call_count': call_count,'call_incidents':call_incidents,
     'call_incidents':call_incidents, 'status_descriptions':call_status_desr}

    return render(request, 'veoc/unrelated_report.html', values)

def filter_unrelated_call_report(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from','')
        date_to = request.POST.get('date_to','')

        call_count = call_log.objects.all().filter(call_category = 3).filter(date_reported__range=[date_from, date_to]).count()
        call_incidents = call_incident_category.objects.all()
        call_unrelated = unrelated_calls_category.objects.all()
        call_status_desr = incident_status.objects.all()
        call_logs = call_log.objects.all().filter(call_category = 3).filter(date_reported__range=[date_from, date_to])
        day_from = date_from
        day_to = date_to

        call_cat_incident = []
        for calls in call_logs:
            _call_category = calls.call_category.id
            if _call_category == 3:
                calls_disease = calls.call_category_incident
                call_cat_disease = unrelated_calls_category.objects.filter(id = calls_disease).values_list('description', flat=True).first()
                call_cat_incident.append(call_cat_disease)
            else:
                print('Call category not in DB')

        my_list_data = zip(call_logs, call_cat_incident)

        values = {'call_logs': my_list_data, 'contact_type_vals':contacts, 'call_count': call_count,'call_incidents':call_incidents,
         'call_incidents':call_incidents, 'status_descriptions':call_status_desr, 'day_from':day_from, 'day_to': day_to}

        return render(request, 'veoc/unrelated_report.html', values)

def disease_report(request):
    if request.method == 'POST':
        id = request.POST.get('id','')
        incident_stat = request.POST.get('status_name','')
        remarks = request.POST.get('remarks','')
        action = request.POST.get('action','')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        disease.objects.filter(pk=id).update(incident_status=incident_stat, remarks=remarks, action_taken=action,
                        updated_by=userObject, updated_at=current_date)

    _reported_diseases_count = disease.objects.all().count()
    disease_status_desr = incident_status.objects.all()
    _disease = disease.objects.all() #filter(date_reported__gte = date.today()- timedelta(days=30))

    diseas = {'reported_diseases_count':_reported_diseases_count,'disease_vals': _disease, 'status_descriptions':disease_status_desr}

    return render(request, 'veoc/disease_report.html', diseas)

def filter_disease_report(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from','')
        date_to = request.POST.get('date_to','')

        day_from = date_from
        day_to = date_to
        _reported_diseases_count = disease.objects.all().filter(date_reported__range=[date_from, date_to]).count()
        disease_status_desr = incident_status.objects.all()
        _disease = disease.objects.all().filter(date_reported__range=[date_from, date_to]) #filter(date_reported__gte = date.today()- timedelta(days=30))

        diseas = {'reported_diseases_count':_reported_diseases_count,'disease_vals': _disease,
                    'status_descriptions':disease_status_desr, 'day_from':day_from, 'day_to': day_to}

        return render(request, 'veoc/disease_report.html', diseas)

def events_report(request):

    if request.method == 'POST':
        id = request.POST.get('id','')
        incident_stat = request.POST.get('status_name','')
        remarks = request.POST.get('remarks','')
        action = request.POST.get('action','')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        event.objects.filter(pk=id).update(incident_status=incident_stat, remarks=remarks, action_taken=action,
                        updated_by=userObject, updated_at=current_date)

    reported_events_count = event.objects.all().count()
    disease_status_desr = incident_status.objects.all()
    reported_events = event.objects.all()

    events = {'reported_events_count': reported_events_count,
            'event_vals': reported_events, 'status_descriptions':disease_status_desr}

    return render(request, 'veoc/events_report.html', events)

def filter_events_report(request):

    if request.method == 'POST':
        date_from = request.POST.get('date_from','')
        date_to = request.POST.get('date_to','')
        day_from = date_from
        day_to = date_to

        reported_events_count = event.objects.all().filter(date_reported__range=[date_from, date_to]).count()
        disease_status_desr = incident_status.objects.all()
        reported_events = event.objects.all().filter(date_reported__range=[date_from, date_to])

        events = {'reported_events_count': reported_events_count, 'event_vals': reported_events,
                'status_descriptions':disease_status_desr, 'day_from':day_from, 'day_to': day_to}

        return render(request, 'veoc/events_report.html', events)

# @login_required
def daily_reports(request):

    if request.method == 'POST':
        datefilter =request.POST.get('date_reported','')

        # Get significant IncidentStatusSerializer
        sign_calls = call_log.objects.all().filter(significant = 'True').filter(date_reported=datefilter)
        sign_diseases = disease.objects.all().filter(significant = 'True').filter(date_reported=datefilter)
        sign_events = event.objects.all().filter(significant_event = 'True').filter(date_reported=datefilter)

        #Check id significants are all empty
        if (sign_calls =="") and (sign_diseases == "") and sign_events =="":
           significant_events_none="None"
        else:
           significant_events_none=""

        #Getting diseases and events reported within Kenya
        kenya_disease = disease.objects.all().filter(reporting_region = 4).filter(date_reported=datefilter)
        kenya_events = event.objects.all().filter(reporting_region = 4).filter(date_reported=datefilter)

        #Getting diseases and events reported within East Africa
        ea_disease = disease.objects.all().filter(reporting_region = 3).filter(date_reported=datefilter)
        ea_events = event.objects.all().filter(reporting_region = 3).filter(date_reported=datefilter)

        #Getting diseases and events reported within Africa
        africa_disease = disease.objects.all().filter(reporting_region = 2).filter(date_reported=datefilter)
        africa_events = event.objects.all().filter(reporting_region = 2).filter(date_reported=datefilter)

        #Getting diseases and events reported Gloablly
        global_disease = disease.objects.all().filter(reporting_region = 1).filter(date_reported=datefilter)
        global_events = event.objects.all().filter(reporting_region = 1).filter(date_reported=datefilter)

        #getting dhis2 data from eoc
        dhis_diseases = dhis_reported_diseases.objects.all().filter(eventDate=datefilter)
        dhis_events = dhis_reported_events.objects.all().filter(eventDate=datefilter)

        #call logs databse
        # daily_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=2).filter(date_reported=datefilter).count()
        # daily_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(date_reported=datefilter).count()
        # daily_enquiry = Call_flashback_logs_count + Unrelated_call_logs_count
        # daily_total_calls = daily_conf_call_log_count + daily_rum_call_log_count + daily_enquiry


        disease_types = dhis_disease_type.objects.all()
        # watchers = mytimetable.objects.all().filter(from_date__lte = datefilter, to_date__gte = datefilter)

        data = {'date_filter':datefilter, 'significant_calls':sign_calls, 'significant_diseases':sign_diseases,
            'significant_events':sign_events, 'significant_events_none':significant_events_none, 'kenya_disease':kenya_disease,
             'kenya_events':kenya_events, 'ea_disease':ea_disease, 'ea_events':ea_events, 'africa_disease':africa_disease,
             'africa_events': africa_events, 'global_disease':global_disease, 'global_events':global_events, 'dhis_diseases':dhis_diseases,
             'dhis_events':dhis_events}

        return render(request,"veoc/generate_pdf.html",data)

    else:
        day = time.strftime("%Y-%m-%d")
        return render(request, 'veoc/generate_pdf.html',{'day': day})

def ongoing_tasks(request):
    if request.method == 'POST':
        id = request.POST.get('id','')
        incident_stat = request.POST.get('status_name','')
        remarks = request.POST.get('remarks','')
        action = request.POST.get('action','')
        c_status = request.POST.get('closed','')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        disease.objects.filter(pk=id).update(incident_status=incident_stat, remarks=remarks, action_taken=action,
                        case_status=c_status, updated_by=userObject, updated_at=current_date)

    _disease_count = disease.objects.all().filter(case_status = 1).count
    _event_count = event.objects.all().filter(case_status = 1).count
    # total_count = _disease_count+_event_count
    disease_status_desr = incident_status.objects.all()
    my_disease = disease.objects.filter(case_status = 1)
    _event = event.objects.all().filter(case_status = 1)
    current_date = date.today()#.strftime('%Y-%m-%d')

    print(current_date)

    date_incident = []
    for inc_date in my_disease:
        d_reported = inc_date.date_reported
        print(d_reported.date())
        delta = current_date - d_reported.date()
        print(delta.days)
        date_incident.append(delta.days)

    my_disease_data = zip(my_disease, date_incident)

    result_list = sorted(chain(my_disease, _event), key=attrgetter('date_reported'))

    diseas = {'disease_vals': my_disease_data, 'disease_vals_count': _disease_count,
        'status_descriptions':disease_status_desr, 'current_date' :current_date}

    return render(request, 'veoc/ongoing_tasks.html', diseas)

def filter_ongoing_tasks(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from','')
        date_to = request.POST.get('date_to','')
        day_from = date_from
        day_to = date_to

        _disease_count = disease.objects.all().filter(case_status = 1).filter(date_reported__range=[date_from, date_to]).count
        _event_count = event.objects.all().filter(case_status = 1).filter(date_reported__range=[date_from, date_to]).count
        # total_count = _disease_count+_event_count
        disease_status_desr = incident_status.objects.all()
        my_disease = disease.objects.filter(case_status = 1).filter(date_reported__range=[date_from, date_to])
        _event = event.objects.all().filter(case_status = 1).filter(date_reported__range=[date_from, date_to])
        current_date = date.today()

        print(current_date)

        date_incident = []
        for inc_date in my_disease:
            d_reported = inc_date.date_reported
            print(d_reported.date())
            delta = current_date - d_reported.date()
            print(delta.days)
            date_incident.append(delta.days)

        my_disease_data = zip(my_disease, date_incident)

        result_list = sorted(chain(my_disease, _event), key=attrgetter('date_reported'))

        diseas = {'disease_vals': my_disease_data, 'disease_vals_count': _disease_count,
            'disease_status_desr': disease_status_desr, 'day_from':day_from, 'day_to': day_to}

        return render(request, 'veoc/ongoing_tasks.html', diseas)

def case_definition(request):

    if request.method == "POST":
        code = request.POST.get('code','')
        condition = request.POST.get('condition','')
        incubation = request.POST.get('incubation','')
        suspected = request.POST.get('suspected_definition','')
        confirmed = request.POST.get('confirmed_definition','')
        signs = request.POST.get('signs','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        standard_case_definitions.objects.create(code=code, condition=condition, incubation_period=incubation,
        suspected_standard_case_def=suspected, confirmed_standard_case_def=confirmed, signs_and_symptoms=signs,
        updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

    case_definition_count = standard_case_definitions.objects.all().count()
    _standard_case_definitions = standard_case_definitions.objects.all()

    data_values = {'case_definition_count': case_definition_count,
                    'standard_case_definitions': _standard_case_definitions}

    return render(request, "veoc/case_defination.html", data_values)

def generate_pdf(request):
    return render(request, 'veoc/generate_pdf.html')

def All_contacts_report(request):

    contacts = {'contacts_val': contact.objects.all(),
                'contact_type_vals': contact_type.objects.all()}

    return render(request, 'veoc/all_contacts_report.html', contacts)

def Contact_type_report(request, id):
    contacts = contact_type.objects.all()
    contacts = {'contacts_val': contact.objects.all().filter(contact_type_id = id),
                'contact_type_description': contact_type.objects.get(pk = id),
                'contact_type_vals': contact_type.objects.all()}

    return render(request, 'veoc/all_contacts_report.html', contacts)

def all_contact_edit(request,editid):
    all_contacts = {'all_contacts': contact.objects.get(pk=editid)}

    return render(request, 'veoc/all_contacts_edit.html', all_contacts)

def contacts_edited_submit(request):
     if request.method=='POST':

        myid=request.POST.get('id','')
        f_name=request.POST.get('fname','')
        s_name=request.POST.get('sname','')
        design=request.POST.get('designation','')
        mob=request.POST.get('mobile','')
        _mail=request.POST.get('email','')

        d_type=designation.objects.get(description=design)
        cur_user=request.user.username
        user=str(User.objects.get(username=cur_user))
        # user=User.objects.get(username=cur_user)
        # user=request.user.username

        EOC_Contacts.objects.filter(pk=myid).update(first_name=f_name,second_name=s_name,designation=d_type,mobile=mob,email=_mail,created_by=user)

        values = {'eocContacts': EOC_Contacts.objects.all(), 'designation': Designation.objects.all()}

        return render(request, 'veoc/surveillance_contacts.html', values)

def idsr_data(request):

    if request.method == "POST":

        _weekly_report_count = idsr_weekly_facility_report.objects.all().count()
        _organizations = organizational_units.objects.all()
        _diseases = idsr_diseases.objects.all()
        _reported_incidents = idsr_reported_incidents.objects.all()
        _idsr_weekly_report = idsr_weekly_facility_report.objects.all()

        values = {'idsr_weekly_reports': _idsr_weekly_report, 'organizations':_organizations,
        'weekly_report_count': _weekly_report_count, 'diseases':_diseases, 'reported_incidents': _reported_incidents}

        return render(request, 'veoc/idsr_report.html', values)

    else:
        dhis_cases = idsr_weekly_facility_report.objects.all().count()
        week_no = idsr_weekly_facility_report.objects.order_by('org_unit_id').values('period').distinct()

        values = {'dhis_cases': dhis_cases, 'week_no': week_no}
        return render(request, 'veoc/idsr_report.html', values)

def reportable_diseases(request):

    _dhis_reported_diseases_count = dhis_reported_diseases.objects.all().count()
    _organizations = organizational_units.objects.all()
    _dhis_reported_diseases_report = dhis_reported_diseases.objects.all()
    _drop_down_diseases = dhis_reported_diseases.objects.all()
    # _drop_down_diseases = dhis_reported_diseases.objects.order_by('disease_type_id').values('disease_type_id').distinct()
    # print(_drop_down_diseases)
    _drop_down_periods = dhis_reported_diseases.objects.order_by().values('period').distinct()
    dhis_case_values = []
    for _dhis_reported_cases in _dhis_reported_diseases_report:
        dhis_data_values = dhis_disease_data_values.objects.filter(dhis_reported_disease_id = _dhis_reported_cases).values_list('data_value', flat=True).first()
        dhis_case_values.append(dhis_data_values)

    _dhis_cases = dhis_disease_data_values.objects.all()
    my_list_data = zip(_dhis_reported_diseases_report, dhis_case_values)

    values = {'dhis_reported_diseases_count': _dhis_reported_diseases_count, 'organizations':_organizations,
    'dhis_reported_diseases_reports': my_list_data, 'dhis_cases': _dhis_cases,
    'drop_down_diseases': _drop_down_diseases, 'drop_down_periods': _drop_down_periods }

    return render(request, 'veoc/reportable_diseases_report.html', values)

def reportable_diseases_filters(request):
    global filt_data
    if request.method == 'POST':
        filter_disease = request.POST.get('idsr_disease','')
        filter_period = request.POST.get('period','')
        filter_date = request.POST.get('date_reported','')

        print(filter_disease)
        print(filter_period)
        print(filter_date)

        #check for null values then filter based on values
        if (filter_disease == "") and (filter_period == "") and (filter_date == ""):
            print('No values sent')
        else:
            print('values sent')
            if filter_disease:
                print('disease ipo')
                if filter_period:
                    print('period ipo pia')
                    if filter_date:
                        print('date ipo pia')
                        # variable_column = 'disease_type_id'
                        # filt_data = variable_column + filter_disease
                        # print(filt_data)

                        variable_column = "disease_type_id"
                        search_type = "contains"
                        filter = variable_column + '__' + search_type
                        #stopped at find a way of passing the filter to the query
                        # _dhis_reported_diseases_count = dhis_reported_diseases.objects.filter(**{ filter: filter_disease }).count()
                        # filt_data = {filter : filter_disease}
                        # print(_dhis_reported_diseases_count)
                    else:
                        print('date hamna')
                else:
                    print('period hamna')
                    if filter_date:
                        print('date ipo pia')
                    else:
                        print('date hamna')
            else:
                print('disease hamna')
                if filter_period:
                    print('period ipo pia')
                    if filter_date:
                        print('date ipo pia')
                    else:
                        print('date hamna')
                else:
                    print('period hamna')
                    if filter_date:
                        print('date ipo pia')
                    else:
                        print('date hamna')

    # print(filt_data)
    _dhis_reported_diseases_count = dhis_reported_diseases.objects.all().count()
    _organizations = organizational_units.objects.all()
    _dhis_reported_diseases_report = dhis_reported_diseases.objects.all()
    _drop_down_diseases = dhis_reported_diseases.objects.all()
    _drop_down_periods = dhis_reported_diseases.objects.order_by().values('period').distinct()
    dhis_case_values = []
    for _dhis_reported_cases in _dhis_reported_diseases_report:
        dhis_data_values = dhis_disease_data_values.objects.filter(dhis_reported_disease_id = _dhis_reported_cases).values_list('data_value', flat=True).first()
        dhis_case_values.append(dhis_data_values)

    _dhis_cases = dhis_disease_data_values.objects.all()
    my_list_data = zip(_dhis_reported_diseases_report, dhis_case_values)

    values = {'dhis_reported_diseases_count': _dhis_reported_diseases_count, 'organizations':_organizations,
    'dhis_reported_diseases_reports': my_list_data, 'dhis_cases': _dhis_cases,
    'drop_down_diseases': _drop_down_diseases, 'drop_down_periods': _drop_down_periods }

    return render(request, 'veoc/reportable_diseases_report.html', values)

def reportable_event(request):

    _dhis_reported_events_count = dhis_reported_events.objects.all().count()
    _organizations = organizational_units.objects.all()
    _dhis_reported_events_report = dhis_reported_events.objects.all()
    _drop_down_events = dhis_reported_events.objects.all()
    dhis_case_values = []
    for _dhis_reported_cases in _dhis_reported_events_report:
        dhis_data_values = dhis_event_data_values.objects.filter(dhis_reported_event_id = _dhis_reported_cases).values_list('data_value', flat=True).first()
        dhis_case_values.append(dhis_data_values)

    _dhis_cases = dhis_event_data_values.objects.all()
    my_list_data = zip(_dhis_reported_events_report, dhis_case_values)

    values = {'dhis_reported_events_count': _dhis_reported_events_count, 'organizations':_organizations,
    'dhis_reported_events_report': my_list_data, 'dhis_cases': _dhis_cases, 'drop_down_events': _drop_down_events }

    return render(request, 'veoc/reportable_event_report.html', values)

def upload_csv(request):
	data = {}
	if "GET" == request.method:
		return render(request, "veoc/upload_csv.html", data)
    # if not GET, then proceed
	try:
		csv_file = request.FILES["csv_file"]
		if not csv_file.name.endswith('.csv'):
			messages.error(request,'File is not CSV type')
			return HttpResponseRedirect(reverse("veoc:upload_csv"))
        #if file is too large, return
		if csv_file.multiple_chunks():
			messages.error(request,"Uploaded file is too big (%.2f MB)." % (csv_file.size/(1000*1000),))
			return HttpResponseRedirect(reverse("veoc:upload_csv"))

		file_data = csv_file.read().decode("utf-8")

		lines = file_data.split("\n")
		#loop over the lines and save them in db. If error , store as string and then display
		for line in lines:
			fields = line.split(",")
			data_dict = {}
			data_dict["name"] = fields[0]
			data_dict["start_date_time"] = fields[1]
			data_dict["end_date_time"] = fields[2]
			data_dict["notes"] = fields[3]
			try:
				form = EventsForm(data_dict)
				if form.is_valid():
					form.save()
				else:
					logging.getLogger("error_logger").error(form.errors.as_json())
			except Exception as e:
				logging.getLogger("error_logger").error(repr(e))
				pass

	except Exception as e:
		logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
		messages.error(request,"Unable to upload file. "+repr(e))

	return HttpResponseRedirect(reverse("veoc:upload_csv"))

# @login_required
def daily_report_submit(request):
    datefilter =request.POST.get('date_reported','')
    disease_types = disease_type.objects.all().exclude(description = 'none')
    watchers = mytimetable.objects.all().filter(from_date__lte = datefilter, to_date__gte = datefilter)

    # for watch in watchers:
    #     w_name = EOC_Contacts.objects.filter(first_name = watch).get('first_name', 'second_name')
    #
    #     print(w_name)
    #watchersb = mytimetable.objects.all()
    #print('yeeee')
    # disease_report_stat= {}
    # for disease_type in disease_types:
    #    diseases_count = Disease.objects.all().filter(disease_type_id=disease_type.id).count()
    #    disease_report_stat[disease_type.description] = diseases_count


    call_log_count_stat= {}

    #count flash back log
    Call_flashback_logs_count =  call_flashback.objects.all().filter(date_reported=datefilter).count()
    call_log_count_stat["Other enquiries"] =  Call_flashback_logs_count

    #count unrelated call
    Unrelated_call_logs_count =  Unrelated_calls.objects.all().filter(date_reported=datefilter).count()
    call_log_count_stat["Unrelated calls"] =  Unrelated_call_logs_count

    event_types = Event_type.objects.all().exclude(description = 'none')
    for event_type in event_types:
       call_logs_count = Call_log.objects.all().filter(event_type_id=event_type.id).filter(date_reported=datefilter).count()
       call_log_count_stat[event_type.description] =  call_logs_count

    disease_types = Disease_type.objects.all().exclude(description = 'none')
    for disease_type in disease_types:
       call_logs_count = Call_log.objects.all().filter(disease_type_id=disease_type.id).filter(date_reported=datefilter).count()
       call_log_count_stat[disease_type.description] =  call_logs_count
       call_log_sum = sum(call_log_count_stat.values())

    daily_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=2).filter(date_reported=datefilter).count()
    daily_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(date_reported=datefilter).count()
    daily_enquiry = Call_flashback_logs_count + Unrelated_call_logs_count
    daily_total_calls = daily_conf_call_log_count + daily_rum_call_log_count + daily_enquiry
    # print(daily_conf_call_log_count)

    regions = Region.objects.all()
    diseases_list = {}
    events_list = {}
    for region in regions:
       diseases = Disease.objects.all().filter(region_id=region.id).filter(date_created=datefilter)
       diseases_list[region.description] = diseases
       events = Event.objects.all().filter(region_id=region.id).filter(date_created=datefilter)
       events_list[region.description] = events

    #Get all significant events,diseases and Call logs
    #significant_diseases = Disease.objects.all().filter(significant = "True").filter(date_created=datefilter)
    significant_diseases = "None"
    #significant_events = Event.objects.all().filter(significant = "True").filter(date_created=datefilter)
    significant_events = "None"
    #significant_call_logs = Call_log.objects.all().filter(significant = "True").filter(date_reported=datefilter)
    significant_call_logs = ""
    #if there are no significant events indicate as none
    if (significant_events =="") and (significant_diseases == "") and significant_call_logs =="":
       significant_events_none="None"
    else:
       significant_events_none=""

    events = {'significant_diseases': significant_diseases,'significant_events': significant_events,'significant_call_logs': significant_call_logs,
              'watchers': watchers,'event_vals': Event.objects.all(),"date_filter":datefilter,"significant_events_none": significant_events_none,
              "diseases": diseases_list, "events": events_list, "call_log_count_stat": call_log_count_stat, "call_log_sum": call_log_sum,
              'daily_conf_call_log_count': daily_conf_call_log_count, 'daily_rum__call_log_count': daily_rum_call_log_count,
              'daily_enquiry': daily_enquiry, 'daily_total_calls': daily_total_calls}
    return render(request, 'veoc/daily_report.html', events)

def weekly_report(request):

    ##get five years from current year
    y_ = 0
    yrs_ = []
    while y_ < 5:
        dt = datetime.now()
        yr_val = datetime.now().replace(year = dt.year - y_)
        final_year = yr_val.year
        data = {'year': final_year}
        yrs_.append(data)
        y_ = y_ + 1

    epi_wks = {'epi_years': yrs_}

    return render(request, 'veoc/weekly_report.html', epi_wks)

def weekly_report_submit(request):

    ###################################################################################
    iso_date = request.POST.get('epi_week','')
    iso_year = request.POST.get('epi_year','')

    date_data = iso_date.split("#")
    start_date = date_data[0]
    end_date = date_data[1]

    # print(iso_year)
    # print(start_date)
    # print(end_date)

    y_ = 0
    yrs_ = []
    while y_ < 5:
        dt = datetime.now()
        yr_val = datetime.now().replace(year = dt.year - y_)
        final_year = yr_val.year
        data = {'year': final_year}
        yrs_.append(data)
        y_ = y_ + 1

    epi_yrs = {'epi_years': yrs_}
    #######################################################################################

    disease_types = Disease_type.objects.all().exclude(description = 'none')
    disease_report_stat= {}
    for disease_type in disease_types:
       diseases_count = Disease.objects.all().filter(disease_type_id=disease_type.id).count()
       disease_report_stat[disease_type.description] = diseases_count

    #x = request.POST.get('date_from','')
    #print x
    #==date_from = request.POST.get('date_from','')
   # y =request.POST.get('date_to','')
    #==date_to = request.POST.get('date_to','')

    #watchers = mytimetable.objects.all().filter(from_date__lte = date_from, to_date__gte = date_from)
    watchers = mytimetable.objects.all().filter(from_date__lte = start_date, to_date__gte = end_date)
    call_log_count_stat= {}

    #count flash back log
    #==Call_flashback_logs_count =  Call_flashback.objects.all().filter(date_reported__range=[date_from, date_to]).count()
    Call_flashback_logs_count =  Call_flashback.objects.all().filter(date_reported__range=[start_date, end_date]).count()
    call_log_count_stat["Other enquiries"] =  Call_flashback_logs_count

    #count unrelated call
    #==Unrelated_call_logs_count =  Unrelated_calls.objects.all().filter(date_reported__range=[date_from, date_to]).count()
    Unrelated_call_logs_count =  Unrelated_calls.objects.all().filter(date_reported__range=[start_date, end_date]).count()
    call_log_count_stat["Unrelated calls"] =  Unrelated_call_logs_count

    event_types = Event_type.objects.all().exclude(description = 'none')
    for event_type in event_types:
       #==call_logs_count = Call_log.objects.all().filter(event_type_id=event_type.id).filter(date_reported__range=[date_from, date_to]).count()
       call_logs_count = Call_log.objects.all().filter(event_type_id=event_type.id).filter(date_reported__range=[start_date, end_date]).count()
       call_log_count_stat[event_type.description] =  call_logs_count

    disease_types = Disease_type.objects.all().exclude(description = 'none')
    for disease_type in disease_types:
       #call_logs_count = Call_log.objects.all().filter(disease_type_id=disease_type.id).filter(date_reported__range=[date_from, date_to]).count()
       call_logs_count = Call_log.objects.all().filter(disease_type_id=disease_type.id).filter(date_reported__range=[start_date, end_date]).count()
       call_log_count_stat[disease_type.description] =  call_logs_count
       call_log_sum = sum(call_log_count_stat.values())

    #wkly_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=2).filter(date_reported__range=[date_from, date_to]).count()
    wkly_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=2).filter(date_reported__range=[start_date, end_date]).count()
    # wkly_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(date_reported__range=[date_from, date_to]).count()
    wkly_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(date_reported__range=[start_date, end_date]).count()
    wkly_enquiry = Call_flashback_logs_count + Unrelated_call_logs_count
    wkly_total_calls = wkly_conf_call_log_count + wkly_rum_call_log_count + wkly_enquiry
    # print(rum_disease_call_log_count)

    regions = Region.objects.all()
    diseases_list = {}
    events_list = {}
    for region in regions:
       diseases = Disease.objects.all().filter(region_id=region.id).filter(date_created__range=[start_date, end_date])
       diseases_list[region.description] = diseases
       events = Event.objects.all().filter(region_id=region.id).filter(date_created__range=[start_date, end_date])
       events_list[region.description] = events

    #Get all significant events,diseases and Call logs
    #significant_diseases = Disease.objects.all().filter(significant = "True").filter(date_created__range=[start_date, end_date])
    significant_diseases = ""
    #significant_events = Event.objects.all().filter(significant = "True").filter(date_created__range=[start_date, end_date])
    significant_events = ""
    #significant_call_logs = Call_log.objects.all().filter(significant = "True").filter(date_reported__range=[start_date, end_date])
    significant_call_logs = ""
    #if there are no significant events indicate as none
    if (significant_events =="") and (significant_diseases == "") and significant_call_logs =="":
       significant_events_none="None"
    else:
       significant_events_none=""

    # significant_events = Significant_event.objects.all().filter(date_created__range=[date_from, date_to])
    # if not significant_events :
    #  significant_events_none="None"
    #
    # media_reports = Significant_event.objects.all().filter(date_created__range=[date_from, date_to])
    # if not media_reports :
    #  media_reports_none="None"

    # events = {'event_vals': Event.objects.all(),"diseases": diseases_list,"date_from":date_from,"date_to":date_to,
    events = {'event_vals': Event.objects.all(),"diseases": diseases_list,"date_from":start_date,"date_to":end_date,
              # "media_reports":media_reports,"media_reports_none":media_reports_none,
              "significant_events_none": significant_events_none,'watchers': watchers,
              "significant_diseases": significant_diseases,"significant_events": significant_events, "events": events_list,
              "call_log_count_stat": call_log_count_stat, "call_log_sum": call_log_sum,
              'wkly_conf_call_log_count': wkly_conf_call_log_count, 'wkly_rum_call_log_count': wkly_rum_call_log_count,
              'wkly_enquiry':wkly_enquiry,'wkly_total_calls': wkly_total_calls}

    events.update(epi_yrs) #add api years to the dictionary

    return render(request, 'veoc/weekly_report.html', events)

def Periodic_Report(request):
    return render(request, 'veoc/periodic_report.html')

def analytics(request):
    return render(request, 'veoc/analytics.html')

def users_list(request):
    users_count = User.objects.all().count()
    users = User.objects.all()
    # org_units = organizational_units.objects.all().filter(hierarchylevel__lt=3).order_by('name')
    org_units = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    user_groups = Group.objects.all()

    values = {'users_count': users_count, 'users':users, 'org_units': org_units, 'user_groups':user_groups}

    return render(request, 'veoc/users.html', values)

def get_org_unit(request):
    if request.method == 'POST':
        global org_units
        access_level = request.POST.get('access_level','')

        if access_level == 'National':
            org_units = organizational_units.objects.all().filter(hierarchylevel=1).order_by('name')

        else:
            org_units = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')

        serialized=serialize('json',org_units)
        obj_list=json.loads(serialized)

        return HttpResponse(json.dumps(obj_list),content_type="application/json")

def diseases_list(request):
    if request.method == "POST":
        uid = request.POST.get('uid','')
        disease_name = request.POST.get('disease_name','')
        priority = request.POST.get('priority','')

        if not priority:
            priority=False
        else:
            priority=True

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        dhis_disease_type.objects.create(uid=uid, name=disease_name, priority_disease=priority)

    disease_count = dhis_disease_type.objects.all().count
    disease_vals = dhis_disease_type.objects.all()
    values = {'disease_count':disease_count, 'disease_vals': disease_vals}

    return render(request, 'veoc/diseaselist.html', values)

def events_list(request):
    if request.method == "POST":
        uid = request.POST.get('uid','')
        event_name = request.POST.get('event_name','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        dhis_event_type.objects.create(uid=uid, name=event_name)

    event_count = dhis_event_type.objects.all().count
    event_vals = dhis_event_type.objects.all()
    values = {'event_count':event_count, 'event_vals': event_vals}

    return render(request, 'veoc/eventlist.html', values)

def disgnation_list(request):
    if request.method == "POST":
        design = request.POST.get('designation','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        designation.objects.create(designation_description=design, updated_at=current_date,
                created_by=userObject, updated_by=userObject, created_at=current_date)

    designations_count = designation.objects.all().count
    designation_vals = designation.objects.all()
    values = {'designation_vals_count':designations_count, 'designation_vals': designation_vals}

    return render(request, 'veoc/disgnationlist.html', values)

def edit_disgnation_list(request):
    if request.method == "POST":
        myid = request.POST.get('id','')
        design = request.POST.get('description','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #updating values to database
        designation.objects.filter(pk=myid).update(designation_description=design, updated_at=current_date,
                created_by=userObject, updated_by=userObject, created_at=current_date)

    designations_count = designation.objects.all().count
    designation_vals = designation.objects.all()
    values = {'designation_vals_count':designations_count, 'designation_vals': designation_vals}

    return render(request, 'veoc/disgnationlist.html', values)

def data_list(request):
    if request.method == "POST":
        source = request.POST.get('data_source','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        data_source.objects.create(source_description=source, updated_at=current_date,
                created_by=userObject, updated_by=userObject, created_at=current_date)

    data_source_count = data_source.objects.all().count
    data_sources = data_source.objects.all()
    values = {'data_source_count':data_source_count, 'data_sources': data_sources}

    return render(request, 'veoc/datasourcelist.html', values)

def edit_data_list(request):
    if request.method == "POST":
        myid = request.POST.get('id','')
        source = request.POST.get('data_source','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')
        print(myid)
        #get current user
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        data_source.objects.filter(pk=myid).update(source_description=source, updated_at=current_date,
                created_by=userObject, updated_by=userObject, created_at=current_date)

    data_source_count = data_source.objects.all().count
    data_sources = data_source.objects.all()
    values = {'data_source_count':data_source_count, 'data_sources': data_sources}

    return render(request, 'veoc/datasourcelist.html', values)

def contact_list(request):
    if request.method == "POST":
        cont_type = request.POST.get('description','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #saving values to databse
        contact_type.objects.create(contact_description=cont_type, updated_at=current_date,
                created_by=userObject, updated_by=userObject, created_at=current_date)

    contact_types_count = contact_type.objects.all().count
    contact_types = contact_type.objects.all()
    values = {'contact_types_count':contact_types_count, 'contact_types': contact_types}

    return render(request, 'veoc/contacttypelist.html', values)

def call_register_form(request):
    form = forms.call_logs_form()
    return render(request, 'veoc.call_register.html', {'call_reg_form':form} )

def call_flashback(request):
    return render(request, 'veoc/call_flashback.html')

def google_map(request):
    return render(request, 'veoc/google-map.html')

def data_map(request):
    return render(request, 'veoc/data-map.html')

def facility_map(request):
    return render(request, 'veoc/facility-map.html')

def police_map(request):
    return render(request, 'veoc/police-map.html')

def lab_refferal_map(request):
    return render(request, 'veoc/lab_refferal-map.html')

def flot_charts(request):
    return render(request, 'veoc/flot-charts.html')

def bar_charts(request):
    return render(request, 'veoc/bar-charts.html')

def line_charts(request):
    return render(request, 'veoc/line-charts.html')

def area_charts(request):
    return render(request, 'veoc/area-charts.html')

# @login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('settings:profile')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        user_form = UserForm(instance=request.user)

        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'veoc/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def user_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, isinstance=request.user.profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('veoc/profile')
    else:
        user = request.user
        profile = user.profile
        form = ProfileForm(isinstance=profile)

    args = {}
    args.update(csrf(request))

    args['form'] = form

    return render_to_response('veoc/profile', args)

# @permission_required(admin.can_add_log_entry)
def org_unit(request):
    template = "upload_csv.html"

    prompt = {
        'order': 'Order of the CSV file to upload'
    }

    if request.method == "GET":
        return render(request, 'veoc/upload_csv.html', prompt)

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        message.error(request, 'This is NOT a CSV file')

    data_set = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.render(io_string, delimiter=',', quotechar="|"):
        _, created = organizational_units.objects.update_or_create(
            uid = column[0],
            organisationunitid = column[1],
            name = column[2],
            code = column[3],
            parentid = column[4],
            hierarchylevel = column[5]
        )

    context = {}
    return render(request, 'veoc/upload_csv.html', context)

def process_idsr_data(request):
    org_units = organizational_units.objects.filter(hierarchylevel__gte = 5).values_list('uid', flat=True).order_by('id')
    url = "https://testhis.uonbi.ac.ke/api/29/analytics.json"
    organization_units = []

    for org_unit in org_units:
        organization_units.append(org_unit)

    # The length of the organization units
    print(len(organization_units))

    pull_dhis_idsr_data.delay(organization_units, url)

    return HttpResponse("")

@csrf_exempt
def get_diseases(request):
    if request.method=="POST":

        allvals=dhis_disease_type.objects.all().order_by('name')
        serialized=serialize('json',allvals)
        obj_list=json.loads(serialized)

        return HttpResponse(json.dumps(obj_list),content_type="application/json")

def get_disease_cordinates(request):
    if request.method=="POST":

        dtype=request.POST.get('dtype','')
        mydtype = dhis_disease_type.objects.get(name = dtype)
        allvals=list(disease.objects.filter(disease_type=mydtype).values('county__name','county__latitude','county__longitude'))
        data=json.dumps(allvals)

    return HttpResponse(data,content_type="application/json")

def get_barchartvals(request):

    if request.method=='POST':

        diseaseType=request.POST.get('dt','')
        diseaseT=dhis_disease_type.objects.get(name=diseaseType)

        # for county in counties:
        call_count = call_log.objects.filter(disease_type = diseaseT).values('county__name')
        allvals=list(call_log.objects.filter(disease_type=diseaseT).values('county__name'))

        data=json.dumps(allvals)

        return HttpResponse(data,content_type="application/json")

@csrf_exempt
def get_pie_disease(request):
    if request.method=="POST":

        dtype=request.POST.get('dtype','')
        mydtype = dhis_disease_type.objects.get(name=dtype)
        allvals2 = list(disease.objects.filter(disease_type=mydtype).filter(date_reported__gte = date.today()- timedelta(days=30)).values('county__name','subcounty__name').annotate(mytotal=Count('county__name')))

        data=json.dumps(allvals2)

    return HttpResponse(data,content_type="application/json")

@csrf_exempt
def get_pie_event(request):
    if request.method=="POST":
        etype=request.POST.get('etype','')
        myetype = dhis_event_type.objects.get(name=etype)
        allvals2 = list(event.objects.filter(event_type=myetype).filter(date_reported__gte = date.today()- timedelta(days=30)).values('county__name','subcounty__name').annotate(mytotal=Count('county__name')))
        data=json.dumps(allvals2)

    return HttpResponse(data,content_type="application/json")

@csrf_exempt
def get_dhis_disease(request):
    print('inside get_dhis_diseases')
    if request.method=="POST":
        disease_type=request.POST.get('dhis_disease_type','')
        mydisease_type = idsr_diseases.objects.get(name=disease_type)
        # my_disease_id = mydisease_type.id
        # print(my_disease_id)

        # dhis_graph_data = list(v_dhis_national_data_view.objects.all().filter(idsr_disease_id = mydisease_type).values('data_value', 'period', 'idsr_incident_id__name'))
        dhis_graph_data = list(v_dhis_national_report_data_view.objects.all().filter(idsr_disease_id = mydisease_type).values('cases', 'deaths', 'period'))
        print(dhis_graph_data)

        #pull cases associated with this deseases
        # my_disease_cases = list(idsr_weekly_national_report.objects.all().filter(idsr_disease_id = mydisease_type).filter(idsr_incident_id = 1).values('data_value', 'period', 'idsr_incident_id__name'))
        # my_disease_deaths = list(idsr_weekly_national_report.objects.all().filter(idsr_disease_id = mydisease_type).filter(idsr_incident_id = 2).values('data_value', 'period' ,'idsr_incident_id__name'))
        # cases = my_disease_cases + my_disease_deaths
        # print(cases)
        # allvals2 = list(idsr_weekly_national_report.objects.filter(idsr_disease_id=mydisease_type).values('idsr_disease_id__name','idsr_incident_id__name').annotate(casestotal=Count('data_value').annotate(deathtotal=Count('data_value')))
        #
        data=json.dumps(dhis_graph_data)

    return HttpResponse(data,content_type="application/json")

@csrf_exempt
def get_piedrilldown_disease(request):
    if request.method=="POST":

        cty=request.POST.get('ctype','')
        dty=request.POST.get('dtype','')
        myctype=organizational_units.objects.all().filter(hierarchylevel = 2).get(name=cty)
        mydtype=dhis_disease_type.objects.get(name=dty)
        allvals2=list(disease.objects.filter(county=myctype,disease_type=mydtype).filter(date_reported__gte = date.today()- timedelta(days=30)).values('subcounty__name').annotate(mytotal=Count('subcounty__name')))

        data=json.dumps(allvals2)

    return HttpResponse(data,content_type="application/json")

@csrf_exempt
def get_piedrilldown_event(request):
    if request.method=="POST":

        cty=request.POST.get('ctype','')
        ety=request.POST.get('etype','')
        myctype=organizational_units.objects.all().filter(hierarchylevel = 2).get(name=cty)
        myetype=dhis_event_type.objects.get(name=ety)
        allvals2=list(event.objects.filter(county=myctype,event_type=myetype).filter(date_reported__gte = date.today()- timedelta(days=30)).values('subcounty__name').annotate(mytotal=Count('subcounty__name')))

        data=json.dumps(allvals2)

    return HttpResponse(data,content_type="application/json")

def get_chart_vals(request):
    global cases_data
    if request.method=="POST":
        chart_d_type = dhis_disease_type.objects.all().order_by('name')
        print(chart_d_type)
        _cases = []
        for crt_tpye in chart_d_type:
            disease_description = list(disease.objects.filter(disease_type_id = crt_tpye.id).filter(date_reported__gte = date.today()- timedelta(days=30)).values('disease_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct())
            _cases.append(disease_description)
            print(_cases)
        cases_data = json.dumps(_cases)

        return HttpResponse(cases_data,content_type="application/json")

    else:
        return HttpResponse("No data.")

def get_disease_modal(request):
    if request.method=="POST":
        disease_type = dhis_disease_type.objects.all()
        all_data = []
        for disease_data in disease_type:
            call_log_data = call_log.objects.all().filter(disease_type_id = disease_data.id).order_by("-date_reported")[:30]
            # call_log_data = list(Call_log.objects.all().filter(disease_type_id = disease_data.id).values('date', 'disease_type__id', 'county__id', 'subcounty__id', 'incident_status__id').order_by("-date_reported")[:30])
        #print the length to find loops
            # for call_data in call_log_data:
            data = list(call_log.objects.all().filter(disease_type_id=disease_data.id).values('disease_type__name', 'county__name', 'subcounty__name', 'location', 'description' ,'incident_status__id', 'action_taken').distinct().order_by("-date_reported")[:30])

            all_data.append(data)
        _data = json.dumps(all_data)
    # print(all_data)

    return HttpResponse(_data,content_type="application/json")

def facilities_mappings(request):

    return render(request, 'veoc/facilities_mappings.html')

def disease_mappings(request):
    diseases = dhis_disease_type.objects.all().order_by('name')
    values = {'diseases': diseases}

    return render(request, 'veoc/disease_mappings.html', values)

def police_post_mappings(request):

    return render(request, 'veoc/police_post_mappings.html')

def lab_referrals_mappings(request):

    return render(request, 'veoc/lab_referrals_mappings.html')

def heat_maps(request):

    return render(request, 'veoc/heat_maps.html')

def get_facilities_ward(request):

    if request.method=="POST":
        ward = request.POST.get('ward','')
        print(ward)

        ward_parent_id = organizational_units.objects.get(organisationunitid = ward)
        allvals=list(organizational_units.objects.filter(parentid = ward_parent_id).values('name','latitude','longitude'))
        data=json.dumps(allvals)

    return HttpResponse(data,content_type="application/json")

def get_facilities_ward(request):

    if request.method=="POST":
        ward = request.POST.get('ward','')
        print(ward)

        ward_parent_id = organizational_units.objects.get(organisationunitid = ward)
        allvals=list(organizational_units.objects.filter(parentid = ward_parent_id).values('name','latitude','longitude'))
        data=json.dumps(allvals)

    return HttpResponse(data,content_type="application/json")

def get_facilities_county(request):

    if request.method=="POST":
        # county = request.POST.get('county','')
        # print(county)

        # county_parent_id = organizational_units.objects.get(name = county)
        allvals=list(organizational_units.objects.filter(hierarchylevel = 2).values('name','latitude','longitude'))
        data=json.dumps(allvals)

    return HttpResponse(data,content_type="application/json")

def get_police_posts_county(request):

    if request.method=="POST":
        county = request.POST.get('county','')
        print(county)

        # get county id where county = posted county
        #county_id = County.objects.values().filter(description=county).values_list('id')
        #print(county_id)

        #allvals=list(Police_posts.objects.values().filter(county=county_id))
        #print(allvals)

        # data=json.dumps(allvals)
        data=json.dumps(["allvals"])

        return HttpResponse(data,content_type="application/json")

def get_police_posts(request):

    if request.method=="POST":

        allvals=list(police_post.objects.values())
        print(allvals)

        data=json.dumps(allvals)

        return HttpResponse(data,content_type="application/json")

def get_lab_posts(request):

    if request.method=="POST":
        allvals=list(referral_labs.objects.values())

        data=json.dumps(allvals)

        return HttpResponse(data,content_type="application/json")

def week_shift(request):
    event = {'events': eoc_events_calendar.objects.all()}
    print(event)
    return render(request, 'veoc/weekly_shift.html', event)

def calendar_events_create(request):
    if request.method=='POST':

        name=request.POST.get('name','')
        description = request.POST.get('description', '')
        start_date=request.POST.get('start_date','')
        end_date=request.POST.get('end_date','')
        time = request.POST.get('time', '')

        cur_user=request.user.username
        created_by=User.objects.get(username=cur_user)

        insert = eoc_events_calendar(event_name=name, start_date=start_date, time=time,
                end_date=end_date, event_description=description, created_by=created_by, updated_by=created_by)

        insert.save()
        #find ways of retrieving the saved id and loop to send the success message after confirmation
        success="Event created successfully"
        messages.success(request, success)
        # return HttpResponseRedirect("veoc/weekly_shift.html")
        return render(request,"veoc/weekly_shift.html",{"success":success, 'events' : eoc_events_calendar.objects.all()})

    else:
        success="Contact not created,try again"
        messages.error(request, success)
        return render(request,"veoc/weekly_shift.html",{"success":success, 'events' : eoc_events_calendar.objects.all()})

def eoc_contacts(request):
    contacts_count = staff_contact.objects.all().count
    eocContacts = staff_contact.objects.all()
    design = designation.objects.all()
    eoc = {'eocContacts': eocContacts, 'designation': design,
            'contacts_count':contacts_count}

    return render(request, 'veoc/surveillance_contacts.html', eoc)

def eoc_contacts_create(request):

    if request.method=='POST':
        first_name=request.POST.get('first_name','')
        last_name=request.POST.get('last_name','')
        designatn=request.POST.get('designation','')
        phone_number=request.POST.get('phone_number','')
        email_address=request.POST.get('email_address','')
        team_lead=request.POST.get('lead','')

        if not team_lead:
            team_lead=False
        else:
            team_lead=True

        designation_source=designation.objects.get(designation_description=designatn)
        cur_user=request.user.username
        created_by=User.objects.get(username=cur_user)

        day = time.strftime("%Y-%m-%d")

        insert = staff_contact(first_name=first_name, last_name=last_name, designation=designation_source, phone_number=phone_number,
                                  email_address=email_address, team_lead=team_lead, created_by=created_by, updated_by=created_by)
        insert.save()

        success="Contact created successfully"
        messages.success(request, success)

        return render(request,"veoc/surveillance_contacts.html",{"success":success,'eocContacts': staff_contact.objects.all(), 'designation': designation.objects.all()})

    else:
        success="Contact not created,try again"
        messages.error(request, success)
        return render(request,"veoc/surveillance_contacts.html",{"success":success,'eocContacts': staff_contact.objects.all(), 'designation': designation.objects.all()})

def contact_edit(request):
    if request.method=='POST':
        contacts_id = request.POST.get('id','')
        first_name=request.POST.get('first_name','')
        last_name=request.POST.get('last_name','')
        designatn=request.POST.get('designation','')
        phone_number=request.POST.get('phone_number','')
        email_address=request.POST.get('email_address','')
        team_lead=request.POST.get('lead','')

        if not team_lead:
            team_lead=False
        else:
            team_lead=True

        designation_source=designation.objects.get(pk=designatn)
        cur_user=request.user.username
        created_by=User.objects.get(username=cur_user)

        day = time.strftime("%Y-%m-%d")

        staff_contact.objects.filter(pk=contacts_id).update(first_name=first_name,
            last_name=last_name, designation=designation_source, phone_number=phone_number,
            email_address=email_address, team_lead=team_lead, created_by=created_by, updated_by=created_by)

        success="Contact updated successfully"
        messages.success(request, success)

        return render(request,"veoc/surveillance_contacts.html",{"success":success,'eocContacts': staff_contact.objects.all(), 'designation': designation.objects.all()})

    else:
        success="Contact not created,try again"
        messages.error(request, success)
        return render(request,"veoc/surveillance_contacts.html",{"success":success,'eocContacts': staff_contact.objects.all(), 'designation': designation.objects.all()})


def allocation_sheet(request):
    return render(request, 'veoc/alocation_sheet.html')

def contact_json(request):
    all_ = staff_contact.objects.all()
    print('inside contact_json')
    print(all_)
    serialized = serialize('json', all_,use_natural_foreign_keys=True,use_natural_primary_keys=True)
    obj_list=json.loads(serialized)

    return HttpResponse(json.dumps(obj_list),content_type='application/json')

def get_existing_timetable(request):
    all_ = watcher_schedule.objects.all()

    serialized = serialize('json', all_,use_natural_foreign_keys=True,use_natural_primary_keys=True)
    obj_list=json.loads(serialized)

    return HttpResponse(json.dumps(obj_list),content_type='application/json')

def get_timetables(request):
    if request.method=='POST':
        contactarray=request.POST.getlist('contactsarray[]')
        fdate=request.POST.get('fromdate','')
        tdate=request.POST.get('todate','')

        #looks for the week number of the date
        d=fdate.split('-')
        wkno = date(int(d[0]),int(d[1]),int(d[2])).isocalendar()[1]
        print(wkno)

        for x in contactarray:
            insertingcont=watcher_schedule(watcher_details=x,week_no=wkno,from_date=fdate,to_date=tdate)
            insertingcont.save()

            #send email to the contacts saved to be watchers
            # watcher_email = EOC_Contacts.objects.values('email').filter(first_name = x)
            # print(watcher_email)
            #
            # for email in watcher_email:
            #     _email = email['email']
            #     print(str(email))
            #     subject = "EOC Watcher time table"
            #     message = "Hello "+x+",\n\n"+"This is to notify you that you have been scheduled to work as a watcher in the EOC as from : "\
            #               + fdate+" to : " + tdate+".\n"+"Please contact the EOC manager for any enquiries or query."+"\n\n"\
            #               +"This is an automated notifier please do not reply."
            #
            #     send_mail(subject, message, settings.EMAIL_HOST_USER, [_email], fail_silently=False)

    myresponse="success adding contacts to timetable"
    data=json.dumps(myresponse)

    return HttpResponse(data,content_type="application/json")

def search_watchers(request):

    if request.method=='POST':
        search_date=request.POST.get('searchdate','')
        time_table = watcher_schedule.objects.values('from_date', 'to_date').distinct()

        for x in time_table:
            from_d = x['from_date']
            to_d = x['to_date']

            q_data = from_d < search_date < to_d
            if q_data:
                myresponse = mytimetable.objects.all().filter(from_date = from_d, to_date = to_d)
                print('watchers : ' + str(myresponse))

                serialized = serialize('json', myresponse,use_natural_foreign_keys=True,use_natural_primary_keys=True)
                obj_list=json.loads(serialized)
                data=json.dumps(obj_list)

                break
            else:
                myresponse = "No watchers set for the week selected"
                data=json.dumps(myresponse)

    return HttpResponse(data,content_type="application/json")

def get_existing_timetable(request):
    all_ = watcher_schedule.objects.all()

    serialized = serialize('json', all_,use_natural_foreign_keys=True,use_natural_primary_keys=True)
    obj_list=json.loads(serialized)

    return HttpResponse(json.dumps(obj_list),content_type='application/json')

def watchers_schedule(request):

    #select watchers set for current week and over not past teams
    current_date = date.today().strftime ('%Y-%m-%d')
    d=current_date.split('-')
    current_wkno = date(int(d[0]),int(d[1]),int(d[2])).isocalendar()[1]
    w = watcher_schedule.objects.filter(week_no__gte = current_wkno)
    watch = {'watchers': w}

    return render(request, 'veoc/watchers_schedule.html', watch)

def all_contact(request):
    all_contacts = contact.objects.all()
    contact_count = contact.objects.all().count
    designatn = designation.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    c_type = contact_type.objects.all()

    values = {'contacts': all_contacts, 'contact_count': contact_count, 'designations': designatn, 'county': county, 'contact_types': c_type }

    # return render(request, 'veoc/contact.html', values)
    return render(request, 'veoc/cont.html', values)

def add_contact(request):

    if request.method=='POST':
        f_name = request.POST.get('first_name','')
        l_name = request.POST.get('last_name','')
        design = request.POST.get('designation','')
        phone = request.POST.get('phone_no','')
        email = request.POST.get('email','')
        c_type = request.POST.get('contact_type','')
        cnty = request.POST.get('county','')
        subcnty = request.POST.get('subcounty','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk = current_user.id)
        designationObject = designation.objects.get(pk = design)
        contactTypeObject = contact_type.objects.get(pk = c_type)
        countyObject = organizational_units.objects.get(name = cnty)
        subcountyObject = organizational_units.objects.get(organisationunitid = subcnty)

        #saving values to database
        contact.objects.create(designation=designationObject, type_of_contact=contactTypeObject, county=countyObject, subcounty=subcountyObject,
        first_name=f_name, last_name=l_name, phone_number=phone, email_address=email,
        updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

    all_contacts = contact.objects.all()
    contact_count = contact.objects.all().count
    designatn = designation.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    c_type = contact_type.objects.all()

    values = {'contacts': all_contacts, 'contact_count': contact_count, 'designations': designatn, 'county': county, 'contact_types': c_type }

    return render(request, 'veoc/contact.html', values)

def minutes(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=1).count
    documents = document_repository.objects.all().filter(category=1)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/minutes.html', values)

def sitreps(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=2).count
    documents = document_repository.objects.all().filter(category=2)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/sitrep.html', values)

def protocol(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=6).count
    documents = document_repository.objects.all().filter(category=6)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/protocol.html', values)

def out_report(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=7).count
    documents = document_repository.objects.all().filter(category=7)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/out_report.html', values)

def bulletins(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=3).count
    documents = document_repository.objects.all().filter(category=3)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/bulletins.html', values)

def publications(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=4).count
    documents = document_repository.objects.all().filter(category=4)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/publications.html', values)

def case_documents(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=8).count
    documents = document_repository.objects.all().filter(category=8)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/case_documents.html', values)

def sops(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=9).count
    documents = document_repository.objects.all().filter(category=9)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/sops.html', values)

def others(request):
    document_categories = repository_categories.objects.all()
    documents_count = document_repository.objects.all().filter(category=5).count
    documents = document_repository.objects.all().filter(category=5)

    values = {'document_categories': document_categories, 'documents_count': documents_count,
        'documents': documents}

    return render(request, 'veoc/others.html', values)

def add_document(request):

    if request.method=='POST':
        cat = request.POST.get('category','')
        descriptn = request.POST.get('description','')
        authr = request.POST.get('author','')
        file=request.FILES.get('file','')
        public = request.POST.get('public','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        print(current_user)
        print(file)
        userObject = User.objects.get(pk = current_user.id)
        categoryObject = repository_categories.objects.get(pk = cat)

        #saving values to database
        doc_rep=document_repository()
        doc_rep.category=categoryObject
        doc_rep.description=descriptn
        doc_rep.author=authr
        doc_rep.myfile=file
        doc_rep.public_document=public
        doc_rep.updated_at=current_date
        doc_rep.created_by=userObject
        doc_rep.updated_by=userObject
        doc_rep.created_at=current_date
        doc_rep.save()

        if cat == '1':
            documents_count = document_repository.objects.all().filter(category=1).count
            documents = document_repository.objects.all().filter(category=1)
            template = 'veoc/minutes.html'
        elif cat=='2':
            documents_count = document_repository.objects.all().filter(category=2).count
            documents = document_repository.objects.all().filter(category=2)
            template = 'veoc/sitrep.html'
        elif cat=='3':
            documents_count = document_repository.objects.all().filter(category=3).count
            documents = document_repository.objects.all().filter(category=3)
            template = 'veoc/bulletins.html'
        elif cat=='4':
            documents_count = document_repository.objects.all().filter(category=4).count
            documents = document_repository.objects.all().filter(category=4)
            template = 'veoc/publications.html'
        elif cat=='5':
            documents_count = document_repository.objects.all().filter(category=5).count
            documents = document_repository.objects.all().filter(category=5)
            template = 'veoc/others.html'
        elif cat=='6':
            documents_count = document_repository.objects.all().filter(category=6).count
            documents = document_repository.objects.all().filter(category=6)
            template = 'veoc/protocol.html'
        elif cat=='7':
            documents_count = document_repository.objects.all().filter(category=7).count
            documents = document_repository.objects.all().filter(category=7)
            template = 'veoc/out_report.html'
        elif cat=='8':
            documents_count = document_repository.objects.all().filter(category=8).count
            documents = document_repository.objects.all().filter(category=8)
            template = 'veoc/case_documents.html'
        else:
            documents_count = document_repository.objects.all().filter(category=9).count
            documents = document_repository.objects.all().filter(category=9)
            template = 'veoc/sops.html'

        document_categories = repository_categories.objects.all()

        values = {'document_categories': document_categories, 'documents_count': documents_count,
            'documents': documents}

        return render(request, template, values)

def edit_document(request):

    if request.method=='POST':
        myid = request.POST.get('id','')
        cat = request.POST.get('category','')
        descriptn = request.POST.get('description','')
        authr = request.POST.get('author','')
        file=request.FILES.get('file','')
        public = request.POST.get('public','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        print(current_user)
        print(file)
        userObject = User.objects.get(pk = current_user.id)
        categoryObject = repository_categories.objects.get(pk = cat)

        #saving edited values to database
        document_repository.objects.filter(pk=myid).update(category=categoryObject,
        description=descriptn, author=authr, myfile=file, public_document=public,
        updated_at=current_date, created_by=userObject, updated_by=userObject,
        created_at=current_date)

        if cat == '1':
            documents_count = document_repository.objects.all().filter(category=1).count
            documents = document_repository.objects.all().filter(category=1)
            template = 'veoc/minutes.html'
        elif cat=='2':
            documents_count = document_repository.objects.all().filter(category=2).count
            documents = document_repository.objects.all().filter(category=2)
            template = 'veoc/sitrep.html'
        elif cat=='3':
            documents_count = document_repository.objects.all().filter(category=3).count
            documents = document_repository.objects.all().filter(category=3)
            template = 'veoc/bulletins.html'
        elif cat=='4':
            documents_count = document_repository.objects.all().filter(category=4).count
            documents = document_repository.objects.all().filter(category=4)
            template = 'veoc/publications.html'
        elif cat=='5':
            documents_count = document_repository.objects.all().filter(category=5).count
            documents = document_repository.objects.all().filter(category=5)
            template = 'veoc/others.html'
        elif cat=='6':
            documents_count = document_repository.objects.all().filter(category=6).count
            documents = document_repository.objects.all().filter(category=6)
            template = 'veoc/protocol.html'
        elif cat=='7':
            documents_count = document_repository.objects.all().filter(category=7).count
            documents = document_repository.objects.all().filter(category=7)
            template = 'veoc/out_report.html'
        elif cat=='8':
            documents_count = document_repository.objects.all().filter(category=8).count
            documents = document_repository.objects.all().filter(category=8)
            template = 'veoc/case_documents.html'
        else:
            documents_count = document_repository.objects.all().filter(category=9).count
            documents = document_repository.objects.all().filter(category=9)
            template = 'veoc/sops.html'

        document_categories = repository_categories.objects.all()

        values = {'document_categories': document_categories, 'documents_count': documents_count,
            'documents': documents}

        return render(request, template, values)

def public_document(request):
    documents = document_repository.objects.all().filter(public_document='t')
    values = {'documents': documents}

    return render(request, 'veoc/public_documents.html', values)

def module_feedback(request):
    if request.method == 'POST':
        id = request.POST.get('id','')
        challnge = request.POST.get('challange','')
        recomm = request.POST.get('recommendation','')
        is_adressed = request.POST.get('is_adressed','')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        feedback.objects.filter(pk=id).update(challenge=challnge, recommendation=recomm,
                challange_addressed=is_adressed, updated_by=userObject, updated_at=current_date)

    modules=system_modules.objects.all()
    feedback_count=feedback.objects.all().count
    feedbacks=feedback.objects.all()

    values = {'modules': modules, 'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/feedback.html', values)

def add_feedback(request):
    if request.method=='POST':
        module = request.POST.get('module','')
        report_date = request.POST.get('report_date','')
        challnge = request.POST.get('challange','')
        recomm = request.POST.get('recommendation','')
        reporter = request.POST.get('user','')
        is_adressed = request.POST.get('is_adressed','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        # print(current_user)
        # print(challnge)
        userObject = User.objects.get(pk = current_user.id)
        moduleTypeObject = system_modules.objects.get(pk = module)

        #saving values to database
        feedback.objects.create(module_type=moduleTypeObject, challenge=challnge, recommendation=recomm,
                challange_addressed=is_adressed, updated_at=current_date, created_by=userObject,
                updated_by=userObject, created_at=current_date)

    modules=system_modules.objects.all()
    feedback_count=feedback.objects.all().count
    feedbacks=feedback.objects.all()

    values = {'modules': modules, 'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/feedback.html', values)

def edit_feedback(request):
    if request.method=='POST':
        myid = request.POST.get('feedback_id','')
        module = request.POST.get('module','')
        report_date = request.POST.get('report_date','')
        challnge = request.POST.get('challange','')
        recomm = request.POST.get('recommendation','')
        reporter = request.POST.get('user','')
        is_adressed = request.POST.get('is_adressed','')

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        #get current user
        current_user = request.user
        # print(current_user)
        # print(challnge)
        # print(myid)
        userObject = User.objects.get(pk = current_user.id)
        moduleTypeObject = system_modules.objects.get(pk = module)

        #saving edited values to database
        feedback.objects.filter(pk=myid).update(module_type=moduleTypeObject,
                challenge=challnge, recommendation=recomm, challange_addressed=is_adressed,
                updated_at=current_date, created_by=userObject, updated_by=userObject,
                created_at=current_date)

    modules=system_modules.objects.all()
    feedback_count=feedback.objects.all().count
    feedbacks=feedback.objects.all()

    values = {'modules': modules, 'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/feedback.html', values)


def module_general_feedback(request):

    if request.method == 'POST':
        challnge = request.POST.get('challange','')
        is_adressed = request.POST.get('is_adressed','')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk = current_user.id)
        # print(userObject)

        #get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        general_feedback.objects.create(challenge=challnge,
                challange_addressed=is_adressed, updated_at=current_date,
                created_by=userObject, updated_by=userObject, created_at=current_date)

    feedback_count = general_feedback.objects.all().count
    feedbacks = general_feedback.objects.all()

    values = {'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/gen_feedback.html', values)
