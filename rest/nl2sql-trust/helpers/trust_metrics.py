# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import logging
import os
import datetime
import numpy as np
import pandas as pd

import constants
from helpers import database_util as db
from helpers.config_json_helper import config_boostrap as confb
from helpers.oci_helper_boostrap import oci_boostrap as ocib
# from helpers.finetune_db import ModelUsageDAO

database_date_format:str
python_format:str

def set_globals():
    global database_date_format, python_format
    database_date_format = confb.dconfig["database"]["date_format"]
    python_format = confb.dconfig["metrics"]["python_format"]

############################################
#           INTERPOLATE METHODS            #
############################################
def get_series_weeks(boundaries_list):
    """
    ## GET_SERIES_WEEKS METHOD                                  #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    # Initialization of date variables
    start_date, end_date = get_format_dates(boundaries_list)
    date_delta = end_date - start_date
    date_len = date_delta.days + 1
    date_range = pd.date_range(start_date, end_date).strftime(python_format)
    weekday_list = []

    # Return list
    date_list = []

    # Initialize return list with list of days start date and current date
    for index in range(date_len):
        weekday_list.append([date_range[index],
                             datetime.datetime.strptime(date_range[index], python_format).date().isoweekday()])

    i = 1
    for index, data in enumerate(weekday_list):
        if index == 0 and data[1] != 1:
            days_diff = 1 - data[1]
            pd_date = pd.Timestamp(data[0])
            do_monday = pd.tseries.offsets.DateOffset(n=days_diff)
            prev_monday = (pd_date + do_monday).strftime(python_format)
            date_list.append([prev_monday, i])
            i += 1
        elif data[1] == 1:
            date_list.append([date_range[index], i])
            i += 1

    # return the date list
    return date_list

def get_series_dates(boundaries_list):
    """
    ## GET_SERIES_DATES METHOD                                  #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    # Initialization of date variables
    start_date, end_date = get_format_dates(boundaries_list)
    date_delta = end_date - start_date
    date_len = date_delta.days + 1
    date_range = pd.date_range(start_date, end_date).strftime(python_format)

    # Return list
    date_list = []

    # Initialize return list with list of days start date and current date
    i = 1
    for index in range(date_len):
        date_list.append([date_range[index], i])
        i += 1

    # Format to match database for comparison
    for index, month in enumerate(date_list):
        date_list[index][0] = month[0].upper()

    # return the date list
    return date_list

def get_format_dates(boundaries_list):
    start_date = boundaries_list[0]
    end_date = boundaries_list[1]

    if start_date is None:

        try:
            connection = db.db_get_connection()
            latest_date = db.latest_model(connection, constants.MODEL_PURPOSE)
        except TypeError:
            latest_date = confb.dconfig["metrics"]["start_date"]

        start_date = latest_date
    elif isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, python_format)

    if end_date is None:
        end_date = datetime.datetime.today()
    elif isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, python_format)

    return start_date, end_date


############################################
#              TRUST METRICS               #
############################################
def size_trust_library(start_date=None, end_date=None,domain=None):
    """
    ## TRUST_LIBRARY FUNCTION                        #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    logging.info("metrics : Size_trust_library entry")

    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Size of Trust Library",
        "y-title": "Size",
        "x-title": "Day",
        "series": [
            {"name": "",
             "data": []
             }
        ]
    }

    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""select
                    to_char(certified_date, '{database_date_format}') as day, 
                    count(*) as count  
                from
                    trust_library
                where
                    (is_deprecated is null or is_deprecated = 0)
                group by day
                order by to_date(day, '{database_date_format}')"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    series_data = []
    total_count = 0

    for index in range(len(date_list)):
        series_data.append([date_list[index][1], 0])

    for idx in range(len(sql_ret)):
        for jdx in range(len(date_list)):
            if sql_ret[idx][0] == date_list[jdx][0]:
                series_data[jdx][1] = sql_ret[idx][1]

    for index, data in enumerate(series_data):
        total_count += data[1]
        series_data[index] = [index + 1, total_count]

    trust_dict["series"][0]["data"] = series_data

    logging.debug(trust_dict)
    return trust_dict

def size_trust_library_source(start_date=None, end_date=None,domain=None):
    """
    ## SIZE TRUST LIBRARY SOURCE                        #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    logging.info("metrics : Size_trust_library_source entry")

    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Size of Trust Library by Certification Mode",
        "y-title": "Size",
        "x-title": "Day",
        "series": [
            {"name": "manual",
             "data": []
             },
            {"name": "auto-certified",
             "data": []
             }
        ]
    }

    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""  select 
                    to_char(t.certified_date, '{database_date_format}') as day, 
                    count(case when (w.prompt_source = 'auto' or w.prompt_source = 'upload' or w.prompt_source = 'user') then 1 end) as manual, 
                    count(case when w.prompt_source = 'user-autocertify' then 1 end) as "auto-certified"
                from
                    trust_library t
                    join certify_state w on t.certify_state_id = w.id
                where
                    (is_deprecated is null or is_deprecated = 0)
                group by day
                order by to_date(day, '{database_date_format}')"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []
        total_count = 0

        for index in range(len(date_list)):
            series_data.append([date_list[index][1], 0])

        for idx, data in enumerate(date_list):
            for jdx, val in enumerate(sql_ret):
                if data[0] == val[0]:
                    series_data[idx] = ([date_list[idx][1], sql_ret[jdx][series_index + 1]])

        for index, data in enumerate(series_data):
            total_count += data[1]
            series_data[index] = [index + 1, total_count]

        trust_dict["series"][series_index]["data"] = series_data

        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

