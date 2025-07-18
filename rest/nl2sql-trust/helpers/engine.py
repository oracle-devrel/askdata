import logging
import datetime
from helpers import database_util as db
from helpers.config_json_helper import config_boostrap as confb

def refresh_autofill_cache(previous_last_record_stamp):
    """
    ## REFRESH_AUTOFILL_CACHE FUNCTION                        #
    | Property           |   Description                                      |
    |--------------------|----------------------------------------------------|
    |previous_last_record_stamp  | Last date of the cache refresh                     |
    ``` previous_last_record_stamp example : 20-APR-2025 22:12:45 ```
    """
    logging.info("Engine : engine refresh autofill cache")

    # Dictionary initialization to match JSON
    engine_dict = {
        "new_last_record_tstamp" : "",	
        "prompts": []
    }

    last_record_tstamp = previous_last_record_stamp

    # Check for last_record_tstamp val, if empty set for datetime now, else check formatted correctly
    if last_record_tstamp is None:
        last_record_tstamp = datetime.datetime.strftime(datetime.datetime(2025, 1, 1), "%d-%b-%Y %H:%M:%S")
    elif isinstance(last_record_tstamp, str):
        pass
    else:
        last_record_tstamp = datetime.datetime.strftime(last_record_tstamp, "%d-%b-%Y %H:%M:%S")

    # Execute sql
    sql = f"""  select 
                    to_char(certified_date, '{confb.config.database.datetime_format}') as tstamp, 
                    prompt_txt as prompt 
                from trust_library
                where certified_date >= to_date('{last_record_tstamp}', '{confb.config.database.datetime_format}')"""
    
    logging.debug(f"referesh_autofill_cache {sql}")
    connection = db.db_get_connection()
    sql_ret = db.db_select(connection=connection, select_statement=sql)
    connection.close()

    # Method-specific post-processing
    prompts_list = []
    sql_ret.sort()

    for data in sql_ret:
        engine_dict["new_last_record_tstamp"] = data[0]
        prompts_list.append(data[1])

    # Check if engine_dict is empty. If so add last_record_tstamp to JSON
    if len(engine_dict["new_last_record_tstamp"]) == 0:
        engine_dict["new_last_record_tstamp"] = last_record_tstamp
    
    engine_dict["prompts"] = prompts_list

    logging.debug(engine_dict)
    print(engine_dict)
    return engine_dict

