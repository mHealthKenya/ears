from rest_framework import serializers
from rest_framework.serializers import CharField
from .models import *
from dateutil import relativedelta


class DiseaseTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = dhis_disease_type
        fields = ('uid',)
        # fields = ('id', 'uid', 'name', 'priority_disease')


class EventTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = dhis_event_type
        fields = ('name',)
        # fields = ('id', 'uid', 'name')


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = data_source
        fields = ('source_description',)
        # fields = ('id', 'source_description')


class ReportingRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = reporting_region
        fields = ('id', 'region_description')


class IncidentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = incident_status
        fields = ('status_description',)


class ReportingRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = reporting_region
        fields = ('region_description',)


class OrganizationalUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = organizational_units
        fields = ('name',)
        # fields = ('id', 'uid','organisationunitid','name','parentid','hierarchylevel')


class DiseaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    disease_type = DiseaseTypesSerializer()
    data_source = DataSourceSerializer()
    incident_status = IncidentStatusSerializer()
    county = OrganizationalUnitsSerializer()
    subcounty = OrganizationalUnitsSerializer()
    ward = OrganizationalUnitsSerializer()
    reporting_region = ReportingRegionSerializer()

    class Meta:
        model = disease
        fields = (
        'id', 'disease_type', 'data_source', 'incident_status', 'county', 'subcounty', 'ward', 'reporting_region',
        'date_reported',
        'cases', 'deaths', 'remarks', 'action_taken', 'significant')

        read_only_fields = ('disease_type',)
        depth = 1


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = event
        fields = ('id', 'event_type', 'data_source', 'incident_status', 'county', 'subcounty', 'reporting_region',
                  'date_reported',
                  'cases', 'deaths', 'remarks', 'action_taken', 'significant_event', 'created_by', 'updated_by')


class QuarantineSerializer(serializers.ModelSerializer):
    class Meta:
        model = quarantine_contacts
        fields = '__all__'


class BorderSerializer(serializers.ModelSerializer):
    class Meta:
        model = border_points
        fields = '__all__'


class TruckSerializer(serializers.ModelSerializer):
    patient_contacts = serializers.PrimaryKeyRelatedField(queryset=quarantine_contacts.objects.all())
    border_point = serializers.PrimaryKeyRelatedField(queryset=border_points.objects.all())

    class Meta:
        model = truck_quarantine_contacts        
        fields = ('company_phone', 'patient_contacts', 'company_street', 'breathing_difficulty', 'border_point',)

    def to_representation(self, value):
        data = super().to_representation(value)
        print(value)
        con_serializer = QuarantineSerializer(value.patient_contacts)
        mode_serializer = BorderSerializer(value.border_point)
        data['patient_contacts'] = con_serializer.data
        data['border_point'] = mode_serializer.data
        data['patient_contacts']['created_by'] = User.objects.get(id=data['patient_contacts']['created_by']).username
        date1 = datetime.strptime(str(date.today()), '%Y-%m-%d')
        date2 = datetime.strptime(data['patient_contacts']['dob'], '%Y-%m-%d')
        diff = relativedelta.relativedelta(date1, date2)
        if diff.years == 0:
            diff.years = "Unknown"
        data['patient_contacts']['dob'] = diff.years
        data['patient_contacts'].update({'truck_prof': "<a href=\"/truck_driver_profile/" + str(
            data['patient_contacts'][
                'id']) + "\" class=\"btn btn-info btn-sm pull-left\" title=\"View Profile\"><i class=\"fa fa-eye\"></i></a>"})
        data['patient_contacts'].update({'truck_info': "<button type=\"button\" id=\"map_view\" class=\"btn btn-info "
                                                       "btn-sm pull-left map_view\"\n data-toggle=\"modal\" "
                                                       "data-target=\"#mapViewModal\" data-id=\""
                                                       + str(data['patient_contacts']['id']) + "\" data-names=\""
                                                       + data['patient_contacts']['first_name'] + ' '
                                                       + data['patient_contacts'][
                                                           'last_name'] + "\" data-last_contact=\""
                                                       + data['patient_contacts']['date_of_contact']
                                                       + "\" data-phone_number=\""
                                                       + data['patient_contacts']['phone_number'] +
                                                       "\" title=\"Open Map View\"> <i class=\"fa fa-map-marker\">\ " \
                                                       "</i> </button>"})

        return data
