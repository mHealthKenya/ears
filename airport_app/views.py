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
    return render(request, 'airport_app/airport_register.html')


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

    quar_sites = weighbridge_sites.objects.all().order_by('weighbridge_name')
    bord_points = border_points.objects.all().order_by('border_name')
    truck_cont_details = []
    q_data_count = 0
    context = {}
    data = {}
    if user_level == 1 or user_level == 2:

        if request.method == 'POST':
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')

            print("inside National")
            # add a border point filter to enable filtering specific border point--------
            q_data_count = quarantine_contacts.objects.filter(date_of_contact__gte=date_from,
                                                              date_of_contact__lte=date_to). \
                filter(source='WEB REGISTRATION').count()
            q_data = airline_quarantine.objects.filter(patient_contacts__date_of_contact__gte=date_from,
                                                       patient_contacts__date_of_contact__lte=date_to,
                                                       patient_contacts__source='WEB REGISTRATION'). \
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
            data = {'quarantine_data_count': q_data_count, 'weigh_name': quar_sites, 'border_points': bord_points,
                    'my_list_data': my_list_data, 'start_day': day, 'end_day': day, 'page_obj': page_obj}

            return render(request, 'airport_app/airport_list.html', data)

        else:
            print("inside National")
            # add a border point filter to enable filtering specific border point--------
            q_data_count = quarantine_contacts.objects.all().filter(source='WEB REGISTRATION').count()
            my_model = airline_quarantine.objects.filter(patient_contacts__source='WEB REGISTRATION'). \
                order_by('-patient_contacts__date_of_contact')

            paginator = Paginator(my_model, 10)
            page_number = request.GET.get('page')
            try:
                page_obj = paginator.page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            my_list_data = page_obj
            day = time.strftime("%Y-%m-%d")
            data = {'quarantine_data_count': q_data_count, 'weigh_name': quar_sites, 'border_points': bord_points,
                    'my_list_data': my_list_data, 'start_day': day, 'end_day': day, 'page_obj': page_obj}

            return render(request, 'airport_app/airport_list.html', data)

    elif user_level == 7:

        if request.method == 'POST':
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')

            print("inside Border")
            # find ways of filtering data based on the border point-------
            q_data_count = quarantine_contacts.objects.filter(date_of_contact__gte=date_from,
                                                              date_of_contact__lte=date_to).filter(
                source='Truck Registration').count()
            q_data = quarantine_contacts.objects.filter(source='Truck Registration').filter(
                date_of_contact__gte=date_from, date_of_contact__lte=date_to).order_by('-date_of_contact')
            for d in q_data:
                t_details = truck_quarantine_contacts.objects.filter(patient_contacts=d.id).filter(
                    border_point__border_name=user_access_level).values_list('border_point__border_name',
                                                                             flat=True).first()
                print(t_details)
                truck_cont_details.append(t_details)

        else:
            print("inside Border")
            # find ways of filtering data based on the border point-------
            q_data_count = quarantine_contacts.objects.all().filter(source='Truck Registration').count()
            q_data = quarantine_contacts.objects.filter(source='Truck Registration').order_by('-date_of_contact')
            for d in q_data:
                t_details = truck_quarantine_contacts.objects.filter(patient_contacts=d.id).filter(
                    border_point__border_name=user_access_level).values_list('border_point__border_name',
                                                                             flat=True).first()
                # print(t_details)
                truck_cont_details.append(t_details)
    else:
        if request.method == 'POST':
            # border_point = request.POST.get('border_point','')
            date_from = request.POST.get('date_from', '')
            date_to = request.POST.get('date_to', '')

            print("inside non border users")
            q_data_count = quarantine_contacts.objects.filter(date_of_contact__gte=date_from,
                                                              date_of_contact__lte=date_to).filter(
                source='Kitu hakuna').count()
            q_data = quarantine_contacts.objects.filter(source='Kitu hakuna').filter(date_of_contact__gte=date_from,
                                                                                     date_of_contact__lte=date_to).order_by(
                '-date_of_contact')
            for d in q_data:
                t_details = truck_quarantine_contacts.objects.filter(patient_contacts=d.id)
                truck_cont_details.append(t_details)

        else:
            print("inside non border users")
            q_data_count = quarantine_contacts.objects.all().filter(source='Kitu hakuna').count()
            q_data = quarantine_contacts.objects.filter(source='Kitu hakuna').order_by('-date_of_contact')
            for d in q_data:
                t_details = truck_quarantine_contacts.objects.filter(patient_contacts=d.id)
                truck_cont_details.append(t_details)

        my_list_data = zip(q_data, truck_cont_details)

        data = {'quarantine_data_count': q_data_count, 'weigh_name': quar_sites, 'border_points': bord_points,
                'my_list_data': my_list_data, 'start_day': date_from, 'end_day': date_to}

        my_list_data = zip(q_data, truck_cont_details)
        print(context['page_obj'])

        day = time.strftime("%Y-%m-%d")
        data = {'quarantine_data_count': q_data_count, 'weigh_name': quar_sites, 'border_points': bord_points,
                'my_list_data': my_list_data, 'start_day': day, 'end_day': day}
        print(truck_cont_details)

    return render(request, 'airport_app/airport_list.html', data)


@login_required
def airport_follow_up(request):

    qua_contacts = quarantine_contacts.objects.all().filter(source__contains="Truck Registration")
    follow_data = quarantine_follow_up.objects.filter(patient_contacts__source="WEB REGISTRATION")
    follow_data_count = quarantine_follow_up.objects.filter(patient_contacts__source="WEB REGISTRATION").count()

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
    return render(request, 'airport_app/airport_follow_up.html', data)


@login_required
def airport_symtomatic(request):
    return render(request, 'airport_app/airport_symptomatic.html')


@login_required
def complete_airport(request):
    return render(request, 'airport_app/complete_airport.html')
