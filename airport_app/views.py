#from django.shortcuts import render

# Create your views here.
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
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from django.conf import settings
from django.core.serializers import serialize
from django.db import IntegrityError, transaction
from django.db.models import *
from django.core.paginator import Paginator
from django.http import FileResponse
from veoc.models import *
from airport_app.models import *
from veoc.forms import *
from django.views.decorators.csrf import *
#from . import forms
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
        fever = request.POST.get('fever','')
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
        else :
            countyObject = organizational_units.objects.get(organisationunitid = 18)
            subcountyObject = organizational_units.objects.get(organisationunitid = 18)
            wardObject = organizational_units.objects.get(organisationunitid = 18)

        user_phone = "+254"
        #check if the leading character is 0
        if str(phone_number[0]) == "0":
            user_phone = user_phone + str(phone_number[1:])
            # print("number leading with 0")
        else:
            user_phone = user_phone + str(phone_number)
            # print("number not leading with 0")

        #get todays date
        current_date = datetime.now()

        #get current user
        current_user = request.user
        print(current_user)
        userObject = User.objects.get(pk = current_user.id)
        site_name = "Home"
        qua_site = quarantine_sites.objects.get(site_name = site_name)
        contact_save = ''
        source = "Web Registration"
        contact_identifier = uuid.uuid4().hex
        #Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number = phone_number, first_name = first_name, last_name=last_name)
        if details_exist :
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(mob_ex.created_at))

            return HttpResponse("error")
        else:
            #saving values to databse
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name, middle_name=middle_name,
            county=countyObject, subcounty=subcountyObject, ward=wardObject,sex=sex, dob=dob, passport_number=passport_number,
            phone_number=phone_number, email_address=email_address, date_of_contact=date_of_arrival, source=source,
            nationality=nationality, drugs="no", nok=nok, nok_phone_num=nok_phone_number, cormobidity="None",
            origin_country=origin_country, place_of_diagnosis="Airport", quarantine_site=qua_site,contact_uuid=contact_identifier,
            updated_at=current_date, created_by=userObject, updated_by=userObject, created_at=current_date)

            contact_save.save()
            trans_one = transaction.savepoint()

            patients_contacts_id = contact_save.pk
            print(patients_contacts_id)
            patientObject = quarantine_contacts.objects.get(pk = patients_contacts_id)
            if patients_contacts_id:

                airport_user_save = airline_quarantine.objects.create(airline=airline, flight_number=flight_number, seat_number=seat_number, destination_city=destination_city, travel_history=countries_visited, cough=cough, breathing_difficulty=breathing_difficulty, fever=fever, chills=chills, temperature=fever, measured_temperature=measured_temperature,arrival_airport_code=arrival_airport_code, released=released, risk_assessment_referal=risk_assessment_referal, designated_hospital_referal=designated_hospital_referal, created_at=current_date, updated_at=current_date, patients_contacts_id=patientObject, created_by_id=userObject, updated_by_id=userObject, residence=residence, estate=estate, postal_address=postal_address, status="Active")

                airport_user_save.save()
            else:
                print("not working")


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
        qua_site = quarantine_sites.objects.all().filter(active = True).order_by('site_name')
        day = time.strftime("%Y-%m-%d")

        data = {'country':cntry,'county':county, 'day':day, 'qua_site':qua_site}

        return render(request, 'airport_app/airport_register.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        qua_site = quarantine_sites.objects.all().filter(active = True).order_by('site_name')
        day = time.strftime("%Y-%m-%d")

        data = {'country':cntry,'county':county, 'day':day, 'qua_site':qua_site}

        return render(request, 'airport_app/airport_register.html', data)

@login_required
def airport_list(request):

    return render(request, 'airport_app/airport_list.html')

@login_required
def airport_follow_up(request):

    return render(request, 'airport_app/airport_follow_up.html')

@login_required
def airport_symtomatic(request):

    return render(request, 'airport_app/airport_symtomatic.html')

@login_required
def complete_airport(request):

    return render(request, 'airport_app/complete_airport.html')
