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

    return render(request, 'airport_app/airport_register.html')
