import logging
import os
import datetime
import pandas as pd

import constants
from helpers import database_util as db
from helpers.config_helper import nlp2sql_config as conf

########################################################################
#                      GET_SERIES_DATES FUNCTION                       #
########################################################################
def get_series_dates(input_date):
    if input_date is None:
        return None
    
    # Initialization of date variables: today, difference between today and input, and list of all days between today and input
    today = datetime.datetime.today().date().strftime("%m/%d/%Y")
    date_delta = datetime.datetime.today() - datetime.datetime.strptime(input_date, "%m/%d/%Y")
    date_range = pd.date_range(input_date, today).strftime("%m/%d/%Y")

    # Return list and count variables
    date_list = []

    # Initialize return list with list of days start date and current date
    i = 0
    for index in range(date_delta.days):
        i += 1
        date_list.append([date_range[index], i])

    # return the date list
    return date_list

def size_trust_library_source():
    """
    ## SIZE TRUST LIBRARY SOURCE                        #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """

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
    logging.info("metrics : Size_trust_library_source entry")
    start_date = conf.db_config.env_startup_date
    date_list = get_series_dates(start_date)

    # Execute sql
    sql = f"""  select 
                    to_char(t.certified_date, '{conf.db_config.date_format}') as day, 
                    count(case when w.prompt_source = 'auto' then 1 end) as auto, 
                    count(case when w.prompt_source = 'upload' then 1 end) as upload, 
                    count(case when w.prompt_source = 'user' then 1 end) as "user"
                from
                    trust_library t
                join certify_state w on t.certify_state_id = w.id
                group by day
                order by to_date(day, '{conf.db_config.date_format}')"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []
        total_count = 0

        for index in range(len(date_list)):
            series_data.append([date_list[index][1], 0])

        for idx, data in enumerate(date_list):
            for jdx, val in enumerate(sql_ret):
                if data[0] == val[0]:
                    series_data[idx] = ([date_list[idx][1], sql_ret[jdx][series_index+1]])

        for index, data in enumerate(series_data):
            total_count += data[1]
            series_data[index] = [index+1, total_count]

        trust_dict["series"][series_index]["data"] = series_data

        series_index += 1

    return trust_dict

def users_number_prompts():
    ########################################################################
    #                        USERS: NUMBER OF PROMPTS                       #
    ########################################################################
    # Dictionary initialization to match JSON
    trust_dict = {"title": "Number of Prompts (Queries)",
                  "y-title": "Prompts",
                  "x-title": "Day",
                  "series": [
                      {"name": "",
                       "data": []
                       }
                  ]
                  }
    # Get interpolated date range
    start_date = conf.db_config.env_startup_date
    logging.info("metrics : User: Number of prompts")
    date_list = get_series_dates(start_date)

    # Execute sql
    sql = f"""
            select 
                to_char(execution_date, '{conf.db_config.date_format}') as day, 
                count(*) as prompts
            from execution_log 
                where is_action = 0
            group by day
            order by to_date(day, '{conf.db_config.date_format}')
            """

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()


    ''' Post processing: none
    '''
    series_data = []

    for index in range(len(date_list)):
        series_data.append([date_list[index][1], 0])

    for idx in range(len(sql_ret)):
        for jdx in range(len(date_list)):
            if sql_ret[idx][0] == date_list[jdx][0]:
                series_data[jdx][1] = sql_ret[idx][1]
    for index, data in enumerate(date_list):
        date_list[index] = [index + 1, data[1]]

    trust_dict["series"][0]["data"] = series_data
    logging.debug(trust_dict)

    return trust_dict

def users_number_prompts_trust_level():
    """
    ## USERS: NUMBER OF PROMPTS BY TRUST LEVEL                              #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    ########################################################################
    #                        USERS: NUMBER OF PROMPTS BY TRUST LEVEL       #
    ########################################################################
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Number of Prompts (Queries) by Trust Level",
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
    start_date = conf.db_config.env_startup_date
    logging.info("metrics : User: Number of prompts by trust level")
    date_list = get_series_dates(start_date)

    # Execute sql
    # TODO: implement is action in trust percentages method
    sql = f"""  
            select 
                to_char(execution_date, '{conf.db_config.date_format}') as day,
                count(case when is_trusted = 1 then 1 end) as trusted, 
                count(case when (is_prompt_equiv = 1 or is_template_equiv = 1) then 1 end) as "semi-trusted",
                count(case when (is_trusted = 0 and is_prompt_equiv = 0 and is_template_equiv = 0) then 1 end) as untrusted
            from
                execution_log
            where 
                is_action = 0
            group by day
            order by to_date(day, '{conf.db_config.date_format}')
        """

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    ''' Post processing: none
    '''
    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []

        for index in range(len(date_list)):
            series_data.append([date_list[index][1], 0])

        for idx, data in enumerate(date_list):
            for jdx, val in enumerate(sql_ret):
                if data[0] == val[0]:
                    series_data[idx] = ([date_list[idx][1], sql_ret[jdx][series_index + 1]])

        for index, data in enumerate(series_data):
            series_data[index] = [index + 1, data[1]]

        trust_dict["series"][series_index]["data"] = series_data

        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

