import json
# import request
import urllib.request as request
import csv
# import pickle
import http.client

from veoc.models import *

def save_dhis_idsr_data(org_units, url):
    """saves data from dhis2 into veoc database, idsr_results table"""

    querystring = {"dimension": [
           "dx:ZQiG8Aidl8J.dCd7yKlyqk4;ZQiG8Aidl8J.GR4pbqLKhMV;ZQiG8Aidl8J.PTWBeC1K2HJ;ZQiG8Aidl8J.EqEj84xFkHz;RGozddXpuwI.dCd7yKlyqk4;RGozddXpuwI.GR4pbqLKhMV;RGozddXpuwI.PTWBeC1K2HJ;RGozddXpuwI.EqEj84xFkHz;ycHTiTrGfHi.dCd7yKlyqk4;ycHTiTrGfHi.GR4pbqLKhMV;ycHTiTrGfHi.PTWBeC1K2HJ;ycHTiTrGfHi.EqEj84xFkHz;YjkS8YBwtM3.dCd7yKlyqk4;YjkS8YBwtM3.GR4pbqLKhMV;YjkS8YBwtM3.PTWBeC1K2HJ;YjkS8YBwtM3.EqEj84xFkHz;wajkorhT4I5.dCd7yKlyqk4;wajkorhT4I5.GR4pbqLKhMV;wajkorhT4I5.PTWBeC1K2HJ;wajkorhT4I5.EqEj84xFkHz;TVbSuL9AdcI.dCd7yKlyqk4;TVbSuL9AdcI.GR4pbqLKhMV;TVbSuL9AdcI.PTWBeC1K2HJ;TVbSuL9AdcI.EqEj84xFkHz;tn0o15uvfgP.dCd7yKlyqk4;tn0o15uvfgP.GR4pbqLKhMV;tn0o15uvfgP.PTWBeC1K2HJ;tn0o15uvfgP.EqEj84xFkHz;sL7vw21TOKw.dCd7yKlyqk4;sL7vw21TOKw.GR4pbqLKhMV;sL7vw21TOKw.PTWBeC1K2HJ;sL7vw21TOKw.EqEj84xFkHz;GJDppyWOYYM.dCd7yKlyqk4;GJDppyWOYYM.GR4pbqLKhMV;GJDppyWOYYM.PTWBeC1K2HJ;GJDppyWOYYM.EqEj84xFkHz;lJotmrRnSnD.dCd7yKlyqk4;lJotmrRnSnD.GR4pbqLKhMV;lJotmrRnSnD.PTWBeC1K2HJ;lJotmrRnSnD.EqEj84xFkHz;Tz0tiCQ8o6X.dCd7yKlyqk4;Tz0tiCQ8o6X.GR4pbqLKhMV;Tz0tiCQ8o6X.PTWBeC1K2HJ;Tz0tiCQ8o6X.EqEj84xFkHz;IVT5avXg4CC.dCd7yKlyqk4;IVT5avXg4CC.GR4pbqLKhMV;IVT5avXg4CC.PTWBeC1K2HJ;IVT5avXg4CC.EqEj84xFkHz;SLnpLPVE4RI.dCd7yKlyqk4;SLnpLPVE4RI.GR4pbqLKhMV;SLnpLPVE4RI.PTWBeC1K2HJ;SLnpLPVE4RI.EqEj84xFkHz;eH7m94f1Mrv.dCd7yKlyqk4;eH7m94f1Mrv.GR4pbqLKhMV;eH7m94f1Mrv.PTWBeC1K2HJ;eH7m94f1Mrv.EqEj84xFkHz;rnUg5fAPgxU.dCd7yKlyqk4;rnUg5fAPgxU.GR4pbqLKhMV;rnUg5fAPgxU.PTWBeC1K2HJ;rnUg5fAPgxU.EqEj84xFkHz;LsOkVqvtIrA.dCd7yKlyqk4;LsOkVqvtIrA.GR4pbqLKhMV;LsOkVqvtIrA.PTWBeC1K2HJ;LsOkVqvtIrA.EqEj84xFkHz;WXmC1SmmY8j.dCd7yKlyqk4;WXmC1SmmY8j.GR4pbqLKhMV;WXmC1SmmY8j.PTWBeC1K2HJ;WXmC1SmmY8j.EqEj84xFkHz;BBZVk4BJ62Y.VOGsN2CJ4V9;BBZVk4BJ62Y.AElGEFxvUmt;S8DADvgv6Gy.dCd7yKlyqk4;S8DADvgv6Gy.GR4pbqLKhMV;S8DADvgv6Gy.PTWBeC1K2HJ;S8DADvgv6Gy.EqEj84xFkHz;JVnFrA3WVI5.dCd7yKlyqk4;JVnFrA3WVI5.GR4pbqLKhMV;JVnFrA3WVI5.PTWBeC1K2HJ;JVnFrA3WVI5.EqEj84xFkHz;wU5FlwAagjX.dCd7yKlyqk4;wU5FlwAagjX.GR4pbqLKhMV;wU5FlwAagjX.PTWBeC1K2HJ;wU5FlwAagjX.EqEj84xFkHz;dvgrSof8WCi.dCd7yKlyqk4;dvgrSof8WCi.GR4pbqLKhMV;dvgrSof8WCi.PTWBeC1K2HJ;dvgrSof8WCi.EqEj84xFkHz;ODvEuLyeZP5.Gs4AqH6n3mV;ODvEuLyeZP5.FIYMDBzdabP;ODvEuLyeZP5.dbZfB6Oub9K;ODvEuLyeZP5.ROXPeIvP89X;jm11FQme3t0.Gs4AqH6n3mV;jm11FQme3t0.FIYMDBzdabP;jm11FQme3t0.dbZfB6Oub9K;jm11FQme3t0.ROXPeIvP89X;HW4qfFRzitH.Gs4AqH6n3mV;HW4qfFRzitH.FIYMDBzdabP;HW4qfFRzitH.dbZfB6Oub9K;HW4qfFRzitH.ROXPeIvP89X;IYnqoV2vlRq.Gs4AqH6n3mV;IYnqoV2vlRq.FIYMDBzdabP;IYnqoV2vlRq.dbZfB6Oub9K;IYnqoV2vlRq.ROXPeIvP89X;LwwVppGxNJk.dCd7yKlyqk4;LwwVppGxNJk.GR4pbqLKhMV;LwwVppGxNJk.PTWBeC1K2HJ;LwwVppGxNJk.EqEj84xFkHz;NQwgklXIeG2.dCd7yKlyqk4;NQwgklXIeG2.GR4pbqLKhMV;NQwgklXIeG2.PTWBeC1K2HJ;NQwgklXIeG2.EqEj84xFkHz",
           "pe:2018", "ou:LEVEL-5;GOhRziVaDUw"], "displayProperty": "NAME"}

    for org_unit in org_units:
        org_entity = str(org_unit)
        querystring["dimension"][2] = 'ou:'+ org_entity

        headers = {
            'authorization': "Basic SURTUjpTdXJ2ZWlsbGFuY2VAMjAxOQ==",
            'cache-control': "no-cache",
            'postman-token': "c5c6b7c3-8e47-7483-57b3-3091929e9d40"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        my_array = response.json()
        # print(my_array)

        try:
            #pulling values from the arrays
           data_sets = (my_array['rows'][0][0])
           period = (my_array['rows'][0][1])
           organization_unit = (my_array['rows'][0][2])
           data_value = (my_array['rows'][0][3])

           #Splitting the orgs to get the actual case values and the diseases
           data_elements = data_sets.split(".")
           incident_element = data_elements[0]
           disease_element = data_elements[1]

           #get database primarykeys to save in idsr_report DataTable
           disease_id = idsr_diseases.objects.filter(name = disease_element).values_list('id', flat=True)
           incident_id = idsr_reported_incidents.objects.filter(name = incident_element).values_list('id', flat=True)
           org_unit_id = organizational_units.objects.filter(name = organization_unit).values_list('id', flat=True)

           #saving data to the idsr_report table
           idsr_weekly_report.objects.create(idsr_disease_id = disease_id, idsr_incident_id = incident_id, org_unit_id = org_unit_id,
           period = period, data_value = data_value)

           print (count, "Record inserted successfully into mobile table")

           print("incident_element {} and disease_element {} period {} organization_unit {} data_value {}".format(incident_element, disease_element, period, organization_unit, data_value))


        except (IndexError, KeyError) as error:
           # key or index is missing, handle an unexpected response
           print ("Oops,Error while fetching data from array -> ", error)
