import os

import requests
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
from django.contrib.auth.decorators import login_required
import csv, io
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from django.conf import settings
from django.core.serializers import serialize
from django.db import IntegrityError, transaction
from django.db.models import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import FileResponse

from .models import *
from veoc.models import *
from airport_app.models import *
from veoc.forms import *
from django.views.decorators.csrf import *
# from . import forms
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
        temperature = request.POST.get('measured_temperature','')
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

        user_phone = "+254"
        #check if the leading character is 0
        if str(phone_number[0]) == "0":
            user_phone = user_phone + str(phone_number[1:])
            # print("number leading with 0")
        else:
            user_phone = user_phone + str(phone_number)
            # print("number not leading with 0")

        # get current user
        current_user = request.user
        user_id = current_user.id
        # print(current_user)
        userObject = User.objects.get(pk=current_user.id)
        #weigh_site = weighbridge_sites.objects.get(weighbridge_name=weighbridge_name)
        #bord_name = border_points.objects.get(border_name=border_name)
        #site_name = ''
        quar_site = quarantine_sites.objects.filter(site_name="Country Border")
        for site in quar_site:
            site_name = site.id

        contact_save = ''
        current_date = datetime.now()
        source = "Airport Registration"
        # Check if mobile number exists in the table
        details_exist = quarantine_contacts.objects.filter(phone_number=phone_number, first_name=first_name,
                                                           last_name=last_name,
                                                           date_of_contact__gte=date.today() - timedelta(days=14))
        if details_exist:
            for mob_ex in details_exist:
                print("Details exist Phone Number" + str(mob_ex.phone_number) + "Registered on :" + str(
                    mob_ex.created_at))

            return HttpResponse("error")
        else:
            language = 1
            quarantineObject = quarantine_sites.objects.get(pk=site_name)
            languageObject = translation_languages.objects.get(pk=language)
            contact_identifier = uuid.uuid4().hex
            # saving values to quarantine_contacts database first
            contact_save = quarantine_contacts.objects.create(first_name=first_name, last_name=last_name,
                                                              middle_name=middle_name,
                                                              county=countyObject, subcounty=subcountyObject,
                                                              ward=wardObject, sex=sex, dob=dob,
                                                              passport_number=passport_number,
                                                              phone_number=phone_number, date_of_contact=date_of_arrival,
                                                              communication_language=languageObject,
                                                              nationality=nationality, drugs="No", nok=nok,
                                                              nok_phone_num=nok_phone_number, cormobidity="None",
                                                              origin_country=origin_country,
                                                              quarantine_site=quarantineObject, source=source,
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
                    airport_user_save = airline_quarantine.objects.create(airline=airline, flight_number=flight_number, seat_number=seat_number, destination_city=destination_city, travel_history=countries_visited, cough=cough, breathing_difficulty=breathing_difficulty, fever=fever, chills=chills, temperature=temperature, measured_temperature=measured_temperature,arrival_airport_code=arrival_airport_code, released=released, risk_assessment_referal=risk_assessment_referal, designated_hospital_refferal=designated_hospital_referal, created_at=current_date, updated_at=current_date, patient_contacts_id=patient_id, created_by_id=user_id, updated_by_id=user_id, residence=residence, estate=estate, postal_address=postal_address, status="True")

                    airport_user_save.save()
                except IntegrityError:
                    transaction.savepoint_rollback(trans_one)
                    return HttpResponse("error")

            patients_contacts_id = contact_save.pk
            print(patients_contacts_id)
            print(patients_contacts_id)
            patientObject = quarantine_contacts.objects.get(pk = patients_contacts_id)
            if contact_save:
                print("in")
                airport_user_save = airline_quarantine.objects.create(airline=airline, flight_number=flight_number, seat_number=seat_number, destination_city=destination_city, travel_history=countries_visited, cough=cough, breathing_difficulty=breathing_difficulty, fever=fever, chills=chills, temperature=fever, measured_temperature=measured_temperature,arrival_airport_code=arrival_airport_code, released=released, risk_assessment_referal=risk_assessment_referal, designated_hospital_referal=designated_hospital_referal, created_at=current_date, updated_at=current_date, patients_contacts_id=patientObject, created_by_id=userObject, updated_by_id=userObject, residence=residence, estate=estate, postal_address=postal_address, status="Active")


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

        return render(request, 'airport_app/airport_register.html', data)

    else:
        cntry = country.objects.all()
        county = organizational_units.objects.all().filter(hierarchylevel = 2).order_by('name')
        day = time.strftime("%Y-%m-%d")

        data = {'country':cntry,'county':county, 'day':day}

        return render(request, 'airport_app/airport_register.html', data)


@login_required
def airport_list(request):
    current_user = request.user
    u = User.objects.get(username=current_user.username)
    user_access_level = u.persons.access_level
    print("Access Level---", user_access_level)

    user_level = ""
    user_group = request.user.groups.values_list('id', flat=True)
    # print(user_group)
    for grp in user_group:
        user_level = grp
    # print(user_level)

    bord_points = border_points.objects.all().order_by('border_name')
    truck_cont_details = []

    if request.method == 'POST':
        if user_level == 1 or user_level == 2:
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')

            print("inside National")
            q_data_count = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(patient_contacts__date_of_contact__gte=date_from, patient_contacts__date_of_contact__lte=date_to). \
                filter(patient_contacts__source='Airport Registration').count()
            q_data = airline_quarantine.objects.select_related('patient_contacts') \
                .filter(patient_contacts__date_of_contact__gte=date_from,
                        patient_contacts__date_of_contact__lte=date_to,
                        patient_contacts__source='Airport Registration'). \
                order_by('-patient_contacts__date_of_contact')

        elif user_level == 7:
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')

            print("inside Border")
            # find ways of filtering data based on the border point-------
            q_data_count = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(patient_contacts__date_of_contact__gte=date_from, patient_contacts__date_of_contact__lte=date_to). \
                filter(patient_contacts__source='Airport Registration').count()
            q_data = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(border_point__border_name=user_access_level,
                       patient_contacts__source='Airport Registration',
                       patient_contacts__date_of_contact__gte=date_from,
                       patient_contacts__date_of_contact__lte=date_to). \
                order_by('-patient_contacts__date_of_contact')

        else:
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')

            print("inside non border users")
            q_data_count = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(patient_contacts__date_of_contact__gte=date_from, patient_contacts__date_of_contact__lte=date_to). \
                filter(patient_contacts__source='Kitu hakuna').count()
            q_data = airline_quarantine.objects.select_related('patient_contacts'). \
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
            q_data_count = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Airport Registration').count()
            q_data = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Airport Registration').order_by('-patient_contacts__date_of_contact')

        elif user_level == 7:
            print("inside Border")
            # find ways of filtering data based on the border point-------
            q_data_count = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Airport Registration').count()
            q_data = airline_quarantine.objects.select_related('patient_contacts'). \
                filter(patient_contacts__source='Airport Registration', border_point__border_name=user_access_level). \
                order_by('-date_of_contact')

        else:
            print("inside non border users")
            q_data_count = airline_quarantine.objects.select_related('patient_contacts').filter(
                patient_contacts__source='Kitu hakuna').count()
            q_data = airline_quarantine.objects.select_related('patient_contacts'). \
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
        data = {'quarantine_data_count': q_data_count, 'my_list_data': my_list_data, 'start_day': day, 'end_day': day, 'page_obj': page_obj}

    return render(request, 'airport_app/airport_list.html', data)


#@login_required
def airport_follow_up(request):

    qua_contacts = quarantine_contacts.objects.all().filter(source__contains="Airport Registration")
    follow_data = quarantine_follow_up.objects.filter(patient_contacts__source="Airport Registration")
    follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__source="Airport Registration").count()

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
        search_symptoms(f_data)

    data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'page_obj': page_obj}
    return render(request, 'airport_app/airport_follow_up.html', data)