def percentage_prompts_trust_level():
    """
    ## PERCENTAGE_OF_PROMPTS_BY_TRUST_LEVEL                         #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    ########################################################################
    #            PERCENTAGE_OF_PROMPTS_BY_TRUST_LEVEL                      #
    ########################################################################
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
    logging.info("metrics : Percentage_prompts_trust_level entry")
    # Get interpolated date range
    start_date = conf.db_config.env_startup_date
    date_list = get_series_dates(start_date)

    # Execute sql
    sql = f"""  select 
                    to_char(execution_date, '{conf.db_config.date_format}') as day, 
                    count(case when is_trusted = 1 then 1 end) as trusted, 
                    count(case when (is_prompt_equiv = 1 or is_template_equiv = 1) then 1 end) as "semi-trusted",
                    count(case when (is_trusted = 0 and is_prompt_equiv = 0 and is_template_equiv = 0) then 1 end) as untrusted,
                    count(*) as total
                from
                    execution_log
                where
                    is_action = 0
                group by day
                order by to_date(day, '{conf.db_config.date_format}')"""

    # python post-processing:
            # for each day, the series value is a percentage of the total across each series for the day.  Round to 1 decimal e.g. 33.3
            # thus, for each day the sum of all series should = 100.0

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []

        for index in range(len(date_list)):
            series_data.append([date_list[index][1], 0])

        for idx, data in enumerate(date_list):
            for jdx, val in enumerate(sql_ret):
                if data[0] == val[0]:
                    series_data[idx] = ([date_list[idx][1], round((sql_ret[jdx][series_index+1] / sql_ret[jdx][4]) * 100, 1)])

        trust_dict["series"][series_index]["data"] = series_data

        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

def users_number():
    ########################################################################
    #                        USERS: number per day                         #
    ########################################################################
    """
    ## TRUST_LIBRARY FUNCTION                        #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                    |
    """
    # Dictionary initialization to match JSON
    trust_dict = {
        "title": "Number of Users",
        "y-title": "Number",
        "x-title": "Day",
        "series": [
            {"name": "",
             "data": []
             }
        ]
    }
    # Get interpolated date range
    start_date = conf.db_config.env_startup_date
    logging.info("metrics : user_number")
    date_list = get_series_dates(start_date)

    # Execute sql
    # TODO: implement is action in trust percentages method
    sql = f"""  
            select 
                to_char(execution_date, '{conf.db_config.date_format}') as day,
                count(distinct user_id)
            from execution_log
            group by day
            order by to_date(day, '{conf.db_config.date_format}') 
        """ 

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    ''' Post processing: none
    '''
    series_index = 0
    while series_index < len(trust_dict["series"]):
        series_data = []

        for index in range(len(date_list)):
            series_data.append([date_list[index][1], 0])

        for idx, data in enumerate(date_list):
            for jdx, val in enumerate(sql_ret):
                if data[0] == val[0]:
                    series_data[idx] = ([date_list[idx][1], sql_ret[jdx][series_index + 1]])

        for index, data in enumerate(series_data):
            series_data[index] = [index + 1, data[1]]

        trust_dict["series"][series_index]["data"] = series_data

        series_index += 1

    logging.debug(trust_dict)
    return trust_dict

def size_trust_library():
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
    start_date = conf.db_config.env_startup_date
    date_list = get_series_dates(start_date)

    # Execute sql
    sql = f"""select
                    to_char(certified_date, '{conf.db_config.date_format}') as day, 
                    count(*) as count  
                from
                    trust_library
                group by day
                order by to_date(day, '{conf.db_config.date_format}')"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Post processing to populate trust_dict with series sequence (1, 2, 3...) and cumulative sum of counts
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
        series_data[index] = [index+1, total_count]

    trust_dict["series"][0]["data"] = series_data

    logging.debug(trust_dict)
    return trust_dict

