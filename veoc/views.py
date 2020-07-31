import os

import xlrd
from django.core.files.storage import default_storage
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib.auth import authenticate, login as login_auth, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.template import RequestContext, loader
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
import csv, io
import requests
from pytest import fail
from django.views.generic import ListView
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from django.conf import settings
from django.core.serializers import serialize
from django.db import IntegrityError, transaction
from django.db.models import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import FileResponse
from rest_framework.generics import RetrieveAPIView

from veoc.models import *
from veoc.forms import *
from django.views.decorators.csrf import *
from . import forms
from rest_framework import viewsets
from veoc.serializer import *
from veoc.tasks import pull_dhis_idsr_data
from datetime import date, timedelta, datetime
from django.utils import timezone
from collections import Counter
from django import template
import time
import json
from itertools import chain
from operator import attrgetter
from time import gmtime, strftime
import uuid
from django.core.mail import send_mail
from django.conf import settings

@login_required
def airport_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name','')
        middle_name = request.POST.get('middle_name','')
        last_name = request.POST.get('last_name','')
        sex = request.POST.get('sex','')
        dob = request.POST.get('dob','')
        nationality = request.POST.get('nationality','')
        origin_country = request.POST.get('country','')
        date_of_arrival = request.POST.get('date_of_arrival','')
        cnty = request.POST.get('county','')
        sub_cnty = request.POST.get('subcounty','')
        ward = request.POST.get('ward','')
        passport_number = request.POST.get('passport_number','')
        phone_number = request.POST.get('phone_number','')
        email_address = request.POST.get('email_address','')
        airline = request.POST.get('airline','')
        flight_number = request.POST.get('flight_number','')
        seat_number = request.POST.get('seat_number','')
        destination_city = request.POST.get('destination_city','')
        countries_visited = request.POST.get('countries_visited','')
        temperature = request.POST.get('fever','')
        feverish = request.POST.get('feverish','')
        chills = request.POST.get('chills','')
        cough = request.POST.get('cough','')
        breathing_difficulty = request.POST.get('breathing_difficulty','')
        nok = request.POST.get('nok','')
        nok_phone_number = request.POST.get('nok_phone_num','')
        residence = request.POST.get('residence','')
        estate = request.POST.get('estate','')
        postal_address = request.POST.get('postal_address','')
        measured_temperature = request.POST.get('measured_temperature','')
        arrival_airport_code = request.POST.get('arrival_airport_code','')
        released = request.POST.get('released','')
        risk_assessment_referal = request.POST.get('risk_assessment_referal','')
        designated_hospital_referal = request.POST.get('designated_hospital_referal','')

        if origin_country.lower() == "kenya" :
            countyObject = organizational_units.objects.get(name = cnty)
            subcountyObject = organizational_units.objects.get(name = sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid = ward)
        else:
            countyObject = organizational_units.objects.get(organisationunitid = 18)
            subcountyObject = organizational_units.objects.get(organisationunitid = 18)
            wardObject = organizational_units.objects.get(organisationunitid = 18)

        # country_code = country.objects.get(name = )
        user_phone = "+254"
        # Remove spacing on the number
        mobile_number = phone_number.replace(" ", "")
        print(mobile_number)
        # check if the leading character is 0
        if str(mobile_number[0]) == "0":
            user_phone = user_phone + str(mobile_number[1:])
            print("number leading with 0")
        elif str(mobile_number[0]) == "+":
            user_phone = mobile_number
            print("Save phone number as it is")
        elif str(mobile_number[0:2]) == "25":
            user_phone = "+" + str(mobile_number[0:])
            print("Save phone number with appended +")
        else:
            user_phone = user_phone + str(mobile_number)
            print("number not leading with 0")

        # get current user
        current_user = request.user
        # print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        site_name = ''
        quar_site = quarantine_sites.objects.filter(site_name="Home")
        for site in quar_site:
            site_name = site.id

        # site_name = quarantine_sites.objects.values_list('id', flat=True).get(site_name="Home")
        # print("site_name")
        # print(site_name)
        contact_save = ''
        current_date = timezone.now()
        source = "Web Airport Registration"
        # Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number=phone_number, first_name=first_name,last_name=last_name,
                                                           date_of_contact__gte=date.today() - timedelta(days=14))
        if details_exist:
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(mob_ex.created_at))

            return HttpResponse("error")
        else:
            language = 1
            quarantineObject = quarantine_sites.objects.get(pk=site_name)
            languageObject = translation_languages.objects.get(pk=language)
            contact_identifier = uuid.uuid4().hex
            # saving values to quarantine_contacts database first
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name, middle_name=middle_name, county=countyObject,
                            subcounty=subcountyObject, ward=wardObject, sex=sex, dob=dob, passport_number=passport_number, phone_number=user_phone,
                            date_of_contact=date_of_arrival, communication_language=languageObject, nationality=nationality, drugs="None", nok=nok,email_address=email_address,
                            nok_phone_num=nok_phone_number, cormobidity="None", origin_country=origin_country, quarantine_site=quarantineObject, source=source,
                            contact_uuid=contact_identifier, updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

            contact_save.save()
            print(contact_save.pk)
            trans_one = transaction.savepoint()

            # patients_contacts_id = contact_save.pk
            # print(patients_contacts_id)
            # patientObject = quarantine_contacts.objects.get(pk = patients_contacts_id)
            if contact_save:
                print("working")
                print(temperature)
                airport_user_save = airline_quarantine.objects.create(airline=airline, flight_number=flight_number, seat_number=seat_number,
                                          destination_city=destination_city, travel_history=countries_visited, cough=cough, breathing_difficulty=breathing_difficulty,
                                          fever=feverish, chills=chills, temperature=temperature, measured_temperature=measured_temperature, arrival_airport_code=arrival_airport_code,
                                          released=released, risk_assessment_referal=risk_assessment_referal, designated_hospital_refferal=designated_hospital_referal,
                                          created_at=current_date, updated_at=current_date, patient_contacts=contact_save, created_by=userObject, updated_by=userObject,
                                          residence=residence, estate=estate, postal_address=postal_address, status='t')

                airport_user_save.save()
                print(airport_user_save.id)
            else:
                print("data not saved in truck quarantine contacts")

        #check if details have been saved
        if contact_save:
            # send sms to the patient for successful registration_form
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            # msg = "Thank you " + first_name + " for registering. You will be required to send your temperature details during this quarantine period of 14 days. Please download the self reporting app on this link: https://cutt.ly/AtbvdxD"
            msg = "Thank you " + first_name + " for registering on self quarantine. You will be required to send your daily temperature details during this quarantine period of 14 days. Ministry of Health"
            msg2 = first_name +", for self reporting iPhone users and non-smart phone users, dial *299# to send daily details, for Android phone users, download the self reporting app on this link: http://bit.ly/jitenge_moh . Ministry of Health"

            #process first message
            pp = {"phone_no": phone_number, "message": msg}
            payload = json.dumps(pp)

            #process second message
            pp2 = {"phone_no": phone_number, "message": msg2}
            payload2 = json.dumps(pp2)
            # payload = "{\r\n   \"phone_no\": \"+254705255873\",\r\n   \"message\": \"TEST CORONA FROM EARS SYSTEM\"\r\n}"

            headers = {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            #send first message
            response = requests.request("POST", url, headers=headers, data = payload, verify=False)

            print(response.text.encode('utf8'))
            #convert string response to a dictionary
            msg_resp = eval(response.text)
            print(msg_resp)

            #check if Success is in the Dictionary values
            success = 'Success' in msg_resp.values()
            print(success)

            if success:
                print("Successfully sent first sms")
                #send Second message
                response2 = requests.request("POST", url, headers=headers, data = payload2, verify=False)

                print(response2.text.encode('utf8'))

        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        day = time.strftime("%Y-%m-%d")

        data = {'country':cntry,'county':county, 'day':day}

        return render(request, 'veoc/airport_register.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        day = time.strftime("%Y-%m-%d")

        data = {'country':cntry,'county':county, 'day':day}

        return render(request, 'veoc/airport_register.html', data)

def ailrine_registration(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name','')
        middle_name = request.POST.get('middle_name','')
        last_name = request.POST.get('last_name','')
        sex = request.POST.get('sex','')
        dob = request.POST.get('dob','')
        nationality = request.POST.get('nationality','')
        origin_country = request.POST.get('country','')
        date_of_arrival = request.POST.get('date_of_arrival','')
        cnty = request.POST.get('county','')
        sub_cnty = request.POST.get('subcounty','')
        ward = request.POST.get('ward','')
        passport_number = request.POST.get('passport_number','')
        phone_number = request.POST.get('phone_number','')
        email_address = request.POST.get('email_address','')
        airline = request.POST.get('airline','')
        flight_number = request.POST.get('flight_number','')
        seat_number = request.POST.get('seat_number','')
        destination_city = request.POST.get('destination_city','')
        countries_visited = request.POST.get('countries_visited','')
        temperature = request.POST.get('fever','')
        feverish = request.POST.get('feverish','')
        chills = request.POST.get('chills','')
        cough = request.POST.get('cough','')
        breathing_difficulty = request.POST.get('breathing_difficulty','')
        nok = request.POST.get('nok','')
        nok_phone_number = request.POST.get('nok_phone_num','')
        residence = request.POST.get('residence','')
        estate = request.POST.get('estate','')
        postal_address = request.POST.get('postal_address','')
        #measured_temperature = Null
        arrival_airport_code = '0'
        released = 'f'
        risk_assessment_referal = 'f'
        designated_hospital_referal = 'f'

        countyObject = organizational_units.objects.get(organisationunitid = 18)
        subcountyObject = organizational_units.objects.get(organisationunitid = 18)
        wardObject = organizational_units.objects.get(organisationunitid = 18)

        # country_code = country.objects.get(name = )
        user_phone = "+254"
        # Remove spacing on the number
        mobile_number = phone_number.replace(" ", "")
        print(mobile_number)
        # check if the leading character is 0
        if str(mobile_number[0]) == "0":
            user_phone = user_phone + str(mobile_number[1:])
            print("number leading with 0")
        elif str(mobile_number[0]) == "+":
            user_phone = mobile_number
            print("Save phone number as it is")
        elif str(mobile_number[0:2]) == "25":
            user_phone = "+" + str(mobile_number[0:])
            print("Save phone number with appended +")
        else:
            user_phone = user_phone + str(mobile_number)
            print("number not leading with 0")

        site_name = ''

        # site_name = quarantine_sites.objects.values_list('id', flat=True).get(site_name="Home")
        # print("site_name")
        # print(site_name)
        userObject = User.objects.get(pk=1)
        site_name = ''
        quar_site = quarantine_sites.objects.filter(site_name="Home")
        for site in quar_site:
            site_name = site.id

        contact_save = ''
        current_date = timezone.now()
        source = "Web Airport Self Registration"
        # Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number=phone_number, first_name=first_name,last_name=last_name,
                                                           date_of_contact__gte=date.today() - timedelta(days=14))
        if details_exist:
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(mob_ex.created_at))

            return HttpResponse("error")
        else:
            language = 1
            quarantineObject = quarantine_sites.objects.get(pk=site_name)
            languageObject = translation_languages.objects.get(pk=language)
            contact_identifier = uuid.uuid4().hex
            # saving values to quarantine_contacts database first
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name, middle_name=middle_name, county=countyObject,
                            subcounty=subcountyObject, ward=wardObject, sex=sex, dob=dob, passport_number=passport_number, phone_number=user_phone,
                            date_of_contact=date_of_arrival, communication_language=languageObject, nationality=nationality, drugs="None", nok=nok,email_address=email_address,
                            nok_phone_num=nok_phone_number, cormobidity="None", origin_country=origin_country, quarantine_site=quarantineObject, source=source,
                            contact_uuid=contact_identifier, updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

            contact_save.save()
            print(contact_save.pk)
            trans_one = transaction.savepoint()

            # patients_contacts_id = contact_save.pk
            # print(patients_contacts_id)
            # patientObject = quarantine_contacts.objects.get(pk = patients_contacts_id)
            if contact_save:
                print("working")
                print(temperature)
                airport_user_save = airline_quarantine.objects.create(airline=airline, flight_number=flight_number, seat_number=seat_number,
                                          destination_city=destination_city, travel_history=countries_visited, cough=cough, breathing_difficulty=breathing_difficulty,
                                          fever=feverish, chills=chills, temperature=temperature, arrival_airport_code=arrival_airport_code,
                                          released=released, risk_assessment_referal=risk_assessment_referal, designated_hospital_refferal=designated_hospital_referal,
                                          created_at=current_date, updated_at=current_date, patient_contacts=contact_save, created_by=userObject, updated_by=userObject,
                                          residence=residence, estate=estate, postal_address=postal_address, status='t')

                airport_user_save.save()
                print(airport_user_save.id)
            else:
                print("data not saved in truck quarantine contacts")


        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        day = time.strftime("%Y-%m-%d")

        data = {'country':cntry,'county':county, 'day':day}

        return render(request, 'veoc/airline_travellers.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        day = time.strftime("%Y-%m-%d")

        data = {'country':cntry,'county':county, 'day':day}

        return render(request, 'veoc/airline_travellers.html', data)

@login_required
def edit_airport_complete(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name','')
        middle_name = request.POST.get('middle_name','')
        last_name = request.POST.get('last_name','')


        airport_id = request.POST.get('airport_id','')
        measured_temperature = request.POST.get('measured_temperature','')
        arrival_airport_code = request.POST.get('arrival_airport_code','')
        released = request.POST.get('released','')
        risk_assessment_referal = request.POST.get('risk_assessment_referal','')
        designated_hospital_referal = request.POST.get('designated_hospital_referal','')

        # get current user
        current_user = request.user
        # print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        contact_save = ''
        current_date = datetime.now()
        source = "Web Airport Registration"

        contact_identifier = uuid.uuid4().hex
        # saving values to quarantine_contacts database firstobjects.filter(pk=myid).update
        airport_user_save = airline_quarantine.objects.filter(patient_contacts_id=airport_id).update(measured_temperature=measured_temperature, arrival_airport_code=arrival_airport_code,
                                  released=released, risk_assessment_referal=risk_assessment_referal, designated_hospital_refferal=designated_hospital_referal,
                                 updated_at=current_date, updated_by=userObject)
        #airport_user_save.save()
        print(airport_id)
        print(airline_quarantine.objects.get(pk=2))


        cntry = country.objects.all()
        day = time.strftime("%Y-%m-%d")
        data = { 'country': cntry, 'start_day': day,
                'end_day': day}

        return render(request, 'veoc/airport_list_incomplete.html', data)

    else:
        cntry = country.objects.all()
        day = time.strftime("%Y-%m-%d")
        data = { 'country': cntry, 'start_day': day,
                'end_day': day}

        return render(request, 'veoc/airport_list_incomplete.html', data)


@login_required
def airport_list_incomplete(request):
    if request.method == "POST":
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')
        day = time.strftime("%Y-%m-%d")

        all_data = quarantine_contacts.objects.all().filter(source='Web Airport Registration').filter(
            date_of_contact__gte=date_from, date_of_contact__lte=date_to).order_by('-date_of_contact')
        q_data_count = quarantine_contacts.objects.all().filter(source='Web Airport Registration').filter(
            date_of_contact__gte=date_from, date_of_contact__lte=date_to).count()

        data = {'all_data': all_data, 'all_data_count': q_data_count,'day': day}

    else:
        all_data = quarantine_contacts.objects.all().filter(source='Web Airport Registration').filter(
            date_of_contact__lte=date.today() - timedelta(days=14)).order_by('-date_of_contact')
        q_data_count = quarantine_contacts.objects.all().filter(source='Web Airport Registration').filter(
            date_of_contact__lte=date.today() - timedelta(days=14)).count()
        day = time.strftime("%Y-%m-%d")

        data = {'all_data': all_data, 'all_data_count': q_data_count, 'day': day}

    return render(request, 'veoc/airport_list_incomplete.html', data)


# export raw data as csv_file
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;  filename="users.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ['Username', 'First name', 'Last name', 'Email address', 'Is Superuser', 'Last Login', 'Is Staff', 'Is Active',
         'Date Joined'])
    users = User.objects.all().values_list('username', 'first_name', 'last_name', 'email', 'is_superuser', 'last_login',
                                           'is_staff', 'is_active', 'date_joined')
    for user in users:
        writer.writerow(user)
    return response


# export raw data as csv_file fro truck quarantine list
def truck_export_csv(request):
    q_data = quarantine_contacts.objects.filter(source='Truck Registration').order_by('-date_of_contact')
    for d in q_data:
        t_details = truck_quarantine_contacts.objects.values_list('street')
        # truck_cont_details = []
        # truck_cont_details.append(t_details)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;  filename="truck_drivers_quarantine_list.csv"'
    writer = csv.writer(response)
    writer.writerow(['Street', 'Village', 'Number Plate', 'Company Name', 'Company Phone', 'Company Pyysical Address',
                     'Company Street', 'Company Building', 'Cough', 'Breathing Difficulty', 'Fever', 'Sample Taken',
                     'Action Taken', 'Hotel', 'Hotel Phone Number', 'Hotel Town', 'Date Check In', 'Date Check Out',
                     'Temperature'])
    t_details = truck_quarantine_contacts.objects.values_list('street', 'village', 'vehicle_registration',
                                                              'company_name', 'company_phone',
                                                              'company_physical_address', 'company_street',
                                                              'company_building', 'cough', 'breathing_difficulty',
                                                              'fever', 'sample_taken', 'action_taken', 'hotel',
                                                              'hotel_phone', 'hotel_town', 'date_check_in',
                                                              'date_check_out', 'temperature')
    # truckers = User.objects.all().values_list('username', 'first_name', 'last_name', 'email', 'is_superuser', 'last_login', 'is_staff', 'is_active', 'date_joined')
    for obj in t_details:
        writer.writerow(obj)
    return response

def raw_quarantine_contacts_csv(request):
    q_data = v_quarantine_contacts.objects.values_list('contact_id', 'first_name', 'middle_name', 'last_name', 'sex', 'dob', 'passport_number', 'phone_number',
                'email_address', 'origin_country', 'nationality', 'county', 'subcounty', 'source', 'quarantine_site', 'sms_communication_language', 'date_of_contact', 'created_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;  filename="raw_quarantine_contacts_data.csv"'
    writer = csv.writer(response)
    writer.writerow(['contact_id', 'first_name', 'middle_name', 'last_name', 'sex', 'dob', 'passport_number', 'phone_number', 'email_address', 'origin_country',
                     'nationality', 'county', 'subcounty', 'source', 'quarantine_site', 'sms_communication_language', 'date_of_contact', 'created_at'])

    for obj in q_data:
        writer.writerow(obj)
    return response

def raw_follow_up_csv(request):
    follow_data = v_follow_up.objects.values_list('patient_contacts_id', 'source', 'first_name', 'last_name', 'phone_number', 'passport_number', 'reporting_date',
                'county', 'subcounty', 'self_quarantine', 'follow_up_day', 'thermal_gun', 'body_temperature', 'cough', 'difficulty_breathing', 'fever', 'comment')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;  filename="raw_follow_up_data.csv"'
    writer = csv.writer(response)
    writer.writerow(['patient_contacts_id', 'source', 'first_name', 'last_name', 'phone_number', 'passport_number', 'reporting_date', 'county', 'subcounty',
                     'self_quarantine', 'follow_up_day', 'thermal_gun', 'body_temperature', 'cough', 'difficulty_breathing', 'fever', 'comment'])

    for obj in follow_data:
        writer.writerow(obj)
    return response

def raw_lab_results_csv(request):
    lab_data = v_lab_results.objects.values_list('name', 'patient_contacts_id', 'phone_number', 'id_number', 'sex', 'dob', 'testing_lab', 'date_tested',
                'result', 'system_registration_date', 'nationality', 'origin_country', 'county', 'sub_county', 'source', 'border_name', 'date_received')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;  filename="raw_quarantine_contacts_data.csv"'
    writer = csv.writer(response)
    writer.writerow(['name', 'patient_contacts_id', 'phone_number', 'id_number', 'sex', 'dob', 'testing_lab', 'date_tested', 'result',
                     'system_registration_date', 'nationality', 'origin_country', 'county', 'sub_county', 'source', 'border_name', 'date_received'])

    for obj in lab_data:
        writer.writerow(obj)
    return response

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


class myDict(dict):

    def __init__(self):
        self = dict()

    def add(self, key, value):
        self[key] = value


register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


def not_in_manager_group(user):
    if user:
        return user.groups.filter(name='National Managers').count() == 0
    return False


def login(request):
    global next
    context = {}

    if request.method == "POST":
        user_name = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=user_name, password=password)

        if user is not None:
            if user.is_active:
                # check if user has logged in for the first time
                if user.last_login == None:
                    print('Not registered')
                    next = '/edit_profile/'
                    # login user before redirecting them to the change password page
                    login_auth(request, user)
                    return HttpResponse(next)
                else:
                    print('user already registered')
                # request.session.set_expiry(60)
                login_auth(request, user)
                # get the person org unit to redirect to the correct Dashboard
                user_access_level = ""
                user_group = request.user.groups.values_list('id', flat=True)
                print(user_group)
                for grp in user_group:
                    user_access_level = grp
                    print(user_access_level)

                # Get access level to determine what dashboard to loads
                if user_access_level == 1 or user_access_level == 2:
                    print('inside National dashboard')
                    next = '/dashboard/'
                    print(next)

                elif user_access_level == 3 or user_access_level == 5:
                    print('inside county dashboard')
                    next = '/county_dashboard/'
                    print(next)

                elif user_access_level == 4 or user_access_level == 6:
                    print('inside subcounty dashboard')
                    next = '/subcounty_dashboard/'
                    print(next)

                elif user_access_level == 7:
                    print('inside border dashboard')
                    next = '/border_dashboard/'
                    print(next)

                else:
                    print('inside Facility dashboard')
                    next = '/facility_dashboard/'
                    print(next)

                return HttpResponse(next)
            else:
                return HttpResponse("error")
                # context["error"] = "User Not Active. Contact Admin for activations"
                # return render(request, 'veoc/login.html', context)
        else:
            return HttpResponse("error")
            # return HttpResponseRedirect(settings.LOGIN_URL)
            # context["error"] = "Username or Password Does NOT exists"
            # return render(request, 'veoc/login.html', context)
    else:
        return render(request, 'veoc/login.html')


# change password method: it allows a user to change their password and also sends an email with the details
@login_required
def edit_profile(request):
    current_user = request.user
    # setting the password to the entered password
    if request.method == 'POST':
        email = request.POST.get('email', '')
        phone_no = request.POST.get('phone_no', '')
        password = request.POST.get('newpassword_two', '')
        password_one = request.POST.get('newpassword_one', '')
        if password == password_one:
            # current_user = request.user
            user = User.objects.get(username=current_user.username)
            user.set_password(password)
            persons.objects.filter(user_id=current_user.id).update(phone_number=phone_no)
            user.email = email
            user.save()
            # send email informing user their password has been changed
            subject = 'Jitenge Profile Details Change'
            message = 'Dear ' + current_user.username + ',' + '\n' + 'You have changed your profile on the Jitenge System. Your new password is ' + password + ' and your email is' + email + '. Please login with your new credentials here: https://ears.mhealthkenya.co.ke/login/' + '\n' + 'Thank You. ' + '\n' + 'Jitenge System.'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, email_from, recipient_list)
            messages.success(request, 'Password Changed successfully.')
            return HttpResponseRedirect(settings.LOGIN_URL)
        elif password != password_one and password_one == '':
            messages.success(request, 'Kindly enter the new password on both fields.')
        else:
            messages.error(request, 'Passwords do not match. Please make sure they match.')

    # u = User.objects.get(username=current_user.username)
    # get user details from User and Persons gtables
    u = User.objects.get(username=current_user.username)
    person = persons.objects.get(user_id=current_user.id)
    values = {'u': u, 'person': person}

    return render(request, 'veoc/edit_profile.html', values)


def logout(request):
    return HttpResponseRedirect(settings.LOGIN_URL)


@login_required
def access_dashboard(request):
    # get the person org unit to redirect to the correct Dashboard
    # current_user = request.user
    # u = User.objects.get(username=current_user.username)
    # user_access_level = u.persons.access_level
    #
    # print(user_access_level)

    user_access_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_access_level = grp
    print(user_access_level)

    # Get access level to determine what dashboard to loads
    if user_access_level == 1 or user_access_level == 2:
        print('inside National dashboard')
        next = '/dashboard/'
        print(next)

    elif user_access_level == 3 or user_access_level == 5:
        print('inside county dashboard')
        next = '/county_dashboard/'
        print(next)

    elif user_access_level == 4 or user_access_level == 6:
        print('inside subcounty dashboard')
        next = '/subcounty_dashboard/'
        print(next)

    elif user_access_level == 7:
        print('inside border dashboard')
        next = '/border_dashboard/'
        print(next)

    else:
        print('inside Facility dashboard')
        next = '/facility_dashboard/'
        print(next)

    # messages.info(request, 'Your password was updated successfully!')
    return HttpResponseRedirect(next)


def user_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        user_name = request.POST.get('user_name', '')
        email = request.POST.get('email', '')
        phone_no = request.POST.get('phone_no', '')
        access_level = request.POST.get('access_level', '')
        org_unit = org_unit = request.POST.get('org_unit', '')
        sub_cnty = request.POST.get('subcounty', '')
        user_group = request.POST.get('usergroup', '')
        super_user = request.POST.get('user_status', '')
        qua_site = request.POST.get('qua_site', '')
        border_pnt = request.POST.get('border_pnt', '')

        # if user is National user, default county and subcounty id to the
        # national id (Kenya id)
        if org_unit == '':
            org_unit = 18
        if sub_cnty == '':
            sub_cnty = 18

        acc_level = access_level
        # check to populate persons table
        if access_level == 'Border':
            acc_level = border_pnt
        elif access_level == 'Facility':
            acc_level = qua_site

        user = User.objects.create_user(username=user_name, email=email, password=email, first_name=first_name,
                                        last_name=last_name, is_superuser=super_user, is_staff="t", is_active="t")

        user.save()

        subject = 'Jitenge System Registration'
        message = 'Dear ' + first_name + ',' + '\n' + '\n' + 'You have been registered on the Jitenge System (EARS - Emergency Alert Reporting System) ' + '\n' + 'Your username is ' + user_name + ' and your password is  ' + email + '. They are both case sensitive, you may use these credentials for the initial login. You will be prompted to change your password once you login for the first time.' + '\n' + 'You can access the system through this link https://ears.mhealthkenya.co.ke/.' + '\n' + 'Thank You.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, email_from, recipient_list)

        user_id = user.pk
        userObject = User.objects.get(pk=user_id)
        userGroupObject = Group.objects.get(name=user_group)
        orgunitObject = organizational_units.objects.get(organisationunitid=org_unit)
        subcntyObject = organizational_units.objects.get(organisationunitid=sub_cnty)
        # print(user_id)

        # save user into user_groups table
        user.groups.add(userGroupObject)

        # save the user in persons tables
        user_person = persons.objects.create(user=userObject, org_unit=orgunitObject, phone_number=phone_no,
                                             access_level=acc_level, county=orgunitObject, sub_county=subcntyObject)

    users_count = User.objects.all().count()
    users = User.objects.all()
    org_units = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    user_groups = Group.objects.all()

    values = {'users_count': users_count, 'users': users, 'org_units': org_units, 'user_groups': user_groups}

    return render(request, 'veoc/users.html', values)