def percentage_prompts_trust_level(start_date=None, end_date=None,domain=None):
    """
    ## PERCENTAGE_OF_PROMPTS_BY_TRUST_LEVEL                         #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    """
    logging.info("metrics : Percentage_prompts_trust_level entry")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Percentage of Prompts by Trust Level",
        "y-title": "%",
        "x-title": "Day",
        "series": [
            {"name": "trusted",
             "data": []
             },
            {"name": "untrusted",
             "data": []
             }
        ]
    }

    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""  select
                    to_char(execution_date, '{database_date_format}') as day,
                    count(case when is_trusted = 1 or is_autocertify = 1 then 1 end) as trusted,
                    count(case when is_trusted = 0 and (is_autocertify = 0 or is_autocertify is null) then 1 end) as untrusted,
                    count(*) as total
                from
                    execution_log
                where
                    is_action = 0
                group by day
                order by to_date(day, '{database_date_format}')"""

    # python post-processing:
    # for each day, the series value is a percentage of the total across each series for the day.  Round to 1 decimal e.g. 33.3
    # thus, for each day the sum of all series should = 100.0

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    trusted_count = 0
    untrusted_count = 0
    total_count = 0

    series_index = 0
    TRUSTED = 0
    UNTRUSTED = 1

    for series in trust_dict["series"]:
        results = []

        # get the percentage prompts over entire date range
        for row in sql_ret:
            row_date = row[0]
            trusted_count = row[1]
            untrusted_count = row[2]
            total_count = row[3]

            if total_count == 0:
                results.append([row_date, round((0 / 1) * 100, 1)])

            else:
                if series_index == TRUSTED:
                    results.append([row_date, round(trusted_count / total_count * 100, 1)])
                if series_index == UNTRUSTED:
                    results.append([row_date, round(untrusted_count / total_count * 100, 1)])

        series_data = []

        # build the series
        percentage = 0
        for d in date_list:
            series_date = d[0]
            series_date_num = d[1]

            for row in results:
                row_date = row[0]
                if series_date == row_date:
                    percentage = row[1]

            series_data.append([series_date_num, percentage])

        trust_dict["series"][series_index]["data"] = series_data
        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

############################################
#               USER METRICS               #
############################################
def users_number(start_date=None, end_date=None,domain=None):
    """
    ## USERS: NUMBER OF USERS                            #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    logging.info("metrics : user_number")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Unique Users",
        "y-title": "Number",
        "x-title": "Day",
        "series": [
            {"name": "",
             "data": []
             }
        ]
    }
    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""  
            select 
                to_char(execution_date, '{database_date_format}') as day,
                count(distinct user_id)
            from execution_log
            group by day
            order by to_date(day, '{database_date_format}') 
        """

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-Processing
    series_data = []

    for index in range(len(date_list)):
        series_data.append([date_list[index][1], 0])

    for idx in range(len(sql_ret)):
        for jdx in range(len(date_list)):
            if sql_ret[idx][0] == date_list[jdx][0]:
                series_data[jdx][1] = sql_ret[idx][1]
                break

    for index, data in enumerate(series_data):
        series_data[index] = [index + 1, data[1]]

    trust_dict["series"][0]["data"] = series_data

    logging.debug(trust_dict)
    return trust_dict

def users_number_prompts(start_date=None, end_date=None,domain=None):
    """
    ## USERS: NUMBER OF PROMPTS METHOD                              #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    logging.info("metrics : User: Number of prompts")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Number of Prompts",
        "y-title": "Prompts",
        "x-title": "Day",
        "series": [
            {"name": "",
             "data": []
             }
        ]
    }
    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""
            select 
                to_char(execution_date, '{database_date_format}') as day, 
                count(*) as prompts
            from execution_log 
                where is_action = 0
            group by day
            order by to_date(day, '{database_date_format}')
            """

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-Processing
    series_data = []

    for index in range(len(date_list)):
        series_data.append([date_list[index][1], 0])

    for idx in range(len(sql_ret)):
        for jdx in range(len(date_list)):
            if sql_ret[idx][0] == date_list[jdx][0]:
                series_data[jdx][1] = sql_ret[idx][1]
                break

    for index, data in enumerate(date_list):
        date_list[index] = [index + 1, data[1]]

    trust_dict["series"][0]["data"] = series_data

    logging.debug(trust_dict)
    return trust_dict

def users_number_prompts_trust_level(start_date=None, end_date=None,domain=None):
    """
    ## USERS: NUMBER OF PROMPTS BY TRUST LEVEL                              #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    logging.info("metrics : User: Number of prompts by trust level")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Number of Prompts by Trust Level",
        "y-title": "Number",
        "x-title": "Day",
        "series": [
            {"name": "trusted",
             "data": []
             },
            {"name": "untrusted",
             "data": []
             }
        ]
    }
    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""  
            select 
                to_char(execution_date, '{database_date_format}') as day,
                count(case when is_trusted = 1 or is_autocertify = 1 then 1 end) as trusted, 
                count(case when is_trusted = 0 and (is_autocertify = 0 or is_autocertify is null) then 1 end) as untrusted
            from
                execution_log
            where 
                is_action = 0
            group by day
            order by to_date(day, '{database_date_format}')
        """
    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-Processing
    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []

        for index in range(len(date_list)):
            series_data.append([date_list[index][1], 0])

        for idx, data in enumerate(date_list):
            for jdx, val in enumerate(sql_ret):
                if data[0] == val[0]:
                    series_data[idx] = ([date_list[idx][1], sql_ret[jdx][series_index + 1]])
                    break

        for index, data in enumerate(series_data):
            series_data[index] = [index + 1, data[1]]

        trust_dict["series"][series_index]["data"] = series_data

        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

############################################
#              METHOD TEMPLATE             #
############################################
def method_name_like_service_name(start_date=None, end_date=None):
    """
    This format of documentation is getting picked up by mkdocs.
    ## SOMETHING SOMETHING SOMETHING                        #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                |
    """
    # Dictionary initialization to match JSON
    trust_dict = {"key": "dict specific to each method"}

    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""specific to method"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Method-specific post-processing
    """
    for index, data in enumerate(date_list):
        total_count += data[1]
        date_list[index] = [index + 1, total_count]
    """

    return trust_dict

def accuracy_cumulative(start_date=None, end_date=None, domain=None):

    logging.info("metrics : accuracy_cumulative entry")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Cumulative Accuracy",
        "y-title": "Cum Accuracy",
        "x-title": "Day",
        "series": [
            {"name": "",
             "data": []
             },
        ]
    }

    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_dates(boundaries_list)

    # Execute sql
    sql = f"""    select
                    to_char(cert_proc_date, 'DD-MON-YYYY') as day, 
                    count(case when pass_fail = 'Pass' then 1 end) as row_pass,
                    count(case when prompt_source in ('user','auto', 'upload')  then 1 end) as row_count
                from
                    certify_state c
                where
                    is_cert_proc = 1 
                    and prompt_source in ('user','auto', 'upload')
            group by day
            order by to_date(day, 'DD-MON-YYYY')
        """

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    cum_pass = 0
    cum_count = 0

    series_index = 0
    for series in trust_dict["series"]:
        cum_results = []

        # get the cumulative accuracy over entire date range
        for row in sql_ret:
            row_date = row[0]
            cum_pass += row[1]
            cum_count += row[2]
            if cum_count == 0:
                cum_results.append([row_date, round((0 / 1) * 100, 1)])
            else:
                cum_results.append([row_date, round(cum_pass / cum_count * 100, 1)])

        series_data = []

        # establish cum accuracy on first day in selected date range
        cum_accuracy = 0
        #first_date_in_list = row_date = datetime.datetime.strptime(date_list[0][0], python_format)
        first_date_in_list = datetime.datetime.strptime(date_list[0][0], python_format)
        for row in cum_results:
            row_date = datetime.datetime.strptime(row[0], python_format)
            if row_date >= first_date_in_list:
                break
            cum_accuracy = row[1]

        # build the series
        for d in date_list:
            series_date = d[0]
            series_date_num = d[1]

            for row in cum_results:
                row_date = row[0]
                if series_date == row_date:
                    cum_accuracy = row[1]

            series_data.append([series_date_num, cum_accuracy])

        trust_dict["series"][series_index]["data"] = series_data
        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

if __name__ == "__main__":
    logging.getLogger(constants.METRICS_LAYER).setLevel(logging.DEBUG)
    confb.read_configuration(environment=os.getenv("NL2SQL_ENV"))
    logging.getLogger('oci').setLevel(logging.DEBUG)
    ocib.cnx= { # This is required to obtain the first trust_config.json file.
        "auth_mode":os.getenv("NL2SQL_OCI_MODE"),
        "namespace":os.getenv("NL2SQL_OCI_NS"),
        "region": os.getenv('NL2SQL_OCI_REGION','us-chicago-1'),
        "bucket": os.getenv("NL2SQL_OCI_BUCKET")
    }
    confb.setup()
