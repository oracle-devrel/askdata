# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from connect_vector_db import create_db_connection, load_config_db, close_db_connection
from database_conn_pool import get_connection
from sqlalchemy import text
import configparser
import logging
import pandas as pd
import pickle
from helper_methods import get_iquery_cache, get_idata_cache, apply_formatting, format_column_name, set_conversation_cache, get_conversation_cache, reset_conversation_cache
from llm_handler import chat_instructmode_llm, chat_with_llm
from graph_generator import create_conversation_message

config = configparser.RawConfigParser()
config.read('ConfigFile.properties')
logger = logging.getLogger("app_logger")

def get_recent_conversations(email_address):
    connection,cursor = None, None
    results = []
    try:
        config_file = 'ConfigFile.properties'
        #db_config = load_config(config_file)
        db_config = load_config_db('trust', config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()

        #_sql = """
        #    select id, convo_prompt from execution_log
        #    where user_id in (select id from app_users where lower(EMAIL_ADDRESS) = lower(:1)) and convo_seq_num = 1
        #    order by execution_date desc fetch first 5 rows only
        #"""
        
        _sql = """
            select e.id, e.convo_prompt
            from  execution_log e
            join (
                select max(id) as max_id from execution_log
                where user_id in (select id from app_users where lower(EMAIL_ADDRESS) = lower(:1)) and convo_seq_num = 1
                group by lower(convo_prompt)
                ) 
            latest on e.id = latest.max_id
            order by e.id desc fetch first 5 rows only
        """
        cursor.execute(_sql, (email_address,))
        results = cursor.fetchall()
        logger.debug(f"Retrieved {len(results)} records for email: {email_address}")
    except Exception as e:
        logger.error(f"Error retrieving recent prompts:\n {e}")
        results = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
    return results

def get_frequent_conversations(email_address):
    connection,cursor = None, None
    results = []
    try:
        config_file = 'ConfigFile.properties'
        #db_config = load_config(config_file)
        db_config = load_config_db('trust', config_file)
        connection = create_db_connection(db_config)
        cursor = connection.cursor()

        _sql = """
            select * from (
                select max(id) as id, convo_prompt, count(1) as usage_count
                from execution_log
                where user_id in (select id from app_users where lower(EMAIL_ADDRESS) = lower(:1)) and convo_seq_num = 1
                group by convo_prompt)
            order by usage_count desc, id desc
            fetch first 5 rows only
            """
        cursor.execute(_sql, (email_address,))
        results = cursor.fetchall()
        logger.debug(f"Retrieved {len(results)} records for email: {email_address}")
    except Exception as e:
        logger.error(f"Error retrieving recent prompts:\n {e}")
        results = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
    return results

def submit_conversation_to_agent(userId, idataId, prompt):
    response = None
    df  = pd.DataFrame()
    df_structure = None
    searchedKey = idataId+"_detailedInsights"
    try:
        #RESET conversation
        if prompt == "RESET":
            logger.debug("resetting conversation..")
            reset_conversation_cache(searchedKey)
            return "conversation cleared"
        # auto-insights
        if prompt == "Get Insights for the current Dataset":
            df_s = get_idata_cache(idataId, "idata")
            df = pickle.loads(df_s)
            logger.debug("top 5 rows from cache...")
            logger.debug(df.head())
            agent_prompt = get_agent_prompt(prompt, df)
            llm_response = chat_instructmode_llm(agent_prompt)
        # detailed-insights
        else:
            iquery = get_iquery_cache(idataId)
            if iquery:
                logger.debug(f"******iquery******{iquery}")
                rbac_user_id = ""
                if config.get('DatabaseSection', 'database.rbac') == 'Y':
                    logger.debug("RBAC is enabled")
                    rbac_user_id = userId
                else:
                    logger.debug("RBAC is disabled")
                try:
                    with get_connection(rbac_user_id, "") as connection:
                        connection.execute(text("alter session set nls_date_format = 'YYYY-MM-DD'"))
                        query_result = connection.execute(text(iquery))
                        column_names_iquery = query_result.keys()
                        results = query_result.fetchall()
                        converted_list = [tuple(list(row)) for row in results]
                        df = pd.DataFrame(converted_list, columns=column_names_iquery)
                        df = df.rename(columns=lambda x: format_column_name(x))
                        df = df.apply(apply_formatting)
                        columns = df.columns.tolist()
                        #df_structure = "{{'" + "', '".join(columns) + "'}}"
                        df_structure = "{'" + "', '".join(columns) + "'}"
                        logger.debug(df_structure)
                        logger.debug("few rows of data extracted from db...")
                        logger.debug(df.head(5).to_string(index=False))
                except Exception as e:
                    logger.error("Database exception occurred")
                    logger.error(f"Exception occurred: {e}")
                    return {"message": "Error occurred while retrieving data using interactive query"}

            #construct conversation obj 
            conversation = []
            #searchedKey = idataId+"_detailedInsights"
            retrieved_obj = get_conversation_cache(searchedKey)
            logger.debug(f"conversation key searched: {searchedKey}")
            if retrieved_obj is not None:
                conversation = pickle.loads(retrieved_obj)
            else:
                logger.debug("prior conversation not found for drill down request!")
                conversation = []

            if len(conversation) == 0:
                logger.debug("creating the first prompt for detailed insights")
                #agent_prompt = f"print hello and current time, then tell me how many rows are there in the {df}"
                agent_prompt = get_agent_prompt(prompt, df)
                conversation = create_conversation_message(agent_prompt,conversation,"USER")
            else:
                agent_prompt = f"{prompt}. You are given a pandas DataFrame with the following structure:{df_structure}."
                conversation = create_conversation_message(agent_prompt,conversation,"USER")
            logger.debug("adding conversation to cache..")
            conversation_obj = pickle.dumps(conversation)
            set_conversation_cache(searchedKey,conversation_obj)
            logger.debug(conversation)
            logger.debug("calling llm with conversation...")
            llm_response = chat_with_llm(conversation)
            #generated_code = extract_python_code(response)
            logger.debug("Adding assistant message to the conversation...")
            conversation = create_conversation_message(llm_response,conversation,"ASSISTANT")
            logger.debug("adding conversation to cache..")
            conversation_obj = pickle.dumps(conversation)
            set_conversation_cache(searchedKey,conversation_obj)
            logger.debug(conversation)
            #logger.debug(f"Generated Code:\n{generated_code}")
            #llm_response = chat_instructmode_llm(agent_prompt)
        response = f"""<html>{llm_response}<html>"""
    except Exception as e:
        logger.error(f"An internal server error occurred: {e}")
        return {"message": "An internal server error occurred, please contact administrator."}
    return response

def get_agent_prompt(user_prompt, df):
    columns = df.columns.tolist()
    df_structure = "{'" + "', '".join(columns) + "'}"
    msg = rf"""
        You are a skilled data analyst. Given a pandas DataFrame, its structure, and a user query, analyze the data and generate insights that directly answer the user's question.

        ### Instructions
        - Interpret the user prompt.
        - Examine the structure of the DataFrame to understand available fields.
        - Provide relevant data insights: summaries, trends, comparisons, or anomalies.
        - Present the findings in a clear, concise paragraph using natural language for a business user. Don't use technical words such as dataframe.
        - Write a narrative that presents the key insights using bullet points wherever needed.
        - Limit your response to less than 300 words.
        - Present the response in a well formatted HTML with bullets and paragraphs.

        ### DataFrame: 
        {df}

        ### DataFrame Schema: 
        {df_structure}

        ### User Prompt:
        {user_prompt}
        """
    return msg