@csrf_exempt
def dashboard(request):
    _dcall_logs = disease.objects.all().filter(data_source=1).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(data_source=1).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _total_cor_quarantine = quarantine_contacts.objects.all().count()
    _total_ongoing_quarantine = quarantine_contacts.objects.all().filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    _total_completed_quarantine = quarantine_contacts.objects.all().filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    marquee_call_log = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []  # an array that collects all confirmed diseases and maps them to the marquee
    print("Hello Moto")
    # checks if dictionary has values for the past 7 days
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

    # Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(call_category=1).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=1)).order_by("-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(call_category=1).filter(incident_status=1).order_by(
        "-date_reported").count()
    # print(rum_disease_call_log_count)

    # Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(incident_status=3).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(call_category=2).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(call_category=2).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count = conf_event_count + conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()

    # changed call logs button
    disease_related_calls = call_log.objects.filter(call_category=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(call_category=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).filter(
        call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).filter(
        call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    # Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease=True)
    disease_report_stat = {}
    thirty_days_stat = {}
    for d_type in disease_types:
        diseases_count = disease.objects.all().filter(disease_type_id=d_type.id).count()
        thirty_days_disease_count = disease.objects.all().filter(disease_type_id=d_type.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).count()
        if thirty_days_disease_count > 0:
            disease_report_stat[d_type.name] = diseases_count
            thirty_days_stat[d_type.name] = thirty_days_disease_count

            # print("^^^thirty day^^^^")
            # print(thirty_days_stat)

    # picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    # ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat = {}
    events_thirty_days_stat = {}
    for e_type in event_types:
        events_count = event.objects.all().filter(event_type_id=e_type.id).count()
        events_thirty_days_disease_count = event.objects.all().filter(event_type_id=e_type.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).count()
        if events_thirty_days_disease_count > 0:
            events_report_stat[e_type.name] = events_count
            events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))
    print("test est")
    # populating the total quarantine respondents
    qua_contacts = quarantine_contacts.objects.all()
    qua_contacts_comp = quarantine_contacts.objects.filter(created_at__gte=date.today() - timedelta(days=14)).order_by(
        "-created_at")
    qua_contacts_ong = quarantine_contacts.objects.filter(created_at__lte=date.today() - timedelta(days=14)).order_by(
        "-created_at")
    total_follow_up_stat = 0
    today_follow_up_stat = 0
    total_male = 0
    total_female = 0
    ongoing_male = 0
    ongoing_female = 0
    completed_male = 0
    completed_female = 0

    current_date = date.today().strftime('%Y-%m-%d')
    c_date = date.today()
    today_time = datetime.combine(c_date, datetime.min.time())
    # midnight = today_time.strftime('%Y-%m-%d')
    midnight = today_time.strftime('%Y-%m-%d %H:%M:%S')
    midnight_time = midnight + "+03"
    # print(midnight)
    # print(midnight_time)
    total_follow_up_stat= quarantine_follow_up.objects.values('patient_contacts').distinct().count()

    today_follow_up_stat = quarantine_follow_up.objects.filter(Q(created_at__gte=midnight) | Q(created_at__gte=midnight_time)).count()

    # Getting gender totals, ongoing, completed
    for gender in qua_contacts:
        if gender.sex == "Male":
            total_male += 1
        else:
            total_female += 1
    for gender in qua_contacts_comp:
        if gender.sex == "Male":
            ongoing_male += 1
        else:
            ongoing_female += 1
    for gender in qua_contacts_ong:
        if gender.sex == "Male":
            completed_male += 1
        else:
            completed_female += 1

    # print("gender numbers....")
    # print(total_male)
    # print(total_female)
    # print("ongoing gender numbers....")
    # print(ongoing_male)
    # print(ongoing_female)
    # print("completed gender numbers....")
    # print(completed_male)
    # print(completed_female)

    user_access_level = ""
    user_group = request.user.groups.values_list('name', flat=True)
    print("hapa sasa")
    print(user_group)
    for grp in user_group:
       user_access_level = grp
    print(user_access_level)

    # Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}  # variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(county_id=cnty.id).filter(
            date_reported__gte=date.today() - timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid=cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(subcounty_id=subcnty.id).filter(county_id=cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name': cnty.name, 'id': cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)
    print(series)

    # pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(disease_type_id=crt_tpye.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('disease_type__name', 'county__name',
                                                                         'subcounty__name', 'cases',
                                                                         'deaths').distinct()
        cases.append(disease_descriptions)

    # pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(event_type_id=crt_tpye.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('event_type__name', 'county__name',
                                                                         'subcounty__name', 'cases',
                                                                         'deaths').distinct()
        event_cases.append(event_descriptions)

    # line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        # dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id = crt_tpye.id).values('idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period', 'data_value').distinct()
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id=crt_tpye.id).values(
            'idsr_disease_id__name', 'org_unit_id_id__name', 'period', 'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    # pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    # covid-19 line graph quarantine sites_count
    qua_sites = quarantine_sites.objects.all().order_by('site_name')
    ongoing_cases = {}
    completed_cases = {}
    # counter = 0
    for qua_site in qua_sites:
        ongoing_array = myDict()
        completed_array = myDict()

        qua_completed_contacts = quarantine_contacts.objects.filter(quarantine_site_id=qua_site.id).filter(
            created_at__gte=date.today() - timedelta(days=14)).count()
        qua_ongoing_contacts = quarantine_contacts.objects.filter(quarantine_site_id=qua_site.id).filter(
            created_at__lte=date.today() - timedelta(days=14)).count()
        qua_total_contacts = quarantine_contacts.objects.filter(quarantine_site_id=qua_site.id).count()

        if qua_completed_contacts > 0 or qua_ongoing_contacts > 0:
            # if counter < 10 :
            ongoing_array.add('ongoing', qua_ongoing_contacts)
            completed_array.add("completed", qua_completed_contacts)

            ongoing_cases[qua_site.site_name + " - " + str(qua_total_contacts) + " Cases"] = qua_ongoing_contacts
            completed_cases[qua_site.site_name] = qua_completed_contacts

            # counter += 1

    print(ongoing_cases)
    print(completed_cases)

    # **************************
    #     combinded_array = myDict()
    #     qua_completed_contacts = quarantine_contacts.objects.filter(quarantine_site_id = qua_site.id).filter(created_at__gte = date.today()- timedelta(days=14)).count()
    #     qua_ongoing_contacts = quarantine_contacts.objects.filter(quarantine_site_id = qua_site.id).filter(created_at__lte = date.today()- timedelta(days=14)).count()
    #
    #     combinded_array.add("ongoing",qua_ongoing_contacts)
    #     combinded_array.add("completed",qua_completed_contacts)
    #     print("------")
    #     # print(combinded_array)
    #
    #     ongoing_cases[qua_site.site_name] = combinded_array
    # print(ongoing_cases)

    # pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active=False)

    template = loader.get_template('veoc/dashboard.html')
    context = RequestContext(request, {
        'user_level': user_access_level,
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'total_cor_quarantine': _total_cor_quarantine,
        'total_ongoing_quarantine': _total_ongoing_quarantine,
        'total_completed_quarantine': _total_completed_quarantine,
        'total_follow_up_stat': total_follow_up_stat,
        'today_follow_up_stat': today_follow_up_stat,
        'total_pie_male': total_male, 'total_pie_female': total_female,
        'total_pie_comp_male': completed_male, 'total_pie_comp_female': completed_female,
        'total_pie_ong_male': ongoing_male, 'total_pie_ong_female': ongoing_female,
        'd_count': disease.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls': disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported"),
        'disease_vals': disease.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat, 'quarantine_completed_cases': completed_cases,
        'disease_reported_dash_vals': disease_reported_dash_vals, 'quarantine_ongoing_cases': ongoing_cases,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))


@login_required
def county_dashboard(request):
    user_access_level = ""
    user_group = request.user.groups.values_list('name', flat=True)
    print(user_group)
    for grp in user_group:
        user_access_level = grp
    print(user_access_level)

    # get the person org unit to dislay county on the Dashboard
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_county_id = u.persons.county_id

    # get county names
    county_object = organizational_units.objects.get(pk=user_county_id)
    county_name = county_object.name

    _dcall_logs = disease.objects.all().filter(county=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(county=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(county=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(county=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _total_cor_quarantine = quarantine_contacts.objects.all().filter(county=user_county_id).count()
    _total_ongoing_quarantine = quarantine_contacts.objects.all().filter(county=user_county_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    _total_completed_quarantine = quarantine_contacts.objects.all().filter(county=user_county_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    marquee_call_log = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []  # an array that collects all confirmed diseases and maps them to the marquee

    # checks if dictionary has values for the past 7 days
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

    # Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(county=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(county=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(county=user_county_id).filter(call_category=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=1)).order_by(
        "-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(county=user_county_id).filter(call_category=1).filter(
        incident_status=1).order_by("-date_reported").count()
    # print(rum_disease_call_log_count)

    # Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(county=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(county=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(county=user_county_id).filter(incident_status=3).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(county=user_county_id).filter(call_category=2).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(county=user_county_id).filter(call_category=2).filter(
        incident_status=1).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count = conf_event_count + conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(county=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()

    # changed call logs button
    disease_related_calls = call_log.objects.filter(county=user_county_id).filter(call_category=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(county=user_county_id).filter(call_category=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(county=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(county=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    # Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease=True)
    disease_report_stat = {}
    thirty_days_stat = {}
    for d_type in disease_types:
        diseases_count = disease.objects.all().filter(county=user_county_id).filter(disease_type_id=d_type.id).count()
        thirty_days_disease_count = disease.objects.all().filter(county=user_county_id).filter(
            disease_type_id=d_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if thirty_days_disease_count > 0:
            disease_report_stat[d_type.name] = diseases_count
            thirty_days_stat[d_type.name] = thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    # ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat = {}
    events_thirty_days_stat = {}
    for e_type in event_types:
        events_count = event.objects.all().filter(county=user_county_id).filter(event_type_id=e_type.id).count()
        events_thirty_days_disease_count = event.objects.all().filter(county=user_county_id).filter(
            event_type_id=e_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if events_thirty_days_disease_count > 0:
            events_report_stat[e_type.name] = events_count
            events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))

    # Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}  # variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(county=user_county_id).filter(county_id=cnty.id).filter(
            date_reported__gte=date.today() - timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid=cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(county=user_county_id).filter(subcounty_id=subcnty.id).filter(
                county_id=cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name': cnty.name, 'id': cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)

    # pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(county=user_county_id).filter(disease_type_id=crt_tpye.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('disease_type__name', 'county__name',
                                                                         'subcounty__name', 'cases',
                                                                         'deaths').distinct()
        cases.append(disease_descriptions)

    # pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(county=user_county_id).filter(event_type_id=crt_tpye.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('event_type__name', 'county__name',
                                                                         'subcounty__name', 'cases',
                                                                         'deaths').distinct()
        event_cases.append(event_descriptions)

    # line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id=crt_tpye.id).values(
            'idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period',
            'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    # pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    # covid-19 line graph quarantine sites_count
    qua_sites = quarantine_sites.objects.all().order_by('site_name')
    ongoing_cases = {}
    completed_cases = {}
    for qua_site in qua_sites:
        ongoing_array = myDict()
        completed_array = myDict()

        qua_completed_contacts = quarantine_contacts.objects.all().filter(county=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__gte=date.today() - timedelta(days=14)).count()
        qua_ongoing_contacts = quarantine_contacts.objects.all().filter(county=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__lte=date.today() - timedelta(days=14)).count()
        qua_total_contacts = quarantine_contacts.objects.all().filter(county=user_county_id).filter(
            quarantine_site_id=qua_site.id).count()

        if qua_completed_contacts > 0 or qua_ongoing_contacts > 0:
            ongoing_array.add('ongoing', qua_ongoing_contacts)
            completed_array.add("completed", qua_completed_contacts)

            ongoing_cases[qua_site.site_name + " - " + str(qua_total_contacts) + " Cases"] = qua_ongoing_contacts
            completed_cases[qua_site.site_name] = qua_completed_contacts

    # print(ongoing_cases)
    # print(completed_cases)

    # populating the total quarantine respondents
    qua_contacts = quarantine_contacts.objects.all().filter(county=user_county_id)
    qua_contacts_comp = quarantine_contacts.objects.filter(county=user_county_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at")
    qua_contacts_ong = quarantine_contacts.objects.filter(county=user_county_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at")
    total_follow_up_stat = 0
    today_follow_up_stat = 0
    total_male = 0
    total_female = 0
    ongoing_male = 0
    ongoing_female = 0
    completed_male = 0
    completed_female = 0

    current_date = date.today().strftime('%Y-%m-%d')
    c_date = date.today()
    today_time = datetime.combine(c_date, datetime.min.time())
    midnight = today_time.strftime('%Y-%m-%d %H:%M:%S')
    midnight_time = midnight + "+03"
    # print(midnight)
    # print(midnight_time)

    for qua_contact in qua_contacts:
        followup = quarantine_follow_up.objects.all().filter(patient_contacts=qua_contact.id).count()
        if followup > 0:
            total_follow_up_stat += 1

    # populating the todays quarantine respondents
    for today_qua_contact in qua_contacts:
        current_date = date.today().strftime('%Y-%m-%d')
        today_followup = quarantine_follow_up.objects.all().filter(patient_contacts=today_qua_contact.id).filter(
            patient_contacts=today_qua_contact.id).filter(
            Q(created_at__gte=midnight) | Q(created_at__gte=midnight_time)).count()
        if today_followup > 0:
            today_follow_up_stat += 1

    # Getting gender totals, ongoing, completed
    for gender in qua_contacts:
        if gender.sex == "Male":
            total_male += 1
        else:
            total_female += 1
    for gender in qua_contacts_comp:
        if gender.sex == "Male":
            ongoing_male += 1
        else:
            ongoing_female += 1
    for gender in qua_contacts_ong:
        if gender.sex == "Male":
            completed_male += 1
        else:
            completed_female += 1

    # print("gender numbers....")
    # print(total_male)
    # print(total_female)
    # print("ongoing gender numbers....")
    # print(ongoing_male)
    # print(ongoing_female)
    # print("completed gender numbers....")
    # print(completed_male)
    # print(completed_female)

    # print(total_follow_up_stat)
    # print(today_follow_up_stat)

    # pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active=False)

    template = loader.get_template('veoc/county_dashboard.html')
    context = RequestContext(request, {
        'user_level': user_access_level,
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'total_cor_quarantine': _total_cor_quarantine,
        'total_ongoing_quarantine': _total_ongoing_quarantine,
        'total_completed_quarantine': _total_completed_quarantine,
        'total_follow_up_stat': total_follow_up_stat,
        'today_follow_up_stat': today_follow_up_stat,
        'total_pie_male': total_male, 'total_pie_female': total_female,
        'total_pie_comp_male': completed_male, 'total_pie_comp_female': completed_female,
        'total_pie_ong_male': ongoing_male, 'total_pie_ong_female': ongoing_female,
        'd_count': disease.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls': disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported"),
        'disease_vals': disease.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat,
        'disease_reported_dash_vals': disease_reported_dash_vals,
        'county_name': county_name,
        'sub_elements': sub_call_stat, 'quarantine_completed_cases': completed_cases,
        'disease_reported_dash_vals': disease_reported_dash_vals, 'quarantine_ongoing_cases': ongoing_cases,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))


@login_required
def subcounty_dashboard(request):
    user_access_level = ""
    user_group = request.user.groups.values_list('name', flat=True)
    print(user_group)
    for grp in user_group:
        user_access_level = grp
    print(user_access_level)

    # get the person org unit to display subcounty on the Dashboard
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_county_id = u.persons.sub_county_id

    # get county names
    county_object = organizational_units.objects.get(pk=user_county_id)
    sub_county_name = county_object.name

    # print(user_county_id)
    # print(sub_county_name)

    _dcall_logs = disease.objects.all().filter(subcounty=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(subcounty=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _total_cor_quarantine = quarantine_contacts.objects.all().filter(subcounty=user_county_id).count()
    _total_ongoing_quarantine = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    _total_completed_quarantine = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    marquee_call_log = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []  # an array that collects all confirmed diseases and maps them to the marquee

    # checks if dictionary has values for the past 7 days
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

    # Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(
        call_category=1).filter(incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=1)).order_by(
        "-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=1).filter(
        incident_status=1).order_by("-date_reported").count()
    # print(rum_disease_call_log_count)

    # Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=3).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=2).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=2).filter(
        incident_status=1).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count = conf_event_count + conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()

    # changed call logs button
    disease_related_calls = call_log.objects.filter(subcounty=user_county_id).filter(call_category=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(subcounty=user_county_id).filter(call_category=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    # Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease=True)
    disease_report_stat = {}
    thirty_days_stat = {}
    for d_type in disease_types:
        diseases_count = disease.objects.all().filter(subcounty=user_county_id).filter(
            disease_type_id=d_type.id).count()
        thirty_days_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(
            disease_type_id=d_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if thirty_days_disease_count > 0:
            disease_report_stat[d_type.name] = diseases_count
            thirty_days_stat[d_type.name] = thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    # ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat = {}
    events_thirty_days_stat = {}
    for e_type in event_types:
        events_count = event.objects.all().filter(subcounty=user_county_id).filter(event_type_id=e_type.id).count()
        events_thirty_days_disease_count = event.objects.all().filter(subcounty=user_county_id).filter(
            event_type_id=e_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if events_thirty_days_disease_count > 0:
            events_report_stat[e_type.name] = events_count
            events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))

    # Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}  # variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(subcounty=user_county_id).filter(county_id=cnty.id).filter(
            date_reported__gte=date.today() - timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid=cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(subcounty=user_county_id).filter(
                subcounty_id=subcnty.id).filter(county_id=cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name': cnty.name, 'id': cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)

    # pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(subcounty=user_county_id).filter(
            disease_type_id=crt_tpye.id).filter(date_reported__gte=date.today() - timedelta(days=30)).values(
            'disease_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        cases.append(disease_descriptions)

    # pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(subcounty=user_county_id).filter(event_type_id=crt_tpye.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('event_type__name', 'county__name',
                                                                         'subcounty__name', 'cases',
                                                                         'deaths').distinct()
        event_cases.append(event_descriptions)

    # line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id=crt_tpye.id).values(
            'idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period',
            'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    # pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    # covid-19 line graph quarantine sites_count
    qua_sites = quarantine_sites.objects.all().order_by('site_name')
    ongoing_cases = {}
    completed_cases = {}
    for qua_site in qua_sites:
        ongoing_array = myDict()
        completed_array = myDict()

        qua_completed_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__gte=date.today() - timedelta(days=14)).count()
        qua_ongoing_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__lte=date.today() - timedelta(days=14)).count()
        qua_total_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).count()

        if qua_completed_contacts > 0 or qua_ongoing_contacts > 0:
            ongoing_array.add('ongoing', qua_ongoing_contacts)
            completed_array.add("completed", qua_completed_contacts)

            ongoing_cases[qua_site.site_name + " - " + str(qua_total_contacts) + " Cases"] = qua_ongoing_contacts
            completed_cases[qua_site.site_name] = qua_completed_contacts

    # print(ongoing_cases)
    # print(completed_cases)

    # populating the total quarantine respondents
    qua_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id)
    qua_contacts_comp = quarantine_contacts.objects.filter(subcounty=user_county_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at")
    qua_contacts_ong = quarantine_contacts.objects.filter(subcounty=user_county_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at")
    total_follow_up_stat = 0
    today_follow_up_stat = 0
    total_male = 0
    total_female = 0
    ongoing_male = 0
    ongoing_female = 0
    completed_male = 0
    completed_female = 0

    current_date = date.today().strftime('%Y-%m-%d')
    c_date = date.today()
    today_time = datetime.combine(c_date, datetime.min.time())
    midnight = today_time.strftime('%Y-%m-%d %H:%M:%S')
    midnight_time = midnight + "+03"
    # print(midnight)
    # print(midnight_time)

    for qua_contact in qua_contacts:
        followup = quarantine_follow_up.objects.all().filter(patient_contacts=qua_contact.id).count()
        if followup > 0:
            total_follow_up_stat += 1

    # populating the todays quarantine respondents
    for today_qua_contact in qua_contacts:
        current_date = date.today().strftime('%Y-%m-%d')
        today_followup = quarantine_follow_up.objects.all().filter(patient_contacts=today_qua_contact.id).filter(
            patient_contacts=today_qua_contact.id).filter(
            Q(created_at__gte=midnight) | Q(created_at__gte=midnight_time)).count()
        if today_followup > 0:
            today_follow_up_stat += 1

    # Getting gender totals, ongoing, completed
    for gender in qua_contacts:
        if gender.sex == "Male":
            total_male += 1
        else:
            total_female += 1
    for gender in qua_contacts_comp:
        if gender.sex == "Male":
            ongoing_male += 1
        else:
            ongoing_female += 1
    for gender in qua_contacts_ong:
        if gender.sex == "Male":
            completed_male += 1
        else:
            completed_female += 1

    # print("gender numbers....")
    # print(total_male)
    # print(total_female)
    # print("ongoing gender numbers....")
    # print(ongoing_male)
    # print(ongoing_female)
    # print("completed gender numbers....")
    # print(completed_male)
    # print(completed_female)

    # print(total_follow_up_stat)
    # print(today_follow_up_stat)

    # pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active=False)

    template = loader.get_template('veoc/subcounty_dashboard.html')
    context = RequestContext(request, {
        'user_level': user_access_level,
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'total_cor_quarantine': _total_cor_quarantine,
        'total_ongoing_quarantine': _total_ongoing_quarantine,
        'total_completed_quarantine': _total_completed_quarantine,
        'total_follow_up_stat': total_follow_up_stat,
        'today_follow_up_stat': today_follow_up_stat,
        'total_pie_male': total_male, 'total_pie_female': total_female,
        'total_pie_comp_male': completed_male, 'total_pie_comp_female': completed_female,
        'total_pie_ong_male': ongoing_male, 'total_pie_ong_female': ongoing_female,
        'd_count': disease.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls': disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported"),
        'disease_vals': disease.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat,
        'sub_county_name': sub_county_name, 'quarantine_completed_cases': completed_cases,
        'disease_reported_dash_vals': disease_reported_dash_vals, 'quarantine_ongoing_cases': ongoing_cases,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))


@login_required
def border_dashboard(request):
    user_access_level = ""
    user_group = request.user.groups.values_list('name', flat=True)
    print(user_group)
    for grp in user_group:
        user_access_level = grp
    print(user_access_level)

    # get the person org unit to display subcounty on the Dashboard
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_county_id = u.persons.sub_county_id

    # get county names
    county_object = organizational_units.objects.get(pk=user_county_id)
    sub_county_name = county_object.name

    # print(user_county_id)
    # print(sub_county_name)

    _dcall_logs = disease.objects.all().filter(subcounty=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(subcounty=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _total_cor_quarantine = quarantine_contacts.objects.all().filter(subcounty=user_county_id).count()
    _total_ongoing_quarantine = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    _total_completed_quarantine = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    marquee_call_log = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []  # an array that collects all confirmed diseases and maps them to the marquee

    # checks if dictionary has values for the past 7 days
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

    # Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(
        call_category=1).filter(incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=1)).order_by(
        "-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=1).filter(
        incident_status=1).order_by("-date_reported").count()
    # print(rum_disease_call_log_count)

    # Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=3).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=2).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=2).filter(
        incident_status=1).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count = conf_event_count + conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()

    # changed call logs button
    disease_related_calls = call_log.objects.filter(subcounty=user_county_id).filter(call_category=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(subcounty=user_county_id).filter(call_category=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    # Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease=True)
    disease_report_stat = {}
    thirty_days_stat = {}
    for d_type in disease_types:
        diseases_count = disease.objects.all().filter(subcounty=user_county_id).filter(
            disease_type_id=d_type.id).count()
        thirty_days_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(
            disease_type_id=d_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if thirty_days_disease_count > 0:
            disease_report_stat[d_type.name] = diseases_count
            thirty_days_stat[d_type.name] = thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    # ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat = {}
    events_thirty_days_stat = {}
    for e_type in event_types:
        events_count = event.objects.all().filter(subcounty=user_county_id).filter(event_type_id=e_type.id).count()
        events_thirty_days_disease_count = event.objects.all().filter(subcounty=user_county_id).filter(
            event_type_id=e_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if events_thirty_days_disease_count > 0:
            events_report_stat[e_type.name] = events_count
            events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))

    # Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}  # variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(subcounty=user_county_id).filter(county_id=cnty.id).filter(
            date_reported__gte=date.today() - timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid=cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(subcounty=user_county_id).filter(
                subcounty_id=subcnty.id).filter(county_id=cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name': cnty.name, 'id': cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)

    # pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(subcounty=user_county_id).filter(
            disease_type_id=crt_tpye.id).filter(date_reported__gte=date.today() - timedelta(days=30)).values(
            'disease_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        cases.append(disease_descriptions)

    # pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(subcounty=user_county_id).filter(event_type_id=crt_tpye.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('event_type__name', 'county__name',
                                                                         'subcounty__name', 'cases',
                                                                         'deaths').distinct()
        event_cases.append(event_descriptions)

    # line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id=crt_tpye.id).values(
            'idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period',
            'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    # pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    # covid-19 line graph quarantine sites_count
    qua_sites = quarantine_sites.objects.all().order_by('site_name')
    ongoing_cases = {}
    completed_cases = {}
    for qua_site in qua_sites:
        ongoing_array = myDict()
        completed_array = myDict()

        qua_completed_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__gte=date.today() - timedelta(days=14)).count()
        qua_ongoing_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__lte=date.today() - timedelta(days=14)).count()
        qua_total_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).count()

        if qua_completed_contacts > 0 or qua_ongoing_contacts > 0:
            ongoing_array.add('ongoing', qua_ongoing_contacts)
            completed_array.add("completed", qua_completed_contacts)

            ongoing_cases[qua_site.site_name + " - " + str(qua_total_contacts) + " Cases"] = qua_ongoing_contacts
            completed_cases[qua_site.site_name] = qua_completed_contacts

    # print(ongoing_cases)
    # print(completed_cases)

    # populating the total quarantine respondents
    qua_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id)
    qua_contacts_comp = quarantine_contacts.objects.filter(subcounty=user_county_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at")
    qua_contacts_ong = quarantine_contacts.objects.filter(subcounty=user_county_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at")
    total_follow_up_stat = 0
    today_follow_up_stat = 0
    total_male = 0
    total_female = 0
    ongoing_male = 0
    ongoing_female = 0
    completed_male = 0
    completed_female = 0

    current_date = date.today().strftime('%Y-%m-%d')
    c_date = date.today()
    today_time = datetime.combine(c_date, datetime.min.time())
    midnight = today_time.strftime('%Y-%m-%d %H:%M:%S')
    midnight_time = midnight + "+03"
    # print(midnight)
    # print(midnight_time)

    for qua_contact in qua_contacts:
        followup = quarantine_follow_up.objects.all().filter(patient_contacts=qua_contact.id).count()
        if followup > 0:
            total_follow_up_stat += 1

    # populating the todays quarantine respondents
    for today_qua_contact in qua_contacts:
        current_date = date.today().strftime('%Y-%m-%d')
        today_followup = quarantine_follow_up.objects.all().filter(patient_contacts=today_qua_contact.id).filter(
            patient_contacts=today_qua_contact.id).filter(
            Q(created_at__gte=midnight) | Q(created_at__gte=midnight_time)).count()
        if today_followup > 0:
            today_follow_up_stat += 1

    # Getting gender totals, ongoing, completed
    for gender in qua_contacts:
        if gender.sex == "Male":
            total_male += 1
        else:
            total_female += 1
    for gender in qua_contacts_comp:
        if gender.sex == "Male":
            ongoing_male += 1
        else:
            ongoing_female += 1
    for gender in qua_contacts_ong:
        if gender.sex == "Male":
            completed_male += 1
        else:
            completed_female += 1

    # print("gender numbers....")
    # print(total_male)
    # print(total_female)
    # print("ongoing gender numbers....")
    # print(ongoing_male)
    # print(ongoing_female)
    # print("completed gender numbers....")
    # print(completed_male)
    # print(completed_female)

    # print(total_follow_up_stat)
    # print(today_follow_up_stat)

    # pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active=False)

    template = loader.get_template('veoc/border_dashboard.html')
    context = RequestContext(request, {
        'user_level': user_access_level,
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'total_cor_quarantine': _total_cor_quarantine,
        'total_ongoing_quarantine': _total_ongoing_quarantine,
        'total_completed_quarantine': _total_completed_quarantine,
        'total_follow_up_stat': total_follow_up_stat,
        'today_follow_up_stat': today_follow_up_stat,
        'total_pie_male': total_male, 'total_pie_female': total_female,
        'total_pie_comp_male': completed_male, 'total_pie_comp_female': completed_female,
        'total_pie_ong_male': ongoing_male, 'total_pie_ong_female': ongoing_female,
        'd_count': disease.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls': disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported"),
        'disease_vals': disease.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat,
        'sub_county_name': sub_county_name, 'quarantine_completed_cases': completed_cases,
        'disease_reported_dash_vals': disease_reported_dash_vals, 'quarantine_ongoing_cases': ongoing_cases,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))


@login_required
def facility_dashboard(request):
    user_access_level = ""
    user_group = request.user.groups.values_list('name', flat=True)
    print(user_group)
    for grp in user_group:
        user_access_level = grp
    print(user_access_level)

    # get the person org unit to display subcounty on the Dashboard
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_county_id = u.persons.sub_county_id

    # get county names
    county_object = organizational_units.objects.get(pk=user_county_id)
    sub_county_name = county_object.name

    # check quarantine facilty user is assigned to
    # facility_access = quarantine_sites.objects.filter(team_lead = user_id)
    # facilty_name
    # if facility_access :
    #     facilty_name = facility_access.site_name
    #
    # else:
    #     facilty_name = "No Facility Allocated to User"
    #
    # print(facilty_name)

    # print(user_county_id)
    # print(sub_county_name)

    _dcall_logs = disease.objects.all().filter(subcounty=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported")
    _ecall_logs = event.objects.all().filter(subcounty=user_county_id).filter(data_source=1).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _events = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    _disease = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=7)).order_by("-date_reported")
    marquee_call_log = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_disease = []  # an array that collects all confirmed diseases and maps them to the marquee
    marquee_events = []  # an array that collects all confirmed diseases and maps them to the marquee

    # checks if dictionary has values for the past 7 days
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

    # Diseases reported - confirmed diseases cases
    conf_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_disease_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(
        call_category=1).filter(incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=1)).order_by(
        "-date_reported").count()
    rum_disease_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=1).filter(
        incident_status=1).order_by("-date_reported").count()
    # print(rum_disease_call_log_count)

    # Events reported - confirmed cases
    conf_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    rum_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    susp_event_count = event.objects.all().filter(subcounty=user_county_id).filter(incident_status=3).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    conf_event_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=2).filter(
        incident_status=2).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    rum_event_call_log_count = call_log.objects.all().filter(subcounty=user_county_id).filter(call_category=2).filter(
        incident_status=1).filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
        "-date_reported").count()
    # print(rum_event_call_log_count)

    e_conf_count = conf_event_count + conf_event_call_log_count
    conf_call_count = conf_disease_call_log_count
    rum_call_count = rum_disease_call_log_count
    total_call_count = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()

    # changed call logs button
    disease_related_calls = call_log.objects.filter(subcounty=user_county_id).filter(call_category=1).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    event_related_calls = call_log.objects.filter(subcounty=user_county_id).filter(call_category=2).filter(
        date_reported__gte=date.today() - timedelta(days=30)).order_by("-date_reported").count()
    tot_urelated = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    tot_flashes = call_log.objects.filter(subcounty=user_county_id).filter(
        date_reported__gte=date.today() - timedelta(days=30)).filter(call_category=3).order_by("-date_reported").count()
    total_unrelated_calls = tot_urelated + tot_flashes

    # Populating the pie_chart
    counties = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    disease_types = dhis_disease_type.objects.all().filter(priority_disease=True)
    disease_report_stat = {}
    thirty_days_stat = {}
    for d_type in disease_types:
        diseases_count = disease.objects.all().filter(subcounty=user_county_id).filter(
            disease_type_id=d_type.id).count()
        thirty_days_disease_count = disease.objects.all().filter(subcounty=user_county_id).filter(
            disease_type_id=d_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if thirty_days_disease_count > 0:
            disease_report_stat[d_type.name] = diseases_count
            thirty_days_stat[d_type.name] = thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    disease_reported_dash_vals = dict(Counter(thirty_days_stat).most_common(3))

    # ph events bar graph
    event_types = dhis_event_type.objects.all()
    events_report_stat = {}
    events_thirty_days_stat = {}
    for e_type in event_types:
        events_count = event.objects.all().filter(subcounty=user_county_id).filter(event_type_id=e_type.id).count()
        events_thirty_days_disease_count = event.objects.all().filter(subcounty=user_county_id).filter(
            event_type_id=e_type.id).filter(date_reported__gte=date.today() - timedelta(days=30)).count()
        if events_thirty_days_disease_count > 0:
            events_report_stat[e_type.name] = events_count
            events_thirty_days_stat[e_type.name] = events_thirty_days_disease_count

    # picking the highest disease numbers for dashboard diseases
    events_reported_dash_vals = dict(Counter(events_thirty_days_stat).most_common(3))

    # Populating the bargraph
    # counties = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
    # sub_counties = sub_county.objects.all()
    call_stats = {}  # variable that collects county descriptions from their id's (to be used as an index)
    sub_call_stat = {}

    series_data = {}
    series = []
    data_val = []
    data_record = []

    for cnty in counties:
        call_count = call_log.objects.all().filter(subcounty=user_county_id).filter(county_id=cnty.id).filter(
            date_reported__gte=date.today() - timedelta(days=1)).count()
        sub_counties = organizational_units.objects.all().filter(parentid=cnty.organisationunitid).order_by('name')
        if call_count > 0:
            # print(call_count)
            call_stats[cnty.name] = call_count
        for subcnty in sub_counties:
            call_subcny = call_log.objects.all().filter(subcounty=user_county_id).filter(
                subcounty_id=subcnty.id).filter(county_id=cnty.id).count()
            if call_subcny > 0:
                sub_call_stat[subcnty.name, cnty.name] = call_subcny

                val = {'name': cnty.name, 'id': cnty.name}
                data_record = [subcnty.name, call_subcny]
                # print(data_record)
        data_val.append(data_record)
    series.append(series_data)

    # pie_chart disease data
    chart_d_type = dhis_disease_type.objects.all().order_by('name')
    cases = []
    disease_status = []
    for crt_tpye in chart_d_type:
        disease_descriptions = disease.objects.filter(subcounty=user_county_id).filter(
            disease_type_id=crt_tpye.id).filter(date_reported__gte=date.today() - timedelta(days=30)).values(
            'disease_type__name', 'county__name', 'subcounty__name', 'cases', 'deaths').distinct()
        cases.append(disease_descriptions)

    # pie_chart events data
    chart_e_type = dhis_event_type.objects.all().order_by('name')
    event_cases = []
    event_status = []
    for crt_tpye in chart_e_type:
        event_descriptions = event.objects.filter(subcounty=user_county_id).filter(event_type_id=crt_tpye.id).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('event_type__name', 'county__name',
                                                                         'subcounty__name', 'cases',
                                                                         'deaths').distinct()
        event_cases.append(event_descriptions)

    # line graph dhis2 diseases data
    chart_dhis_type = idsr_diseases.objects.all().order_by('name')
    dhis_cases = []
    dhis_status = []
    for crt_tpye in chart_dhis_type:
        dhis_descriptions = idsr_weekly_national_report.objects.filter(idsr_disease_id_id=crt_tpye.id).values(
            'idsr_disease_id__name', 'org_unit_id_id__name', 'idsr_incident_id_id__name', 'period',
            'data_value').distinct()
        dhis_cases.append(dhis_descriptions)

    # pulling all eoc status for the drop down for change
    eoc_Status = eoc_status.objects.all()

    # covid-19 line graph quarantine sites_count
    qua_sites = quarantine_sites.objects.filter(subcounty=user_county_id).order_by('site_name')
    # qua_sites = quarantine_sites.objects.filter(team_lead = user_id).order_by('site_name')
    ongoing_cases = {}
    completed_cases = {}
    site_id = 0
    for qua_site in qua_sites:
        ongoing_array = myDict()
        completed_array = myDict()
        site_id = qua_site.id

        qua_completed_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__gte=date.today() - timedelta(days=14)).count()
        qua_ongoing_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).filter(created_at__lte=date.today() - timedelta(days=14)).count()
        qua_total_contacts = quarantine_contacts.objects.all().filter(subcounty=user_county_id).filter(
            quarantine_site_id=qua_site.id).count()

        if qua_completed_contacts > 0 or qua_ongoing_contacts > 0:
            ongoing_array.add('ongoing', qua_ongoing_contacts)
            completed_array.add("completed", qua_completed_contacts)

            ongoing_cases[qua_site.site_name + " - " + str(qua_total_contacts) + " Cases"] = qua_ongoing_contacts
            completed_cases[qua_site.site_name] = qua_completed_contacts

    print(ongoing_cases)
    print(completed_cases)

    # populating the total quarantine respondents
    print(site_id)
    _total_cor_quarantine = quarantine_contacts.objects.filter(quarantine_site__id=site_id).count()
    _total_ongoing_quarantine = quarantine_contacts.objects.all().filter(quarantine_site__id=site_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at").count()
    _total_completed_quarantine = quarantine_contacts.objects.all().filter(quarantine_site__id=site_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at").count()

    qua_contacts = quarantine_contacts.objects.all().filter(quarantine_site__id=site_id)
    qua_contacts_comp = quarantine_contacts.objects.filter(quarantine_site__id=site_id).filter(
        created_at__gte=date.today() - timedelta(days=14)).order_by("-created_at")
    qua_contacts_ong = quarantine_contacts.objects.filter(quarantine_site__id=site_id).filter(
        created_at__lte=date.today() - timedelta(days=14)).order_by("-created_at")
    total_follow_up_stat = 0
    today_follow_up_stat = 0
    total_male = 0
    total_female = 0
    ongoing_male = 0
    ongoing_female = 0
    completed_male = 0
    completed_female = 0

    current_date = date.today().strftime('%Y-%m-%d')
    c_date = date.today()
    today_time = datetime.combine(c_date, datetime.min.time())
    midnight = today_time.strftime('%Y-%m-%d %H:%M:%S')
    midnight_time = midnight + "+03"
    # print(midnight)
    # print(midnight_time)

    for qua_contact in qua_contacts:
        followup = quarantine_follow_up.objects.all().filter(patient_contacts=qua_contact.id).count()
        if followup > 0:
            total_follow_up_stat += 1

    # populating the todays quarantine respondents
    for today_qua_contact in qua_contacts:
        current_date = date.today().strftime('%Y-%m-%d')
        today_followup = quarantine_follow_up.objects.all().filter(patient_contacts=today_qua_contact.id).filter(
            patient_contacts=today_qua_contact.id).filter(
            Q(created_at__gte=midnight) | Q(created_at__gte=midnight_time)).count()
        if today_followup > 0:
            today_follow_up_stat += 1

    # Getting gender totals, ongoing, completed
    for gender in qua_contacts:
        if gender.sex == "Male":
            total_male += 1
        else:
            total_female += 1
    for gender in qua_contacts_comp:
        if gender.sex == "Male":
            ongoing_male += 1
        else:
            ongoing_female += 1
    for gender in qua_contacts_ong:
        if gender.sex == "Male":
            completed_male += 1
        else:
            completed_female += 1

    # print(total_follow_up_stat)
    # print(today_follow_up_stat)

    # pulling eoc status as set by only the eoc manager
    set_eoc_status = eoc_status.objects.all().exclude(active=False)

    template = loader.get_template('veoc/facility_dashboard.html')
    context = RequestContext(request, {
        'user_level': user_access_level,
        'marquee_call_log': marquee_call_log,
        'marquee_disease': marquee_disease,
        'marquee_events': marquee_events,
        'total_cor_quarantine': _total_cor_quarantine,
        'total_ongoing_quarantine': _total_ongoing_quarantine,
        'total_completed_quarantine': _total_completed_quarantine,
        'total_follow_up_stat': total_follow_up_stat,
        'today_follow_up_stat': today_follow_up_stat,
        'total_pie_male': total_male, 'total_pie_female': total_female,
        'total_pie_comp_male': completed_male, 'total_pie_comp_female': completed_female,
        'total_pie_ong_male': ongoing_male, 'total_pie_ong_female': ongoing_female,
        'd_count': disease.objects.filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_disease_count': conf_disease_count,
        'rum_disease_count': rum_disease_count,
        'e_count': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported").count(),
        'conf_event_count': conf_event_count,
        'rum_event_count': rum_event_count,
        'susp_event_count': susp_event_count,
        'conf_call_count': conf_call_count,
        'rum_call_count': rum_call_count,
        'total_call_count': total_call_count,
        'disease_related_calls': disease_related_calls,
        'event_related_calls': event_related_calls,
        'total_unrelated_calls': total_unrelated_calls,
        'vals': call_log.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported"),
        'disease_vals': disease.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'event_vals': event.objects.all().filter(date_reported__gte=date.today() - timedelta(days=30)).order_by(
            "-date_reported")[:5],
        'contact_type_vals': contacts,
        'thirty_days_stat': thirty_days_stat,
        'events_thirty_days_stat': events_thirty_days_stat,
        'elements': call_stats,
        'sub_elements': sub_call_stat,
        'sub_county_name': sub_county_name, 'quarantine_completed_cases': completed_cases,
        'disease_reported_dash_vals': disease_reported_dash_vals, 'quarantine_ongoing_cases': ongoing_cases,
        'pie_diseases': cases, 'pie_events': event_cases, 'dhis_graph_data': dhis_cases,
        'eoc_status': eoc_Status, 'set_eoc_status': set_eoc_status
    })

    return HttpResponse(template.render(context.flatten()))


@login_required
def call_register(request):
    if request.method == 'POST':
        callcategory = request.POST.get('callCategory', '')
        diseasetype = request.POST.get('diseaseType', '')
        eventtype = request.POST.get('eventType', '')
        unrelated_incident = request.POST.get('incidentType', '')
        callername = request.POST.get('callerName', '')
        callernumber = request.POST.get('callerNumber', '')
        region = request.POST.get('region', '')
        locatn = request.POST.get('location', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        ward = request.POST.get('ward', '')
        status = request.POST.get('status', '')
        datereported = request.POST.get('dateReported', '')
        descriptn = request.POST.get('description', '')
        actiontaken = request.POST.get('actionTaken', '')
        significant = request.POST.get('callSignificant', '')

        # check significant eventType
        significant_events = ""
        if significant == 'on':
            significant_events = "t"
        else:
            significant_events = "f"

        # Check call_category_incident
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
                    unrelatedObject = unrelated_calls_category.objects.get(description=unrelated_incident)
                    call_inc_category = unrelatedObject.id
                    print("category urelated incident: ")
                    print("call_inc_category: ")
                    # print(call_inc_category)

                    # getting objects of foreignKeys
                    # checks if county data is chosen
                    callcategoryObject = call_incident_category.objects.get(incident_description=callcategory)
                    countyObject = organizational_units.objects.get(organisationunitid=18)
                    subcountyObject = organizational_units.objects.get(organisationunitid=18)
                    wardObject = organizational_units.objects.get(organisationunitid=18)
                    regionObject = reporting_region.objects.get(region_description='Kenya')
                    incidentObject = incident_status.objects.get(status_description='Rumour')

            else:
                # call_inc_category = eventtype
                eventObject = dhis_event_type.objects.get(name=eventtype)
                call_inc_category = eventObject.id
                print("category event type: ")
                print("call_inc_category: ")
                # print(call_inc_category)

                # getting objects of foreignKeys
                # checks if county data is chosen
                if cnty == "":
                    callcategoryObject = call_incident_category.objects.get(incident_description=callcategory)
                    countyObject = organizational_units.objects.get(organisationunitid=18)
                    subcountyObject = organizational_units.objects.get(organisationunitid=18)
                    wardObject = organizational_units.objects.get(organisationunitid=18)
                    regionObject = reporting_region.objects.get(region_description=region)
                    incidentObject = incident_status.objects.get(status_description=status)

                else:
                    callcategoryObject = call_incident_category.objects.get(incident_description=callcategory)
                    countyObject = organizational_units.objects.get(organisationunitid=cnty)
                    subcountyObject = organizational_units.objects.get(organisationunitid=sub_cnty)
                    wardObject = organizational_units.objects.get(organisationunitid=ward)
                    regionObject = reporting_region.objects.get(region_description=region)
                    incidentObject = incident_status.objects.get(status_description=status)
        else:
            # call_inc_category = diseasetype
            diseaseObject = dhis_disease_type.objects.get(name=diseasetype)
            call_inc_category = diseaseObject.id
            print("category disease type: ")
            print("call_inc_category: ")
            # print(call_inc_category)

            # getting objects of foreignKeys
            # checks if county data is chosen
            if cnty == "":
                callcategoryObject = call_incident_category.objects.get(incident_description=callcategory)
                countyObject = organizational_units.objects.get(organisationunitid=18)
                subcountyObject = organizational_units.objects.get(organisationunitid=18)
                wardObject = organizational_units.objects.get(organisationunitid=18)
                regionObject = reporting_region.objects.get(region_description=region)
                incidentObject = incident_status.objects.get(status_description=status)

            else:
                callcategoryObject = call_incident_category.objects.get(incident_description=callcategory)
                countyObject = organizational_units.objects.get(name=cnty)
                subcountyObject = organizational_units.objects.get(name=sub_cnty)
                wardObject = organizational_units.objects.get(organisationunitid=ward)
                regionObject = reporting_region.objects.get(region_description=region)
                incidentObject = incident_status.objects.get(status_description=status)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        # print(current_user)
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        call_log.objects.create(call_category=callcategoryObject, call_category_incident=call_inc_category,
                                incident_status=incidentObject,
                                reporting_region=regionObject, county=countyObject, subcounty=subcountyObject,
                                ward=wardObject, location=locatn, caller_name=callername,
                                caller_number=callernumber, date_reported=datereported, call_description=descriptn,
                                action_taken=actiontaken,
                                significant=significant_events, updated_at=current_date, created_by=userObject,
                                updated_by=userObject, created_at=current_date)

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
    call_county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    # call_county = county.objects.all().order_by('description')
    diseases = dhis_disease_type.objects.all().order_by('name')
    events = dhis_event_type.objects.all().order_by('name')
    day = time.strftime("%Y-%m-%d")

    data = {'call_category': call_category, 'unrelated_calls': unrelated_calls, 'regions': regions,
            'incident_status': status,
            'county': call_county, 'diseases': diseases, 'events': events, 'day': day}

    return render(request, 'veoc/call_register_form.html', data)


def get_county(request):
    if request.method == "POST":
        counties = organizational_units.objects.filter(hierarchylevel=2)

        serialized = serialize('json', counties)
        obj_list = json.loads(serialized)

        print(obj_list)
        print(json.dumps(obj_list))

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


def get_subcounty(request):
    obj_list = None
    if request.method == "POST":
        mycounty = request.POST.get('county', '')
        print(mycounty)
        county_parent_id = organizational_units.objects.get(name=mycounty)
        sub_counties = organizational_units.objects.filter(parentid=county_parent_id)

        serialized = serialize('json', sub_counties)
        obj_list = json.loads(serialized)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


def usersubcounty(request):
    obj_list = None
    if request.method == "POST":
        org_id = request.POST.get('county', '')
        print(org_id)
        county_parent_id = organizational_units.objects.get(organisationunitid=org_id)
        sub_counties = organizational_units.objects.filter(parentid=county_parent_id)

        serialized = serialize('json', sub_counties)
        obj_list = json.loads(serialized)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


def get_group(request):
    obj_list = None
    if request.method == "POST":
        _name = request.POST.get('name', '')

        print(_name)
        group_name = Group.objects.all()
        print(group_name)
        _group = group_name.filter(name__icontains=_name)

        print(_group)
        serialized = serialize('json', _group)
        obj_list = json.loads(serialized)
        print(obj_list)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


def get_ward(request):
    if request.method == "POST":
        mysubcounty = request.POST.get('subcounty', '')

        subcounty_parent_id = organizational_units.objects.get(name=mysubcounty)
        wards = organizational_units.objects.filter(parentid=subcounty_parent_id)

        serialized = serialize('json', wards)
        obj_list = json.loads(serialized)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


def call_report(request):
    # check if there is an edit on an entry and save
    if request.method == 'POST':
        id = request.POST.get('id', '')
        incident_stat = request.POST.get('status_name', '')
        descrp = request.POST.get('description_name', '')
        action = request.POST.get('action_taken', '')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        call_log.objects.filter(pk=id).update(incident_status=incident_stat, call_description=descrp,
                                              action_taken=action, updated_by=userObject, updated_at=current_date)

    call_count = call_log.objects.exclude(call_category=3).count()
    call_incidents = call_incident_category.objects.all()
    call_status_desr = incident_status.objects.all()
    call_logs = call_log.objects.exclude(call_category=3)
    day_from = time.strftime("%Y-%m-%d")
    day_to = time.strftime("%Y-%m-%d")

    call_cat_incident = []
    for calls in call_logs:
        _call_category = calls.call_category.id
        # print(_call_category)
        if _call_category == 1:
            calls_disease = calls.call_category_incident
            # print(calls_disease)
            call_cat_disease = dhis_disease_type.objects.filter(id=calls_disease).values_list('name', flat=True).first()
            # print(call_cat_disease)
            call_cat_incident.append(call_cat_disease)
        elif _call_category == 2:
            call_event = calls.call_category_incident
            # print(call_event)
            call_cat_event = dhis_event_type.objects.filter(id=call_event).values_list('name', flat=True).first()
            # print(call_cat_event)
            call_cat_incident.append(call_cat_event)
        else:
            print('Call category not in DB')

    # print(call_cat_incident)
    my_list_data = zip(call_logs, call_cat_incident)

    values = {'call_logs': my_list_data, 'contact_type_vals': contacts, 'call_count': call_count, 'success': "",
              'call_incidents': call_incidents, 'status_descriptions': call_status_desr}

    return render(request, 'veoc/call_report.html', values)


def filter_call_report(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        call_count = call_log.objects.exclude(call_category=3).filter(date_reported__range=[date_from, date_to]).count()
        call_incidents = call_incident_category.objects.all()
        call_status_desr = incident_status.objects.all()
        call_logs = call_log.objects.exclude(call_category=3).filter(date_reported__range=[date_from, date_to])
        day_from = date_from
        day_to = date_to

        call_cat_incident = []
        for calls in call_logs:
            _call_category = calls.call_category.id
            if _call_category == 1:
                calls_disease = calls.call_category_incident
                call_cat_disease = dhis_disease_type.objects.filter(id=calls_disease).values_list('name',
                                                                                                  flat=True).first()
                call_cat_incident.append(call_cat_disease)
            elif _call_category == 2:
                call_event = calls.call_category_incident
                call_cat_event = dhis_event_type.objects.filter(id=call_event).values_list('name', flat=True).first()
                call_cat_incident.append(call_cat_event)
            else:
                print('Call category not in DB')

        my_list_data = zip(call_logs, call_cat_incident)

        values = {'call_logs': my_list_data, 'contact_type_vals': contacts, 'call_count': call_count, 'success': "",
                  'call_incidents': call_incidents, 'status_descriptions': call_status_desr, 'day_from': day_from,
                  'day_to': day_to}

        return render(request, 'veoc/call_report.html', values)


@login_required
def disease_register(request):
    if request.method == 'POST':
        diseasetype = request.POST.get('diseaseType', '')
        datasource = request.POST.get('dataSource', '')
        region = request.POST.get('region', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        ward = request.POST.get('ward', '')
        status = request.POST.get('status', '')
        datereported = request.POST.get('dateReported', '')
        cases = request.POST.get('cases', '')
        deaths = request.POST.get('deaths', '')
        descriptn = request.POST.get('description', '')
        actiontaken = request.POST.get('actionTaken', '')
        significant = request.POST.get('callSignificant', '')

        # check significant eventType
        significant_events = ""
        if significant == 'on':
            significant_events = "t"
        else:
            significant_events = "f"

            # checks if data values for county exists, if not, selected region not Kenya
            # NB : organizational_unit 18 is Kenya in the database
        if region == "Kenya":
            countyObject = organizational_units.objects.get(name=cnty)
            subcountyObject = organizational_units.objects.get(name=sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid=ward)
        else:
            countyObject = organizational_units.objects.get(organisationunitid=18)
            subcountyObject = organizational_units.objects.get(organisationunitid=18)
            wardObject = organizational_units.objects.get(organisationunitid=18)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        diseaseObject = dhis_disease_type.objects.get(name=diseasetype)
        datasourceObject = data_source.objects.get(source_description=datasource)
        regionObject = reporting_region.objects.get(region_description=region)
        incidentObject = incident_status.objects.get(status_description=status)

        # saving values to databse
        disease.objects.create(disease_type=diseaseObject, incident_status=incidentObject, county=countyObject,
                               subcounty=subcountyObject, data_source=datasourceObject,
                               ward=wardObject, reporting_region=regionObject, date_reported=datereported, cases=cases,
                               deaths=deaths, remarks=descriptn, action_taken=actiontaken,
                               significant=significant_events, updated_at=current_date, created_by=userObject,
                               updated_by=userObject, created_at=current_date)

        # check if the incident is within kenya to save in DHIS2
        if region == "Kenya":
            # check if the reported case is confirmed to save in dhis2 data tables
            if status == 'Confirmed':
                # saving data into dhis2 data dataTables
                rep_disease = dhis_disease_data_elements.objects.filter(name__contains=diseasetype).values_list('id',
                                                                                                                flat=True).order_by(
                    'id')

                r_disease = ''
                # pulling the data value from the object
                for rep in rep_disease:
                    r_disease = rep

                # check if there is a data element that is in disease type before saving
                if rep_disease:
                    print('saving into dhis data tables')
                    # create current week/year number
                    dt = timezone.now()
                    wk_val = dt.isocalendar()[1]
                    yr_val = dt.replace(year=dt.year)
                    final_year = yr_val.year
                    weeknum = str(final_year) + str(wk_val)
                    print(weeknum)
                    # save into dhis reported disease
                    dhis_reported_diseases.objects.create(org_unit_id=wardObject, program='Jt6SPO0bjKB',
                                                          disease_type=diseaseObject, eventDate=current_date,
                                                          stored_by='eoc_user', period=weeknum, status='COMPLETED')
                    # get latest key of data just entered to save into data values
                    disease_id = dhis_reported_diseases.objects.order_by('-id')[0]
                    disease_pk = disease_id.id
                    # get object of the reported disease to store into data values
                    rep_eve_Object = dhis_reported_diseases.objects.get(pk=disease_pk)
                    # get object of the data element to store into data values
                    red_object1 = dhis_disease_data_elements.objects.get(id=r_disease)
                    red_object2 = dhis_disease_data_elements.objects.get(id=30)
                    # save the data valus objects
                    dhis_disease_data_values.objects.create(dhis_reported_disease_id=rep_eve_Object,
                                                            data_element_id=red_object1, data_value=cases)
                    dhis_disease_data_values.objects.create(dhis_reported_disease_id=rep_eve_Object,
                                                            data_element_id=red_object2, data_value=diseasetype)
                else:
                    print('no associated disease element on disease types - not saved in dhis2 data elements')
            else:
                print('unconfirmed incident - not saved in dhis2 data elements')
        else:
            print('global incident case - not saved in dhis2 data elements')

        # check if disease is infectious disease to save to GEPP tables
        infect_disease = diseaseObject.infectious_disease
        print(infect_disease)

        if infect_disease:
            # save data to the infectious disease tables
            print("Reported disease is an infectous disease")

            infectious_disease.objects.create(disease_type=diseaseObject, incident_status=incidentObject,
                                              data_source=datasourceObject, reporting_region=regionObject,
                                              date_reported=datereported, remarks=descriptn,
                                              updated_at=current_date, created_by=userObject, updated_by=userObject,
                                              created_at=current_date)

        else:
            print("Reported disease not infectous disease")

    regions = reporting_region.objects.all()
    status = incident_status.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    diseases = dhis_disease_type.objects.all().order_by('name')
    datasource = data_source.objects.all().order_by('source_description')
    day = time.strftime("%Y-%m-%d")

    data = {'diseases': diseases, 'datasource': datasource, 'regions': regions, 'incident_status': status,
            'county': county, 'day': day}

    return render(request, 'veoc/disease_form.html', data)


@login_required
def line_lising_excel(request):
    if request.method == "GET":
        return render(request, 'veoc/line_listing.html')
    try:
        csv_file = request.FILES['file']
        print("in")
        # read_data(csv_file.file, request)
        title = []
        print(csv_file.file)
        wb = xlrd.open_workbook(csv_file.file.name)
        sheet = wb.sheet_by_index(0)
        sheet.cell_value(0, 0)
        for n in range(sheet.nrows):
            if n == 0:
                title = sheet.row_values(n)
            else:
                row = sheet.row_values(n)
                ex_rows = {title[i]: row[i] for i in range(len(title))}
                excel_date = int(ex_rows['Date'])

                print(xlrd.xldate.xldate_as_datetime(ex_rows['Date'], wb.datemode))
                lst = moh_line_listing.objects.create(date=xlrd.xldate.xldate_as_datetime(ex_rows['Date'], wb.datemode),
                                                      facility_name=ex_rows['Facility Name'],
                                                      county=ex_rows['County'], sub_county=ex_rows['Sub County'],
                                                      ward=ex_rows['Ward'], patient_names=ex_rows['Patient Name'],
                                                      patient_status=ex_rows['Patient Status'],
                                                      contact_number=ex_rows['Contact Number'],
                                                      age=ex_rows['Age'], sex=ex_rows['Sex'],
                                                      village=ex_rows['Village'],
                                                      disease_condition=ex_rows['Disease/ Condition'],
                                                      date_seen_at_facility=xlrd.xldate.xldate_as_datetime(
                                                          ex_rows['Date Seen at Facility'], wb.datemode),
                                                      date_onset_disease=ex_rows['Date onset of Disease'],
                                                      no_doses_of_vaccine=ex_rows['Number of doses of vaccine'],
                                                      lab_test=ex_rows['Lab Tests'], outcome=ex_rows['Outcome'],
                                                      epi_week=ex_rows['EPI Week'], comments=ex_rows['Comments'])
                print(lst)

        messages.success(request, 'DONE')
        return render(request, 'veoc/line_listing.html')

    except MultiValueDictKeyError:
        messages.warning(request, 'Select file before uploading', fail_silently=True)
        return render(request, 'veoc/line_listing.html')
    except xlrd.XLRDError:
        messages.warning(request, 'THIS IS NOT AN EXCEL FILE. Select an excel file', fail_silently=True)
        return render(request, 'veoc/line_listing.html')


@login_required
def quarantine_excel(request):
    if request.method == "GET":
        return render(request, 'veoc/quarantine_file_upload.html')
    try:
        csv_file = request.FILES['file']
        read_data(csv_file.file, request)
        messages.success(request, 'DONE')
        return render(request, 'veoc/quarantine_file_upload.html')

    except MultiValueDictKeyError:
        messages.warning(request, 'Select file before uploading', fail_silently=True)
        return render(request, 'veoc/quarantine_file_upload.html')
    except xlrd.XLRDError:
        messages.warning(request, 'THIS IS NOT AN EXCEL FILE. Select an excel file', fail_silently=True)
        return render(request, 'veoc/quarantine_file_upload.html')


def read_data(f, r):
    title = []
    print(f)
    wb = xlrd.open_workbook(f.name)
    sheet = wb.sheet_by_index(0)
    sheet.cell_value(0, 0)
    for n in range(sheet.nrows):
        if n == 0:
            title = sheet.row_values(n)
        else:
            row = sheet.row_values(n)
            ex_rows = {title[i]: row[i] for i in range(len(title))}
            print(ex_rows)
            save_data(ex_rows, r)


def save_data(d, request):
    first_name = d['first_name']
    last_name = d['last_name']
    sex = d['gender']
    dob = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(d['dob']) - 2)
    passport_number = d['id_passport_number']
    phone_number = d['phone_number']
    email_address = d['email_address']
    origin_country = d['country_of_origin']
    cnty = d['county']
    sub_cnty = d['subcounty']
    ward = d['ward']
    place_of_diagnosis = d['place_of_diagnosis']
    site_name = d['quarantine_site']
    date_of_contact = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(d['date_of_arrival']) - 2)
    nationality = d['nationality']
    comorbidity = d['comorbidity']
    drugs = d['any_drugs_on']
    nextofkin = d['nextofkin']
    nok_phone_number = d['nextofkin_phone_number']

    if origin_country.lower() == "kenya":
        countyObject = organizational_units.objects.get(name=cnty)
        subcountyObject = organizational_units.objects.get(name=sub_cnty)
        wardObject = organizational_units.objects.get(organisationunitid=ward)
    else:
        countyObject = organizational_units.objects.get(organisationunitid=18)
        subcountyObject = organizational_units.objects.get(organisationunitid=18)
        wardObject = organizational_units.objects.get(organisationunitid=18)

    user_phone = "+254"
    # check if the leading character is 0
    if str(phone_number[0]) == "0":
        user_phone = user_phone + str(phone_number[1:])
        # print("number leading with 0")
    else:
        user_phone = user_phone + str(phone_number)

    current_date = timezone.now()

    # get current user
    current_user = request.user
    print(current_user)
    userObject = User.objects.get(pk=current_user.id)
    qua_site = quarantine_sites.objects.get(site_name=site_name)
    contact_save = ''
    source = "Web Registration"
    contact_identifier = uuid.uuid4().hex
    # Check if mobile number exists in the table
    details_exist = quarantine_contacts.objects.filter(phone_number=user_phone, first_name=first_name,
                                                       last_name=last_name)
    if details_exist:
        for mob_ex in details_exist:
            messages.error(request, "Details already exist" + str(mob_ex.phone_number) + "Registered on :" + str(
                mob_ex.created_at), fail_silently=True)
    else:
        contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name,
                                                          county=countyObject, subcounty=subcountyObject,
                                                          ward=wardObject, sex=sex, dob=dob,
                                                          passport_number=passport_number,
                                                          phone_number=user_phone, email_address=email_address,
                                                          date_of_contact=date_of_contact, source=source,
                                                          nationality=nationality, drugs=drugs, nok=nextofkin,
                                                          nok_phone_num=nok_phone_number, cormobidity=comorbidity,
                                                          origin_country=origin_country,
                                                          place_of_diagnosis=place_of_diagnosis,
                                                          quarantine_site=qua_site, contact_uuid=contact_identifier,
                                                          updated_at=current_date, created_by=userObject,
                                                          updated_by=userObject, created_at=current_date)

        contact_save.save()

    # check if details have been saved


def moh_line_listing_template(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'Documents\\MOH 503 linelisting form.xlsx')
    print(file_path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


def download_template(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'Documents\\new_exp.xlsx')
    print(file_path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


@login_required
def quarantine_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        middle_name = request.POST.get('middle_name', '')
        last_name = request.POST.get('last_name', '')
        sex = request.POST.get('sex', '')
        dob = request.POST.get('dob', '')
        passport_number = request.POST.get('passport_number', '')
        phone_number = request.POST.get('phone_number', '')
        email_address = request.POST.get('email_address', '')
        origin_country = request.POST.get('country', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        ward = request.POST.get('ward', '')
        place_of_diagnosis = request.POST.get('place_of_diagnosis', '')
        site_name = request.POST.get('q_site_name', '')
        date_of_contact = request.POST.get('date_of_contact', '')
        nationality = request.POST.get('nationality', '')
        comorbidity = request.POST.get('comorbidity', '')
        drugs = request.POST.get('drugs', '')
        nextofkin = request.POST.get('nok', '')
        nok_phone_number = request.POST.get('nok_phone_num', '')

        if origin_country.lower() == "kenya":
            countyObject = organizational_units.objects.get(name=cnty)
            subcountyObject = organizational_units.objects.get(name=sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid=ward)
        else:
            countyObject = organizational_units.objects.get(organisationunitid=18)
            subcountyObject = organizational_units.objects.get(organisationunitid=18)
            wardObject = organizational_units.objects.get(organisationunitid=18)

        user_phone = "+254"
        # check if the leading character is 0
        if str(phone_number[0]) == "0":
            user_phone = user_phone + str(phone_number[1:])
            # print("number leading with 0")
        else:
            user_phone = user_phone + str(phone_number)
            # print("number not leading with 0")

        # get todays date
        current_date = timezone.now()

        # get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        qua_site = quarantine_sites.objects.get(site_name=site_name)
        contact_save = ''
        source = "Web Registration"
        contact_identifier = uuid.uuid4().hex
        # Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number=user_phone, first_name=first_name,
                                                           last_name=last_name)
        if details_exist:
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(
                    mob_ex.created_at))

            return HttpResponse("error")
        else:
            # saving values to databse
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name,
                                                              middle_name=middle_name,
                                                              county=countyObject, subcounty=subcountyObject,
                                                              ward=wardObject, sex=sex, dob=dob,
                                                              passport_number=passport_number,
                                                              phone_number=user_phone, email_address=email_address,
                                                              date_of_contact=date_of_contact, source=source,
                                                              nationality=nationality, drugs=drugs, nok=nextofkin,
                                                              nok_phone_num=nok_phone_number, cormobidity=comorbidity,
                                                              origin_country=origin_country,
                                                              place_of_diagnosis=place_of_diagnosis,
                                                              quarantine_site=qua_site, contact_uuid=contact_identifier,
                                                              updated_at=current_date, created_by=userObject,
                                                              updated_by=userObject, created_at=current_date)

            contact_save.save()

        # check if details have been saved
        if contact_save:
            # send sms to the patient for successful registration_form
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            # msg = "Thank you " + first_name + " for registering. You will be required to send your temperature details during this quarantine period of 14 days. Please download the self reporting app on this link: https://cutt.ly/AtbvdxD"
            msg = "Thank you " + first_name + " for registering on self quarantine. You will be required to send your daily temperature details during this quarantine period of 14 days. Ministry of Health"
            msg2 = first_name + ", for self reporting iPhone users and non-smart phone users, dial *299# to send daily details, for Android phone users, download the self reporting app on this link: http://bit.ly/jitenge_moh . Ministry of Health"

            # process first message
            pp = {"phone_no": phone_number, "message": msg}
            payload = json.dumps(pp)

            # process second message
            pp2 = {"phone_no": phone_number, "message": msg2}
            payload2 = json.dumps(pp2)
            # payload = "{\r\n   \"phone_no\": \"+254705255873\",\r\n   \"message\": \"TEST CORONA FROM EARS SYSTEM\"\r\n}"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            # send first message
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))
            # convert string response to a dictionary
            msg_resp = eval(response.text)
            print(msg_resp)

            # check if Success is in the Dictionary values
            success = 'Success' in msg_resp.values()
            print(success)

            if success:
                print("Successfully sent first sms")
                # send Second message
                response2 = requests.request("POST", url, headers=headers, data=payload2, verify=False)

                print(response2.text.encode('utf8'))

        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        qua_site = quarantine_sites.objects.all().filter(active=True).order_by('site_name')
        day = time.strftime("%Y-%m-%d")

        data = {'country': cntry, 'county': county, 'day': day, 'qua_site': qua_site}

        return render(request, 'veoc/quarantine_registration_form.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        qua_site = quarantine_sites.objects.all().filter(active=True).order_by('site_name')
        day = time.strftime("%Y-%m-%d")

        data = {'country': cntry, 'county': county, 'day': day, 'qua_site': qua_site}

        return render(request, 'veoc/quarantine_registration_form.html', data)


@login_required
def home_care_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        middle_name = request.POST.get('middle_name', '')
        last_name = request.POST.get('last_name', '')
        sex = request.POST.get('sex', '')
        dob = request.POST.get('dob', '')
        passport_number = request.POST.get('passport_number', '')
        phone_number = request.POST.get('phone_number', '')
        origin_country = request.POST.get('country', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        ward = request.POST.get('ward', '')
        place_of_diagnosis = request.POST.get('place_of_diagnosis', '')
        date_of_contact = request.POST.get('date_of_contact', '')
        nationality = request.POST.get('nationality', '')
        comorbidity = request.POST.get('comorbidity', '')
        drugs = request.POST.get('drugs', '')
        nextofkin = request.POST.get('nok', '')
        nok_phone_number = request.POST.get('nok_phone_num', '')

        if origin_country.lower() == "kenya":
            countyObject = organizational_units.objects.get(name=cnty)
            subcountyObject = organizational_units.objects.get(name=sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid=ward)
        else:
            countyObject = organizational_units.objects.get(organisationunitid=18)
            subcountyObject = organizational_units.objects.get(organisationunitid=18)
            wardObject = organizational_units.objects.get(organisationunitid=18)

        user_phone = "+254"
        # Remove spacing on the number
        mobile_number = phone_number.replace(" ", "")
        print(mobile_number)
        # check if the leading character is 0
        if str(mobile_number[0]) == "0":
            user_phone = user_phone + str(mobile_number[1:])
            print("number leading with 0")
        elif str(mobile_number[0]) == "+":
            user_phone = mobile_number
            print("Save phone number as it is")
        elif str(mobile_number[0:2]) == "25":
            user_phone = "+" + str(mobile_number[0:])
            print("Save phone number with appended +")
        else:
            user_phone = user_phone + str(mobile_number)
            print("number not leading with 0")

        current_date = timezone.now()
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        contact_save = ''
        source = "Web Homecare Module"
        contact_identifier = uuid.uuid4().hex
        # Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number=user_phone, first_name=first_name,
                                                           last_name=last_name)
        if details_exist:
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(
                    mob_ex.created_at))

            return HttpResponse("error")
        else:
            # saving values to databse
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name,
                                                              middle_name=middle_name,
                                                              county=countyObject, subcounty=subcountyObject,
                                                              ward=wardObject, sex=sex, dob=dob,
                                                              passport_number=passport_number,
                                                              phone_number=user_phone, date_of_contact=date_of_contact,
                                                              source=source,
                                                              nationality=nationality, drugs=drugs, nok=nextofkin,
                                                              nok_phone_num=nok_phone_number, cormobidity=comorbidity,
                                                              origin_country=origin_country,
                                                              place_of_diagnosis=place_of_diagnosis,
                                                              contact_uuid=contact_identifier,
                                                              updated_at=current_date, created_by=userObject,
                                                              updated_by=userObject, created_at=current_date)

            contact_save.save()
            trans_one = transaction.savepoint()

            patient_id = contact_save.pk
            print(patient_id)
            patientObject = quarantine_contacts.objects.get(pk=patient_id)
            # save contacts in the track_quarantine_contacts if data has been saved on the quarantine contacts
            if patient_id:
                try:
                    home_care_save = home_based_care.objects.create(patient_contacts=patientObject,
                                                                    health_care_worker=userObject,
                                                                    data_source=source, date_created=current_date)

                    home_care_save.save()
                except IntegrityError:
                    transaction.savepoint_rollback(trans_one)
                    return HttpResponse("error")

            else:
                print("data not saved in quarantine contactshome based care")

        # check if details have been saved
        if contact_save:
            # send sms to the patient for successful registration_form
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            # msg = "Thank you " + first_name + " for registering. You will be required to send your temperature details during this quarantine period of 14 days. Please download the self reporting app on this link: https://cutt.ly/AtbvdxD"
            msg = "Thank you " + first_name + " for registering on home isolation. You will be required to send your daily temperature details during this quarantine period of 14 days. Ministry of Health"
            msg2 = first_name + ", for self reporting iPhone users and non-smart phone users, dial *299# to send daily details, for Android phone users, download the self reporting app on this link: http://bit.ly/jitenge_moh . Ministry of Health"

            # process first message
            pp = {"phone_no": phone_number, "message": msg}
            payload = json.dumps(pp)

            # process second message
            pp2 = {"phone_no": phone_number, "message": msg2}
            payload2 = json.dumps(pp2)
            # payload = "{\r\n   \"phone_no\": \"+254705255873\",\r\n   \"message\": \"TEST CORONA FROM EARS SYSTEM\"\r\n}"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            # send first message
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))
            # convert string response to a dictionary
            msg_resp = eval(response.text)
            print(msg_resp)

            # check if Success is in the Dictionary values
            success = 'Success' in msg_resp.values()
            print(success)

            if success:
                print("Successfully sent first sms")
                # send Second message
                response2 = requests.request("POST", url, headers=headers, data=payload2, verify=False)

                print(response2.text.encode('utf8'))

        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        qua_site = quarantine_sites.objects.all().filter(active=True).order_by('site_name')
        day = time.strftime("%Y-%m-%d")

        data = {'country': cntry, 'county': county, 'day': day, 'qua_site': qua_site}

        return render(request, 'veoc/home_care_registration_form.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        qua_site = quarantine_sites.objects.all().filter(active=True).order_by('site_name')
        day = time.strftime("%Y-%m-%d")

        data = {'country': cntry, 'county': county, 'day': day, 'qua_site': qua_site}

        return render(request, 'veoc/home_care_registration_form.html', data)


@login_required
def truck_driver_profile(request, profileid):

    patient_contact_object = quarantine_contacts.objects.filter(id = profileid)
    print(patient_contact_object)

    lab_res = truck_quarantine_lab.objects.filter(patient_contacts = profileid)
    lab_res_count = truck_quarantine_lab.objects.filter(patient_contacts = profileid).count()

    # lab_data = truck_quarantine_lab.objects.get(pk=profileid).annotate(
    patient_details = truck_quarantine_contacts.objects.filter(patient_contacts = profileid).annotate(
            first_name=F("patient_contacts__first_name"),
            last_name=F("patient_contacts__last_name"),
            sex=F("patient_contacts__sex"),
            age=F("patient_contacts__dob"),
            passport_number=F("patient_contacts__passport_number"),
            phone_number=F("patient_contacts__phone_number"),
            nationality=F("patient_contacts__nationality"),
            origin_country=F("patient_contacts__origin_country"),
            quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
            source=F("patient_contacts__source"),
            date_of_contact=F("patient_contacts__date_of_contact"),
            created_by=F("patient_contacts__created_by_id__username"),
        )

    # print(patient_details)

    follow_up_details = quarantine_follow_up.objects.filter(patient_contacts = profileid).order_by('follow_up_day').annotate(
            first_name=F("patient_contacts__first_name"),
            last_name=F("patient_contacts__last_name"),
            sex=F("patient_contacts__sex"),
            age=F("patient_contacts__dob"),
            passport_number=F("patient_contacts__passport_number"),
            phone_number=F("patient_contacts__phone_number"),
            nationality=F("patient_contacts__nationality"),
            origin_country=F("patient_contacts__origin_country"),
            quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
            source=F("patient_contacts__source"),
            date_of_contact=F("patient_contacts__date_of_contact"),
            created_by=F("patient_contacts__created_by_id__username"),
        ).order_by('created_at')

    # print(follow_up_details)
    follow_up_details_count = quarantine_follow_up.objects.filter(patient_contacts = profileid).order_by('follow_up_day').count()

    lab_data = truck_quarantine_lab.objects.filter(patient_contacts = profileid).annotate(
            first_name=F("patient_contacts__first_name"),
            last_name=F("patient_contacts__last_name"),
            sex=F("patient_contacts__sex"),
            age=F("patient_contacts__dob"),
            passport_number=F("patient_contacts__passport_number"),
            phone_number=F("patient_contacts__phone_number"),
            nationality=F("patient_contacts__nationality"),
            origin_country=F("patient_contacts__origin_country"),
            date_of_contact=F("patient_contacts__date_of_contact"),
            # created_by=F("patient_contacts__created_by_id__username"),
        )

    lab_results = covid_results.objects.filter(patient_contacts = profileid)
    # print(lab_data)

    labs = testing_labs.objects.all()
    cntry = country.objects.all()
    lab_res_types = covid_results_classifications.objects.all().order_by('id')
    samp_types = covid_sample_types.objects.all().order_by('id')
    day = time.strftime("%Y-%m-%d")

    data = {'patient_contact_object': patient_contact_object, 'lab_data': lab_data, 'patient_details':patient_details, 'lab_res': lab_res, 'lab_results': lab_results,
            'lab_res_count':lab_res_count,  'labs': labs, 'lab_res_types':lab_res_types, 'samp_types':samp_types, 'day':day, 'country': cntry,
            'follow_up_details':follow_up_details, 'follow_up_details_count':follow_up_details_count, "pic": quarantine_contacts.objects.get(id=profileid)}


    return render(request, 'veoc/truck_driver_profile.html', data)


@login_required
def truck_driver_revisit(request):
    if request.method == 'POST':
        myid = request.POST.get('id', '')
        date_of_arrival = request.POST.get('date_of_arrival', '')
        border_name = request.POST.get('border_name', '')
        weighbridge_name = request.POST.get('weighbridge_name', '')
        cough = request.POST.get('cough', '')
        breathing_difficulty = request.POST.get('breathing_difficulty', '')
        fever = request.POST.get('fever', '')
        sample_taken = request.POST.get('sample_taken', '')
        sample_taken = request.POST.get('sample_taken', '')
        temperature = request.POST.get('sample_taken', '')

    return render(request, 'veoc/truck_quarantine_complete.html', data)


@login_required
def truck_driver_edit(request):
    if request.method == 'POST':

        myid = request.POST.get('id', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone', '')
        passport_number = request.POST.get('passport', '')
        v_reg = request.POST.get('v_reg', '')
        nextofkin = request.POST.get('nok', '')
        nok_phone_number = request.POST.get('nok_phone_num', '')

        # print(myid)
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        patient_contact_object = truck_quarantine_contacts.objects.filter(id=myid)
        p_contacts = ''

        for p_cont in patient_contact_object:
            p_contacts = p_cont.patient_contacts.id

        # print(p_contacts)
        # contact_object = quarantine_contacts.objects.get(pk = p_contacts)

        qua_edit = quarantine_contacts.objects.filter(pk=p_contacts).update(first_name=first_name, last_name=last_name,
                                                                            phone_number=phone_number,
                                                                            passport_number=passport_number,
                                                                            nok=nextofkin,
                                                                            nok_phone_num=nok_phone_number,
                                                                            created_by=userObject)

        truck_quarantine_contacts.objects.filter(patient_contacts=myid).update(vehicle_registration=v_reg)

        # print(qua_edit)

        if qua_edit:
            print("Saving success")
            return JsonResponse({'success': True})

        else:
            print("Saving error")
            return JsonResponse({'error': "error"})

    return HttpResponse("Hello from Edit!")


@login_required
def lab_certificate(request):
    if request.method == 'POST':
        lab_id = request.POST.get('lab_id', '')
        print(lab_id)

        cert_data = truck_quarantine_lab.objects.get(pk=lab_id)
        print(cert_data)

        serialized = serialize('json', cert_data)
        obj_list = json.loads(serialized)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")

        # return JsonResponse({'success':cert_data})


@login_required
def truck_driver_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        middle_name = request.POST.get('middle_name', '')
        last_name = request.POST.get('last_name', '')
        sex = request.POST.get('sex', '')
        dob = request.POST.get('dob', '')
        phone_number = request.POST.get('phone_number', '')
        passport_number = request.POST.get('passport_number', '')
        nationality = request.POST.get('nationality', '')
        origin_country = request.POST.get('country', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        ward = request.POST.get('ward', '')
        nextofkin = request.POST.get('nok', '')
        nok_phone_number = request.POST.get('nok_phone_num', '')
        village = request.POST.get('village', '')
        street = request.POST.get('street', '')
        weighbridge_name = request.POST.get('weighbridge_name', '')
        border_name = request.POST.get('border_name', '')
        date_of_contact = request.POST.get('date_of_arrival', '')
        cough = request.POST.get('cough', '')
        breathing_difficulty = request.POST.get('breathing_difficulty', '')
        fever = request.POST.get('fever', '')
        temp = request.POST.get('temperature', '')
        sample_taken = request.POST.get('sample_taken', '')
        comorbidity = request.POST.get('comorbidity', '')
        drugs = request.POST.get('drugs', '')
        company_name = request.POST.get('company_name', '')
        company_phone = request.POST.get('company_phone', '')
        company_address = request.POST.get('company_address', '')
        company_street = request.POST.get('company_street', '')
        company_building = request.POST.get('company_building', '')
        vehicle_registration = request.POST.get('vehicle_registration', '')
        hotel = request.POST.get('hotel_name', '')
        hotel_phone = request.POST.get('hotel_phone', '')
        hotel_town = request.POST.get('hotel_town', '')
        date_check_in = request.POST.get('date_check_in', '')
        date_check_out = request.POST.get('date_check_out', '')
        action_taken = request.POST.get('action_taken', '')
        language = request.POST.get('communication_language', '')
        if request.FILES:
            driver_image = request.FILES['photo']
        else:
            driver_image = ''

        if origin_country.lower() == "kenya":
            countyObject = organizational_units.objects.get(name=cnty)
            subcountyObject = organizational_units.objects.get(name=sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid=ward)
        else:
            countyObject = organizational_units.objects.get(organisationunitid=18)
            subcountyObject = organizational_units.objects.get(organisationunitid=18)
            wardObject = organizational_units.objects.get(organisationunitid=18)

        # country_code = country.objects.get(name = )
        user_phone = "+254"
        # Remove spacing on the number
        mobile_number = phone_number.replace(" ", "")
        print(mobile_number)
        # check if the leading character is 0
        if str(mobile_number[0]) == "0":
            user_phone = user_phone + str(mobile_number[1:])
            print("number leading with 0")
        elif str(mobile_number[0]) == "+":
            user_phone = mobile_number
            print("Save phone number as it is")
        elif str(mobile_number[0:2]) == "25":
            user_phone = "+" + str(mobile_number[0:])
            print("Save phone number with appended +")
        else:
            user_phone = user_phone + str(mobile_number)
            print("number not leading with 0")

        # get todays date
        # current_date = date.today().strftime('%Y-%m-%d')
        current_date = timezone.now()

        # get current user
        current_user = request.user
        # print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        weigh_site = weighbridge_sites.objects.get(weighbridge_name=weighbridge_name)
        bord_name = border_points.objects.get(border_name=border_name)
        site_name = ''
        quar_site = quarantine_sites.objects.filter(site_name="Country Border")
        for site in quar_site:
            site_name = site.id

        contact_save = ''
        source = "Truck Registration"
        # Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number=user_phone, first_name=first_name,
                                                           last_name=last_name,
                                                           date_of_contact__gte=date.today() - timedelta(days=14))
        if details_exist:
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(
                    mob_ex.created_at))

            return HttpResponse("error")
        else:
            quarantineObject = quarantine_sites.objects.get(pk=site_name)
            languageObject = translation_languages.objects.get(pk=language)
            contact_identifier = uuid.uuid4().hex
            # saving values to quarantine_contacts database first
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name, middle_name=middle_name,
                             county=countyObject, subcounty=subcountyObject, ward=wardObject, sex=sex, dob=dob, passport_number=passport_number,
                             phone_number=user_phone, date_of_contact=date_of_contact, communication_language=languageObject,
                             nationality=nationality, drugs=drugs, nok=nextofkin, nok_phone_num=nok_phone_number, cormobidity=comorbidity,
                             origin_country=origin_country, quarantine_site=quarantineObject, source=source, contact_uuid=contact_identifier,
                             updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

            contact_save.save()
            trans_one = transaction.savepoint()

            patient_id = contact_save.pk
            print(patient_id)
            # save contacts in the track_quarantine_contacts if data has been saved on the quarantine contacts
            if patient_id:
                try:
                    truck_save = truck_quarantine_contacts.objects.create(patient_contacts=contact_save, street=street, village=village,
                                    vehicle_registration=vehicle_registration,company_name=company_name, company_phone=company_phone,
                                    border_point=bord_name,company_physical_address=company_address,company_street=company_street,
                                    company_building=company_building,temperature=temp,weighbridge_facility=weigh_site, cough=cough,
                                    breathing_difficulty=breathing_difficulty, fever=fever, sample_taken=sample_taken,
                                    action_taken=action_taken, hotel=hotel,hotel_phone=hotel_phone,hotel_town=hotel_town,
                                    date_check_in=date_check_in,date_check_out=date_check_out,driver_image=driver_image)

                    truck_save.save()
                except IntegrityError:
                    transaction.savepoint_rollback(trans_one)
                    return HttpResponse("error")

            else:
                print("data not saved in truck quarantine contacts")

        # check if details have been saved
        if not contact_save:
            # send sms to the patient for successful registration_form
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = ''
            msg2 = ''
            print(language)
            if language == "1":
                # Language is english
                print("inside english")
                msg = "Thank you " + first_name + " for registering on self quarantine. You will be required to send your daily temperature details during this quarantine period of 14 days. Ministry of Health"
                msg2 = first_name + ", for self reporting iPhone users and non-smart phone users, dial *299# to send daily details, for Android phone users, download the self reporting app on this link: https://cutt.ly/jitenge_moh . Ministry of Health"
            elif language == "2":
                # language is Swahili
                msg = "Asante " + first_name + " kwa kujisajili. Unahitajika kuripoti dalili yako ya afya kila siku kwa siku 14. Wizara ya Afya."
                msg2 = first_name + ", ikiwa huna simu ya kidigitali ama una iPhone, bonyeza *299# kuripoti dalili ya afya. Watumizi wa simu aina ya Android, wanaweza kupakua Jitenge App kupitia https://cutt.ly/jitenge_moh.  Wizara ya Afya."
            elif language == "3":
                # language is French
                msg = "Merci " + first_name + " de votre inscription. Vous devrez envoyer vos détails de température quotidiens pendant cette periode d'isolation de 14 jours. Ministre de la Santé"
                msg2 = first_name + ", pour l'auto déclaration les utilisateurs de iphone et les utilisateurs de téléphone non intelligent, composent *299# d'envoyer détails du quotidien, pour les utilisateurs de téléphone intelligent telechargez l'application d'auto déclaration sur ce lien https://cutt.ly/jitenge_moh. Ministre de la santé."

            # process first message
            pp = {"phone_no": mobile_number, "message": msg}
            payload = json.dumps(pp)

            # process second message
            pp2 = {"phone_no": mobile_number, "message": msg2}
            payload2 = json.dumps(pp2)
            # payload = "{\r\n   \"phone_no\": \"+254705255873\",\r\n   \"message\": \"TEST CORONA FROM EARS SYSTEM\"\r\n}"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            # send first message
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            # print(response.text.encode('utf8'))
            # convert string response to a dictionary
            msg_resp = eval(response.text)
            # print(msg_resp)

            # check if Success is in the Dictionary values
            success = 'Success' in msg_resp.values()
            # print(success)

            if success:
                print("Successfully sent first sms")
                # send Second message
                response2 = requests.request("POST", url, headers=headers, data=payload2, verify=False)

                # print(response2.text.encode('utf8'))

        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        weigh_site = weighbridge_sites.objects.all().filter(active=True).order_by('weighbridge_name')
        b_points = border_points.objects.all().filter(active=True).order_by('border_name')
        language = translation_languages.objects.all()
        day = time.strftime("%Y-%m-%d")

        data = {'country': cntry, 'county': county, 'day': day, 'weigh_site': weigh_site, 'border_points': b_points,
                'language': language}

        return render(request, 'veoc/truck_driver_registration.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        weigh_site = weighbridge_sites.objects.all().filter(active=True).order_by('weighbridge_name')
        b_points = border_points.objects.all().filter(active=True).order_by('border_name')
        language = translation_languages.objects.all()
        day = time.strftime("%Y-%m-%d")

        qs = User.objects.filter(groups__name='National Watchers')
        print(qs.query)
        # for q in qs :
        #     val = q.

        data = {'country': cntry, 'county': county, 'day': day, 'weigh_site': weigh_site, 'border_points': b_points,
                'language': language}

        return render(request, 'veoc/truck_driver_registration.html', data)


@login_required
def truck_driver_register_new(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        middle_name = request.POST.get('middle_name', '')
        last_name = request.POST.get('last_name', '')
        sex = request.POST.get('sex', '')
        dob = request.POST.get('dob', '')
        phone_number = request.POST.get('phone_number', '')
        passport_number = request.POST.get('passport_number', '')
        nationality = request.POST.get('nationality', '')
        origin_country = request.POST.get('country', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        ward = request.POST.get('ward', '')
        nextofkin = request.POST.get('nok', '')
        nok_phone_number = request.POST.get('nok_phone_num', '')
        village = request.POST.get('village', '')
        street = request.POST.get('street', '')
        weighbridge_name = request.POST.get('weighbridge_name', '')
        border_name = request.POST.get('border_name', '')
        date_of_contact = request.POST.get('date_of_arrival', '')
        cough = request.POST.get('cough', '')
        breathing_difficulty = request.POST.get('breathing_difficulty', '')
        fever = request.POST.get('fever', '')
        temp = request.POST.get('temperature', '')
        sample_taken = request.POST.get('sample_taken', '')
        comorbidity = request.POST.get('comorbidity', '')
        drugs = request.POST.get('drugs', '')
        company_name = request.POST.get('company_name', '')
        company_phone = request.POST.get('company_phone', '')
        company_address = request.POST.get('company_address', '')
        company_street = request.POST.get('company_street', '')
        company_building = request.POST.get('company_building', '')
        vehicle_registration = request.POST.get('vehicle_registration', '')
        hotel = request.POST.get('hotel_name', '')
        hotel_phone = request.POST.get('hotel_phone', '')
        hotel_town = request.POST.get('hotel_town', '')
        date_check_in = request.POST.get('date_check_in', '')
        date_check_out = request.POST.get('date_check_out', '')
        action_taken = request.POST.get('action_taken', '')
        language = request.POST.get('communication_language', '')

        # values for lab tests
        # patient_contact = request.POST.get('id','')
        case_id = request.POST.get('case_id', '')
        type_of_case = request.POST.get('type_of_case', '')
        sample_no = request.POST.get('sample_no', '')
        travel_history = request.POST.get('travel_history', '')
        travel_from = request.POST.get('travel_from', '')
        contact_with_case = request.POST.get('contact_with_case', '')
        confirmed_case = request.POST.get('confirmed_case', '')
        have_symptoms = request.POST.get('have_symptoms', '')
        onset_symptoms = request.POST.get('onset_symptoms', '')
        date_specimen_collected = request.POST.get('date_specimen_collected', '')
        symptoms_shown = request.POST.get('symptoms_shown', '')
        speci_type = request.POST.get('specimen_type', '')
        lab_name = request.POST.get('lab_name', '')

        if request.FILES:
            driver_image = request.FILES['photo']
        else:
            driver_image = ''

        if origin_country.lower() == "kenya":
            countyObject = organizational_units.objects.get(name=cnty)
            subcountyObject = organizational_units.objects.get(name=sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid=ward)
        else:
            countyObject = organizational_units.objects.get(organisationunitid=18)
            subcountyObject = organizational_units.objects.get(organisationunitid=18)
            wardObject = organizational_units.objects.get(organisationunitid=18)

        # country_code = country.objects.get(name = )
        user_phone = "+254"
        # Remove spacing on the number
        mobile_number = phone_number.replace(" ", "")
        print(mobile_number)
        # check if the leading character is 0
        if str(mobile_number[0]) == "0":
            user_phone = user_phone + str(mobile_number[1:])
            print("number leading with 0")
        elif str(mobile_number[0]) == "+":
            user_phone = mobile_number
            print("Save phone number as it is")
        elif str(mobile_number[0:2]) == "25":
            user_phone = "+" + str(mobile_number[0:])
            print("Save phone number with appended +")
        else:
            user_phone = user_phone + str(mobile_number)
            print("number not leading with 0")

        # get todays date
        # current_date = date.today().strftime('%Y-%m-%d')
        current_date = timezone.now()

        # get current user
        current_user = request.user
        # print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        weigh_site = weighbridge_sites.objects.get(weighbridge_name=weighbridge_name)
        bord_name = border_points.objects.get(border_name=border_name)
        site_name = ''
        quar_site = quarantine_sites.objects.filter(site_name="Country Border")
        for site in quar_site:
            site_name = site.id

        contact_save = ''
        source = "Truck Registration"
        # Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number=user_phone, first_name=first_name,
                                                           last_name=last_name,
                                                           date_of_contact__gte=date.today() - timedelta(
                                                               days=14)).first()
        if details_exist:
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(
                    mob_ex.created_at))

            return HttpResponse("error")
        else:
            quarantineObject = quarantine_sites.objects.get(pk=site_name)
            languageObject = translation_languages.objects.get(pk=language)
            contact_identifier = uuid.uuid4().hex
            # saving values to quarantine_contacts database first
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name,
                                                              middle_name=middle_name,
                                                              county=countyObject, subcounty=subcountyObject,
                                                              ward=wardObject, sex=sex, dob=dob,
                                                              passport_number=passport_number,
                                                              phone_number=user_phone, date_of_contact=date_of_contact,
                                                              communication_language=languageObject,
                                                              nationality=nationality, drugs=drugs, nok=nextofkin,
                                                              nok_phone_num=nok_phone_number, cormobidity=comorbidity,
                                                              origin_country=origin_country,
                                                              quarantine_site=quarantineObject, source=source,
                                                              contact_uuid=contact_identifier,
                                                              updated_at=current_date, created_by=userObject,
                                                              updated_by=userObject, created_at=current_date)

            contact_save.save()
            trans_one = transaction.savepoint()

            patient_id = contact_save.pk
            print(patient_id)
            # check whether the patientObject has been set

            patientObject = truck_quarantine_contacts.objects.get(pk=patient_id)

            # save contacts in the track_quarantine_contacts if data has been saved on the quarantine contacts
            if patient_id:
                try:
                    truck_save = truck_quarantine_contacts.objects.create(patient_contacts=patientObject, street=street,
                                                                          village=village,
                                                                          vehicle_registration=vehicle_registration,
                                                                          company_name=company_name,
                                                                          company_phone=company_phone,
                                                                          border_point=bord_name,
                                                                          company_physical_address=company_address,
                                                                          company_street=company_street,
                                                                          company_building=company_building,
                                                                          temperature=temp,
                                                                          weighbridge_facility=weigh_site, cough=cough,
                                                                          breathing_difficulty=breathing_difficulty,
                                                                          fever=fever, sample_taken=sample_taken,
                                                                          action_taken=action_taken, hotel=hotel,
                                                                          hotel_phone=hotel_phone,
                                                                          hotel_town=hotel_town,
                                                                          date_check_in=date_check_in,
                                                                          date_check_out=date_check_out,
                                                                          driver_image=driver_image)

                    truck_save.save()
                except IntegrityError:
                    transaction.savepoint_rollback(trans_one)
                    return HttpResponse("error")

                # if patient id exists, save lab details to
                # patient_contact_object = truck_quarantine_contacts.objects.filter(id = contact_save.pk)
                labsObjects = testing_labs.objects.get(pk=lab_name).first()
                lab_res_typesObjects = covid_results_classifications.objects.get(pk=4).first()
                samp_typesObjects = covid_sample_types.objects.get(pk=speci_type).first()
                p_contacts = ''

                # for p_cont in patient_contact_object:
                #            p_contacts = p_cont.patient_contacts.id

                # print(p_contacts)
                contact_object = 275  # quarantine_contacts.objects.get(pk = contact_save.pk).first()

                lab_identifier = uuid.uuid4().hex
                # print(lab_identifier)
                print(contact_object);
                save_lab = truck_quarantine_lab.objects.create(patient_contacts=contact_object,
                                                               test_sample_uuid=lab_identifier,
                                                               case_identification_id=case_id,
                                                               sample_number=sample_no, travel_history=travel_history,
                                                               contact_with_case=contact_with_case,
                                                               confirmed_case_name=confirmed_case,
                                                               have_symptoms=have_symptoms,
                                                               onset_of_symptoms=onset_symptoms,
                                                               symptoms_shown=symptoms_shown, type_of_case=type_of_case,
                                                               date_specimen_collected=date_specimen_collected,
                                                               specimen_type=samp_typesObjects, lab=labsObjects,
                                                               travel_from=travel_from,
                                                               lab_results=lab_res_typesObjects,
                                                               date_lab_confirmation=current_date,
                                                               created_at=current_date,
                                                               updated_at=current_date, created_by=userObject,
                                                               updated_by=userObject, processed=0,
                                                               sample_identifier="T00000")

                lab_id = save_lab.pk
                print(lab_id)
                sam_identifier = 'T'

                if len(str(lab_id)) == 1:
                    sam_identifier = "T000" + str(lab_id)
                elif len(str(lab_id)) == 2:
                    sam_identifier = "T00" + str(lab_id)
                elif len(str(lab_id)) == 3:
                    sam_identifier = "T0" + str(lab_id)
                elif len(str(lab_id)) == 4:
                    sam_identifier = "T" + str(lab_id)
                else:
                    sam_identifier = sam_identifier + str(lab_id)

                print(sam_identifier)

                # update the sample identifier
                truck_quarantine_lab.objects.filter(pk=lab_id).update(sample_identifier=sam_identifier)

                if save_lab:
                    print("Saving success")
                    return JsonResponse({'success': True, 'sample_identifier': sam_identifier})

                else:
                    print("Saving error")
                    return JsonResponse({'error': "error"})


            # return HttpResponse("Hello from Laboratory!")

            else:
                print("data not saved in truck quarantine contacts")

        # check if details have been saved
        if not contact_save:
            # send sms to the patient for successful registration_form
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = ''
            msg2 = ''
            print(language)
            if language == "1":
                # Language is english
                print("inside english")
                msg = "Thank you " + first_name + " for registering on self quarantine. You will be required to send your daily temperature details during this quarantine period of 14 days. Ministry of Health"
                msg2 = first_name + ", for self reporting iPhone users and non-smart phone users, dial *299# to send daily details, for Android phone users, download the self reporting app on this link: https://cutt.ly/jitenge_moh . Ministry of Health"
            elif language == "2":
                # language is Swahili
                msg = "Asante " + first_name + " kwa kujisajili. Unahitajika kuripoti dalili yako ya afya kila siku kwa siku 14. Wizara ya Afya."
                msg2 = first_name + ", ikiwa huna simu ya kidigitali ama una iPhone, bonyeza *299# kuripoti dalili ya afya. Watumizi wa simu aina ya Android, wanaweza kupakua Jitenge App kupitia https://cutt.ly/jitenge_moh.  Wizara ya Afya."
            elif language == "3":
                # language is French
                msg = "Merci " + first_name + " de votre inscription. Vous devrez envoyer vos détails de température quotidiens pendant cette periode d'isolation de 14 jours. Ministre de la Santé"
                msg2 = first_name + ", pour l'auto déclaration les utilisateurs de iphone et les utilisateurs de téléphone non intelligent, composent *299# d'envoyer détails du quotidien, pour les utilisateurs de téléphone intelligent telechargez l'application d'auto déclaration sur ce lien https://cutt.ly/jitenge_moh. Ministre de la santé."

            # process first message
            pp = {"phone_no": mobile_number, "message": msg}
            payload = json.dumps(pp)

            # process second message
            pp2 = {"phone_no": mobile_number, "message": msg2}
            payload2 = json.dumps(pp2)
            # payload = "{\r\n   \"phone_no\": \"+254705255873\",\r\n   \"message\": \"TEST CORONA FROM EARS SYSTEM\"\r\n}"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            # send first message
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            # print(response.text.encode('utf8'))
            # convert string response to a dictionary
            msg_resp = eval(response.text)
            # print(msg_resp)

            # check if Success is in the Dictionary values
            success = 'Success' in msg_resp.values()
            # print(success)

            if success:
                print("Successfully sent first sms")
                # send Second message
                response2 = requests.request("POST", url, headers=headers, data=payload2, verify=False)

                # print(response2.text.encode('utf8'))

        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        weigh_site = weighbridge_sites.objects.all().filter(active=True).order_by('weighbridge_name')
        b_points = border_points.objects.all().filter(active=True).order_by('border_name')
        language = translation_languages.objects.all()
        day = time.strftime("%Y-%m-%d")
        samp_types = covid_sample_types.objects.all().order_by('id')
        labs = testing_labs.objects.all()

        data = {'country': cntry, 'county': county, 'day': day, 'weigh_site': weigh_site, 'border_points': b_points,
                'language': language, 'labs': labs, 'samp_types': samp_types}

        return render(request, 'veoc/truck_driver_registration_tabs.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
        weigh_site = weighbridge_sites.objects.all().filter(active=True).order_by('weighbridge_name')
        b_points = border_points.objects.all().filter(active=True).order_by('border_name')
        language = translation_languages.objects.all()
        day = time.strftime("%Y-%m-%d")
        samp_types = covid_sample_types.objects.all().order_by('id')
        labs = testing_labs.objects.all()

        qs = User.objects.filter(groups__name='National Watchers')
        print(qs.query)
        # for q in qs :
        #     val = q.

        data = {'country': cntry, 'county': county, 'day': day, 'weigh_site': weigh_site, 'border_points': b_points,
                'language': language, 'labs': labs, 'samp_types': samp_types}

        return render(request, 'veoc/truck_driver_registration_tabs.html', data)


@login_required
def truck_driver_lab_test(request):
    if request.method == 'POST':
        patient_contact = request.POST.get('id', '')
        case_id = request.POST.get('case_id', '')
        type_of_case = request.POST.get('type_of_case', '')
        sample_no = request.POST.get('sample_no', '')
        travel_history = request.POST.get('travel_history', '')
        travel_from = request.POST.get('travel_from', '')
        contact_with_case = request.POST.get('contact_with_case', '')
        confirmed_case = request.POST.get('confirmed_case', '')
        have_symptoms = request.POST.get('have_symptoms', '')
        onset_symptoms = request.POST.get('onset_symptoms', '')
        date_specimen_collected = request.POST.get('date_specimen_collected', '')
        symptoms_shown = request.POST.get('symptoms_shown', '')
        speci_type = request.POST.get('specimen_type', '')
        lab_name = request.POST.get('lab_name', '')

        # get todays date
        current_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        # print(current_date)

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        patient_contact_object = truck_quarantine_contacts.objects.filter(id=patient_contact)
        labsObjects = testing_labs.objects.get(pk=lab_name)
        lab_res_typesObjects = covid_results_classifications.objects.get(pk=4)
        samp_typesObjects = covid_sample_types.objects.get(pk=speci_type)
        p_contacts = ''

        for p_cont in patient_contact_object:
            p_contacts = p_cont.patient_contacts.id

        # print(p_contacts)
        contact_object = quarantine_contacts.objects.get(pk=p_contacts)

        lab_identifier = uuid.uuid4().hex
        # print(lab_identifier)

        # save_lab_details
        save_lab = truck_quarantine_lab.objects.create(patient_contacts=contact_object, test_sample_uuid=lab_identifier,
                                                       case_identification_id=case_id,
                                                       sample_number=sample_no, travel_history=travel_history,
                                                       contact_with_case=contact_with_case,
                                                       confirmed_case_name=confirmed_case,
                                                       have_symptoms=have_symptoms, onset_of_symptoms=onset_symptoms,
                                                       symptoms_shown=symptoms_shown, type_of_case=type_of_case,
                                                       date_specimen_collected=date_specimen_collected,
                                                       specimen_type=samp_typesObjects, lab=labsObjects,
                                                       travel_from=travel_from,
                                                       lab_results=lab_res_typesObjects,
                                                       date_lab_confirmation=current_date, created_at=current_date,
                                                       updated_at=current_date, created_by=userObject,
                                                       updated_by=userObject, processed=0, sample_identifier="T00000")

        lab_id = save_lab.pk
        print(lab_id)
        sam_identifier = 'T'

        if len(str(lab_id)) == 1:
            sam_identifier = "T000" + str(lab_id)
        elif len(str(lab_id)) == 2:
            sam_identifier = "T00" + str(lab_id)
        elif len(str(lab_id)) == 3:
            sam_identifier = "T0" + str(lab_id)
        elif len(str(lab_id)) == 4:
            sam_identifier = "T" + str(lab_id)
        else:
            sam_identifier = sam_identifier + str(lab_id)

        print(sam_identifier)

        # update the sample identifier
        truck_quarantine_lab.objects.filter(pk=lab_id).update(sample_identifier=sam_identifier)

        if save_lab:
            print("Saving success")
            return JsonResponse({'success': True, 'sample_identifier': sam_identifier})

        else:
            print("Saving error")
            return JsonResponse({'error': "error"})

    return HttpResponse("Hello from Laboratory!")


@login_required
def disease_view(request, id=None):
    instance = get_object_or_404(disease, id=id)

    context = {
        "disease_instance": instance,
    }
    return render(request, "veoc/disease_view.html", context)


@login_required
def event_view(request, id=None):
    instance = get_object_or_404(event, id=id)

    context = {
        "event_instance": instance,
    }
    return render(request, "veoc/event_view.html", context)


@login_required
def call_log_view(request, id=None):
    instance = get_object_or_404(call_log, id=id)

    context = {
        "call_log_instance": instance,
    }
    return render(request, "veoc/call_log_view.html", context)


@login_required
def event_register(request):
    if request.method == 'POST':
        eventtype = request.POST.get('eventType', '')
        datasource = request.POST.get('dataSource', '')
        region = request.POST.get('region', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        ward = request.POST.get('ward', '')
        status = request.POST.get('status', '')
        datereported = request.POST.get('dateReported', '')
        cases = request.POST.get('cases', '')
        deaths = request.POST.get('deaths', '')
        descriptn = request.POST.get('description', '')
        actiontaken = request.POST.get('actionTaken', '')
        significant = request.POST.get('callSignificant', '')

        # check significant eventType
        significant_events = ""
        if significant == 'on':
            significant_events = "t"
        else:
            significant_events = "f"

        if region == "Kenya":
            countyObject = organizational_units.objects.get(name=cnty)
            subcountyObject = organizational_units.objects.get(name=sub_cnty)
            wardObject = organizational_units.objects.get(organisationunitid=ward)
        else:
            countyObject = organizational_units.objects.get(organisationunitid=18)
            subcountyObject = organizational_units.objects.get(organisationunitid=18)
            wardObject = organizational_units.objects.get(organisationunitid=18)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        eventObject = dhis_event_type.objects.get(name=eventtype)
        datasourceObject = data_source.objects.get(source_description=datasource)
        regionObject = reporting_region.objects.get(region_description=region)
        incidentObject = incident_status.objects.get(status_description=status)

        # saving values to databse
        event.objects.create(event_type=eventObject, incident_status=incidentObject, county=countyObject,
                             subcounty=subcountyObject, data_source=datasourceObject,
                             ward=wardObject, reporting_region=regionObject, date_reported=datereported, cases=cases,
                             deaths=deaths, remarks=descriptn, action_taken=actiontaken,
                             significant_event=significant_events, updated_at=current_date, created_by=userObject,
                             updated_by=userObject, created_at=current_date)

        # check if the incident is within kenya to save in DHIS2
        if region == "Kenya":
            # check if the reported case is confirmed to save in dhis2 data tables
            if status == 'Confirmed':
                # create current week/year number
                dt = timezone.now()
                wk_val = dt.isocalendar()[1]
                yr_val = dt.replace(year=dt.year)
                final_year = yr_val.year
                weeknum = str(final_year) + str(wk_val)
                print(weeknum)
                # saving data into dhis2 data dataTables
                dhis_reported_events.objects.create(org_unit_id=wardObject, program='hH7eq688OJT',
                                                    event_type=eventObject, eventDate=current_date,
                                                    stored_by='eoc_user', period=weeknum, status='COMPLETED')
                # get latest key of data just entered
                event_id = dhis_reported_events.objects.order_by('-id')[0]
                event_pk = event_id.id
                rep_eve_Object = dhis_reported_events.objects.get(pk=event_pk)
                dataElementObject1 = dhis_event_data_elements.objects.get(pk='1')
                dataElementObject2 = dhis_event_data_elements.objects.get(pk='2')
                dataElementObject3 = dhis_event_data_elements.objects.get(pk='3')
                print(dataElementObject3)

                dhis_event_data_values.objects.create(dhis_reported_event_id=rep_eve_Object,
                                                      data_element_id=dataElementObject1, data_value=cases)
                dhis_event_data_values.objects.create(dhis_reported_event_id=rep_eve_Object,
                                                      data_element_id=dataElementObject2, data_value=deaths)
                dhis_event_data_values.objects.create(dhis_reported_event_id=rep_eve_Object,
                                                      data_element_id=dataElementObject3, data_value=eventtype)
            else:
                print('unconfirmed incident - not saved in dhis2 data elements')
        else:
            print('global incident case - not saved in dhis2 data elements')

    regions = reporting_region.objects.all()
    status = incident_status.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    events = dhis_event_type.objects.all().order_by('name')
    datasource = data_source.objects.all().order_by('source_description')
    day = time.strftime("%Y-%m-%d")

    data = {'events': events, 'datasource': datasource, 'regions': regions, 'incident_status': status, 'county': county,
            'day': day}

    return render(request, 'veoc/events_form.html', data)


@login_required
def feedback_create(request):
    if request.method == 'POST':
        module_type = request.POST.get('module_type', '')
        date_created = request.POST.get('date_created', '')
        challenge = request.POST.get('challenge', '')
        recommendation = request.POST.get('recommendation', '')

        cur_user = request.user.username
        usert = User.objects.get(username=cur_user)

        day = time.strftime("%Y-%m-%d")

        insertdata = Feedback(user=usert, module_type=module_type, date_created=date_created, challenge=challenge,
                              recommendation=recommendation)
        insertdata.save()
        success = "Feedback submitted successfully"

        return render(request, "veoc/feedback_form.html", {"success": success, 'day': day})

    else:
        success = ""
        day = time.strftime("%Y-%m-%d")

        return render(request, "veoc/feedback_form.html", {"success": success, 'day': day})


@login_required
def feedback_report(request):
    return render(request, 'veoc/feedback_report.html')


def unrelated_call_report(request):
    # check if there is an edit on an entry and save
    if request.method == 'POST':
        id = request.POST.get('id', '')
        incident_stat = request.POST.get('status_name', '')
        descrp = request.POST.get('description_name', '')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        call_log.objects.filter(pk=id).update(incident_status=incident_stat, call_description=descrp,
                                              updated_by=userObject, updated_at=current_date)

    call_count = call_log.objects.all().filter(call_category=3).count()
    call_incidents = call_incident_category.objects.all()
    call_unrelated = unrelated_calls_category.objects.all()
    call_status_desr = incident_status.objects.all()
    call_logs = call_log.objects.all().filter(call_category=3)

    call_cat_incident = []
    for calls in call_logs:
        _call_category = calls.call_category.id
        if _call_category == 3:
            calls_disease = calls.call_category_incident
            call_cat_disease = unrelated_calls_category.objects.filter(id=calls_disease).values_list('description',
                                                                                                     flat=True).first()
            call_cat_incident.append(call_cat_disease)
        else:
            print('Call category not in DB')

    my_list_data = zip(call_logs, call_cat_incident)

    values = {'call_logs': my_list_data, 'contact_type_vals': contacts, 'call_count': call_count,
              'call_incidents': call_incidents,
              'call_incidents': call_incidents, 'status_descriptions': call_status_desr}

    return render(request, 'veoc/unrelated_report.html', values)


@login_required
def filter_unrelated_call_report(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        call_count = call_log.objects.all().filter(call_category=3).filter(
            date_reported__range=[date_from, date_to]).count()
        call_incidents = call_incident_category.objects.all()
        call_unrelated = unrelated_calls_category.objects.all()
        call_status_desr = incident_status.objects.all()
        call_logs = call_log.objects.all().filter(call_category=3).filter(date_reported__range=[date_from, date_to])
        day_from = date_from
        day_to = date_to

        call_cat_incident = []
        for calls in call_logs:
            _call_category = calls.call_category.id
            if _call_category == 3:
                calls_disease = calls.call_category_incident
                call_cat_disease = unrelated_calls_category.objects.filter(id=calls_disease).values_list('description',
                                                                                                         flat=True).first()
                call_cat_incident.append(call_cat_disease)
            else:
                print('Call category not in DB')

        my_list_data = zip(call_logs, call_cat_incident)

        values = {'call_logs': my_list_data, 'contact_type_vals': contacts, 'call_count': call_count,
                  'call_incidents': call_incidents,
                  'call_incidents': call_incidents, 'status_descriptions': call_status_desr, 'day_from': day_from,
                  'day_to': day_to}

        return render(request, 'veoc/unrelated_report.html', values)


@login_required
def disease_report(request):
    if request.method == 'POST':
        id = request.POST.get('id', '')
        incident_stat = request.POST.get('status_name', '')
        remarks = request.POST.get('remarks', '')
        action = request.POST.get('action', '')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        disease.objects.filter(pk=id).update(incident_status=incident_stat, remarks=remarks, action_taken=action,
                                             updated_by=userObject, updated_at=current_date)

    _reported_diseases_count = disease.objects.all().count()
    disease_status_desr = incident_status.objects.all()
    _disease = disease.objects.all()  # filter(date_reported__gte = date.today()- timedelta(days=30))

    diseas = {'reported_diseases_count': _reported_diseases_count, 'disease_vals': _disease,
              'status_descriptions': disease_status_desr}

    return render(request, 'veoc/disease_report.html', diseas)


@login_required
def infectious_disease_report(request):
    reported_infect_diseases_count = infectious_disease.objects.all().count()
    infect_disease = infectious_disease.objects.all()

    diseas = {'reported_infect_diseases_count': reported_infect_diseases_count,
              'infect_disease': infect_disease}

    return render(request, 'veoc/infectious_diseases.html', diseas)


@login_required
def filter_disease_report(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        day_from = date_from
        day_to = date_to
        _reported_diseases_count = disease.objects.all().filter(date_reported__range=[date_from, date_to]).count()
        disease_status_desr = incident_status.objects.all()
        _disease = disease.objects.all().filter(
            date_reported__range=[date_from, date_to])  # filter(date_reported__gte = date.today()- timedelta(days=30))

        diseas = {'reported_diseases_count': _reported_diseases_count, 'disease_vals': _disease,
                  'status_descriptions': disease_status_desr, 'day_from': day_from, 'day_to': day_to}

        return render(request, 'veoc/disease_report.html', diseas)


@login_required
def events_report(request):
    if request.method == 'POST':
        id = request.POST.get('id', '')
        incident_stat = request.POST.get('status_name', '')
        remarks = request.POST.get('remarks', '')
        action = request.POST.get('action', '')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        event.objects.filter(pk=id).update(incident_status=incident_stat, remarks=remarks, action_taken=action,
                                           updated_by=userObject, updated_at=current_date)

    reported_events_count = event.objects.all().count()
    disease_status_desr = incident_status.objects.all()
    reported_events = event.objects.all()

    events = {'reported_events_count': reported_events_count,
              'event_vals': reported_events, 'status_descriptions': disease_status_desr}

    return render(request, 'veoc/events_report.html', events)


def filter_events_report(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')
        day_from = date_from
        day_to = date_to

        reported_events_count = event.objects.all().filter(date_reported__range=[date_from, date_to]).count()
        disease_status_desr = incident_status.objects.all()
        reported_events = event.objects.all().filter(date_reported__range=[date_from, date_to])

        events = {'reported_events_count': reported_events_count, 'event_vals': reported_events,
                  'status_descriptions': disease_status_desr, 'day_from': day_from, 'day_to': day_to}

        return render(request, 'veoc/events_report.html', events)


@login_required
def daily_reports(request):
    if request.method == 'POST':
        datefilter = request.POST.get('date_reported', '')

        # Get significant IncidentStatusSerializer
        sign_calls = call_log.objects.all().filter(significant='True').filter(date_reported=datefilter)
        sign_diseases = disease.objects.all().filter(significant='True').filter(date_reported=datefilter)
        sign_events = event.objects.all().filter(significant_event='True').filter(date_reported=datefilter)

        # Check id significants are all empty
        if (sign_calls == "") and (sign_diseases == "") and sign_events == "":
            significant_events_none = "None"
        else:
            significant_events_none = ""

        # Getting diseases and events reported within Kenya
        kenya_disease = disease.objects.all().filter(reporting_region=4).filter(date_reported=datefilter)
        kenya_events = event.objects.all().filter(reporting_region=4).filter(date_reported=datefilter)

        # Getting diseases and events reported within East Africa
        ea_disease = disease.objects.all().filter(reporting_region=3).filter(date_reported=datefilter)
        ea_events = event.objects.all().filter(reporting_region=3).filter(date_reported=datefilter)

        # Getting diseases and events reported within Africa
        africa_disease = disease.objects.all().filter(reporting_region=2).filter(date_reported=datefilter)
        africa_events = event.objects.all().filter(reporting_region=2).filter(date_reported=datefilter)

        # Getting diseases and events reported Gloablly
        global_disease = disease.objects.all().filter(reporting_region=1).filter(date_reported=datefilter)
        global_events = event.objects.all().filter(reporting_region=1).filter(date_reported=datefilter)

        # getting dhis2 data from eoc
        dhis_diseases = dhis_reported_diseases.objects.all().filter(eventDate=datefilter)
        dhis_events = dhis_reported_events.objects.all().filter(eventDate=datefilter)

        # call logs databse
        # daily_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=2).filter(date_reported=datefilter).count()
        # daily_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(date_reported=datefilter).count()
        # daily_enquiry = Call_flashback_logs_count + Unrelated_call_logs_count
        # daily_total_calls = daily_conf_call_log_count + daily_rum_call_log_count + daily_enquiry

        disease_types = dhis_disease_type.objects.all()
        # watchers = mytimetable.objects.all().filter(from_date__lte = datefilter, to_date__gte = datefilter)

        data = {'date_filter': datefilter, 'significant_calls': sign_calls, 'significant_diseases': sign_diseases,
                'significant_events': sign_events, 'significant_events_none': significant_events_none,
                'kenya_disease': kenya_disease,
                'kenya_events': kenya_events, 'ea_disease': ea_disease, 'ea_events': ea_events,
                'africa_disease': africa_disease,
                'africa_events': africa_events, 'global_disease': global_disease, 'global_events': global_events,
                'dhis_diseases': dhis_diseases,
                'dhis_events': dhis_events}

        return render(request, "veoc/generate_pdf.html", data)

    else:
        day = time.strftime("%Y-%m-%d")
        return render(request, 'veoc/generate_pdf.html', {'day': day})


@login_required
def quarantine_site_data(request):
    # covid-19 line graph quarantine sites_count
    qua_sites_count = quarantine_sites.objects.all().count()
    qua_sites = quarantine_sites.objects.all().order_by('site_name')
    qua_site_data = {}
    # quarantine_site_array = {}
    for qua_site in qua_sites:
        quarantine_site_array = myDict()

        qua_completed_contacts = quarantine_contacts.objects.filter(quarantine_site_id=qua_site.id).filter(
            created_at__gte=date.today() - timedelta(days=14)).count()
        qua_ongoing_contacts = quarantine_contacts.objects.filter(quarantine_site_id=qua_site.id).filter(
            created_at__lte=date.today() - timedelta(days=14)).count()
        qua_total_contacts = quarantine_contacts.objects.filter(quarantine_site_id=qua_site.id).count()

        # quarantine_site_array.add('site_name', qua_site.site_name)
        quarantine_site_array.add('status', qua_site.active)
        quarantine_site_array.add('completed_cases', qua_completed_contacts)
        quarantine_site_array.add('ongoing_cases', qua_ongoing_contacts)
        quarantine_site_array.add('total_cases', qua_total_contacts)

        qua_site_data[qua_site.site_name] = quarantine_site_array

    print(qua_site_data)
    qua_list_data = zip(qua_site_data)

    data_values = {'quarantine_data_count': qua_sites_count,
                   'quarantine_site_array': qua_list_data}

    return render(request, 'veoc/quarantine_site_data.html', {"data": data_values})


@login_required
def quarantine_list(request):
    global data

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_level = grp
    print(user_level)

    if request.method == 'POST':
        q_site = request.POST.get('quarantine_site', '')
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        cntry = country.objects.all()
        if q_site:
            day = time.strftime("%Y-%m-%d")
            date_to = day
            date_from = day
            if (user_level == 1 or user_level == 2):
                # pull data whose quarantine site id is equal to q_site_name
                print("inside National")
                q_data = quarantine_contacts.objects.filter(quarantine_site=q_site).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(quarantine_site=q_site).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.exclude(site_name='Country Border')
            elif (user_level == 3 or user_level == 5):
                user_county_id = u.persons.county_id
                print(user_county_id)
                # pull data whose quarantine site id is equal to q_site_name
                q_data = quarantine_contacts.objects.filter(quarantine_site=q_site).filter(
                    county_id=user_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(
                    source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(quarantine_site=q_site).filter(
                    county=user_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.all().filter(county=user_county_id).order_by('site_name')
            elif (user_level == 4 or user_level == 6):
                user_sub_county_id = u.persons.sub_county_id
                print(user_sub_county_id)
                # pull data whose quarantine site id is equal to q_site_name
                q_data = quarantine_contacts.objects.filter(quarantine_site=q_site).filter(
                    subcounty_id=user_sub_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(
                    source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(quarantine_site=q_site).filter(
                    subcounty_id=user_sub_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.all().filter(subcounty_id=user_sub_county_id).order_by(
                    'site_name')
            elif (user_level == 7):
                q_data = quarantine_contacts.objects.filter(quarantine_site=q_site).filter(cormobidity="1").exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(quarantine_site=q_site).filter(
                    cormobidity="1").exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.all().filter(active=False).order_by('site_name')
            else:
                q_data = quarantine_contacts.objects.filter(quarantine_site=q_site).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(quarantine_site=q_site).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.filter(site_name=user_access_level).order_by('site_name')
        else:
            if (user_level == 1 or user_level == 2):
                # pull data whose quarantine site id is equal to q_site_name
                print("inside National")
                q_data = quarantine_contacts.objects.filter(date_of_contact__gte=date_from,
                                                            date_of_contact__lte=date_to).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(date_of_contact__gte=date_from,
                                                                  date_of_contact__lte=date_to).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.exclude(site_name='Country Border')
            elif (user_level == 3 or user_level == 5):
                user_county_id = u.persons.county_id
                print(user_county_id)
                # pull data whose quarantine site id is equal to q_site_name
                q_data = quarantine_contacts.objects.filter(date_of_contact__gte=date_from,
                                                            date_of_contact__lte=date_to).filter(
                    county_id=user_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(
                    source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(date_of_contact__gte=date_from,
                                                                  date_of_contact__lte=date_to).filter(
                    county=user_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.filter(county=user_county_id).order_by('site_name')
            elif (user_level == 4 or user_level == 6):
                user_sub_county_id = u.persons.sub_county_id
                print(user_sub_county_id)
                # pull data whose quarantine site id is equal to q_site_name
                q_data = quarantine_contacts.objects.filter(date_created__gte=date_from,
                                                            date_created__lte=date_to).filter(
                    subcounty_id=user_sub_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(
                    source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(date_created__gte=date_from,
                                                                  date_created__lte=date_to).filter(
                    subcounty_id=user_sub_county_id).exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.filter(subcounty_id=user_sub_county_id).order_by('site_name')
            elif (user_level == 7):
                q_data = quarantine_contacts.objects.filter(date_created__gte=date_from,
                                                            date_created__lte=date_to).filter(cormobidity="1").exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(date_created__gte=date_from,
                                                                  date_created__lte=date_to).filter(
                    cormobidity="1").exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.filter(active=False).order_by('site_name')
            else:
                q_data = quarantine_contacts.objects.filter(date_created__gte=date_from,
                                                            date_created__lte=date_to).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.filter(date_created__gte=date_from,
                                                                  date_created__lte=date_to).exclude(
                    source='Jitenge Homecare Module').exclude(source='Truck Registration').exclude(
                    source='Web Homecare Module').exclude(source='RECDTS').count()
                quar_sites = quarantine_sites.objects.filter(site_name=user_access_level).order_by('site_name')
        paginator = Paginator(q_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        data = {'quarantine_data': q_data, 'quarantine_data_count': q_data_count, 'quar_sites': quar_sites,
                'country': cntry, 'start_day': date_from, 'end_day': date_to, 'page_obj': page_obj}
    else:
        if (user_level == 1 or user_level == 2):
            print("inside National")
            q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').order_by(
                '-date_of_contact')
            q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').count()
            quar_sites = quarantine_sites.objects.exclude(site_name='Country Border').order_by('site_name')
        elif (user_level == 3 or user_level == 5):
            print("inside County")
            user_county_id = u.persons.county_id
            print(user_county_id)
            q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                county_id=user_county_id).order_by('-date_of_contact')
            q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                county_id=user_county_id).count()
            quar_sites = quarantine_sites.objects.exclude(site_name='Country Border').filter(
                county_id=user_county_id).order_by('site_name')
        elif (user_level == 4 or user_level == 6):
            print("inside SubCounty")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                subcounty_id=user_sub_county_id).order_by('-date_of_contact')
            q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                subcounty_id=user_sub_county_id).count()
            quar_sites = quarantine_sites.objects.exclude(site_name='Country Border').filter(
                subcounty_id=user_sub_county_id).order_by('site_name')
        elif (user_level == 7):
            print("inside Border")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                cormobidity="1").order_by('-date_of_contact')
            q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                cormobidity="1").count()
            quar_sites = quarantine_sites.objects.all().filter(active=False).order_by('site_name')
        else:
            print("inside Facility")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                subcounty_id=user_sub_county_id).order_by('-date_of_contact')
            q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                source='Truck Registration').exclude(source='Web Homecare Module').exclude(source='RECDTS').filter(
                subcounty_id=user_sub_county_id).count()
            quar_sites = quarantine_sites.objects.filter(site_name=user_access_level).order_by('site_name')

        # paginator = Paginator(q_data, q_data_count)
        #
        # page = request.GET.get('page')
        # quarantine_data = paginator.get_page(page)
        cntry = country.objects.all()
        day = time.strftime("%Y-%m-%d")
        paginator = Paginator(q_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        data = {'quarantine_data': q_data, 'quarantine_data_count': q_data_count, 'quar_sites': quar_sites,
                'country': cntry, 'start_day': day, 'end_day': day, 'page_obj': page_obj}

    return render(request, 'veoc/quarantine_list.html', data)


@login_required
def home_care_list(request):
    global data

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_level = grp
    print(user_level)

    if request.method == 'POST':
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        if (user_level == 1 or user_level == 2):
            print("inside National filter")
            q_data = home_based_care.objects.filter(date_created__gte=date_from, date_created__lte=date_to).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(date_created__gte=date_from,
                                                          date_created__lte=date_to).count()
        elif (user_level == 3 or user_level == 5):
            print("inside County")
            user_county_id = u.persons.county_id
            print(user_county_id)
            q_data = home_based_care.objects.filter(patient_contacts__county_id=user_county_id).filter(
                date_created__gte=date_from, date_created__lte=date_to).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__county_id=user_county_id).filter(
                date_created__gte=date_from, date_created__lte=date_to).count()
        elif (user_level == 4 or user_level == 6):
            print("inside SubCounty")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            q_data = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                date_created__gte=date_from, date_created__lte=date_to).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                origin_country=F("patient_contacts__origin_country"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                date_created__gte=date_from, date_created__lte=date_to).count()
        elif (user_level == 7):
            print("inside Border")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            q_data = home_based_care.objects.filter(date_created__gte=date_from, date_created__lte=date_to).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__cormobidity="1").count()
        else:
            print("inside Facility")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            q_data = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                patient_contacts__created_by=current_user.id).filter(date_created__gte=date_from,
                                                                     date_created__lte=date_to).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).count()

        # day = time.strftime("%Y-%m-%d")
        cntry = country.objects.all()

        paginator = Paginator(q_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = {'home_care_data': q_data, 'home_care_data_count': q_data_count, 'country': cntry,
                'start_day': date_from, 'end_day': date_to, 'page_obj': page_obj}
    else:
        if (user_level == 1 or user_level == 2):
            print("inside National")
            print(current_user.id)
            q_data = home_based_care.objects.all().annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.all().count()
        elif (user_level == 3 or user_level == 5):
            print("inside County")
            user_county_id = u.persons.county_id
            print(user_county_id)
            print(current_user.id)
            q_data = home_based_care.objects.filter(patient_contacts__county_id=user_county_id).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__county_id=user_county_id).count()
        elif (user_level == 4 or user_level == 6):
            print("inside SubCounty")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            print(current_user.id)
            q_data = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).count()
        elif (user_level == 7):
            print("inside Border")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            print(current_user.id)
            q_data = home_based_care.objects.all().annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__cormobidity="1").count()
        else:
            print("inside Facility")
            user_sub_county_id = u.persons.sub_county
            print(user_sub_county_id)
            print(current_user.id)
            q_data = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                patient_contacts__created_by=current_user.id).annotate(
                first_name=F("patient_contacts__first_name"),
                last_name=F("patient_contacts__last_name"),
                sex=F("patient_contacts__sex"),
                age=F("patient_contacts__dob"),
                passport_number=F("patient_contacts__passport_number"),
                phone_number=F("patient_contacts__phone_number"),
                nationality=F("patient_contacts__nationality"),
                origin_country=F("patient_contacts__origin_country"),
                county=F("patient_contacts__county__name"),
                subcounty=F("patient_contacts__subcounty__name"),
                quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                source=F("patient_contacts__source"),
                date_of_contact=F("patient_contacts__date_of_contact"),
                created_by=F("patient_contacts__created_by_id__username"),
            )
            q_data_count = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).count()

        cntry = country.objects.all()
        day = time.strftime("%Y-%m-%d")

        paginator = Paginator(q_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        data = {'home_care_data': q_data, 'home_care_data_count': q_data_count, 'country': cntry, 'start_day': day,
                'end_day': day, 'page_obj': page_obj}

    return render(request, 'veoc/home_care_list.html', data)


@login_required
def t_q_list_json(request):

    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    # print(user_group)
    for grp in user_group:
        user_level = grp
    # print(user_level)
    global q_data

    if user_level == 1 or user_level == 2:
        print("inside National")
        q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
            filter(patient_contacts__source='Truck Registration').count()
        q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
            filter(patient_contacts__source='Truck Registration').order_by('-patient_contacts__date_of_contact')

    elif user_level == 7:
        print("inside Border")
        # find ways of filtering data based on the border point-------
        q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
            filter(patient_contacts__source='Truck Registration').count()
        q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
            filter(patient_contacts__source='Truck Registration', border_point__border_name=user_access_level)

    else:
        print("inside non border users")
        q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts').filter(
            source='Kitu hakuna').count()
        q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
            filter(patient_contacts__source='Kitu hakuna').order_by('-date_of_contact')

    serialized = serialize('json', q_data)
    obj_list = json.loads(serialized)

    print(obj_list)

    return HttpResponse(json.dumps(obj_list), content_type="application/json")

@login_required
def truck_quarantine_list(request):
    global data

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    # print(user_group)
    for grp in user_group:
        user_level = grp
    # print(user_level)

    quar_sites = weighbridge_sites.objects.all().order_by('weighbridge_name')
    bord_points = border_points.objects.all().order_by('border_name')
    truck_cont_details = []
    q_data_count = 0

    if request.method == 'POST':
        if user_level == 1 or user_level == 2:
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')
            id_num = request.POST.get('id_number', '')

            if id_num:
                q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(patient_contacts__passport_number=id_num). \
                    filter(patient_contacts__source='Truck Registration').count()
                q_data = truck_quarantine_contacts.objects.select_related('patient_contacts') \
                    .filter(patient_contacts__passport_number=id_num,
                            patient_contacts__source='Truck Registration'). \
                    order_by('-patient_contacts__date_of_contact')
            else:
                print("inside National")
                # add a border point filter to enable filtering specific border point--------
                q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(patient_contacts__date_of_contact__gte=date_from, patient_contacts__date_of_contact__lte=date_to). \
                    filter(patient_contacts__source='Truck Registration').count()
                q_data = truck_quarantine_contacts.objects.select_related('patient_contacts') \
                    .filter(patient_contacts__date_of_contact__gte=date_from,
                            patient_contacts__date_of_contact__lte=date_to,
                            patient_contacts__source='Truck Registration'). \
                    order_by('-patient_contacts__date_of_contact')

        elif user_level == 7:
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')
            id_num = request.POST.get('id_number', '')

            if id_num:
                q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(patient_contacts__passport_number=id_num). \
                    filter(patient_contacts__source='Truck Registration').count()
                q_data = truck_quarantine_contacts.objects.select_related('patient_contacts') \
                    .filter(patient_contacts__passport_number=id_num,
                            patient_contacts__source='Truck Registration'). \
                    order_by('-patient_contacts__date_of_contact')
            else:
                print("inside Border")
                # find ways of filtering data based on the border point-------
                q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(patient_contacts__date_of_contact__gte=date_from, patient_contacts__date_of_contact__lte=date_to). \
                    filter(patient_contacts__source='Truck Registration').count()
                q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(border_point__border_name=user_access_level,
                           patient_contacts__source='Truck Registration',
                           patient_contacts__date_of_contact__gte=date_from,
                           patient_contacts__date_of_contact__lte=date_to). \
                    order_by('-patient_contacts__date_of_contact')

        else:
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')
            id_num = request.POST.get('id_number', '')

            if id_num:
                q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(patient_contacts__passport_number=id_num). \
                    filter(patient_contacts__source='Truck Registration').count()
                q_data = truck_quarantine_contacts.objects.select_related('patient_contacts') \
                    .filter(patient_contacts__passport_number=id_num,
                            patient_contacts__source='Truck Registration'). \
                    order_by('-patient_contacts__date_of_contact')
            else:
                print("inside non border users")
                q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(patient_contacts__date_of_contact__gte=date_from,
                           patient_contacts__date_of_contact__lte=date_to). \
                    filter(patient_contacts__source='Kitu hakuna').count()
                q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                    filter(patient_contacts__source='Kitu hakuna').filter(patient_contacts__date_of_contact__gte=date_from,
                                                                          date_of_contact__lte=date_to). \
                    order_by('-patient_contacts__date_of_contact')

        paginator = Paginator(q_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        my_list_data = page_obj
        day = time.strftime("%Y-%m-%d")
        data = {'quarantine_data_count': q_data_count, 'border_points': bord_points,
                'my_list_data': my_list_data, 'start_day': day, 'end_day': day, 'page_obj': page_obj}

    else:
        if user_level == 1 or user_level == 2:
            print("inside National")
            # add a border point filter to enable filtering specific border point--------
            q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Truck Registration').count()
            q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Truck Registration').order_by('-patient_contacts__date_of_contact')

        elif user_level == 7:
            print("inside Border")
            # find ways of filtering data based on the border point-------
            q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Truck Registration').count()
            q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Truck Registration', border_point__border_name=user_access_level)

        else:
            print("inside non border users")
            q_data_count = truck_quarantine_contacts.objects.select_related('patient_contacts').filter(
                source='Kitu hakuna').count()
            q_data = truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Kitu hakuna').order_by('-date_of_contact')

        paginator = Paginator(q_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        print(page_obj.number)
        my_list_data = page_obj

        day = time.strftime("%Y-%m-%d")
        data = {'quarantine_data_count': q_data_count, 'border_points': bord_points,
                'my_list_data': my_list_data, 'start_day': day, 'end_day': day, 'page_obj': page_obj}

    return render(request, 'veoc/truck_quarantine_list.html', data)


class AlbumViewSet(viewsets.ModelViewSet):
    model = truck_quarantine_contacts
    serializer_class = TruckSerializer

    def get_queryset(self):
        user_access_level = User.objects.get(username=self.request.user.username).persons.access_level
        user_level = ""
        user_group = self.request.user.groups.values_list('id', flat=True)
        for grp in user_group:
            user_level = grp
        if user_level == 1 or user_level == 2:
            print("inside National")
            return truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Truck Registration').order_by('-patient_contacts__date_of_contact')
        elif user_level == 7:
            print("inside Border")
            return truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Truck Registration', border_point__border_name=user_access_level). \
                order_by('-date_of_contact')
        else:
            print("inside non border users")
            return truck_quarantine_contacts.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Kitu hakuna').order_by('-date_of_contact')



@login_required
def truck_q_list(request):
    all_data = quarantine_contacts.objects.all().filter(source='Truck Registration')
    q_data_count = quarantine_contacts.objects.all().filter(source='Truck Registration').count()
    quar_sites = weighbridge_sites.objects.all().order_by('weighbridge_name')
    # hotel_details = truck_quarantine_contacts.objects.filter(patient_contacts__in=q_data)
    hotel_details = []
    for d in all_data:
        h_details = truck_quarantine_contacts.objects.filter(patient_contacts=d.id)
        hotel_details.append(h_details)

    print(all_data)
    print(q_data_count)
    print(hotel_details)
    my_list_data = zip(all_data, hotel_details)

    print(my_list_data)

    data = {'all_data': my_list_data, 'quarantine_data_count': q_data_count, 'weigh_name': quar_sites}

    return render(request, 'veoc/truck_quarantine_list.html', data)


@login_required
def f_up(request):
    qrnt_contacts = quarantine_contacts.objects.all()

    final_array = []
    client_array = {}
    # follow_up_array = {}
    for qrt_cnt in qrnt_contacts:
        follow_up_array = myDict()
        follow = quarantine_follow_up.objects.filter(patient_contacts=qrt_cnt)
        # print(qrt_cnt.first_name)

        follow_up_array.add('first_name', qrt_cnt.first_name)
        follow_up_array.add('last_name', qrt_cnt.last_name)
        follow_up_array.add('age', qrt_cnt.age)
        follow_up_array.add('gender', qrt_cnt.sex)
        follow_up_array.add('origin_country', qrt_cnt.origin_country)
        follow_up_array.add('date_begin_quarantine', qrt_cnt.date_of_contact)
        follow_up_array.add('quarantine_site', qrt_cnt.quarantine_site.site_name)

        for fllw in follow:
            print(fllw.follow_up_day)
            print(fllw.body_temperature)
            client_array[qrt_cnt.id] = follow_up_array

            final_array.append(client_array)

        print(final_array)

        # client_array = {'first_name': qrt_cnt.first_name}

        # client_array.update(
        #             last_name = str(qrt_cnt.last_name),
        #             age = str(qrt_cnt.age),
        #             gender = str(qrt_cnt.sex),
        #             origin_country = str(qrt_cnt.origin_country),
        #             date_begin_quarantine = str(qrt_cnt.date_of_contact),
        #             place_of_quarantine = str(qrt_cnt.place_of_diagnosis),
        #         )

        # for fllw in follow:
        # print(qrt_cnt.first_name)
        # print(fllw.follow_up_day)
        # print(fllw.body_temperature)

        # follow_array = {'day '+str(fllw.follow_up_day) : fllw.body_temperature
        # follow_up_array.update(follow_up = follow_array)
        # follow_up_array.update({'day '+str(fllw.follow_up_day) : fllw.body_temperature})

        # if follow.__len__() >= 1:
        #     print(qrt_cnt.first_name)
        # client_array['follow_up'] = follow_up_array
        # print(client_array)
        # final_array.append(client_array)

        # print(final_array)

    # print(final_array)
    return render(request, 'veoc/f_up.html', {"data": qrnt_contacts})


@login_required
def follow_up(request):
    global data, follow_data, follow_data_count

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_level = grp
    print(user_level)

    if request.method == 'POST':

        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.filter(created_at__gte=date_from,
                                                              created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(created_at__gte=date_from,
                                                                    created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(created_at__gte=date_from,
                                                                          created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).filter(created_at__gte=date_from,
                                                                                            created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(created_at__gte=date_from,
                                                                            created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(created_at__gte=date_from,
                                                                            created_at__lte=date_to).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()
        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': date_from,
                'end_day': date_to, 'page_obj': page_obj}
    else:
        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.exclude(patient_contacts__source='Truck Registration').exclude(
                patient_contacts__source='RECDTS').exclude(patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(
                patient_contacts__subcounty_id=user_sub_county_id).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__subcounty_id=user_sub_county_id).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).exclude(
                patient_contacts__source='Truck Registration').exclude(patient_contacts__source='RECDTS').exclude(
                patient_contacts__source='Jitenge Homecare Module').exclude(
                patient_contacts__source='Web Homecare Module').count()

        day = time.strftime("%Y-%m-%d")
        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': day, 'end_day': day,
                'page_obj': page_obj}

    # check if temperature is higher than 38.0 to send sms
    # if temperature is higher and sms_status = No send an sms
    for f_data in page_obj:
        temp = f_data.body_temperature
        cntry = f_data.patient_contacts.origin_country
        case_f_name = f_data.patient_contacts.first_name
        case_l_name = f_data.patient_contacts.last_name
        sms_stat = f_data.sms_status
        cap_user = f_data.patient_contacts.created_by.id
        cap_name = f_data.patient_contacts.created_by.first_name
        date_reported = f_data.created_at
        q_site = f_data.patient_contacts.quarantine_site_id

        if temp >= 38.0 and sms_stat == "No":
            quasites = quarantine_sites.objects.all().filter(pk=q_site)
            phone = ''
            user_phone = "+254"
            site_name = ''
            for quasite in quasites:
                site_name = quasite.site_name

            # print(site_name)
            if site_name == "Home":
                # Get contacts of the creator of the cases from the persos table
                person_phone = persons.objects.filter(user_id=cap_user)
                for pers_ph in person_phone:
                    phone = pers_ph.phone_number
                    print("EOC user contact")
                    # print(phone)
            else:
                # Get contact of the quarantine site lead from quarantine sites table
                phone = quasite.team_lead_phone
                print("quarantine lead contact")
                # print(phone)

            # check if the leading character is 0
            if str(phone[0] == ""):
                user_phone = "+254720000000"
            elif str(phone[0]) == "0":
                user_phone = user_phone + str(phone[1:])
                # print("number leading with 0")
            else:
                user_phone = user_phone + str(phone)
                # print("number not leading with 0")

            print(user_phone)
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with high temperature of " + str(
                temp) + " degrees on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            # print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

    return render(request, 'veoc/quarantine_follow_up.html', data)


@login_required
def symptomatic_cases(request):
    global data, follow_data, follow_data_count

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_level = grp
    print(user_level)

    if request.method == 'POST':

        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).filter(created_at__gte=date_from, created_at__lte=date_to).exclude(
                patient_contacts__source='Jitenge Homecare Module').count()

        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': date_from,
                'end_day': date_to, 'page_obj': page_obj}
    else:
        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                follow_up_day__lte=14).exclude(patient_contacts__source='Jitenge Homecare Module').count()

        day = time.strftime("%Y-%m-%d")

        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': day, 'end_day': day,
                'page_obj': page_obj}

    # check if temperature is higher than 38.0 to send sms
    # if temperature is higher and sms_status = No send an sms
    for f_data in page_obj:
        temp = f_data.body_temperature
        cntry = f_data.patient_contacts.origin_country
        case_f_name = f_data.patient_contacts.first_name
        case_l_name = f_data.patient_contacts.last_name
        sms_stat = f_data.sms_status
        cap_user = f_data.patient_contacts.created_by.id
        cap_name = f_data.patient_contacts.created_by.first_name
        date_reported = f_data.created_at
        q_site = f_data.patient_contacts.quarantine_site_id

        if temp >= 38.0 and sms_stat == "No":
            quasites = quarantine_sites.objects.all().filter(pk=q_site)
            phone = ''
            user_phone = "+254"
            site_name = ''
            for quasite in quasites:
                site_name = quasite.site_name

            # print(site_name)
            if site_name == "Home":
                # Get contacts of the creator of the cases from the persos table
                person_phone = persons.objects.filter(user_id=cap_user)
                for pers_ph in person_phone:
                    phone = pers_ph.phone_number
                    print("EOC user contact")
                    # print(phone)
            else:
                # Get contact of the quarantine site lead from quarantine sites table
                phone = quasite.team_lead_phone
                print("quarantine lead contact")
                # print(phone)

            # check if the leading character is 0
            if str(phone[0] == ""):
                user_phone = "+254720000000"
            elif str(phone[0]) == "0":
                user_phone = user_phone + str(phone[1:])
                # print("number leading with 0")
            else:
                user_phone = user_phone + str(phone)
                # print("number not leading with 0")

            print(user_phone)
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with high temperature of " + str(
                temp) + " degrees on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            # print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

    return render(request, 'veoc/quarantine_symptomatic.html', data)


