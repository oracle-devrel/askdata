import logging
import os
import datetime
import numpy as np
import pandas as pd

import constants
from helpers import database_util as db
from helpers.config_json_helper import config_boostrap as confb
from helpers.oci_helper_boostrap import oci_boostrap as ocib
from helpers.finetune_db import ModelUsageDAO

database_date_format:str
python_format:str

def set_globals():
    global database_date_format, python_format
    database_date_format = confb.config.database.date_format
    python_format = confb.config.metrics.python_format

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
        read_models = ModelUsageDAO()

        try:
            latest_date = read_models.latest_model(constants.MODEL_PURPOSE)
        except TypeError:
            latest_date = confb.config.metrics.start_date

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
        "title": "Size of Trust Library by Source",
        "y-title": "Size",
        "x-title": "Day",
        "series": [
            {"name": "auto",
             "data": []
             },
            {"name": "upload",
             "data": []
             },
            {"name": "user",
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
                    count(case when w.prompt_source = 'auto' then 1 end) as auto, 
                    count(case when w.prompt_source = 'upload' then 1 end) as upload, 
                    count(case when w.prompt_source = 'user' then 1 end) as "user"
                from
                    trust_library t
                join certify_state w on t.certify_state_id = w.id
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
            {"name": "semi-trusted",
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
                    count(case when is_trusted = 1 then 1 end) as trusted, 
                    count(case when (is_prompt_equiv = 1 or is_template_equiv = 1) then 1 end) as "semi-trusted",
                    count(case when (is_trusted = 0 and is_prompt_equiv = 0 and is_template_equiv = 0) then 1 end) as untrusted,
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
    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []
        arr = np.asarray(date_list).T

        if series_index > 0:
            series_data.clear()

        for date in range(len(date_list)):
            series_data.append([date_list[date][1], 0])

        for val in sql_ret:
            if np.argwhere(arr == val[0]).size != 0:
                arr_idx = np.argwhere(arr == val[0])[0][1]
                series_data[arr_idx] = ([date_list[arr_idx][1], round((val[series_index + 1] / val[4]) * 100, 1)])

        for index, data in enumerate(series_data):
            if index == 0 and data[1] == 0:
                pass
            else:
                if data[1] == 0:
                    data[1] = series_data[index - 1][1]

        trust_dict["series"][series_index]["data"] = series_data

        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

def accuracy_untrusted(start_date=None, end_date=None,domain=None):
    """
    ## UNTRUSTED_PROMPTS_ACCURACY                         #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    logging.info("metrics : untrusted_prompts_accuracy entry")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Prompt Accuracy: Untrusted",
        "y-title": "Accuracy",
        "x-title": "Week",
        "series": [
            {"name": "auto",
             "data": []
             },
            {"name": "upload",
             "data": []
             },
            {"name": "user",
             "data": []
             }
        ]
    }

    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_weeks(boundaries_list)

    # Execute sql
    sql = f"""  select trunc(prompt_proc_date, 'IW') as week, 

                    count(case when prompt_source = 'auto' and pass_fail = 'Pass' then 1 end) as auto_pass,
                    count(case when prompt_source = 'upload' and pass_fail = 'Pass'  then 1 end) as upload_pass,
                    count(case when prompt_source = 'user' and pass_fail = 'Pass' then 1 end) as user_pass,

                    count(case when prompt_source = 'auto' then 1 end) as auto_count,
                    count(case when prompt_source = 'upload' then 1 end) as upload_count,
                    count(case when prompt_source = 'user'  then 1 end) as user_count

                from
                    certify_state c
                left outer join execution_log e on c.user_execution_id = e.id
                where
                    is_cert_proc = 1 
                    and ((prompt_source = 'user' and is_trusted = 0 and is_prompt_equiv = 0 and is_template_equiv = 0) 
                    or prompt_source in ('auto', 'upload'))
                group by trunc(prompt_proc_date, 'IW')
                order by trunc(prompt_proc_date, 'IW')"""

    # note: this series is represented by week integers, i.e. 1, 2, 3 represent week 1, 2, 3
    # python post-processing:
    # for each series, the day value is (<series>_pass / <series>_count) * 100.  Round to 1 decimal place
    # thus, all values should be between 0.0-1.0 inclusive
    # there is no relation across series
    # note: if <series>_count = 0, then the calculated value is 0.0 (to prevent divide by 0)

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    series_index = 0
    series_pass = 1
    series_count = 4

    while series_index < len(trust_dict["series"]):
        series_data = []
        arr = np.asarray(date_list).T
        index = 0

        for date in range(len(date_list)):
            series_data.append([date_list[date][1], 0])

        # Compare SQL_RET dates to dates in data_list. If there is a match, update series list with math
        for val in sql_ret:
            str_data = datetime.datetime.strftime(val[0], python_format)
            if np.argwhere(arr == str_data).size != 0:
                series_idx = np.argwhere(arr == str_data)[0][1]
                if val[series_count] == 0:
                    series_data[series_idx] = [date_list[series_idx][1], round((0 / 1) * 100, 1)]
                else:
                    series_data[series_idx] = [date_list[series_idx][1], round((val[series_pass] / val[series_count]) * 100, 1)]

        # If first index is 0, set to 0. If index is 0, set to previous value
        # i.e. [[1, 0.0], [2, 0.0], [3, 55.5]]
        #  or  [1, 10.0], [2,55.5], [3, 55.5]]
        for index, data in enumerate(series_data):
            if index == 0 and data[1] == 0:
                pass
            elif int(data[1]) == 0:
                series_data[index][1] = round(series_data[index - 1][1], 1)

        trust_dict["series"][series_index]["data"] = series_data
        series_index += 1
        series_pass += 1
        series_count += 1

    logging.debug(trust_dict)
    return trust_dict

def accuracy_semitrusted(start_date=None, end_date=None, domain=None):
    """
    ## SEMI_TRUSTED_PROMPT_ACCURACY                         #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    logging.info("metrics : semi_trusted_prompts_accuracy entry")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Prompt Accuracy: Semi-trusted",
        "y-title": "Accuracy",
        "x-title": "Week",
        "series": [
            {"name": "semi-trusted",
             "data": []
             }
        ]
    }

    # Get interpolated date range
    boundaries_list = [start_date, end_date]
    date_list = get_series_weeks(boundaries_list)

    # Execute sql
    sql = f"""  select trunc(prompt_proc_date, 'IW') as week, 
                    count(case when prompt_source = 'user' and pass_fail = 'Pass' then 1 end) as user_pass,
                    count(case when prompt_source = 'user'  then 1 end) as user_count
                from
                    certify_state c
                left outer join execution_log e on c.user_execution_id = e.id
                where
                    is_cert_proc = 1 
                    and (prompt_source = 'user' and is_trusted = 0 and (is_prompt_equiv = 1 or is_template_equiv = 1))
                group by trunc(prompt_proc_date, 'IW')
                order by trunc(prompt_proc_date, 'IW')"""

    # note: this series is represented by week integers, i.e. 1, 2, 3 represent week 1, 2, 3
    # python post-processing:
    # for each series, the day value is (<series>_pass / <series>_count) * 100.  Round to 1 decimal place
    # thus, all values should be between 0.0-1.0 inclusive
    # there is no relation across series
    # note: if <series>_count = 0, then the calculated value is 0.0 (to prevent divide by 0)

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post-processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    series_data = []
    arr = np.asarray(date_list).T
    index = 0

    for date in range(len(date_list)):
        series_data.append([date_list[date][1], 0])

    # Compare SQL_RET dates to dates in data_list. If there is a match, update series list with math
    for val in sql_ret:
        str_data = datetime.datetime.strftime(val[0], python_format)
        if np.argwhere(arr == str_data).size != 0:
            series_idx = np.argwhere(arr == str_data)[0][1]
            if val[2] == 0:
                series_data[series_idx] = [date_list[series_idx][1], round((0 / 1) * 100, 1)]
            else:
                series_data[series_idx] = [date_list[series_idx][1], round((val[1] / val[2]) * 100, 1)]

    # If first index is 0, set to 0. If index is 0, set to previous value
    # i.e. [[1, 0.0], [2, 0.0], [3, 55.5]]
    #  or  [1, 10.0], [2,55.5], [3, 55.5]]
    for index, data in enumerate(series_data):
        if index == 0 and data[1] == 0:
            pass
        elif data[1] == 0:
            series_data[index][1] = series_data[index - 1][1]

    trust_dict["series"][0]["data"] = series_data

    logging.debug(trust_dict)
    return trust_dict

def accuracy_by_trust_level(start_date=None, end_date=None,domain=None):
    """
    ## ACCURACY_OF_USER_PROMPTS_BY_TRUST_LEVEL METHOD                        #
    | Parameter        |   Description                                      |
    |------------------|----------------------------------------------------|
    | start_date       |                                                    |
    | end_date         |                                                    |
    """
    logging.info("metrics : user_prompt_accuracy_by_trust_level entry")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Accuracy of User Prompts by Trust Level",
        "y-title": "Accuracy",
        "x-title": "Week",
        "series": [
            {"name": "untrusted",
            "data": []
            },
            {"name": "semitrusted",
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
            to_char(t.certified_date, '{database_date_format}') as day, 
            count(case when (is_prompt_equiv != 1 and is_template_equiv != 1) and pass_fail = 'Pass' then 1 end) as untrusted_pass,
            count(case when (is_prompt_equiv != 1 and is_template_equiv != 1)  then 1 end) as untrusted_count,
            count(case when (is_prompt_equiv = 1 or is_template_equiv = 1) and pass_fail = 'Pass' then 1 end) as semi_trusted_pass,
            count(case when (is_prompt_equiv = 1 or is_template_equiv = 1)  then 1 end) as semi_trusted_count
        from trust_library t
        join certify_state c on t.certify_state_id = c.id
        join execution_log e on c.user_execution_id = e.id
        where c.prompt_source = 'user'
        group by day
        order by to_date(day, '{database_date_format}')"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Method-specific post-processing
    series_index = 0
    series_pass = 1
    series_count = 2

    # GK: change to make accuracy cumulative over weeks (not per week as original design)
    cum_pass = [0, 0]
    cum_count = [0, 0]

    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []
        arr = np.asarray(date_list).T

        if series_index > 0:
            series_data.clear()

        for date in range(len(date_list)):
            series_data.append([date_list[date][1], 0])

        # Compare SQL_RET dates to dates in data_list. If there is a match, update series list with math
        for val in sql_ret:
            logging.info(f"arr value {arr}")
            logging.info(f"sql return value {val}")
            #sql return value ('12-FEB-2025', 7, 7, 0, 0)
            arr_idx = np.argwhere(arr == val[0])[0][1]

            if np.argwhere(arr == val[0]).size != 0:
                if val[series_count] == 0:
                    # GK series_data[series_idx] = [date_list[series_idx][1], round((0 / 1) * 100, 1)]
                    print(arr_idx)
                else:
                    # GK: change to make accuracy cumulative and over days (not per each week as original design)

                    cum_pass[series_index] += val[series_pass]
                    cum_count[series_index] += val[series_count]
                    print(f"{arr_idx}    {cum_pass[series_index]}     {cum_count[series_index]}    {round((cum_pass[series_index] / cum_count[series_index]) * 100, 1)}")
                    series_data[arr_idx] = [date_list[arr_idx][1], round((cum_pass[series_index] / cum_count[series_index]) * 100, 1)]

        # If first index is 0, set to 0. If index is 0, set to previous value
        # i.e. [[1, 0.0], [2, 0.0], [3, 55.5]]
        #  or  [1, 10.0], [2,55.5], [3, 55.5]]
        for index, data in enumerate(series_data):
            if index == 0 and data[1] == 0:
                pass
            elif int(data[1]) == 0:
                series_data[index][1] = round(series_data[index - 1][1], 1)

        trust_dict["series"][series_index]["data"] = series_data
        series_index += 1
        series_pass += 2
        series_count += 2

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
            {"name": "semi-trusted",
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
                count(case when is_trusted = 1 then 1 end) as trusted, 
                count(case when (is_prompt_equiv = 1 or is_template_equiv = 1) then 1 end) as "semi-trusted",
                count(case when (is_trusted = 0 and is_prompt_equiv = 0 and is_template_equiv = 0) then 1 end) as untrusted
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

def size_trust_library_user_prompts_trust(start_date=None, end_date=None,domain=None):
    """
    ## SIZE_OF_TRUST_LIBRARY_BY_USER_PROMPTS_TRUST_LEVEL METHOD                        #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                |
    """
    logging.info("metrics : size_trust_library_user_prompts_trust entry")
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Size of Trust Library by User Prompt Trust Level",
        "y-title": "Number",
        "x-title": "Day",
        "series": [
            {"name": "semi-trusted",
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
                count(case when (is_prompt_equiv = 1 or is_template_equiv = 1) then 1 end) as "semi-trusted",
                count(case when (is_trusted = 0 and is_prompt_equiv = 0 and is_template_equiv = 0) then 1 end) as untrusted
            from
                trust_library t
            join certify_state w on t.certify_state_id = w.id
            join execution_log e on e.id = w.user_execution_id
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
        total_count = 0

        for index in range(len(date_list)):
            series_data.append([date_list[index][1], 0])

        for idx, data in enumerate(date_list):
            for jdx, val in enumerate(sql_ret):
                if data[0] == val[0]:
                    series_data[idx] = ([date_list[idx][1], sql_ret[jdx][series_index + 1]])
                    break

        for index, data in enumerate(series_data):
            series_data[index] = [index + 1, data[1]]

        for index, data in enumerate(series_data):
            total_count += data[1]
            series_data[index] = [index + 1, total_count]

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
