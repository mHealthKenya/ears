from rest_framework import  serializers
from rest_framework.serializers import CharField
from .models import *

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
        fields = ('id', 'disease_type', 'data_source', 'incident_status', 'county', 'subcounty', 'ward', 'reporting_region','date_reported',
        'cases', 'deaths', 'remarks','action_taken', 'significant')

        read_only_fields = ('disease_type',)
        depth = 1

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = event
        fields = ('id', 'event_type', 'data_source', 'incident_status', 'county', 'subcounty', 'reporting_region','date_reported',
        'cases', 'deaths', 'remarks','action_taken', 'significant_event', 'created_by', 'updated_by')