@login_required
def home_care_symtomatic(request):
    global data, follow_data, follow_data_count

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_level = grp
    print(user_level)

    if request.method == 'POST':

        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                created_at__gte=date_from, created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                created_at__gte=date_from, created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__county_id=user_county_id).filter(created_at__gte=date_from,
                                                                   created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__county_id=user_county_id).filter(created_at__gte=date_from,
                                                                   created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(created_at__gte=date_from,
                                                                          created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(created_at__gte=date_from,
                                                                          created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).filter(created_at__gte=date_from,
                                                                                            created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                created_at__gte=date_from, created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__quarantine_site=user_access_level).filter(created_at__gte=date_from,
                                                                            created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__quarantine_site=user_access_level).filter(created_at__gte=date_from,
                                                                            created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': date_from,
                'end_day': date_to, 'page_obj': page_obj}
    else:
        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__county_id=user_county_id).filter(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__county_id=user_county_id).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                self_quarantine=False).filter(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                self_quarantine=False).filter(patient_contacts__source='Jitenge Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        day = time.strftime("%Y-%m-%d")

        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': day, 'end_day': day,
                'page_obj': page_obj}

    return render(request, 'veoc/home_care_symtomatic.html', data)


@login_required
def home_care_follow_up(request):
    global data, follow_data, follow_data_count

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_level = grp
    print(user_level)

    if request.method == 'POST':

        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.filter(created_at__gte=date_from,
                                                              created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(created_at__gte=date_from,
                                                                    created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                created_at__gte=date_from, created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                created_at__gte=date_from, created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                created_at__gte=date_from, created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(created_at__gte=date_from,
                                                                          created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).filter(created_at__gte=date_from,
                                                                                            created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                created_at__gte=date_from, created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(created_at__gte=date_from,
                                                                            created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(created_at__gte=date_from,
                                                                            created_at__lte=date_to).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': date_from,
                'end_day': date_to, 'page_obj': page_obj}
    else:
        if (user_level == 1 or user_level == 2):
            # pull data whose quarantine site id is equal to q_site_name
            print("inside National")
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 3 or user_level == 5):
            user_county_id = u.persons.county_id
            print(user_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 4 or user_level == 6):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__subcounty_id=user_sub_county_id).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        elif (user_level == 7):
            user_sub_county_id = u.persons.sub_county_id
            print(user_sub_county_id)
            follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        else:
            follow_data = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                patient_contacts__source='Jitenge Homecare Module')
            follow_data_count = quarantine_follow_up.objects.filter(
                patient_contacts__quarantine_site=user_access_level).filter(
                patient_contacts__source='Jitenge Homecare Module').count()

        day = time.strftime("%Y-%m-%d")

        paginator = Paginator(follow_data, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'start_day': day, 'end_day': day,
                'page_obj': page_obj}

    return render(request, 'veoc/home_care_follow_up.html', data)


