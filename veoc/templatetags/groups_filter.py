from django import template
from django.contrib.auth.models import Group


register = template.Library()

@register.filter(name='has_group')
def has_group(x,group_name):
    group = Group.objects.get(name=group_name)

    try:
        return group in x.groups.all()
    except:
        group = None