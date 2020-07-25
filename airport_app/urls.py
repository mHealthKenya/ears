import django
from django.conf.urls import url, include
from rest_framework import routers
from . import views
from django.conf import settings
# from . import views, settings
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

#TEMPLATE TAGGING
app_name = 'airport_app'

urlpatterns = [
    #url('api/', include(router.urls)),
    url(r'^airport_register/$', views.airport_register, name='airport_register'),
    url(r'^airport_list/$', views.airport_list, name='airport_list'),
    url(r'^airport_follow_up/$', views.airport_follow_up, name='airport_follow_up'),
    url(r'^airport_symptomatic/$', views.airport_symtomatic, name='airport_symtomatic'),
    url(r'^complete_airport/$', views.complete_airport, name='complete_airport'),
    ]

# urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