@login_required
def airport_symtomatic(request):
    qua_contacts = quarantine_contacts.objects.all().filter(source__contains="Airport Registration")
    follow_data = quarantine_follow_up.objects.filter(patient_contacts__source="Airport Registration").filter(
        Q(body_temperature__gte=38) | Q(fever='YES') | Q(cough='YES') | Q(difficulty_breathing='YES'))
    follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__source="Airport Registration").filter(
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
        search_symptoms(f_data)

    data = {'follow_data': follow_data, 'follow_data_count': follow_data_count}

    return render(request, 'airport_app/airport_symptomatic.html', data)


@login_required
def complete_airport(request):
    return render(request, 'airport_app/complete_airport.html')


def search_symptoms(f_data):
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

@login_required
def complete_airport(request):
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
            patient_contacts__source='Airport Registration')
        follow_data_count = quarantine_follow_up.objects.filter(
            patient_contacts__source='Airport Registration').count()

    elif (user_access_level == "County"):
        user_county_id = u.persons.county_id
        print(user_county_id)
        follow_data = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Airport Registration').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__county_id=user_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Airport Registration').count()

    elif (user_access_level == "SubCounty"):
        user_sub_county_id = u.persons.sub_county_id
        print(user_sub_county_id)
        follow_data = quarantine_follow_up.objects.filter(patient_contacts__subcounty_id=user_sub_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Airport Registration').order_by('-created_at')
        follow_data_count = quarantine_follow_up.objects.filter(
            patient_contacts__subcounty_id=user_sub_county_id).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Airport Registration').count()

    else:
        follow_data = quarantine_contacts.objects.filter(self_quarantine=False).filter(
            created_at__lte=date.today() - timedelta(days=14)).filter(
            patient_contacts__source='Airport Registration').order_by('-created_at')
        follow_data_count = quarantine_contacts.objects.filter(self_quarantine=False).filter(
            patient_contacts__source='Airport Registration').count()

    paginator = Paginator(follow_data, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    data = {'follow_data': follow_data, 'follow_data_count': follow_data_count, 'page_obj': page_obj}

    return render(request, 'airport_app/complete_airport.html', data)
