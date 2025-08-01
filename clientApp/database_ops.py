# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from connect_vector_db import create_db_connection, load_config, close_db_connection
from helper_methods import is_valid_email
import oracledb
import logging

logger = logging.getLogger("app_logger")

def get_user_id_by_email(email_address):
    connection,cursor,user_id = None, None, -9
    try:
        config_file = 'ConfigFile.properties'
        db_config = load_config(config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()

        select_sql = """
            SELECT ID
            FROM APP_USERS
            WHERE lower(EMAIL_ADDRESS) = lower(:1)
        """
        cursor.execute(select_sql, (email_address,))
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            logger.debug(f"Found user ID: {user_id}")
        else:
            logger.debug(f"No user found with email: {email_address}")
    except Exception as e:
        logger.error(f"Error retrieving user ID: {e}")
        user_id = -9
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
    return user_id

def create_app_user(email_address):
    connection, cursor, user_id = None, None, -9
    try:
        if not is_valid_email(email_address):
            logger.error(f"Invalid email address: {email_address}")
            return -9
        config_file = 'ConfigFile.properties'
        db_config = load_config(config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()
        insert_sql = """
            INSERT INTO APP_USERS (EMAIL_ADDRESS)
            VALUES (:1)
            RETURNING ID INTO :2
        """
        user_id_out = cursor.var(int)
        cursor.execute(insert_sql, (email_address, user_id_out))
        connection.commit()
        temp = user_id_out.getvalue()
        user_id = temp[0] if temp else -9
        logger.debug(f"Created new user with ID: {user_id}")
    except Exception as e:
        logger.error(f"Error creating new user: {e}")
        user_id = -9  # Return error code for database issues
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
    return user_id

def get_model_id(llm_type):
    connection,cursor,model_id = None, None, -9
    try:
        config_file = 'ConfigFile.properties'
        db_config = load_config(config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()
        #'GEN-PURPOSE-LMM'
        select_sql = """
            SELECT ID
            FROM MODEL_USAGE
            WHERE UPPER(MODEL_PURPOSE) = UPPER(:1)
            AND USAGE_STOP is NULL
            AND ROWNUM < 2
        """
        cursor.execute(select_sql, (llm_type,))
        result = cursor.fetchone()
        if result:
            model_id = result[0]
            logger.debug(f"Found user ID: {model_id}")
        else:
            logger.debug(f"No model found")
    except Exception as e:
        logger.error(f"Error retrieving model ID: {e}")
        model_id = -9
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
    return model_id

def persist_log_data(actiontype, llm_id, user_id, trust_id, trust_score, user_prompt, convo_prompt, convo_id, convo_seq_num, generated_sql, is_trusted, is_prompt_equiv, is_template_equiv, executed_sql, db_error_code, db_error_txt, is_authorized, is_clarify, is_action, action_type, parentid, user_feedback_code, user_feedback_txt):
    connection = None
    cursor = None
    returnedid = 0
    trust_id = int(trust_id)
    # action type L - new log record, R - Retry , LU - Log Upd, UFT - User Feedback Thumbs up/down, UFM - user feedback message
    try:
        config_file = 'ConfigFile.properties'
        db_config = load_config(config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()

        if actiontype == "L":
            new_id = cursor.var(oracledb.NUMBER)
            if trust_id == 0:
                trust_id = None
            insert_sql = """
                INSERT INTO EXECUTION_LOG(llm_id, user_id, trust_id, trust_score, user_prompt, convo_prompt, convo_id, convo_seq_num, generated_sql,
                                              is_trusted, is_prompt_equiv, is_template_equiv, executed_sql, db_error_code, db_error_txt, is_authorized,
                                              is_clarify, is_action, action_type)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8,:9,:10,:11,:12,:13,:14,:15,:16,:17,:18,:19)  RETURNING id INTO :new_id
            """
            cursor.execute(insert_sql,
                           (llm_id, user_id, trust_id, trust_score, user_prompt, convo_prompt, convo_id, convo_seq_num, generated_sql,
                            is_trusted, is_prompt_equiv, is_template_equiv, executed_sql, db_error_code, db_error_txt, is_authorized,
                            is_clarify, is_action, action_type,new_id))
            logger.debug("new id **" + str(new_id))
            value = new_id.getvalue()
            returnedid = value[0] if value else 0
            logger.debug("row id **" + str(returnedid))
            connection.commit()
            logger.debug("User action parent logging successful.")
        elif actiontype == "R":
            executed_sql = "- RETRY SUCCESS SQL:-" + executed_sql
            upd_sql = """
                UPDATE EXECUTION_LOG Set
                DB_ERROR_TXT = DB_ERROR_TXT || :1
                WHERE ID = :2
            """
            cursor.execute(upd_sql,
                           ( executed_sql,parentid))
            connection.commit()
            logger.debug("User action logging retry successful.")
        elif actiontype == "UFT":
            upd_sql = """
                UPDATE EXECUTION_LOG Set
                USER_FEEDBACK_CODE = :1
                WHERE ID = :2
            """
            cursor.execute(upd_sql,
                           (user_feedback_code,parentid))
            connection.commit()
            logger.debug("User feedback thumps up-down logging successful.")
        elif actiontype == "UFM":
            upd_sql = """
                UPDATE EXECUTION_LOG Set
                USER_FEEDBACK_TXT = :1
                WHERE ID = :2
            """
            cursor.execute(upd_sql,
                           (user_feedback_txt,parentid))
            connection.commit()
            logger.debug("User feedback message logging successful.")

    except Exception as e:
        logger.error(f"Error logging audit data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
    return returnedid

def persist_app_debug(parentid,debugdata):
    connection = None
    cursor = None
    # action type L - new log record, R - Retry , LU - Log Upd, UFT - User Feedback Thumbs up/down, UFM - user feedback message
    try:
        config_file = 'ConfigFile.properties'
        db_config = load_config(config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()
        insert_sql = """
            INSERT INTO APP_DEBUG_DATA(parent_id, debug_data)
            VALUES (:1, :2)
            """
        cursor.execute(insert_sql,
                          (parentid, debugdata))
        connection.commit()
        logger.debug("debug logging successful.")
    except Exception as e:
        logger.error(f"Error logging debug data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)

def log_user_action(certified_score, prompt_txt, sql_query, db_response_code, db_err_txt, generation_engine_nm,
                    sql_lineage, prompt_lineage,is_retry,is_followup, followup_parent_txt,followup_txt,parentid,actiontype,user_response_code,user_response_txt):
    connection = None
    cursor = None
    returnedid = 0
    # action type L - new log record, R - Retry , LU - Log Upd, UFT - User Feedback Thumbs up/down, UFM - user feedback message
    try:
        config_file = 'ConfigFile.properties'
        db_config = load_config(config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()

        if actiontype == "L":
            new_id = cursor.var(oracledb.NUMBER)
            insert_sql = """
                INSERT INTO Executed_Prompts (CERTIFIED_SCORE, PROMPT_TXT, SQL_QUERY, DB_RESPONSE_CODE, DB_ERR_TEXT, GENERATION_ENGINE_NM,
                                      SQL_LINEAGE, PROMPT_LINEAGE,IS_RETRY,IS_FOLLOWUP,FOLLOWUP_PARENT_TXT,FOLLOWUP_TXT)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8,:9,:10,:11,:12)  RETURNING id INTO :new_id
            """
            cursor.execute(insert_sql,
                           (certified_score, prompt_txt, sql_query, db_response_code, db_err_txt, generation_engine_nm, sql_lineage, prompt_lineage,
                            is_retry,is_followup, followup_parent_txt,followup_txt,new_id))
            logger.debug("new id **" + str(new_id))
            value = new_id.getvalue()
            returnedid = value[0] if value else 0
            logger.debug("row id **" + str(returnedid))
            connection.commit()
            logger.debug("User action parent logging successful.")
        elif actiontype == "R":
            insert_sql = """
                INSERT INTO Executed_Prompts_Retry (RETRY_SRC_ID, DB_RESPONSE_CODE,DB_ERR_TEXT,GENERATION_ENGINE_NM)
                VALUES (:1,:2,:3,:4)
            """
            cursor.execute(insert_sql,
                           (parentid, db_response_code, db_err_txt,generation_engine_nm))
            connection.commit()
            logger.debug("User action logging retry successful.")
        elif actiontype == "LU":
            upd_sql = """
                UPDATE Executed_Prompts Set
                DB_RESPONSE_CODE = :1,
                DB_ERR_TEXT = :2,
                GENERATION_ENGINE_NM = :3,
                SQL_QUERY = :4
                WHERE ID = :5
            """
            cursor.execute(upd_sql,
                           (db_response_code, db_err_txt,generation_engine_nm,sql_query,parentid))
            connection.commit()
            logger.debug("User action logging successful.")
        elif actiontype == "UFT":
            upd_sql = """
                UPDATE Executed_Prompts Set
                USER_RESPONSE_CODE = :1
                WHERE ID = :2
            """
            cursor.execute(upd_sql,
                           (user_response_code,parentid))
            connection.commit()
            logger.debug("User feedback thumps up-down logging successful.")
        elif actiontype == "UFM":
            upd_sql = """
                UPDATE Executed_Prompts Set
                USER_RESPONSE_TXT = :1
                WHERE ID = :2
            """
            cursor.execute(upd_sql,
                           (user_response_txt,parentid))
            connection.commit()
            logger.debug("User feedback message logging successful.")

    except Exception as e:
        logger.error(f"Error logging audit data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
    return returnedid