@login_required
def truck_follow_up(request):
    qua_contacts = quarantine_contacts.objects.all().filter(source__contains="Truck Registration")
    follow_data = quarantine_follow_up.objects.all().filter(patient_contacts__in=qua_contacts)
    follow_data_count = quarantine_follow_up.objects.all().filter(patient_contacts__in=qua_contacts).count()

    paginator = Paginator(follow_data, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # check if temperature is higher than 38.0 to send sms
    # if temperature is higher and sms_status = No send an sms
    for f_data in page_obj:
        temp = f_data.body_temperature
        cough = f_data.cough
        breathe = f_data.difficulty_breathing
        fever = f_data.fever
        cntry = f_data.patient_contacts.origin_country
        case_f_name = f_data.patient_contacts.first_name
        case_l_name = f_data.patient_contacts.last_name
        sms_stat = f_data.sms_status
        cap_user = f_data.patient_contacts.created_by.id
        cap_name = f_data.patient_contacts.created_by.first_name
        date_reported = f_data.created_at
        q_site = f_data.patient_contacts.quarantine_site_id
        contact_id = f_data.patient_contacts.id
        print(contact_id)
        # get weighbring based on the contact_id
        # border_p = truck_quarantine_contacts.objects.get(patient_contacts=contact_id)
        # print(border_p)
        # for b in border_p:
        #     bp = b.weighbridge_facility.team_lead_phone
        #     print(bp)

        quasites = quarantine_sites.objects.all().filter(pk=q_site)
        phone = ''
        user_phone = "+254"
        site_name = ''
        for quasite in quasites:
            site_name = quasite.site_name
        # print(site_name)

        if site_name == "Country Border":
            # Get contacts of the creator of the cases from the persos table
            person_phone = persons.objects.filter(user_id=cap_user)
            for pers_ph in person_phone:
                phone = pers_ph.phone_number
                # print("EOC user contact")
        else:
            # Get contact of the quarantine site lead from quarantine sites table
            phone = quasite.team_lead_phone
            # print("quarantine lead contact")

        # check if the leading character is 0
        if str(phone[0]) == "0":
            user_phone = user_phone + str(phone[1:])
            # print("number leading with 0")
        else:
            user_phone = user_phone + str(phone)
            # print("number not leading with 0")

        # print(user_phone)

        if temp >= 38.0 and sms_stat == "No":
            print("High temperature")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with temperature of " + str(temp) + " degrees on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        elif cough == "Yes" and sms_stat == "No":
            print("Has Cough")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with cough on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        elif breathe == "Yes" and sms_stat == "No":
            print("Has Difficulty Breathing")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with difficulty breathing on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        elif fever == "Yes" and sms_stat == "No":
            print("Has Fever")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with fever on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        else:
            print("has none")

    data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'page_obj': page_obj}

    return render(request, 'veoc/truck_quarantine_follow_up.html', data)


