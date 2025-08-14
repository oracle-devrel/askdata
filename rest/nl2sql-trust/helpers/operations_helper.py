# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import logging
import constants
from helpers.config_json_helper import config_boostrap as confb

import helpers.database_util as iou

logger = logging.getLogger(constants.OPERATION_LAYER)

def ops_live_logs(max_row_count:int=1000,domain=None):
    connection = iou.db_get_connection()
    statement = f""" select e.id as id,
                    to_char(execution_date, '{confb.config.database.datetime_format}') as exec_date,
                    a.email_address as user_email,
                    substr(convo_id,10)||'-'||convo_seq_num as convo_seq,
                    (case 
                        when convo_seq_num = 1 then user_prompt 
                        else convo_prompt 
                        end) prompt_txt,
                    (case 
                        when action_type = 'GRAPH' 
                        then 'graph'
                        else 'sql' 
                        end) action,
                    (case 
                        when is_action = 0 and is_trusted = 1 then 'T' 
                        when (is_action = 0 and (is_prompt_equiv = 1 or is_template_equiv = 1)) then 'S' 
                        when is_action = 0 and is_trusted = 0 then 'U' 
                        else ' '
                        end) trust_level,
                    (case
                        when is_action = 0 and is_clarify = 0 then t.sql_txt
                        else ' '
                        end) trusted_sql,
                    (case
                        when is_action = 0 and is_clarify = 0 then generated_sql
                        else ' '
                        end) generated_sql,
                    (case
                        when is_action = 0 and is_clarify = 0 then executed_sql
                        else ' '
                        end) executed_sql,
                    (case 
                        when user_feedback_code = -1 then 'neg' 
                        when user_feedback_code = 1 then 'pos' 
                        when user_feedback_code = 0 then ' ' 
                        end) user_feedback,
                    (case
                        when is_clarify = 1 then 'Y'
                        else ' '
                        end) clarify,
                    (case
                        when is_authorized = 0 then 'N'
                        else ' '
                        end) auth,
                    (case
                        when db_error_code is not null then db_error_code
                        else ' ' 
                        end) db_error_code,
                    (case
                        when is_cert_processed = 1 then 'Y'
                        else ' '
                        end) cert_queue
                from execution_log e
                    join app_users a on a.id = e.user_id
                    join trust_library t on t.id = e.trust_id
                order by e.id desc
                fetch first :1 rows only
                """
    data_list = []
    result = iou.db_select(connection, statement,(max_row_count,))
    connection.close()

    for r in result:
        #prompt = "" if r[3] is None else r[3]

        #id,exec_date,user_email,convo_seq,prompt_txt,action, trust_level, trusted_sql, generated_sql, executed_sql,user_feedback,clarify,auth,db_error_code,cert_queue
        record = {
            "id":r[0],
            "exec_date":r[1], 
            "user_email":r[2],
            "convo_seq":r[3],
            "prompt_txt": r[4],
            "action": r[5],
            "trust_level":r[6],
            "trusted_sql":r[7],
            "generated_sql": r[8],
            "executed_sql": r[9],
            "user_feedback": r[10],
            "clarify": r[11],
            "auth": r[12],
            "db_error_code": r[13],
            "cert_queue": r[14]
            }
    #    logger.debug(r)

        data_list.append(record)
    
    logger.debug(data_list)
    logger.info(f"ops_live_logs returns {len(data_list)} records.")
    return { "record list": data_list }

if __name__ == "__main__":
    pass