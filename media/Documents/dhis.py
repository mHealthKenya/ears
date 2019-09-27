import psycopg2
import requests
import urllib.request as request
import json
import http.client
import csv
import pickle
from urllib.parse import parse_qs

try:
    #EADC database connection
    # connection = psycopg2.connect(user="postgres",
    #                               password="NC`{}?!lmn45",
    #                               host="197.248.10.20",
    #                               port="5432",
    #                               database="veoc")

    #local database connection
    connection = psycopg2.connect(user="postgres",
                                 password="postgres",
                                 host="localhost",
                                 port="5432",
                                 database="veoc")
    cursor = connection.cursor()
    select = "select uid,id,name from veoc_organizational_units where hierarchylevel >= 5 order by id asc"
    cursor.execute(select)
    result = (cursor.fetchall())

    for value in result:

        val = str(value[0])
        id = str(value[1])
        facility = str(value[2])
        # val='BDMjYavKpVQ'
        print(val)

        import requests

        url = "https://testhis.uonbi.ac.ke/api/29/analytics.json"

        querystring = {"dimension": [
            "dx:ZQiG8Aidl8J.dCd7yKlyqk4;ZQiG8Aidl8J.GR4pbqLKhMV;ZQiG8Aidl8J.PTWBeC1K2HJ;"
            "ZQiG8Aidl8J.EqEj84xFkHz;RGozddXpuwI.dCd7yKlyqk4;RGozddXpuwI.GR4pbqLKhMV;"
            "RGozddXpuwI.PTWBeC1K2HJ;RGozddXpuwI.EqEj84xFkHz;ycHTiTrGfHi.dCd7yKlyqk4;"
            "ycHTiTrGfHi.GR4pbqLKhMV;ycHTiTrGfHi.PTWBeC1K2HJ;ycHTiTrGfHi.EqEj84xFkHz;"
            "YjkS8YBwtM3.dCd7yKlyqk4;YjkS8YBwtM3.GR4pbqLKhMV;YjkS8YBwtM3.PTWBeC1K2HJ;"
            "YjkS8YBwtM3.EqEj84xFkHz;wajkorhT4I5.dCd7yKlyqk4;wajkorhT4I5.GR4pbqLKhMV;"
            "wajkorhT4I5.PTWBeC1K2HJ;wajkorhT4I5.EqEj84xFkHz;TVbSuL9AdcI.dCd7yKlyqk4;"
            "TVbSuL9AdcI.GR4pbqLKhMV;TVbSuL9AdcI.PTWBeC1K2HJ;TVbSuL9AdcI.EqEj84xFkHz;"
            "tn0o15uvfgP.dCd7yKlyqk4;tn0o15uvfgP.GR4pbqLKhMV;tn0o15uvfgP.PTWBeC1K2HJ;"
            "tn0o15uvfgP.EqEj84xFkHz;sL7vw21TOKw.dCd7yKlyqk4;sL7vw21TOKw.GR4pbqLKhMV;"
            "sL7vw21TOKw.PTWBeC1K2HJ;sL7vw21TOKw.EqEj84xFkHz;GJDppyWOYYM.dCd7yKlyqk4;"
            "GJDppyWOYYM.GR4pbqLKhMV;GJDppyWOYYM.PTWBeC1K2HJ;GJDppyWOYYM.EqEj84xFkHz;"
            "lJotmrRnSnD.dCd7yKlyqk4;lJotmrRnSnD.GR4pbqLKhMV;lJotmrRnSnD.PTWBeC1K2HJ;"
            "lJotmrRnSnD.EqEj84xFkHz;Tz0tiCQ8o6X.dCd7yKlyqk4;Tz0tiCQ8o6X.GR4pbqLKhMV;"
            "Tz0tiCQ8o6X.PTWBeC1K2HJ;Tz0tiCQ8o6X.EqEj84xFkHz;IVT5avXg4CC.dCd7yKlyqk4;"
            "IVT5avXg4CC.GR4pbqLKhMV;IVT5avXg4CC.PTWBeC1K2HJ;IVT5avXg4CC.EqEj84xFkHz;"
            "SLnpLPVE4RI.dCd7yKlyqk4;SLnpLPVE4RI.GR4pbqLKhMV;SLnpLPVE4RI.PTWBeC1K2HJ;"
            "SLnpLPVE4RI.EqEj84xFkHz;eH7m94f1Mrv.dCd7yKlyqk4;eH7m94f1Mrv.GR4pbqLKhMV;"
            "eH7m94f1Mrv.PTWBeC1K2HJ;eH7m94f1Mrv.EqEj84xFkHz;rnUg5fAPgxU.dCd7yKlyqk4;"
            "rnUg5fAPgxU.GR4pbqLKhMV;rnUg5fAPgxU.PTWBeC1K2HJ;rnUg5fAPgxU.EqEj84xFkHz;"
            "LsOkVqvtIrA.dCd7yKlyqk4;LsOkVqvtIrA.GR4pbqLKhMV;LsOkVqvtIrA.PTWBeC1K2HJ;"
            "LsOkVqvtIrA.EqEj84xFkHz;WXmC1SmmY8j.dCd7yKlyqk4;WXmC1SmmY8j.GR4pbqLKhMV;"
            "WXmC1SmmY8j.PTWBeC1K2HJ;WXmC1SmmY8j.EqEj84xFkHz;BBZVk4BJ62Y.VOGsN2CJ4V9;"
            "BBZVk4BJ62Y.AElGEFxvUmt;S8DADvgv6Gy.dCd7yKlyqk4;S8DADvgv6Gy.GR4pbqLKhMV;"
            "S8DADvgv6Gy.PTWBeC1K2HJ;S8DADvgv6Gy.EqEj84xFkHz;JVnFrA3WVI5.dCd7yKlyqk4;"
            "JVnFrA3WVI5.GR4pbqLKhMV;JVnFrA3WVI5.PTWBeC1K2HJ;JVnFrA3WVI5.EqEj84xFkHz;"
            "wU5FlwAagjX.dCd7yKlyqk4;wU5FlwAagjX.GR4pbqLKhMV;wU5FlwAagjX.PTWBeC1K2HJ;"
            "wU5FlwAagjX.EqEj84xFkHz;dvgrSof8WCi.dCd7yKlyqk4;dvgrSof8WCi.GR4pbqLKhMV;"
            "dvgrSof8WCi.PTWBeC1K2HJ;dvgrSof8WCi.EqEj84xFkHz;ODvEuLyeZP5.Gs4AqH6n3mV;"
            "ODvEuLyeZP5.FIYMDBzdabP;ODvEuLyeZP5.dbZfB6Oub9K;ODvEuLyeZP5.ROXPeIvP89X;"
            "jm11FQme3t0.Gs4AqH6n3mV;jm11FQme3t0.FIYMDBzdabP;jm11FQme3t0.dbZfB6Oub9K;"
            "jm11FQme3t0.ROXPeIvP89X;HW4qfFRzitH.Gs4AqH6n3mV;HW4qfFRzitH.FIYMDBzdabP;"
            "HW4qfFRzitH.dbZfB6Oub9K;HW4qfFRzitH.ROXPeIvP89X;IYnqoV2vlRq.Gs4AqH6n3mV;"
            "IYnqoV2vlRq.FIYMDBzdabP;IYnqoV2vlRq.dbZfB6Oub9K;IYnqoV2vlRq.ROXPeIvP89X;"
            "LwwVppGxNJk.dCd7yKlyqk4;LwwVppGxNJk.GR4pbqLKhMV;LwwVppGxNJk.PTWBeC1K2HJ;"
            "LwwVppGxNJk.EqEj84xFkHz;NQwgklXIeG2.dCd7yKlyqk4;NQwgklXIeG2.GR4pbqLKhMV;"
            "NQwgklXIeG2.PTWBeC1K2HJ;NQwgklXIeG2.EqEj84xFkHz",
            "pe:LAST_52_WEEKS"], "filter": "ou:ZWwPSTkiLWX", "displayProperty": "NAME"}

        querystring["filter"] = "ou:" + val
        querystring

        headers = {
            'authorization': "Basic SURTUjpTdXJ2ZWlsbGFuY2VAMjAxOQ==",
            'cache-control': "no-cache",
            'postman-token': "537c1701-c8aa-be43-5fc2-d30943495622"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)

        print(response.text)

        array = response.json()

        # print(array)

        try:

            datas = (array['rows'])

            for lstIdx, lst in enumerate(datas):
                # print("list idx: " + str(lstIdx))
                for idx, item in enumerate(lst):
                    # print(idx, item)
                    if idx == 0:
                        casesdiseases = item.split(".")
                        if (casesdiseases[0]):
                            disease = casesdiseases[0]
                            # print("Index 0 = {} Disease = {} ".format(
                            #     idx,
                            #     disease
                            # ))
                            sql_select_query = """select id,uid from veoc_idsr_diseases where uid= %s"""
                            cursor.execute(sql_select_query, (disease,))
                            record = cursor.fetchall()
                            for value in record:
                                diseases = str(value[0])
                                # id = str(value[0])
                                # print('Disease ID '+diseases)

                        if (casesdiseases[1]):
                            case = casesdiseases[1]
                            # print("Index 0 = {} Case = {} ".format(
                            #     idx,
                            #     case
                            # ))
                            sql_select_query = """select id,category_id from veoc_idsr_reported_incidents where category_id= %s"""
                            cursor.execute(sql_select_query, (case,))
                            record = cursor.fetchall()
                            for value in record:
                                cases = str(value[0])
                                # print('Case ID '+ cases)

                        # print("Index 0 = {} Value = {} ".format(
                        #     idx,
                        #     casesdiseases
                        # ))
                        # print(item)
                    if idx == 1:
                        period=item

                        # print("Index 1 = {} Period = {} ".format(
                        #     idx,
                        #     period
                        # ))
                    if idx == 2:
                        count=item
                        # print("Index 2 = {} Number of cases = {} ".format(
                        #     idx,
                        #     count
                        # ))
                        print(
                        "Cases = {} Disease = {} period ={} facility_name = {} facilty_id  = {} count = {}".format(
                            cases,
                            diseases,
                            period,
                            facility,
                            id,
                            count))
                        cursor = connection.cursor()
                        sql_insert_query = """ INSERT INTO veoc_idsr_weekly_report (period,data_value,idsr_disease_id_id, idsr_incident_id_id, org_unit_id_id)VALUES (%s,%s,%s,%s,%s) """
                        records = (period, count, diseases, cases, id)
                        # executemany() to insert multiple rows rows
                        result = cursor.execute(sql_insert_query, records)
                        count = cursor.rowcount
                        connection.commit()
                        # print (count, "Record inserted successfully into veoc_idsr_weekly_report table")

                    # if idx == 3:
                    #     print("Index 3 = {} Value = {} ".format(
                    #         idx,
                    #         item
                    #     ))
                    #     print(item)
                    # print("item idx in list: " + str(idx))

                    # print(datas)

                    # print("facility = {} id = {} data = {} ".format(
                    #     facility,
                    #     id, datas
                    # ))

                    # if datas:
                    #     print((array['rows']))
                    #
                    #     # print(len(array['rows']))
                    #     # print("facility = {} id = {} data = {} ".format(
                    #     #     array['rows'],
                    #     #     id, datas
                    #     # ))
                    #     if len(array['rows'][0][0]) > 0:
                    #
                    #         orgs = (array['rows'][0][0])
                    #
                    #         casesdiseases = orgs.split(".")
                    #
                    #         # print(orgs)
                    #
                    #         if (casesdiseases[0]):
                    #             disease = casesdiseases[0]
                    #             # disease='HW4qfFRzitH'
                    #             # print(disease)
                    #
                    #             sql_select_query = """select id,uid from veoc_idsr_diseases where uid= %s"""
                    #             cursor.execute(sql_select_query, (disease,))
                    #             record = cursor.fetchall()
                    #             for value in record:
                    #                 diseases = str(value[0])
                    #                 # id = str(value[0])
                    #                 # print(diseases)
                    #         elif len(casesdiseases[0]) == "":
                    #             diseases = "None"
                    #         #
                    #         # # if len(casesdiseases[0]) >= 0:
                    #         if (casesdiseases[1]):
                    #             case = casesdiseases[1]
                    #
                    #             if (case == 'PTWBeC1K2HJ' or case == 'GR4pbqLKhMV'):
                    #                 # disease = 'HW4qfFRzitH'
                    #                 # print(case)
                    #
                    #                 sql_select_query = """select id,category_id from veoc_idsr_reported_incidents where category_id= %s"""
                    #                 cursor.execute(sql_select_query, (case,))
                    #                 record = cursor.fetchall()
                    #
                    #                 for value in record:
                    #                     cases = str(value[0])
                    #                     # print(cases)
                    #         elif len(casesdiseases[1]) == "":
                    #             cases = "None"
                    #         #
                    #         if len(array['rows'][0][1]) > 0:
                    #             period = (array['rows'][0][1])
                    #             # print(period)
                    #         elif len(array['rows'][0][1]) == "":
                    #             period = 'None'
                    #         if array['rows'][0][2]:
                    #             count = (array['rows'][0][2])
                    #             # print(count)
                    #
                    #         # if array['rows'][0][3]:
                    #         #     count = (array['rows'][0][3])
                    #         # elif len(array['rows'][0][3]) == "":
                    #         #     count = "None"
                    #         #
                    #         # print(casesdiseases)
                    #
                    # print("Cases = {} Disease = {} period = {} facility_name = {} facilty_id  = {} count = {}".format(
                    #     cases,
                    #     diseases,
                    #     period,
                    #     facility,
                    #     id,
                    #     count))
            #
            #         # print(no_of_cases)
            #         # cursor = connection.cursor()
            #         # sql_insert_query = """ INSERT INTO veoc_idsr_weekly_report_copy (period,data_value,idsr_disease_id_id, idsr_incident_id_id, org_unit_id_id)VALUES (%s,%s,%s,%s,%s) """
            #         # records = (period, count, diseases, cases, id)
            #         # # executemany() to insert multiple rows rows
            #         # result = cursor.execute(sql_insert_query, records)
            #         # count = cursor.rowcount
            #         # connection.commit()
            #         # print (count, "Record inserted successfully into veoc_idsr_weekly_report_copy table")



        except (IndexError, KeyError) as error:

            # key or index is missing, handle an unexpected response
            # log.error('Unexpected response after uploading image, got %r', data)
            print ("Oops,Error while fetching data from array -> ", error)

except (Exception, psycopg2.Error) as error:
    print ("Error while fetching data from DB", error)
finally:
    # closing database connection.
    if (connection):
        cursor.close()
        connection.close()
        print("Connection is closed")