@login_required
def truck_symptomatic_cases(request):
    qua_contacts = quarantine_contacts.objects.all().filter(source__contains="Truck Registration")
    follow_data = quarantine_follow_up.objects.all().filter(patient_contacts__in=qua_contacts).filter(
        Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES'))
    follow_data_count = quarantine_follow_up.objects.all().filter(patient_contacts__in=qua_contacts).filter(
        Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES')).count()

    paginator = Paginator(follow_data, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # check if temperature is higher than 38.0 to send sms
    # if temperature is higher and sms_status = No send an sms
    for f_data in page_obj:
        temp = f_data.body_temperature
        cough = f_data.cough
        breathe = f_data.difficulty_breathing
        fever = f_data.fever
        cntry = f_data.patient_contacts.origin_country
        case_f_name = f_data.patient_contacts.first_name
        case_l_name = f_data.patient_contacts.last_name
        sms_stat = f_data.sms_status
        cap_user = f_data.patient_contacts.created_by.id
        cap_name = f_data.patient_contacts.created_by.first_name
        date_reported = f_data.created_at
        q_site = f_data.patient_contacts.quarantine_site_id
        contact_id = f_data.patient_contacts.id
        print(contact_id)
        # get weighbring based on the contact_id
        # border_p = truck_quarantine_contacts.objects.get(patient_contacts=contact_id)
        # print(border_p)
        # for b in border_p:
        #     bp = b.weighbridge_facility.team_lead_phone
        #     print(bp)

        quasites = quarantine_sites.objects.all().filter(pk=q_site)
        phone = ''
        user_phone = "+254"
        site_name = ''
        for quasite in quasites:
            site_name = quasite.site_name
        # print(site_name)

        if site_name == "Country Border":
            # Get contacts of the creator of the cases from the persos table
            person_phone = persons.objects.filter(user_id=cap_user)
            for pers_ph in person_phone:
                phone = pers_ph.phone_number
                # print("EOC user contact")
        else:
            # Get contact of the quarantine site lead from quarantine sites table
            phone = quasite.team_lead_phone
            # print("quarantine lead contact")

        # check if the leading character is 0
        if str(phone[0]) == "0":
            user_phone = user_phone + str(phone[1:])
            # print("number leading with 0")
        else:
            user_phone = user_phone + str(phone)
            # print("number not leading with 0")

        # print(user_phone)

        if temp >= 38.0 and sms_stat == "No":
            print("High temperature")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with temperature of " + str(temp) + " degrees on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        elif cough == "Yes" and sms_stat == "No":
            print("Has Cough")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with cough on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        elif breathe == "Yes" and sms_stat == "No":
            print("Has Difficulty Breathing")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with difficulty breathing on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        elif fever == "Yes" and sms_stat == "No":
            print("Has Fever")
            # send sms notification to the phone number, append +254
            # url = "https://mlab.mhealthkenya.co.ke/api/sms/gateway"
            url = "http://mlab.localhost/api/sms/gateway"
            msg = "Hello " + str(cap_name) + ", your registered quarantined case - " + str(case_f_name) + " " + str(
                case_l_name) + ", quarantined at " + str(
                site_name) + ", requires contact. Reported with fever on " + str(
                date_reported.strftime("%d-%m-%Y")) + ". Login to EARS system for more details."

            pp = {"phone_no": user_phone, "message": msg}
            payload = json.dumps(pp)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE3MGExZGI0ZjFiYWE1ZWNkOGI4YTBiODNlNDc0MTA2NTJiNDg4Mzc4ZTQwNjExNDA0MGQwZmQ2NTEzNTM1NTg5MjFhYjBmNzI1ZDM3NzYwIn0.eyJhdWQiOiI0IiwianRpIjoiMTcwYTFkYjRmMWJhYTVlY2Q4YjhhMGI4M2U0NzQxMDY1MmI0ODgzNzhlNDA2MTE0MDQwZDBmZDY1MTM1MzU1ODkyMWFiMGY3MjVkMzc3NjAiLCJpYXQiOjE1ODQxODk0NTMsIm5iZiI6MTU4NDE4OTQ1MywiZXhwIjoxNjE1NzI1NDUzLCJzdWIiOiI2Iiwic2NvcGVzIjpbXX0.e2Pt76bE6IT7J0hSBpnc7tHShg9BKSXOMuwnQwqC3_xpJXUo2ez7sQPUa4uPp77XQ05xsumNbWapXkqxvVxp-3Gjn-o9UJ39AWHBFRJYqOXM_foZcxRBoXajUfJTTRS5BTMFEfMn2nMeLie9BH7mbgfKBpZXU_3_tClWGUcNbsibbhXgjSxskJoDls8XGVUdgc5pqMZBBBlR9cCrtK3H8PJf6XywMn9CYbw4KF8V1ADC9dYz-Iyhmwe2_LmU3ByTQMaVHCd3GVKWIvlGwNhm2_gRcEHjjZ8_PXR38itUT0M3NTmT6LBeeeb8IWV-3YFkhilbbjA03q9_6f2gjlOpChF4Ut2rC5pqTg7sW5A4PV8gepPnIBpJy5xKQzgf75zDUmuhKlYlirk8MKoRkiIUgWqOZSf49DUxbIaKIijjX3TYrwmBwZ0RTm2keSvk3bt4QutpLRxel6cajbI32rZLuDjs1_MCZNPKAK1ZgPvwt1OaHLM3om0TmSKyugPvhgNJ5fW_on_HLkTbQV6EPqN3Us7S5whFv1MQcwlgsxU9a4CJZa89elr1TaKvqbkaKqGjetwlCDf6AKQmThy5IqQ5zlIRNwlZDgz_DsGyeZUStQhc-HW65NsB_J_fe_jI5tMeRNCz4PE8T0Rghbs8xHLTFKuMGrJL0Rheq6kfEk4c0UM'
            }

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.request("POST", url, headers=headers, data=payload, verify=False)

            print(response.text.encode('utf8'))

            # check if message response is success then update the sms_status column
            quarantine_follow_up.objects.filter(pk=f_data.id).update(sms_status="Yes")

        else:
            print("has none")

    data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'page_obj': page_obj}

    return render(request, 'veoc/truck_quarantine_symptomatic.html', data)


@login_required
def complete_quarantine(request):
    global follow_data, follow_data_count

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    if (user_access_level == 'National'):
        # pull data whose quarantine site id is equal to q_site_name
        print("inside National")
        follow_data = quarantine_follow_up.objects.filter(created_at__lte=date.today() - timedelta(days=14)).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(
            created_at__lte=date.today() - timedelta(days=14)).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').count()

    elif (user_access_level == "County"):
        user_county_id = u.persons.county_id
        print(user_county_id)
        follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').count()

    elif (user_access_level == "SubCounty"):
        user_sub_county_id = u.persons.sub_county_id
        print(user_sub_county_id)
        follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(
            patient_contacts__subcounty_id=user_sub_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').count()

    else:
        follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').filter(
            created_at__lte=date.today() - timedelta(days=14)).order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).exclude(
            patient_contacts__source='Jitenge Homecare Module').exclude(
            patient_contacts__source='Truck Registration').filter(
            created_at__lte=date.today() - timedelta(days=14)).count()

    paginator = Paginator(follow_data, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'page_obj': page_obj}

    return render(request, 'veoc/quarantine_complete.html', data)


