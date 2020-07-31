import django
from django.conf.urls import url, include
from rest_framework import routers
from veoc import views
from django.conf import settings
# from . import views, settings
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

#TEMPLATE TAGGING
app_name = 'veoc'

router = routers.DefaultRouter()
router.register('disease_types', views.disease_type_view)
router.register('event_types', views.event_type_view)
router.register('data_source', views.data_source_view)
router.register('reporting_region', views.reporting_region_view)
router.register('incident_status', views.incident_status_view)
# router.register('organizational_units', views.organizational_unit_view)
router.register('diseases', views.DiseaseView)
router.register('events', views.EventView)
router.register(r'trucker_list', views.AlbumViewSet, 'foobar-detail')

urlpatterns = [
    url(r'^airport_register/$', views.airport_register, name='airport_register'),
    #url(r'^airport_complete/$', views.airport_complete, name='airport_complete'),
    url(r'^edit_airport_complete/$', views.edit_airport_complete, name='edit_airport_complete'),
    url(r'^airport_list_incomplete/$', views.airport_list_incomplete, name='airport_list_incomplete'),
    url(r'^export_csv/$', views.export_csv, name='export_csv'),
    url(r'^truck_export_csv/$', views.truck_export_csv, name='truck_export_csv'),
    url(r'^raw_quarantine_contacts_csv/$', views.raw_quarantine_contacts_csv, name='raw_quarantine_contacts_csv'),
    url(r'^raw_follow_up_csv/$', views.raw_follow_up_csv, name='raw_follow_up_csv'),
    url(r'^raw_lab_results_csv/$', views.raw_lab_results_csv, name='raw_lab_results_csv'),
    url(r'^$', views.login, name='login'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^edit_profile/$', views.edit_profile, name='edit_profile'),
    url(r'^access_dashboard/$', views.access_dashboard, name='access_dashboard'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^county_dashboard/$', views.county_dashboard, name='county_dashboard'),
    url(r'^subcounty_dashboard/$', views.subcounty_dashboard, name='subcounty_dashboard'),
    url(r'^border_dashboard/$', views.border_dashboard, name='border_dashboard'),
    url(r'^facility_dashboard/$', views.facility_dashboard, name='facility_dashboard'),
    url(r'^call_register/$', views.call_register, name='call_register'),
    url(r'^disease_register/$', views.disease_register, name='disease_register'),
    url(r'^event_register/$', views.event_register, name='event_register'),
    url(r'^quarantine_register/$', views.quarantine_register, name='quarantine_register'),
    url(r'^home_care_register/$', views.home_care_register, name='home_care_register'),
    url(r'^quarantine_file_register/$', views.quarantine_excel, name='exupload'),
    url(r'^line_listing/$', views.line_lising_excel, name='moh_line_listing'),
    url(r'^quarantine_template/$', views.download_template, name='quarantine_template'),
    url(r'^line_list_template/$', views.moh_line_listing_template, name='line_listing_template'),
    url(r'^truck_driver_profile/(?P<profileid>[0-9]+)/$', views.truck_driver_profile, name='truck_driver_profile'),
    url(r'^truck_driver_revisit/(?P<profileid>[0-9]+)/$', views.truck_driver_revisit, name='truck_driver_revisit'),
    url(r'^truck_driver_register/$', views.truck_driver_register, name='truck_driver_register'),
    url(r'^truck_driver_revisit/$', views.truck_driver_revisit, name='truck_driver_revisit'),
    url(r'^truck_driver_edit/$', views.truck_driver_edit, name='truck_driver_edit'),
    url(r'^truck_driver_lab_test/$', views.truck_driver_lab_test, name='truck_driver_lab_test'),
    url(r'^lab_certificate/$', views.lab_certificate, name='lab_certificate'),
    url(r'^feedback_create/$', views.feedback_create, name='feedback_create'),
    url(r'^feedback_report/$', views.feedback_report, name='feedback_report'),
    url(r'^upload_csv/$', views.upload_csv, name='upload_csv'),

    url(r'^call_report/$', views.call_report, name='call_report'),
    url(r'^raw_data_downloads/$', views.raw_data_downloads, name='raw_data_downloads'),
    url(r'^filter_call_report/$', views.filter_call_report, name='filter_call_report'),
    url(r'^unrelated_call_report/$', views.unrelated_call_report, name='unrelated_call_report'),
    url(r'^filter_unrelated_call_report/$', views.filter_unrelated_call_report, name='filter_unrelated_call_report'),
    url(r'^disease_report/$', views.disease_report, name='disease_report'),
    url(r'^infectious_disease_report/$', views.infectious_disease_report, name='infectious_disease_report'),
    url(r'^filter_disease_report/$', views.filter_disease_report, name='filter_disease_report'),
    url(r'^events_report/$', views.events_report, name='events_report'),
    url(r'^filter_events_report/$', views.filter_events_report, name='filter_events_report'),
    url(r'^ongoing_tasks/$', views.ongoing_tasks, name='ongoing_tasks'),
    url(r'^line_list_data/$', views.line_list_data, name='line_list_data'),
    url(r'^quarantine_list/$', views.quarantine_list, name='quarantine_list'),
    url(r'^home_care_list/$', views.home_care_list, name='home_care_list'),
    # url(r'^t_q_list_json/$', views.t_q_list_json, name='t_q_list_json'),
    url(r'^truck_quarantine_list/$', views.truck_quarantine_list, name='truck_quarantine_list'),
    url(r'^quarantine_site_report/$', views.quarantine_site_data, name='quarantine_site_data'),
    url(r'^follow_up/$', views.follow_up, name='follow_up'),
    url(r'^symptomatic_cases/$', views.symptomatic_cases, name='symptomatic_cases'),
    url(r'^home_care_follow_up/$', views.home_care_follow_up, name='home_care_follow_up'),
    url(r'^home_care_symtomatic/$', views.home_care_symtomatic, name='home_care_symtomatic'),
    url(r'^truck_follow_up/$', views.truck_follow_up, name='truck_follow_up'),
    url(r'^truck_symptomatic_cases/$', views.truck_symptomatic_cases, name='truck_symptomatic_cases'),
    # url(r'^follow_up/$', views.f_up, name='f_up'),
    url(r'^complete_quarantine/$', views.complete_quarantine, name='complete_quarantine'),
    url(r'^complete_home_care/$', views.complete_home_care, name='complete_home_care'),
    url(r'^truck_ongoing_quarantine/$', views.truck_ongoing_quarantine, name='truck_ongoing_quarantine'),
    url(r'^truck_complete_quarantine/$', views.truck_complete_quarantine, name='truck_complete_quarantine'),
    url(r'^get_quarantine_coordinates/$', views.get_quarantine_coordinates, name='get_quarantine_coordinates'),
    url(r'^filter_ongoing_tasks/$', views.filter_ongoing_tasks, name='filter_ongoing_tasks'),
    url(r'^case_definition/$', views.case_definition, name='case_definition'),

    url(r'^(?P<id>\d+)/disease_view/$', views.disease_view),
    url(r'^(?P<id>\d+)/event_view/$', views.event_view),
    url(r'^(?P<id>\d+)/call_log_view/$', views.call_log_view),

    url(r'^daily_reports/$', views.daily_reports, name='daily_reports'),
    url(r'^daily_report_submit/$', views.daily_report_submit, name='daily_report_submit'),
    url(r'^weekly_reports/$', views.weekly_report, name='weekly_report'),
    url(r'^weekly_report_submit/$', views.weekly_report_submit, name='weekly_report_submit'),
    url(r'^periodic_reports/$', views.Periodic_Report, name='periodic_reports'),

    url(r'^profile/$', views.user_profile, name='user_profile'),

    url(r'^idsr_data/$', views.idsr_data, name='idsr_data'),
    url(r'^reportable_diseases/$', views.reportable_diseases, name='reportable_diseases'),
    url(r'^reportable_diseases_filters/$', views.reportable_diseases_filters, name='reportable_diseases_filters'),
    url(r'^reportable_event/$', views.reportable_event, name='reportable_event'),
    url(r'^upload_csv/$', views.process_idsr_data, name='process_idsr_data'),
    url(r'^generate_pdf/$', views.generate_pdf, name='generate_pdf'),
    url(r'^get_org_unit/$', views.get_org_unit, name='get_org_unit'),

    #Settings Urls
    url(r'^users_list/$', views.users_list, name='users_list'),
    url(r'^user_register/$', views.user_register, name='user_register'),
    url(r'^usersubcounty/$', views.usersubcounty, name='usersubcounty'),
    url(r'^get_group/$', views.get_group, name='get_group'),
    url(r'^diseases_list/$', views.diseases_list, name='diseases_list'),
    url(r'^edit_quarantine_list/$', views.edit_quarantine_list, name='edit_quarantine_list'),
    url(r'^edit_home_isolation_list/$', views.edit_home_isolation_list, name='edit_home_isolation_list'),
    url(r'^edit_home_care_list/$', views.edit_home_care_list, name='edit_home_care_list'),
    url(r'^edit_diseases_list/$', views.edit_diseases_list, name='edit_diseases_list'),
    url(r'^events_list/$', views.events_list, name='events_list'),
    url(r'^border_point/$', views.border_point, name='border_point'),
    url(r'^weigh_site/$', views.weigh_site, name='weigh_site'),
    url(r'^site_list/$', views.site_list, name='site_list'),
    url(r'^edit_events_list/$', views.edit_events_list, name='edit_events_list'),
    url(r'^edit_site_list/$', views.edit_site_list, name='edit_site_list'),
    url(r'^edit_border_point/$', views.edit_border_point, name='edit_border_point'),
    url(r'^edit_weigh_site/$', views.edit_weigh_site, name='edit_weigh_site'),
    url(r'^disgnation_list/$', views.disgnation_list, name='disgnation_list'),
    url(r'^edit_disgnation_list/$', views.edit_disgnation_list, name='edit_disgnation_list'),
    url(r'^data_list/$', views.data_list, name='data_list'),
    url(r'^edit_data_list/$', views.edit_data_list, name='edit_data_list'),
    url(r'^contact_list/$', views.contact_list, name='contact_list'),

    url(r'^get_county/$', views.get_county, name='get_county'),
    url(r'^get_subcounty/$', views.get_subcounty, name='get_subcounty'),
    url(r'^get_ward/$', views.get_ward, name='get_ward'),

    #GIS urls
    url(r'^disease_mappings/$', views.disease_mappings,name='disease_mappings'),
    url(r'^facilities_mappings/$', views.facilities_mappings,name='facilities_mappings'),
    url(r'^get_facilities_county/$', views.get_facilities_county,name='get_facilities_county'),
    url(r'^get_facilities_ward/$', views.get_facilities_ward,name='get_facilities_ward'),
    url(r'^police_post_mappings/$', views.police_post_mappings,name='police_post_mappings'),
    url(r'^get_police_posts_county/$', views.get_police_posts_county,name='get_police_posts_county'),
    # url(r'^get_lab_posts_county/$', views.get_lab_posts_county,name='get_lab_posts_county'),
    url(r'^lab_referrals_mappings/$', views.lab_referrals_mappings,name='lab_referrals_mappings'),
    # url(r'^get_facilities/$', views.get_facilities,name='get_facilities'),
    url(r'^get_police_posts/$', views.get_police_posts,name='get_police_posts'),
    url(r'^get_lab_posts/$', views.get_lab_posts,name='get_lab_posts'),
    url(r'^heat_maps/$', views.heat_maps,name='heat_maps'),

    #EOC STAFF
    url(r'^week_shift/$', views.week_shift, name='week_shift'),
    url(r'^calendar_events_create/', views.calendar_events_create, name='calendar_events_create'),
    url(r'^eoc_cont/$', views.eoc_contacts, name='eoc_cont'),
    url(r'^eoc_contacts_create/', views.eoc_contacts_create, name='eoc_contacts_create'),
    url(r'^eoc_contact_edit/', views.contact_edit, name='eoc_contact_edit'),
    url(r'^allocation_sheet/$', views.allocation_sheet, name='allocation_sheet'),
    url(r'^contact_json/$', views.contact_json, name='contact_json'),
    url(r'^get_existing_timetable/$', views.get_existing_timetable, name='get_existing_timetable'),
    url(r'^get_timetables/$', views.get_timetables, name='get_timetables'),
    url(r'^search_watchers/$', views.search_watchers, name='search_watchers'),
    # url(r'^get_existing_timetable/$', views.get_existing_timetable, name='get_existing_timetable'),
    url(r'^watchers_schedule/$', views.watchers_schedule, name='watchers_schedule'),

    #Contacts
    # url(r'^all_contacts/', views.All_contacts_report, name='all_contacts'),
    # url(r'^(?P<id>\d+)/contact_type/$', views.Contact_type_report),
    # url(r'^all_contacts_edited/(?P<editid>[0-9]+)/$', views.all_contact_edit, name='all_contacts_edited'),
    # url(r'^all_contact_edited_submit/', views.contacts_edited_submit,name='all_contact_edited_submit'),
    url(r'^all_contact/', views.all_contact,name='all_contact'),
    url(r'^add_contact/', views.add_contact,name='add_contact'),

    #Document managers
    url(r'^minutes/$', views.minutes, name='minutes'),
    url(r'^sitreps/$', views.sitreps, name='sitreps'),
    url(r'^protocol/$', views.protocol, name='protocol'),
    url(r'^out_report/$', views.out_report, name='out_report'),
    url(r'^bulletins/$', views.bulletins, name='bulletins'),
    url(r'^publications/$', views.publications, name='publications'),
    url(r'^case_documents/$', views.case_documents, name='case_documents'),
    url(r'^others/$', views.others, name='others'),
    url(r'^sops/$', views.sops, name='sops'),
    url(r'^add_document/$', views.add_document, name='add_document'),
    url(r'^edit_document/$', views.edit_document, name='edit_document'),
    url(r'^public_document/$', views.public_document, name='public_document'),
    url(r'^airline_reg/$', views.airline_reg, name='airline_reg'),
    url(r'^forgot_password/$', views.forgot_password, name='forgot_password'),

    #Feedback section
    url(r'^module_feedback/$', views.module_feedback, name='module_feedback'),
    url(r'^add_feedback/$', views.add_feedback, name='add_feedback'),
    url(r'^edit_feedback/$', views.edit_feedback, name='edit_feedback'),
    url(r'^module_general_feedback/$', views.module_general_feedback, name='module_general_feedback'),

    url(r'^call_flashback/$', views.call_flashback, name='call_flashback'),
    url(r'^google_map/$', views.google_map, name='google_map'),
    url(r'^data_map/$', views.data_map, name='data_map'),
    url(r'^facility_map/$', views.facility_map, name='facility_map'),
    url(r'^police_map/$', views.police_map, name='police_map'),
    url(r'^lab_refferal_map/$', views.lab_refferal_map, name='lab_refferal_map'),
    # url(r'^flot_charts/$', views.flot_charts, name='flot_charts'),
    # url(r'^bar_charts/$', views.bar_charts, name='bar_charts'),
    # url(r'^line_charts/$', views.line_charts, name='line_charts'),
    # url(r'^area_charts/$', views.area_charts, name='area_charts'),

    url(r'^get_diseases/', views.get_diseases,name='get_diseases'),
    url(r'^get_disease_cordinates/', views.get_disease_cordinates,name='get_disease_cordinates'),
    # url(r'^get_barchartvals/$', views.get_barchartvals, name='get_barchartvals'),
    url(r'^get_chart_vals/$', views.get_chart_vals,name='get_chart_vals'),
    url(r'^get_disease_modal/$', views.get_disease_modal,name='get_disease_modal'),
    url(r'^get_pie_disease/', views.get_pie_disease,name='get_pie_disease'),
    url(r'^get_pie_event/', views.get_pie_event,name='get_pie_event'),
    url(r'^get_piedrilldown_disease/', views.get_piedrilldown_disease,name='get_piedrilldown_disease'),
    url(r'^get_piedrilldown_event/', views.get_piedrilldown_event,name='get_piedrilldown_event'),
    url(r'^get_dhis_disease/', views.get_dhis_disease,name='get_dhis_disease'),

# Forms url
    url(r'^call_register_form/$', views.call_register_form, name='call_register_form'),
]

urlpatterns += router.urls
# urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
