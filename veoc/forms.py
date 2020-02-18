from django import forms
from django.contrib.auth.models import User
from veoc.models import *


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = user_profile
        accesslevel = forms.ModelChoiceField(queryset=accesslevel.objects.all().order_by('id'))
        county = forms.ModelChoiceField(queryset=county.objects.all().order_by('description'))
        subcounty = forms.ModelChoiceField(queryset=sub_county.objects.all().order_by('subcounty'))
        fields = ('accesslevel', 'county', 'subcounty')