@login_required
def complete_home_care(request):
    global follow_data, follow_data_count

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    if (user_access_level == 'National'):
        # pull data whose quarantine site id is equal to q_site_name
        print("inside National")
        follow_data = quarantine_follow_up.objects.filter(created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Jitenge Homecare Module')
        follow_data_count = quarantine_follow_up.objects.filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Jitenge Homecare Module').count()

    elif (user_access_level == "County"):
        user_county_id = u.persons.county_id
        print(user_county_id)
        follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Jitenge Homecare Module').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Jitenge Homecare Module').count()

    elif (user_access_level == "SubCounty"):
        user_sub_county_id = u.persons.sub_county_id
        print(user_sub_county_id)
        follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Jitenge Homecare Module').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(
            patient_contacts__subcounty_id=user_sub_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Jitenge Homecare Module').count()

    else:
        follow_data = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Jitenge Homecare Module').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(self_quarantine=False).filter(
            patient_contacts__source='Jitenge Homecare Module').count()

    paginator = Paginator(follow_data, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'page_obj': page_obj}

    return render(request, 'veoc/quarantine_complete.html', data)


@login_required
def truck_ongoing_quarantine(request):
    if request.method == "POST":
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')
        day = time.strftime("%Y-%m-%d")

        all_data = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__gte=date_from, date_of_contact__lte=date_to).order_by('-date_of_contact')
        q_data_count = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__gte=date_from, date_of_contact__lte=date_to).count()
        quar_sites = weighbridge_sites.objects.all().order_by('weighbridge_name')

        data = {'all_data': all_data, 'all_data_count': q_data_count, 'weigh_name': quar_sites, 'day': day}
    else:
        all_data = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__gte=date.today() - timedelta(days=14)).order_by('-date_of_contact')
        q_data_count = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__gte=date.today() - timedelta(days=14)).count()
        quar_sites = weighbridge_sites.objects.all().order_by('weighbridge_name')
        day = time.strftime("%Y-%m-%d")

        data = {'all_data': all_data, 'all_data_count': q_data_count, 'weigh_name': quar_sites, 'day': day}

    return render(request, 'veoc/truck_ongoing_complete.html', data)


@login_required
def raw_data_downloads(request):

    return render(request, 'veoc/raw_data.html')


@login_required
def truck_complete_quarantine(request):
    if request.method == "POST":
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')
        day = time.strftime("%Y-%m-%d")

        all_data = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__gte=date_from, date_of_contact__lte=date_to).order_by('-date_of_contact')
        q_data_count = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__gte=date_from, date_of_contact__lte=date_to).count()
        quar_sites = weighbridge_sites.objects.all().order_by('weighbridge_name')
        bord_sites = border_points.objects.all().order_by('border_name')

        data = {'all_data': all_data, 'all_data_count': q_data_count, 'weigh_name': quar_sites,
                'border_points': bord_sites, 'day': day}



    else:
        all_data = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__lte=date.today() - timedelta(days=14)).order_by('-date_of_contact')
        q_data_count = quarantine_contacts.objects.all().filter(source='Truck Registration').filter(
            date_of_contact__lte=date.today() - timedelta(days=14)).count()
        quar_sites = weighbridge_sites.objects.all().order_by('weighbridge_name')
        bord_sites = border_points.objects.all().order_by('border_name')
        day = time.strftime("%Y-%m-%d")

        data = {'all_data': all_data, 'all_data_count': q_data_count, 'weigh_name': quar_sites,
                'border_points': bord_sites, 'day': day}

    return render(request, 'veoc/truck_quarantine_complete.html', data)


def line_list_data(request):
    all_line_list = moh_line_listing.objects.all()
    all_line_list_count = moh_line_listing.objects.all().count()

    data = {'line_lists': all_line_list, 'line_list_count': all_line_list_count}

    return render(request, 'veoc/line_list_report.html', data)


@login_required
def ongoing_tasks(request):
    if request.method == 'POST':
        id = request.POST.get('id', '')
        incident_stat = request.POST.get('status_name', '')
        remarks = request.POST.get('remarks', '')
        action = request.POST.get('action', '')
        c_status = request.POST.get('closed', '')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        disease.objects.filter(pk=id).update(incident_status=incident_stat, remarks=remarks, action_taken=action,
                                             case_status=c_status, updated_by=userObject, updated_at=current_date)

    _disease_count = disease.objects.all().filter(case_status=1).count
    _event_count = event.objects.all().filter(case_status=1).count
    # total_count = _disease_count+_event_count
    disease_status_desr = incident_status.objects.all()
    my_disease = disease.objects.filter(case_status=1)
    _event = event.objects.all().filter(case_status=1)
    current_date = date.today()  # .strftime('%Y-%m-%d')

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
              'status_descriptions': disease_status_desr, 'current_date': current_date}

    return render(request, 'veoc/ongoing_tasks.html', diseas)