## HOTFIX: 23 April 2025
## Changes:
## pip install pandas
## pip install numpy
import numpy as np
import pandas as pd

# The following are in the configuration file in the current release.
python_format = "%d-%b-%Y"
database_date_format = "DD-MON-YYYY"

def get_format_dates(boundaries_list):
    start_date = boundaries_list[0]
    end_date = boundaries_list[1]
    start_date = datetime.datetime.strptime(start_date, python_format)
    end_date = datetime.datetime.today()
    return start_date, end_date


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

def accuracy_by_trust_level(start_date=None, end_date=None):
    """
    ## ACCURACY_OF_USER_PROMPTS_BY_TRUST_LEVEL METHOD                        #
    | Property         |   Description                                      |
    |------------------|----------------------------------------------------|
    |                  |                                                |
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
    date_list = get_series_weeks(boundaries_list)

    # Execute sql
    sql = f"""select trunc(prompt_proc_date, 'IW') as week, 
            count(case when (is_prompt_equiv != 1 and is_template_equiv != 1) and pass_fail = 'Pass' then 1 end) as untrusted_pass,
            count(case when (is_prompt_equiv != 1 and is_template_equiv != 1)  then 1 end) as untrusted_count,
            count(case when (is_prompt_equiv = 1 or is_template_equiv = 1) and pass_fail = 'Pass' then 1 end) as semi_trusted_pass,
            count(case when (is_prompt_equiv = 1 or is_template_equiv = 1)  then 1 end) as semi_trusted_count

            from certify_state c
            left outer join execution_log e on c.user_execution_id = e.id
            where is_cert_proc = 1 
            and (prompt_source = 'user' and is_trusted = 0)
            group by trunc(prompt_proc_date, 'IW')
            order by trunc(prompt_proc_date, 'IW')"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Method-specific post-processing
    series_index = 0
    series_pass = 1
    series_count = 2

    while series_index < len(trust_dict["series"]):
        series_data = []
        arr = np.asarray(date_list).T

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
        series_pass += 2
        series_count += 2

    logging.debug(trust_dict)
    return trust_dict

def size_trust_library_user_prompts_trust(start_date=None, end_date=None):
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
##

def method_name_like_service_name( ):
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
    start_date = conf.db_config.env_startup_date
    date_list = get_series_dates(start_date)

    # Execute sql
    sql = f"""specific to method"""

    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Method-specific post-processing
    total_count = 0
    """
    for index, data in enumerate(date_list):
        total_count += data[1]
        date_list[index] = [index + 1, total_count]
    """
    logging.debug(trust_dict)
    return trust_dict


if __name__ == "__main__":
    logging.getLogger(constants.METRICS_LAYER).setLevel(logging.DEBUG)
    conf.read_configuration(suffix=os.getenv("NL2SQL_ENV"))
    size_trust_library('02/10/2025')
    #trust_library_source('02/10/2025')