@login_required
def filter_ongoing_tasks(request):
    if request.method == 'POST':
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')
        day_from = date_from
        day_to = date_to

        _disease_count = disease.objects.all().filter(case_status=1).filter(
            date_reported__range=[date_from, date_to]).count
        _event_count = event.objects.all().filter(case_status=1).filter(date_reported__range=[date_from, date_to]).count
        # total_count = _disease_count+_event_count
        disease_status_desr = incident_status.objects.all()
        my_disease = disease.objects.filter(case_status=1).filter(date_reported__range=[date_from, date_to])
        _event = event.objects.all().filter(case_status=1).filter(date_reported__range=[date_from, date_to])
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
                  'disease_status_desr': disease_status_desr, 'day_from': day_from, 'day_to': day_to}

        return render(request, 'veoc/ongoing_tasks.html', diseas)


@login_required
def case_definition(request):
    if request.method == "POST":
        code = request.POST.get('code', '')
        condition = request.POST.get('condition', '')
        incubation = request.POST.get('incubation', '')
        suspected = request.POST.get('suspected_definition', '')
        confirmed = request.POST.get('confirmed_definition', '')
        signs = request.POST.get('signs', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        diseaseObject = dhis_disease_type.objects.get(name=condition)

        # saving values to databse
        standard_case_definitions.objects.create(code=code, condition=diseaseObject, incubation_period=incubation,
                                                 suspected_standard_case_def=suspected,
                                                 confirmed_standard_case_def=confirmed, signs_and_symptoms=signs,
                                                 updated_at=current_date, created_by=userObject, updated_by=userObject,
                                                 created_at=current_date)

    case_definition_count = standard_case_definitions.objects.all().count()
    _standard_case_definitions = standard_case_definitions.objects.all()
    diseases = dhis_disease_type.objects.all().order_by('name')

    data_values = {'case_definition_count': case_definition_count,
                   'standard_case_definitions': _standard_case_definitions,
                   'diseases': diseases}

    return render(request, "veoc/case_defination.html", data_values)


@login_required
def generate_pdf(request):
    return render(request, 'veoc/generate_pdf.html')


@login_required
def All_contacts_report(request):
    contacts = {'contacts_val': contact.objects.all(),
                'contact_type_vals': contact_type.objects.all()}

    return render(request, 'veoc/all_contacts_report.html', contacts)


@login_required
def Contact_type_report(request, id):
    contacts = contact_type.objects.all()
    contacts = {'contacts_val': contact.objects.all().filter(contact_type_id=id),
                'contact_type_description': contact_type.objects.get(pk=id),
                'contact_type_vals': contact_type.objects.all()}

    return render(request, 'veoc/all_contacts_report.html', contacts)


@login_required
def all_contact_edit(request, editid):
    all_contacts = {'all_contacts': contact.objects.get(pk=editid)}

    return render(request, 'veoc/all_contacts_edit.html', all_contacts)


@login_required
def contacts_edited_submit(request):
    if request.method == 'POST':
        myid = request.POST.get('id', '')
        f_name = request.POST.get('fname', '')
        s_name = request.POST.get('sname', '')
        design = request.POST.get('designation', '')
        mob = request.POST.get('mobile', '')
        _mail = request.POST.get('email', '')

        d_type = designation.objects.get(description=design)
        cur_user = request.user.username
        user = str(User.objects.get(username=cur_user))
        # user=User.objects.get(username=cur_user)
        # user=request.user.username

        EOC_Contacts.objects.filter(pk=myid).update(first_name=f_name, second_name=s_name, designation=d_type,
                                                    mobile=mob, email=_mail, created_by=user)

        values = {'eocContacts': EOC_Contacts.objects.all(), 'designation': Designation.objects.all()}

        return render(request, 'veoc/surveillance_contacts.html', values)


@login_required
def idsr_data(request):
    if request.method == "POST":
        _weekly_report_count = idsr_weekly_facility_report.objects.all().count()
        _organizations = organizational_units.objects.all()
        _diseases = idsr_diseases.objects.all()
        _reported_incidents = idsr_reported_incidents.objects.all()
        _idsr_weekly_report = idsr_weekly_facility_report.objects.all()

        values = {'idsr_weekly_reports': _idsr_weekly_report, 'organizations': _organizations,
                  'weekly_report_count': _weekly_report_count, 'diseases': _diseases,
                  'reported_incidents': _reported_incidents}

        return render(request, 'veoc/idsr_report.html', values)

    else:
        dhis_cases = idsr_weekly_facility_report.objects.all().count()
        week_no = idsr_weekly_facility_report.objects.order_by('org_unit_id').values('period').distinct()

        values = {'dhis_cases': dhis_cases, 'week_no': week_no}
        return render(request, 'veoc/idsr_report.html', values)


@login_required
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
        dhis_data_values = dhis_disease_data_values.objects.filter(
            dhis_reported_disease_id=_dhis_reported_cases).values_list('data_value', flat=True).first()
        dhis_case_values.append(dhis_data_values)

    _dhis_cases = dhis_disease_data_values.objects.all()
    my_list_data = zip(_dhis_reported_diseases_report, dhis_case_values)

    values = {'dhis_reported_diseases_count': _dhis_reported_diseases_count, 'organizations': _organizations,
              'dhis_reported_diseases_reports': my_list_data, 'dhis_cases': _dhis_cases,
              'drop_down_diseases': _drop_down_diseases, 'drop_down_periods': _drop_down_periods}

    return render(request, 'veoc/reportable_diseases_report.html', values)


@login_required
def reportable_diseases_filters(request):
    global filt_data
    if request.method == 'POST':
        filter_disease = request.POST.get('idsr_disease', '')
        filter_period = request.POST.get('period', '')
        filter_date = request.POST.get('date_reported', '')

        print(filter_disease)
        print(filter_period)
        print(filter_date)

        # check for null values then filter based on values
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
                        # stopped at find a way of passing the filter to the query
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
        dhis_data_values = dhis_disease_data_values.objects.filter(
            dhis_reported_disease_id=_dhis_reported_cases).values_list('data_value', flat=True).first()
        dhis_case_values.append(dhis_data_values)

    _dhis_cases = dhis_disease_data_values.objects.all()
    my_list_data = zip(_dhis_reported_diseases_report, dhis_case_values)

    values = {'dhis_reported_diseases_count': _dhis_reported_diseases_count, 'organizations': _organizations,
              'dhis_reported_diseases_reports': my_list_data, 'dhis_cases': _dhis_cases,
              'drop_down_diseases': _drop_down_diseases, 'drop_down_periods': _drop_down_periods}

    return render(request, 'veoc/reportable_diseases_report.html', values)


@login_required
def reportable_event(request):
    _dhis_reported_events_count = dhis_reported_events.objects.all().count()
    _organizations = organizational_units.objects.all()
    _dhis_reported_events_report = dhis_reported_events.objects.all()
    _drop_down_events = dhis_reported_events.objects.all()
    dhis_case_values = []
    for _dhis_reported_cases in _dhis_reported_events_report:
        dhis_data_values = dhis_event_data_values.objects.filter(
            dhis_reported_event_id=_dhis_reported_cases).values_list('data_value', flat=True).first()
        dhis_case_values.append(dhis_data_values)

    _dhis_cases = dhis_event_data_values.objects.all()
    my_list_data = zip(_dhis_reported_events_report, dhis_case_values)

    values = {'dhis_reported_events_count': _dhis_reported_events_count, 'organizations': _organizations,
              'dhis_reported_events_report': my_list_data, 'dhis_cases': _dhis_cases,
              'drop_down_events': _drop_down_events}

    return render(request, 'veoc/reportable_event_report.html', values)


def upload_csv(request):
    data = {}
    if "GET" == request.method:
        return render(request, "veoc/upload_csv.html", data)
    # if not GET, then proceed
    try:
        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not CSV type')
            return HttpResponseRedirect(reverse("veoc:upload_csv"))
        # if file is too large, return
        if csv_file.multiple_chunks():
            messages.error(request, "Uploaded file is too big (%.2f MB)." % (csv_file.size / (1000 * 1000),))
            return HttpResponseRedirect(reverse("veoc:upload_csv"))

        file_data = csv_file.read().decode("utf-8")

        lines = file_data.split("\n")
        # loop over the lines and save them in db. If error , store as string and then display
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
        logging.getLogger("error_logger").error("Unable to upload file. " + repr(e))
        messages.error(request, "Unable to upload file. " + repr(e))

    return HttpResponseRedirect(reverse("veoc:upload_csv"))


@login_required
def daily_report_submit(request):
    datefilter = request.POST.get('date_reported', '')
    disease_types = disease_type.objects.all().exclude(description='none')
    watchers = mytimetable.objects.all().filter(from_date__lte=datefilter, to_date__gte=datefilter)

    # for watch in watchers:
    #     w_name = EOC_Contacts.objects.filter(first_name = watch).get('first_name', 'second_name')
    #
    #     print(w_name)
    # watchersb = mytimetable.objects.all()
    # print('yeeee')
    # disease_report_stat= {}
    # for disease_type in disease_types:
    #    diseases_count = Disease.objects.all().filter(disease_type_id=disease_type.id).count()
    #    disease_report_stat[disease_type.description] = diseases_count

    call_log_count_stat = {}

    # count flash back log
    Call_flashback_logs_count = call_flashback.objects.all().filter(date_reported=datefilter).count()
    call_log_count_stat["Other enquiries"] = Call_flashback_logs_count

    # count unrelated call
    Unrelated_call_logs_count = Unrelated_calls.objects.all().filter(date_reported=datefilter).count()
    call_log_count_stat["Unrelated calls"] = Unrelated_call_logs_count

    event_types = Event_type.objects.all().exclude(description='none')
    for event_type in event_types:
        call_logs_count = Call_log.objects.all().filter(event_type_id=event_type.id).filter(
            date_reported=datefilter).count()
        call_log_count_stat[event_type.description] = call_logs_count

    disease_types = Disease_type.objects.all().exclude(description='none')
    for disease_type in disease_types:
        call_logs_count = Call_log.objects.all().filter(disease_type_id=disease_type.id).filter(
            date_reported=datefilter).count()
        call_log_count_stat[disease_type.description] = call_logs_count
        call_log_sum = sum(call_log_count_stat.values())

    daily_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(
        incident_status_id=2).filter(date_reported=datefilter).count()
    daily_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(
        date_reported=datefilter).count()
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

    # Get all significant events,diseases and Call logs
    # significant_diseases = Disease.objects.all().filter(significant = "True").filter(date_created=datefilter)
    significant_diseases = "None"
    # significant_events = Event.objects.all().filter(significant = "True").filter(date_created=datefilter)
    significant_events = "None"
    # significant_call_logs = Call_log.objects.all().filter(significant = "True").filter(date_reported=datefilter)
    significant_call_logs = ""
    # if there are no significant events indicate as none
    if (significant_events == "") and (significant_diseases == "") and significant_call_logs == "":
        significant_events_none = "None"
    else:
        significant_events_none = ""

    events = {'significant_diseases': significant_diseases, 'significant_events': significant_events,
              'significant_call_logs': significant_call_logs,
              'watchers': watchers, 'event_vals': Event.objects.all(), "date_filter": datefilter,
              "significant_events_none": significant_events_none,
              "diseases": diseases_list, "events": events_list, "call_log_count_stat": call_log_count_stat,
              "call_log_sum": call_log_sum,
              'daily_conf_call_log_count': daily_conf_call_log_count,
              'daily_rum__call_log_count': daily_rum_call_log_count,
              'daily_enquiry': daily_enquiry, 'daily_total_calls': daily_total_calls}
    return render(request, 'veoc/daily_report.html', events)


@login_required
def weekly_report(request):
    ##get five years from current year
    y_ = 0
    yrs_ = []
    while y_ < 5:
        dt = timezone.now()
        yr_val = timezone.now().replace(year=dt.year - y_)
        final_year = yr_val.year
        data = {'year': final_year}
        yrs_.append(data)
        y_ = y_ + 1

    epi_wks = {'epi_years': yrs_}

    return render(request, 'veoc/weekly_report.html', epi_wks)


@login_required
def weekly_report_submit(request):
    ###################################################################################
    iso_date = request.POST.get('epi_week', '')
    iso_year = request.POST.get('epi_year', '')

    date_data = iso_date.split("#")
    start_date = date_data[0]
    end_date = date_data[1]

    # print(iso_year)
    # print(start_date)
    # print(end_date)

    y_ = 0
    yrs_ = []
    while y_ < 5:
        dt = timezone.now()
        yr_val = timezone.now().replace(year=dt.year - y_)
        final_year = yr_val.year
        data = {'year': final_year}
        yrs_.append(data)
        y_ = y_ + 1

    epi_yrs = {'epi_years': yrs_}
    #######################################################################################

    disease_types = Disease_type.objects.all().exclude(description='none')
    disease_report_stat = {}
    for disease_type in disease_types:
        diseases_count = Disease.objects.all().filter(disease_type_id=disease_type.id).count()
        disease_report_stat[disease_type.description] = diseases_count

    # x = request.POST.get('date_from','')
    # print x
    # ==date_from = request.POST.get('date_from','')
    # y =request.POST.get('date_to','')
    # ==date_to = request.POST.get('date_to','')

    # watchers = mytimetable.objects.all().filter(from_date__lte = date_from, to_date__gte = date_from)
    watchers = mytimetable.objects.all().filter(from_date__lte=start_date, to_date__gte=end_date)
    call_log_count_stat = {}

    # count flash back log
    # ==Call_flashback_logs_count =  Call_flashback.objects.all().filter(date_reported__range=[date_from, date_to]).count()
    Call_flashback_logs_count = Call_flashback.objects.all().filter(date_reported__range=[start_date, end_date]).count()
    call_log_count_stat["Other enquiries"] = Call_flashback_logs_count

    # count unrelated call
    # ==Unrelated_call_logs_count =  Unrelated_calls.objects.all().filter(date_reported__range=[date_from, date_to]).count()
    Unrelated_call_logs_count = Unrelated_calls.objects.all().filter(
        date_reported__range=[start_date, end_date]).count()
    call_log_count_stat["Unrelated calls"] = Unrelated_call_logs_count

    event_types = Event_type.objects.all().exclude(description='none')
    for event_type in event_types:
        # ==call_logs_count = Call_log.objects.all().filter(event_type_id=event_type.id).filter(date_reported__range=[date_from, date_to]).count()
        call_logs_count = Call_log.objects.all().filter(event_type_id=event_type.id).filter(
            date_reported__range=[start_date, end_date]).count()
        call_log_count_stat[event_type.description] = call_logs_count

    disease_types = Disease_type.objects.all().exclude(description='none')
    for disease_type in disease_types:
        # call_logs_count = Call_log.objects.all().filter(disease_type_id=disease_type.id).filter(date_reported__range=[date_from, date_to]).count()
        call_logs_count = Call_log.objects.all().filter(disease_type_id=disease_type.id).filter(
            date_reported__range=[start_date, end_date]).count()
        call_log_count_stat[disease_type.description] = call_logs_count
        call_log_sum = sum(call_log_count_stat.values())

    # wkly_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=2).filter(date_reported__range=[date_from, date_to]).count()
    wkly_conf_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=2).filter(
        date_reported__range=[start_date, end_date]).count()
    # wkly_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(date_reported__range=[date_from, date_to]).count()
    wkly_rum_call_log_count = Call_log.objects.all().filter(disease_type_id__gt=0).filter(incident_status_id=1).filter(
        date_reported__range=[start_date, end_date]).count()
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

    # Get all significant events,diseases and Call logs
    # significant_diseases = Disease.objects.all().filter(significant = "True").filter(date_created__range=[start_date, end_date])
    significant_diseases = ""
    # significant_events = Event.objects.all().filter(significant = "True").filter(date_created__range=[start_date, end_date])
    significant_events = ""
    # significant_call_logs = Call_log.objects.all().filter(significant = "True").filter(date_reported__range=[start_date, end_date])
    significant_call_logs = ""
    # if there are no significant events indicate as none
    if (significant_events == "") and (significant_diseases == "") and significant_call_logs == "":
        significant_events_none = "None"
    else:
        significant_events_none = ""

    # significant_events = Significant_event.objects.all().filter(date_created__range=[date_from, date_to])
    # if not significant_events :
    #  significant_events_none="None"
    #
    # media_reports = Significant_event.objects.all().filter(date_created__range=[date_from, date_to])
    # if not media_reports :
    #  media_reports_none="None"

    # events = {'event_vals': Event.objects.all(),"diseases": diseases_list,"date_from":date_from,"date_to":date_to,
    events = {'event_vals': Event.objects.all(), "diseases": diseases_list, "date_from": start_date,
              "date_to": end_date,
              # "media_reports":media_reports,"media_reports_none":media_reports_none,
              "significant_events_none": significant_events_none, 'watchers': watchers,
              "significant_diseases": significant_diseases, "significant_events": significant_events,
              "events": events_list,
              "call_log_count_stat": call_log_count_stat, "call_log_sum": call_log_sum,
              'wkly_conf_call_log_count': wkly_conf_call_log_count, 'wkly_rum_call_log_count': wkly_rum_call_log_count,
              'wkly_enquiry': wkly_enquiry, 'wkly_total_calls': wkly_total_calls}

    events.update(epi_yrs)  # add api years to the dictionary

    return render(request, 'veoc/weekly_report.html', events)


@login_required
def users_list(request):
    users_count = User.objects.all().count()
    users = User.objects.all()
    org_units = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    user_groups = Group.objects.all()
    border_pnts = border_points.objects.all()
    quar_sites = quarantine_sites.objects.all()

    values = {'users_count': users_count, 'users': users, 'org_units': org_units, 'user_groups': user_groups,
              'border_points': border_pnts, 'quar_sites': quar_sites}

    return render(request, 'veoc/users.html', values)


def get_org_unit(request):
    if request.method == 'POST':
        global org_units
        access_level = request.POST.get('access_level', '')

        if access_level == 'National':
            org_units = organizational_units.objects.all().filter(hierarchylevel=1).order_by('name')

        else:
            org_units = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')

        serialized = serialize('json', org_units)
        obj_list = json.loads(serialized)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


@login_required
def diseases_list(request):
    if request.method == "POST":
        uid = request.POST.get('uid', '')
        disease_name = request.POST.get('disease_name', '')
        priority = request.POST.get('priority', '')
        infectious = request.POST.get('infectious', '')

        if not priority:
            priority = False
        else:
            priority = True

        if not infectious:
            infectious = False
        else:
            infectious = True

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        dhis_disease_type.objects.create(uid=uid, name=disease_name, priority_disease=priority,
                                         infectious_disease=infectious)

    disease_count = dhis_disease_type.objects.all().count
    disease_vals = dhis_disease_type.objects.all()
    values = {'disease_count': disease_count, 'disease_vals': disease_vals}

    return render(request, 'veoc/diseaselist.html', values)


@login_required
def edit_diseases_list(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        disease_name = request.POST.get('disease_name', '')
        priority = request.POST.get('priority', '')
        infectious = request.POST.get('infectious', '')

        if not priority:
            priority = False
        else:
            priority = True

        if not infectious:
            infectious = False
        else:
            infectious = True

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # updating values to database
        dhis_disease_type.objects.filter(pk=myid).update(name=disease_name, priority_disease=priority,
                                                         infectious_disease=infectious)

    disease_count = dhis_disease_type.objects.all().count
    disease_vals = dhis_disease_type.objects.all()
    values = {'disease_count': disease_count, 'disease_vals': disease_vals}

    return render(request, 'veoc/diseaselist.html', values)


@login_required
def edit_quarantine_list(request):
    global data
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    print(user_group)
    for grp in user_group:
        user_level = grp

    if request.method == "POST":
        myid = request.POST.get('id', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        middle_name = request.POST.get('middle_name', '')
        passport_number = request.POST.get('passport_number', '')
        phone_number = request.POST.get('phone_number', '')
        origin_country = request.POST.get('country', '')
        nationality = request.POST.get('nationality', '')
        nok = request.POST.get('nok', '')
        nok_phone_num = request.POST.get('nok_phone_num', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # updating values to database
        update_record = quarantine_contacts.objects.filter(pk=myid).update(first_name=first_name, last_name=last_name,
                                                                           middle_name=middle_name,
                                                                           passport_number=passport_number,
                                                                           phone_number=phone_number,
                                                                           origin_country=origin_country,
                                                                           nationality=nationality, nok=nok,
                                                                           nok_phone_num=nok_phone_num,
                                                                           updated_by=userObject)

        if update_record:
            if (user_level == 1 or user_level == 2):
                # print("inside National")
                q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').count()
                quar_sites = quarantine_sites.objects.exclude(site_name='Country Border').order_by('site_name')
            elif (user_level == 3 or user_level == 5):
                # print("inside County")
                user_county_id = u.persons.county_id
                print(user_county_id)
                q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').filter(
                    county_id=user_county_id).order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').filter(
                    county_id=user_county_id).count()
                quar_sites = quarantine_sites.objects.exclude(site_name='Country Border').filter(
                    county_id=user_county_id).order_by('site_name')
            elif (user_level == 4 or user_level == 6):
                print("inside SubCounty")
                user_sub_county_id = u.persons.sub_county
                print(user_sub_county_id)
                q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').filter(
                    subcounty_id=user_sub_county_id).order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').filter(
                    subcounty_id=user_sub_county_id).count()
                quar_sites = quarantine_sites.objects.exclude(site_name='Country Border').filter(
                    subcounty_id=user_sub_county_id).order_by('site_name')
            elif (user_level == 7):
                print("inside Border")
                user_sub_county_id = u.persons.sub_county
                print(user_sub_county_id)
                q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').filter(cormobidity="1").order_by(
                    '-date_of_contact')
                q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').filter(cormobidity="1").count()
                quar_sites = quarantine_sites.objects.all().filter(active=False).order_by('site_name')
            else:
                print("inside Facility")
                user_sub_county_id = u.persons.sub_county
                print(user_sub_county_id)
                q_data = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').filter(
                    subcounty_id=user_sub_county_id).order_by('-date_of_contact')
                q_data_count = quarantine_contacts.objects.exclude(source='Jitenge Homecare Module').exclude(
                    source='Truck Registration').exclude(source='Web Homecare Module').filter(
                    subcounty_id=user_sub_county_id).count()
                quar_sites = quarantine_sites.objects.filter(site_name=user_access_level).order_by('site_name')

            cntry = country.objects.all()
            day = time.strftime("%Y-%m-%d")
            data = {'quarantine_data': q_data, 'quarantine_data_count': q_data_count, 'quar_sites': quar_sites,
                    'country': cntry, 'start_day': day, 'end_day': day}

        return render(request, 'veoc/quarantine_list.html', data)


def edit_home_isolation_list(request):
    global data

    # check logged users access level to display relevant records -- national, county, SubCounty
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---")
    print(user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    for grp in user_group:
        user_level = grp

    if request.method == "POST":
        myid = request.POST.get('id', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        middle_name = request.POST.get('middle_name', '')
        passport_number = request.POST.get('passport_number', '')
        phone_number = request.POST.get('phone_number', '')
        origin_country = request.POST.get('country', '')
        nationality = request.POST.get('nationality', '')
        nok = request.POST.get('nok', '')
        nok_phone_num = request.POST.get('nok_phone_num', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # updating values to database
        update_record = quarantine_contacts.objects.filter(pk=myid).update(first_name=first_name, last_name=last_name,
                                                                           middle_name=middle_name,
                                                                           passport_number=passport_number,
                                                                           phone_number=phone_number,
                                                                           origin_country=origin_country,
                                                                           nationality=nationality, nok=nok,
                                                                           nok_phone_num=nok_phone_num,
                                                                           updated_by=userObject)

        if update_record:
            if (user_level == 1 or user_level == 2):
                print("inside National")
                q_data = home_based_care.objects.all().annotate(
                    first_name=F("patient_contacts__first_name"),
                    last_name=F("patient_contacts__last_name"),
                    sex=F("patient_contacts__sex"),
                    age=F("patient_contacts__dob"),
                    passport_number=F("patient_contacts__passport_number"),
                    phone_number=F("patient_contacts__phone_number"),
                    nationality=F("patient_contacts__nationality"),
                    origin_country=F("patient_contacts__origin_country"),
                    quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                    source=F("patient_contacts__source"),
                    date_of_contact=F("patient_contacts__date_of_contact"),
                    created_by=F("patient_contacts__created_by_id__username"),
                )
                q_data_count = home_based_care.objects.all().count()
            elif (user_level == 3 or user_level == 5):
                print("inside County")
                user_county_id = u.persons.county_id
                print(user_county_id)
                q_data = home_based_care.objects.filter(patient_contacts__county_id=user_county_id).annotate(
                    first_name=F("patient_contacts__first_name"),
                    last_name=F("patient_contacts__last_name"),
                    sex=F("patient_contacts__sex"),
                    age=F("patient_contacts__dob"),
                    passport_number=F("patient_contacts__passport_number"),
                    phone_number=F("patient_contacts__phone_number"),
                    nationality=F("patient_contacts__nationality"),
                    origin_country=F("patient_contacts__origin_country"),
                    quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                    source=F("patient_contacts__source"),
                    date_of_contact=F("patient_contacts__date_of_contact"),
                    created_by=F("patient_contacts__created_by_id__username"),
                )
                q_data_count = home_based_care.objects.filter(patient_contacts__county_id=user_county_id).count()
            elif (user_level == 4 or user_level == 6):
                print("inside SubCounty")
                user_sub_county_id = u.persons.sub_county
                print(user_sub_county_id)
                q_data = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).annotate(
                    first_name=F("patient_contacts__first_name"),
                    last_name=F("patient_contacts__last_name"),
                    sex=F("patient_contacts__sex"),
                    age=F("patient_contacts__dob"),
                    passport_number=F("patient_contacts__passport_number"),
                    phone_number=F("patient_contacts__phone_number"),
                    nationality=F("patient_contacts__nationality"),
                    origin_country=F("patient_contacts__origin_country"),
                    quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                    source=F("patient_contacts__source"),
                    date_of_contact=F("patient_contacts__date_of_contact"),
                    created_by=F("patient_contacts__created_by_id__username"),
                )
                q_data_count = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).count()
            elif (user_level == 7):
                print("inside Border")
                user_sub_county_id = u.persons.sub_county
                print(user_sub_county_id)
                q_data = home_based_care.objects.all().annotate(
                    first_name=F("patient_contacts__first_name"),
                    last_name=F("patient_contacts__last_name"),
                    sex=F("patient_contacts__sex"),
                    age=F("patient_contacts__dob"),
                    passport_number=F("patient_contacts__passport_number"),
                    phone_number=F("patient_contacts__phone_number"),
                    nationality=F("patient_contacts__nationality"),
                    origin_country=F("patient_contacts__origin_country"),
                    quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                    source=F("patient_contacts__source"),
                    date_of_contact=F("patient_contacts__date_of_contact"),
                    created_by=F("patient_contacts__created_by_id__username"),
                )
                q_data_count = home_based_care.objects.filter(patient_contacts__cormobidity="1").count()
            else:
                print("inside Facility")
                user_sub_county_id = u.persons.sub_county
                print(user_sub_county_id)
                q_data = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).annotate(
                    first_name=F("patient_contacts__first_name"),
                    last_name=F("patient_contacts__last_name"),
                    sex=F("patient_contacts__sex"),
                    age=F("patient_contacts__dob"),
                    passport_number=F("patient_contacts__passport_number"),
                    phone_number=F("patient_contacts__phone_number"),
                    nationality=F("patient_contacts__nationality"),
                    origin_country=F("patient_contacts__origin_country"),
                    quarantine_site=F("patient_contacts__quarantine_site_id__site_name"),
                    source=F("patient_contacts__source"),
                    date_of_contact=F("patient_contacts__date_of_contact"),
                    created_by=F("patient_contacts__created_by_id__username"),
                )
                q_data_count = home_based_care.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).count()

            cntry = country.objects.all()
            day = time.strftime("%Y-%m-%d")
            data = {'home_care_data': q_data, 'home_care_data_count': q_data_count, 'country': cntry, 'start_day': day,
                    'end_day': day}

    return render(request, 'veoc/home_care_list.html', data)


@login_required
def edit_home_care_list(request):
    return render(request, 'veoc/quarantinelist.html', values)


@login_required
def events_list(request):
    if request.method == "POST":
        uid = request.POST.get('uid', '')
        event_name = request.POST.get('event_name', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        dhis_event_type.objects.create(uid=uid, name=event_name)

    event_count = dhis_event_type.objects.all().count
    event_vals = dhis_event_type.objects.all()
    values = {'event_count': event_count, 'event_vals': event_vals}

    return render(request, 'veoc/eventlist.html', values)


@login_required
def site_list(request):
    if request.method == "POST":
        s_name = request.POST.get('site_name', '')
        lead_name = request.POST.get('lead_names', '')
        lead_phone = request.POST.get('lead_number', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        active = True

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        countyObject = organizational_units.objects.get(name=cnty)
        subcountyObject = organizational_units.objects.get(name=sub_cnty)

        # saving values to databse
        quarantine_sites.objects.create(site_name=s_name, team_lead_names=lead_name, active=active, county=countyObject,
                                        team_lead_phone=lead_phone, created_at=current_date, updated_at=current_date,
                                        subcounty=subcountyObject,
                                        created_by=userObject, updated_by=userObject)

    sites_count = quarantine_sites.objects.all().count
    site_vals = quarantine_sites.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    values = {'sites_count': sites_count, 'site_vals': site_vals, 'county': county}

    return render(request, 'veoc/quarantine_sites.html', values)


@login_required
def border_point(request):
    if request.method == "POST":
        border_name = request.POST.get('border_name', '')
        border_location = request.POST.get('border_location', '')
        lead_name = request.POST.get('lead_names', '')
        lead_phone = request.POST.get('lead_number', '')
        active = True

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        border_points.objects.create(border_name=border_name, border_location=border_location,
                                     team_lead_names=lead_name, active=active,
                                     team_lead_phone=lead_phone, created_at=current_date, updated_at=current_date,
                                     created_by=userObject, updated_by=userObject)

    borders_count = border_points.objects.all().count
    borders_vals = border_points.objects.all()
    values = {'borders_count': borders_count, 'borders_vals': borders_vals}

    return render(request, 'veoc/border_list.html', values)


@login_required
def weigh_site(request):
    if request.method == "POST":
        weighbridge_name = request.POST.get('weighbridge_name', '')
        weighbridge_location = request.POST.get('weighbridge_location', '')
        lead_name = request.POST.get('lead_names', '')
        lead_phone = request.POST.get('lead_number', '')
        active = True

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        weighbridge_sites.objects.create(weighbridge_name=weighbridge_name, weighbridge_location=weighbridge_location,
                                         team_lead_names=lead_name, active=active,
                                         team_lead_phone=lead_phone, created_at=current_date, updated_at=current_date,
                                         created_by=userObject, updated_by=userObject)

    weigh_site_count = weighbridge_sites.objects.all().count
    weigh_site_vals = weighbridge_sites.objects.all()
    values = {'weigh_site_count': weigh_site_count, 'weigh_site_vals': weigh_site_vals}

    return render(request, 'veoc/weighbridge_list.html', values)


@login_required
def edit_border_point(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        border_name = request.POST.get('border_name', '')
        lead_name = request.POST.get('lead_names', '')
        lead_phone = request.POST.get('lead_number', '')
        active = request.POST.get('active', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # updating values to database
        border_points.objects.filter(pk=myid).update(border_name=border_name, team_lead_names=lead_name,
                                                     team_lead_phone=lead_phone, active=active, updated_at=current_date,
                                                     updated_by=userObject)

    border_count = border_points.objects.all().count
    border_vals = border_points.objects.all()
    values = {'border_count': border_count, 'border_vals': border_vals}

    return render(request, 'veoc/border_list.html', values)


@login_required
def edit_weigh_site(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        weighbridge_name = request.POST.get('weighbridge_name', '')
        lead_name = request.POST.get('lead_names', '')
        lead_phone = request.POST.get('lead_number', '')
        active = request.POST.get('active', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # updating values to database
        weighbridge_sites.objects.filter(pk=myid).update(border_name=border_name, team_lead_names=lead_name,
                                                         team_lead_phone=lead_phone, active=active,
                                                         updated_at=current_date,
                                                         updated_by=userObject)

    weighbridge_count = weighbridge_sites.objects.all().count
    weighbridge_vals = weighbridge_sites.objects.all()
    values = {'weighbridge_count': weighbridge_count, 'weighbridge_vals': weighbridge_vals}

    return render(request, 'veoc/weighbridge_list.html', values)


@login_required
def edit_events_list(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        event_name = request.POST.get('event_name', '')

        # updating values to database
        dhis_event_type.objects.filter(pk=myid).update(name=event_name)

    event_count = dhis_event_type.objects.all().count
    event_vals = dhis_event_type.objects.all()
    values = {'event_count': event_count, 'event_vals': event_vals}

    return render(request, 'veoc/eventlist.html', values)


@login_required
def edit_site_list(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        s_name = request.POST.get('site_name', '')
        lead_name = request.POST.get('lead_names', '')
        cnty = request.POST.get('county', '')
        sub_cnty = request.POST.get('subcounty', '')
        lead_phone = request.POST.get('lead_number', '')
        active = request.POST.get('active', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)
        countyObject = organizational_units.objects.get(name=cnty)
        subcountyObject = organizational_units.objects.get(name=sub_cnty)

        # updating values to database
        quarantine_sites.objects.filter(pk=myid).update(site_name=s_name, team_lead_names=lead_name,
                                                        team_lead_phone=lead_phone, active=active,
                                                        updated_at=current_date,
                                                        updated_by=userObject, county=countyObject,
                                                        subcounty=subcountyObject)

    sites_count = quarantine_sites.objects.all().count
    site_vals = quarantine_sites.objects.all()
    values = {'sites_count': sites_count, 'site_vals': site_vals}

    return render(request, 'veoc/quarantine_sites.html', values)


def disgnation_list(request):
    if request.method == "POST":
        design = request.POST.get('designation', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        designation.objects.create(designation_description=design, updated_at=current_date,
                                   created_by=userObject, updated_by=userObject, created_at=current_date)

    designations_count = designation.objects.all().count
    designation_vals = designation.objects.all()
    values = {'designation_vals_count': designations_count, 'designation_vals': designation_vals}

    return render(request, 'veoc/disgnationlist.html', values)


def edit_disgnation_list(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        design = request.POST.get('description', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # updating values to database
        designation.objects.filter(pk=myid).update(designation_description=design, updated_at=current_date,
                                                   created_by=userObject, updated_by=userObject,
                                                   created_at=current_date)

    designations_count = designation.objects.all().count
    designation_vals = designation.objects.all()
    values = {'designation_vals_count': designations_count, 'designation_vals': designation_vals}

    return render(request, 'veoc/disgnationlist.html', values)


def data_list(request):
    if request.method == "POST":
        source = request.POST.get('data_source', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        data_source.objects.create(source_description=source, updated_at=current_date,
                                   created_by=userObject, updated_by=userObject, created_at=current_date)

    data_source_count = data_source.objects.all().count
    data_sources = data_source.objects.all()
    values = {'data_source_count': data_source_count, 'data_sources': data_sources}

    return render(request, 'veoc/datasourcelist.html', values)


@login_required
def edit_data_list(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        source = request.POST.get('data_source', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')
        print(myid)
        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        data_source.objects.filter(pk=myid).update(source_description=source, updated_at=current_date,
                                                   created_by=userObject, updated_by=userObject,
                                                   created_at=current_date)

    data_source_count = data_source.objects.all().count
    data_sources = data_source.objects.all()
    values = {'data_source_count': data_source_count, 'data_sources': data_sources}

    return render(request, 'veoc/datasourcelist.html', values)


def contact_list(request):
    if request.method == "POST":
        cont_type = request.POST.get('description', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # saving values to databse
        contact_type.objects.create(contact_description=cont_type, updated_at=current_date,
                                    created_by=userObject, updated_by=userObject, created_at=current_date)

    contact_types_count = contact_type.objects.all().count
    contact_types = contact_type.objects.all()
    values = {'contact_types_count': contact_types_count, 'contact_types': contact_types}

    return render(request, 'veoc/contacttypelist.html', values)


def call_register_form(request):
    form = forms.call_logs_form()
    return render(request, 'veoc.call_register.html', {'call_reg_form': form})


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
            uid=column[0],
            organisationunitid=column[1],
            name=column[2],
            code=column[3],
            parentid=column[4],
            hierarchylevel=column[5]
        )

    context = {}
    return render(request, 'veoc/upload_csv.html', context)


def process_idsr_data(request):
    org_units = organizational_units.objects.filter(hierarchylevel__gte=5).values_list('uid', flat=True).order_by('id')
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
    if request.method == "POST":
        allvals = dhis_disease_type.objects.all().order_by('name')
        serialized = serialize('json', allvals)
        obj_list = json.loads(serialized)

        return HttpResponse(json.dumps(obj_list), content_type="application/json")


def get_disease_cordinates(request):
    if request.method == "POST":
        dtype = request.POST.get('dtype', '')
        mydtype = dhis_disease_type.objects.get(name=dtype)
        allvals = list(disease.objects.filter(disease_type=mydtype).values('county__name', 'county__latitude',
                                                                           'county__longitude'))
        data = json.dumps(allvals)

    return HttpResponse(data, content_type="application/json")


def get_barchartvals(request):
    if request.method == 'POST':
        diseaseType = request.POST.get('dt', '')
        diseaseT = dhis_disease_type.objects.get(name=diseaseType)

        # for county in counties:
        call_count = call_log.objects.filter(disease_type=diseaseT).values('county__name')
        allvals = list(call_log.objects.filter(disease_type=diseaseT).values('county__name'))

        data = json.dumps(allvals)

        return HttpResponse(data, content_type="application/json")


@csrf_exempt
def get_pie_disease(request):
    if request.method == "POST":
        dtype = request.POST.get('dtype', '')
        mydtype = dhis_disease_type.objects.get(name=dtype)
        allvals2 = list(disease.objects.filter(disease_type=mydtype).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('county__name', 'subcounty__name').annotate(
            mytotal=Count('county__name')))

        data = json.dumps(allvals2)

    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def get_pie_event(request):
    if request.method == "POST":
        etype = request.POST.get('etype', '')
        myetype = dhis_event_type.objects.all().get(name=etype)
        allvals2 = list(event.objects.filter(event_type=myetype).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('county__name', 'subcounty__name').annotate(
            mytotal=Count('county__name')))
        data = json.dumps(allvals2)

    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def get_dhis_disease(request):
    print('inside get_dhis_diseases')
    if request.method == "POST":
        disease_type = request.POST.get('dhis_disease_type', '')
        mydisease_type = idsr_diseases.objects.get(name=disease_type)
        # my_disease_id = mydisease_type.id
        # print(my_disease_id)

        # dhis_graph_data = list(v_dhis_national_data_view.objects.all().filter(idsr_disease_id = mydisease_type).values('data_value', 'period', 'idsr_incident_id__name'))
        dhis_graph_data = list(
            v_dhis_national_report_data_view.objects.all().filter(idsr_disease_id=mydisease_type).values('cases',
                                                                                                         'deaths',
                                                                                                         'period'))
        print(dhis_graph_data)

        # pull cases associated with this deseases
        # my_disease_cases = list(idsr_weekly_national_report.objects.all().filter(idsr_disease_id = mydisease_type).filter(idsr_incident_id = 1).values('data_value', 'period', 'idsr_incident_id__name'))
        # my_disease_deaths = list(idsr_weekly_national_report.objects.all().filter(idsr_disease_id = mydisease_type).filter(idsr_incident_id = 2).values('data_value', 'period' ,'idsr_incident_id__name'))
        # cases = my_disease_cases + my_disease_deaths
        # print(cases)
        # allvals2 = list(idsr_weekly_national_report.objects.filter(idsr_disease_id=mydisease_type).values('idsr_disease_id__name','idsr_incident_id__name').annotate(casestotal=Count('data_value').annotate(deathtotal=Count('data_value')))
        #
        data = json.dumps(dhis_graph_data)

    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def get_piedrilldown_disease(request):
    if request.method == "POST":
        cty = request.POST.get('ctype', '')
        dty = request.POST.get('dtype', '')

        # myctype=organizational_units.objects.all().filter(hierarchylevel = 2).get(name=cty)
        myctype = organizational_units.objects.all().get(name=cty)
        mydtype = dhis_disease_type.objects.get(name=dty)
        allvals2 = list(disease.objects.filter(county=myctype, disease_type=mydtype).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('subcounty__name').annotate(
            mytotal=Count('subcounty__name')))

        data = json.dumps(allvals2)

    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def get_piedrilldown_event(request):
    if request.method == "POST":
        cty = request.POST.get('ctype', '')
        ety = request.POST.get('etype', '')
        print(cty)
        myctype = organizational_units.objects.all().filter(hierarchylevel=2).get(name=cty)
        myetype = dhis_event_type.objects.get(name=ety)
        allvals2 = list(event.objects.filter(county=myctype, event_type=myetype).filter(
            date_reported__gte=date.today() - timedelta(days=30)).values('subcounty__name').annotate(
            mytotal=Count('subcounty__name')))

        data = json.dumps(allvals2)

    return HttpResponse(data, content_type="application/json")


def get_chart_vals(request):
    global cases_data
    if request.method == "POST":
        chart_d_type = dhis_disease_type.objects.all().order_by('name')
        print(chart_d_type)
        _cases = []
        for crt_tpye in chart_d_type:
            disease_description = list(disease.objects.filter(disease_type_id=crt_tpye.id).filter(
                date_reported__gte=date.today() - timedelta(days=30)).values('disease_type__name', 'county__name',
                                                                             'subcounty__name', 'cases',
                                                                             'deaths').distinct())
            _cases.append(disease_description)
            print(_cases)
        cases_data = json.dumps(_cases)

        return HttpResponse(cases_data, content_type="application/json")

    else:
        return HttpResponse("No data.")


def get_disease_modal(request):
    if request.method == "POST":
        disease_type = dhis_disease_type.objects.all()
        all_data = []
        for disease_data in disease_type:
            call_log_data = call_log.objects.all().filter(disease_type_id=disease_data.id).order_by("-date_reported")[
                            :30]
            # call_log_data = list(Call_log.objects.all().filter(disease_type_id = disease_data.id).values('date', 'disease_type__id', 'county__id', 'subcounty__id', 'incident_status__id').order_by("-date_reported")[:30])
            # print the length to find loops
            # for call_data in call_log_data:
            data = list(call_log.objects.all().filter(disease_type_id=disease_data.id).values('disease_type__name',
                                                                                              'county__name',
                                                                                              'subcounty__name',
                                                                                              'location', 'description',
                                                                                              'incident_status__id',
                                                                                              'action_taken').distinct().order_by(
                "-date_reported")[:30])

            all_data.append(data)
        _data = json.dumps(all_data)
    # print(all_data)

    return HttpResponse(_data, content_type="application/json")


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


def Periodic_Report(request):
    return render(request, 'veoc/periodic_report.html')


def get_facilities_ward(request):
    if request.method == "POST":
        ward = request.POST.get('ward', '')
        print(ward)

        ward_parent_id = organizational_units.objects.get(organisationunitid=ward)
        allvals = list(
            organizational_units.objects.filter(parentid=ward_parent_id).values('name', 'latitude', 'longitude'))
        data = json.dumps(allvals)

    return HttpResponse(data, content_type="application/json")


def get_facilities_ward(request):
    if request.method == "POST":
        ward = request.POST.get('ward', '')
        print(ward)

        ward_parent_id = organizational_units.objects.get(organisationunitid=ward)
        allvals = list(
            organizational_units.objects.filter(parentid=ward_parent_id).values('name', 'latitude', 'longitude'))
        data = json.dumps(allvals)

    return HttpResponse(data, content_type="application/json")


def get_facilities_county(request):
    if request.method == "POST":
        # county = request.POST.get('county','')
        # print(county)

        # county_parent_id = organizational_units.objects.get(name = county)
        allvals = list(organizational_units.objects.filter(hierarchylevel=2).values('name', 'latitude', 'longitude'))
        data = json.dumps(allvals)

    return HttpResponse(data, content_type="application/json")


def get_quarantine_coordinates(request):
    if request.method == "POST":
        _id = request.POST.get('item_id', '')

        # print(_id)
        all_coords = list(
            quarantine_follow_up.objects.filter(patient_contacts_id=_id).values('follow_up_day', 'lat', 'lng'))
        my_coords = json.dumps(all_coords)

        # print(my_coords)

    return HttpResponse(my_coords, content_type="application/json")


def get_police_posts_county(request):
    if request.method == "POST":
        county = request.POST.get('county', '')
        print(county)

        # get county id where county = posted county
        # county_id = County.objects.values().filter(description=county).values_list('id')
        # print(county_id)

        # allvals=list(Police_posts.objects.values().filter(county=county_id))
        # print(allvals)

        # data=json.dumps(allvals)
        data = json.dumps(["allvals"])

        return HttpResponse(data, content_type="application/json")


def get_police_posts(request):
    if request.method == "POST":
        allvals = list(police_post.objects.values())
        print(allvals)

        data = json.dumps(allvals)

        return HttpResponse(data, content_type="application/json")


def get_lab_posts(request):
    if request.method == "POST":
        allvals = list(referral_labs.objects.values())

        data = json.dumps(allvals)

        return HttpResponse(data, content_type="application/json")


def week_shift(request):
    event = {'events': eoc_events_calendar.objects.all()}
    return render(request, 'veoc/weekly_shift.html', event)


def calendar_events_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')
        time = request.POST.get('time', '')

        cur_user = request.user.username
        created_by = User.objects.get(username=cur_user)

        insert = eoc_events_calendar(event_name=name, start_date=start_date, time=time,
                                     end_date=end_date, event_description=description, created_by=created_by,
                                     updated_by=created_by)

        insert.save()
        # find ways of retrieving the saved id and loop to send the success message after confirmation
        success = "Event created successfully"
        messages.success(request, success)
        # return HttpResponseRedirect("veoc/weekly_shift.html")
        return render(request, "veoc/weekly_shift.html",
                      {"success": success, 'events': eoc_events_calendar.objects.all()})

    else:
        success = "Contact not created,try again"
        messages.error(request, success)
        return render(request, "veoc/weekly_shift.html",
                      {"success": success, 'events': eoc_events_calendar.objects.all()})


def eoc_contacts(request):
    contacts_count = staff_contact.objects.all().count
    eocContacts = staff_contact.objects.all()
    design = designation.objects.all()
    eoc = {'eocContacts': eocContacts, 'designation': design,
           'contacts_count': contacts_count}

    return render(request, 'veoc/surveillance_contacts.html', eoc)


def eoc_contacts_create(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        designatn = request.POST.get('designation', '')
        phone_number = request.POST.get('phone_number', '')
        email_address = request.POST.get('email_address', '')
        team_lead = request.POST.get('lead', '')

        if not team_lead:
            team_lead = False
        else:
            team_lead = True

        designation_source = designation.objects.get(designation_description=designatn)
        cur_user = request.user.username
        created_by = User.objects.get(username=cur_user)

        day = time.strftime("%Y-%m-%d")

        insert = staff_contact(first_name=first_name, last_name=last_name, designation=designation_source,
                               phone_number=phone_number,
                               email_address=email_address, team_lead=team_lead, created_by=created_by,
                               updated_by=created_by)
        insert.save()

        success = "Contact created successfully"
        messages.success(request, success)

        return render(request, "veoc/surveillance_contacts.html",
                      {"success": success, 'eocContacts': staff_contact.objects.all(),
                       'designation': designation.objects.all()})

    else:
        success = "Contact not created,try again"
        messages.error(request, success)
        return render(request, "veoc/surveillance_contacts.html",
                      {"success": success, 'eocContacts': staff_contact.objects.all(),
                       'designation': designation.objects.all()})


def contact_edit(request):
    if request.method == 'POST':
        contacts_id = request.POST.get('id', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        designatn = request.POST.get('designation', '')
        phone_number = request.POST.get('phone_number', '')
        email_address = request.POST.get('email_address', '')
        team_lead = request.POST.get('lead', '')

        if not team_lead:
            team_lead = False
        else:
            team_lead = True

        designation_source = designation.objects.get(pk=designatn)
        cur_user = request.user.username
        created_by = User.objects.get(username=cur_user)

        day = time.strftime("%Y-%m-%d")

        staff_contact.objects.filter(pk=contacts_id).update(first_name=first_name,
                                                            last_name=last_name, designation=designation_source,
                                                            phone_number=phone_number,
                                                            email_address=email_address, team_lead=team_lead,
                                                            created_by=created_by, updated_by=created_by)

        success = "Contact updated successfully"
        messages.success(request, success)

        return render(request, "veoc/surveillance_contacts.html",
                      {"success": success, 'eocContacts': staff_contact.objects.all(),
                       'designation': designation.objects.all()})

    else:
        success = "Contact not created,try again"
        messages.error(request, success)
        return render(request, "veoc/surveillance_contacts.html",
                      {"success": success, 'eocContacts': staff_contact.objects.all(),
                       'designation': designation.objects.all()})


def allocation_sheet(request):
    return render(request, 'veoc/alocation_sheet.html')


def contact_json(request):
    all_ = staff_contact.objects.all()
    # print('inside contact_json')
    # print(all_)
    serialized = serialize('json', all_, use_natural_foreign_keys=True, use_natural_primary_keys=True)
    obj_list = json.loads(serialized)
    # print(obj_list)

    return HttpResponse(json.dumps(obj_list), content_type='application/json')


def get_existing_timetable(request):
    all_ = watcher_schedule.objects.all()

    serialized = serialize('json', all_, use_natural_foreign_keys=True, use_natural_primary_keys=True)
    obj_list = json.loads(serialized)

    return HttpResponse(json.dumps(obj_list), content_type='application/json')


def get_timetables(request):
    if request.method == 'POST':
        contactarray = request.POST.getlist('contactsarray[]')
        fdate = request.POST.get('fromdate', '')
        tdate = request.POST.get('todate', '')

        # looks for the week number of the date
        d = fdate.split('-')
        wkno = date(int(d[0]), int(d[1]), int(d[2])).isocalendar()[1]
        # print(wkno)

        for x in contactarray:
            print(x)
            cur_user = request.user.username
            created_by = User.objects.get(username=cur_user)
            watchr_details = staff_contact.objects.get(pk=x)
            insertingcont = watcher_schedule(watcher_details=watchr_details, week_no=wkno, from_date=fdate,
                                             to_date=tdate, created_by=created_by, updated_by=created_by)
            insertingcont.save()

            # send email to the contacts saved to be watchers
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

    myresponse = "success adding contacts to timetable"
    data = json.dumps(myresponse)

    return HttpResponse(data, content_type="application/json")


def search_watchers(request):
    if request.method == 'POST':
        search_date = request.POST.get('searchdate', '')
        time_table = watcher_schedule.objects.values('from_date', 'to_date', 'week_no').distinct()

        for x in time_table:
            from_d = x['from_date']
            to_d = x['to_date']
            wkno = x['week_no']

            q_data = from_d < search_date < to_d
            if q_data:
                myresponse = watcher_schedule.objects.all().filter(from_date=from_d, to_date=to_d)

                serialized = serialize('json', myresponse, use_natural_foreign_keys=True, use_natural_primary_keys=True)
                obj_list = json.loads(serialized)
                data = json.dumps(obj_list)

                break
            else:
                myresponse = "No watchers set for the week " + str(wkno) + " selected"
                data = json.dumps(myresponse)

    return HttpResponse(data, content_type="application/json")


def get_existing_timetable(request):
    all_ = watcher_schedule.objects.all()

    serialized = serialize('json', all_, use_natural_foreign_keys=True, use_natural_primary_keys=True)
    obj_list = json.loads(serialized)

    return HttpResponse(json.dumps(obj_list), content_type='application/json')


def watchers_schedule(request):
    # select watchers set for current week and over not past teams
    current_date = date.today().strftime('%Y-%m-%d')
    d = current_date.split('-')
    current_wkno = date(int(d[0]), int(d[1]), int(d[2])).isocalendar()[1]
    w = watcher_schedule.objects.filter(week_no__gte=current_wkno)
    watch = {'watchers': w}

    return render(request, 'veoc/watchers_schedule.html', watch)


def all_contact(request):
    all_contacts = contact.objects.all()
    contact_count = contact.objects.all().count
    designatn = designation.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    c_type = contact_type.objects.all()

    values = {'contacts': all_contacts, 'contact_count': contact_count, 'designations': designatn, 'county': county,
              'contact_types': c_type}

    # return render(request, 'veoc/contact.html', values)
    return render(request, 'veoc/cont.html', values)


def add_contact(request):
    if request.method == 'POST':
        f_name = request.POST.get('first_name', '')
        l_name = request.POST.get('last_name', '')
        design = request.POST.get('designation', '')
        phone = request.POST.get('phone_no', '')
        email = request.POST.get('email', '')
        c_type = request.POST.get('contact_type', '')
        cnty = request.POST.get('county', '')
        subcnty = request.POST.get('subcounty', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        designationObject = designation.objects.get(pk=design)
        contactTypeObject = contact_type.objects.get(pk=c_type)
        countyObject = organizational_units.objects.get(name=cnty)
        subcountyObject = organizational_units.objects.get(organisationunitid=subcnty)

        # saving values to database
        contact.objects.create(designation=designationObject, type_of_contact=contactTypeObject, county=countyObject,
                               subcounty=subcountyObject,
                               first_name=f_name, last_name=l_name, phone_number=phone, email_address=email,
                               updated_at=current_date, created_by=userObject, updated_by=userObject,
                               created_at=current_date)

    all_contacts = contact.objects.all()
    contact_count = contact.objects.all().count
    designatn = designation.objects.all()
    county = organizational_units.objects.all().filter(hierarchylevel=2).order_by('name')
    c_type = contact_type.objects.all()

    values = {'contacts': all_contacts, 'contact_count': contact_count, 'designations': designatn, 'county': county,
              'contact_types': c_type}

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
    if request.method == 'POST':
        cat = request.POST.get('category', '')
        descriptn = request.POST.get('description', '')
        authr = request.POST.get('author', '')
        file = request.FILES.get('file', '')
        public = request.POST.get('public', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        print(current_user)
        print(file)
        userObject = User.objects.get(pk=current_user.id)
        categoryObject = repository_categories.objects.get(pk=cat)

        # saving values to database
        doc_rep = document_repository()
        doc_rep.category = categoryObject
        doc_rep.description = descriptn
        doc_rep.author = authr
        doc_rep.myfile = file
        doc_rep.public_document = public
        doc_rep.updated_at = current_date
        doc_rep.created_by = userObject
        doc_rep.updated_by = userObject
        doc_rep.created_at = current_date
        doc_rep.save()

        if cat == '1':
            documents_count = document_repository.objects.all().filter(category=1).count
            documents = document_repository.objects.all().filter(category=1)
            template = 'veoc/minutes.html'
        elif cat == '2':
            documents_count = document_repository.objects.all().filter(category=2).count
            documents = document_repository.objects.all().filter(category=2)
            template = 'veoc/sitrep.html'
        elif cat == '3':
            documents_count = document_repository.objects.all().filter(category=3).count
            documents = document_repository.objects.all().filter(category=3)
            template = 'veoc/bulletins.html'
        elif cat == '4':
            documents_count = document_repository.objects.all().filter(category=4).count
            documents = document_repository.objects.all().filter(category=4)
            template = 'veoc/publications.html'
        elif cat == '5':
            documents_count = document_repository.objects.all().filter(category=5).count
            documents = document_repository.objects.all().filter(category=5)
            template = 'veoc/others.html'
        elif cat == '6':
            documents_count = document_repository.objects.all().filter(category=6).count
            documents = document_repository.objects.all().filter(category=6)
            template = 'veoc/protocol.html'
        elif cat == '7':
            documents_count = document_repository.objects.all().filter(category=7).count
            documents = document_repository.objects.all().filter(category=7)
            template = 'veoc/out_report.html'
        elif cat == '8':
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
    if request.method == 'POST':
        myid = request.POST.get('id', '')
        cat = request.POST.get('category', '')
        descriptn = request.POST.get('description', '')
        authr = request.POST.get('author', '')
        file = request.FILES.get('file', '')
        public = request.POST.get('public', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        print(current_user)
        print(file)
        userObject = User.objects.get(pk=current_user.id)
        categoryObject = repository_categories.objects.get(pk=cat)

        # saving edited values to database
        document_repository.objects.filter(pk=myid).update(category=categoryObject,
                                                           description=descriptn, author=authr, myfile=file,
                                                           public_document=public,
                                                           updated_at=current_date, created_by=userObject,
                                                           updated_by=userObject,
                                                           created_at=current_date)

        if cat == '1':
            documents_count = document_repository.objects.all().filter(category=1).count
            documents = document_repository.objects.all().filter(category=1)
            template = 'veoc/minutes.html'
        elif cat == '2':
            documents_count = document_repository.objects.all().filter(category=2).count
            documents = document_repository.objects.all().filter(category=2)
            template = 'veoc/sitrep.html'
        elif cat == '3':
            documents_count = document_repository.objects.all().filter(category=3).count
            documents = document_repository.objects.all().filter(category=3)
            template = 'veoc/bulletins.html'
        elif cat == '4':
            documents_count = document_repository.objects.all().filter(category=4).count
            documents = document_repository.objects.all().filter(category=4)
            template = 'veoc/publications.html'
        elif cat == '5':
            documents_count = document_repository.objects.all().filter(category=5).count
            documents = document_repository.objects.all().filter(category=5)
            template = 'veoc/others.html'
        elif cat == '6':
            documents_count = document_repository.objects.all().filter(category=6).count
            documents = document_repository.objects.all().filter(category=6)
            template = 'veoc/protocol.html'
        elif cat == '7':
            documents_count = document_repository.objects.all().filter(category=7).count
            documents = document_repository.objects.all().filter(category=7)
            template = 'veoc/out_report.html'
        elif cat == '8':
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

def airline_reg(request):
    if request.method == "POST":
        myid = request.POST.get('id', '')
        cat = request.POST.get('category', '')
        descriptn = request.POST.get('description', '')
        authr = request.POST.get('author', '')
        file = request.FILES.get('file', '')
        public = request.POST.get('public', '')

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        day = time.strftime("%Y-%m-%d")

        values = {'country':cntry,'county':county, 'day':day}


    return render(request, 'veoc/airline_travellers.html', values)


# forgot password function allowing user to change their password
def forgot_password(request):
    if request.method == "POST":
        searched_email = request.POST.get('search_field', '')
        # added a try and catch so if the email entered does not exist the user can be informed
        try:
            email_details = User.objects.get(email=searched_email)
            # an email is sent to inform the user of the password change
            if email_details != '':
                email_values = {'email_details': email_details}
                subject = 'Jitenge Password Reset'
                message = 'Dear ' + email_details.first_name + ',' + '\n' + 'You have requested for a password reset on the Jitenge System. Your new password is  ' + email_details.email + '. They password is case sesnitive. Please login with your new credentials here: https://ears.mhealthkenya.co.ke/login/' + '\n' + 'Thank You. ' + '\n' + 'Jitenge System.'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [email_details.email]
                send_mail(subject, message, email_from, recipient_list)
                # print(values);

                # user = User.objects.set_password(email_details.email)
                email_details.set_password(email_details.email)
                email_details.save()

                # return HttpResponse("Kindly check your email for further instructions to recover your account")
                messages.success(request, 'We have sent you recovery instructions to your email')
            elif email_details.count > 1:
                messages.success(request, 'Multiple users with this email exist.')
            else:
                return render(request, 'veoc/forgot_password.html')
        except ObjectDoesNotExist:
            # return HttpResponse("That Email does not exist")
            messages.error(request, 'Email does not exist')
    return render(request, 'veoc/forgot_password.html')


def module_feedback(request):
    if request.method == 'POST':
        id = request.POST.get('id', '')
        challnge = request.POST.get('challange', '')
        recomm = request.POST.get('recommendation', '')
        is_adressed = request.POST.get('is_adressed', '')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        feedback.objects.filter(pk=id).update(challenge=challnge, recommendation=recomm,
                                              challange_addressed=is_adressed, updated_by=userObject,
                                              updated_at=current_date)

    modules = system_modules.objects.all()
    feedback_count = feedback.objects.all().count
    feedbacks = feedback.objects.all()

    values = {'modules': modules, 'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/feedback.html', values)


def add_feedback(request):
    if request.method == 'POST':
        module = request.POST.get('module', '')
        report_date = request.POST.get('report_date', '')
        challnge = request.POST.get('challange', '')
        recomm = request.POST.get('recommendation', '')
        reporter = request.POST.get('user', '')
        is_adressed = request.POST.get('is_adressed', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        # print(current_user)
        # print(challnge)
        userObject = User.objects.get(pk=current_user.id)
        moduleTypeObject = system_modules.objects.get(pk=module)

        # saving values to database
        feedback.objects.create(module_type=moduleTypeObject, challenge=challnge, recommendation=recomm,
                                challange_addressed=is_adressed, updated_at=current_date, created_by=userObject,
                                updated_by=userObject, created_at=current_date)

    modules = system_modules.objects.all()
    feedback_count = feedback.objects.all().count
    feedbacks = feedback.objects.all()

    values = {'modules': modules, 'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/feedback.html', values)


def edit_feedback(request):
    if request.method == 'POST':
        myid = request.POST.get('feedback_id', '')
        module = request.POST.get('module', '')
        report_date = request.POST.get('report_date', '')
        challnge = request.POST.get('challange', '')
        recomm = request.POST.get('recommendation', '')
        reporter = request.POST.get('user', '')
        is_adressed = request.POST.get('is_adressed', '')

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        # get current user
        current_user = request.user
        # print(current_user)
        # print(challnge)
        # print(myid)
        userObject = User.objects.get(pk=current_user.id)
        moduleTypeObject = system_modules.objects.get(pk=module)

        # saving edited values to database
        feedback.objects.filter(pk=myid).update(module_type=moduleTypeObject,
                                                challenge=challnge, recommendation=recomm,
                                                challange_addressed=is_adressed,
                                                updated_at=current_date, created_by=userObject, updated_by=userObject,
                                                created_at=current_date)

    modules = system_modules.objects.all()
    feedback_count = feedback.objects.all().count
    feedbacks = feedback.objects.all()

    values = {'modules': modules, 'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/feedback.html', values)


def module_general_feedback(request):
    if request.method == 'POST':
        challnge = request.POST.get('challange', '')
        is_adressed = request.POST.get('is_adressed', '')

        # get user to update_by
        current_user = request.user
        userObject = User.objects.get(pk=current_user.id)
        # print(userObject)

        # get todays date
        current_date = date.today().strftime('%Y-%m-%d')

        general_feedback.objects.create(challenge=challnge,
                                        challange_addressed=is_adressed, updated_at=current_date,
                                        created_by=userObject, updated_by=userObject, created_at=current_date)

    feedback_count = general_feedback.objects.all().count
    feedbacks = general_feedback.objects.all()

    values = {'feedback_count': feedback_count, 'feedbacks': feedbacks}

    return render(request, 'veoc/gen_feedback.html', values)
