# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import os
import uuid
import re
from datetime import datetime
import time
from audit_logging import log_audit_test_insert
import configparser
import requests
import redis
import json
import pandas as pd
from decimal import Decimal
from sqlalchemy import text
import hashlib
import argparse
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn, json, datetime
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import re
import concurrent.futures
from datetime import datetime, timedelta
from get_top_match import return_validated_sql
from sql_metadata import Parser
from generate_embeddings import create_prompt_embd, create_column_embd
from graph_generator import get_plotly_graph, get_empty_graph, get_ojet_graph, processdata, get_summary_llm
import oracledb
from llm_handler import create_user_message, create_assistant_message, chat_conversion,get_llm_sql, check_sql_equiv, get_prompt_equiv, seek_clarification, check_graphing_request, classify_iprompt_request, read_file_to_string, get_sql_prompt, seek_explanation, seek_intent
import pickle
import difflib
from database_ops   import get_user_id_by_email, create_app_user, get_model_id, persist_log_data, log_user_action,persist_app_debug
from database_conn_pool import get_connection
from helper_methods import setup_logger, clean_query, get_image, remove_quotes, draw_bar_chart, apply_formatting, concat_ids, separate_ids, generate_diff_string
from helper_methods import initialize_query_variables, set_chat_cache, get_chat_cache, set_conversation_cache, get_conversation_cache, reset_conversation_cache, set_session_data
from helper_methods import get_session_data, get_prompt_conversation_cache, set_prompt_conversation_cache, set_graph_cache, get_graph_cache, set_iquery_cache, get_iquery_cache, set_idata_cache, get_idata_cache, reset_idata_cache, get_idata_step_counter, remove_limit_fetch
from helper_methods import check_substring_single_space, format_column_name,getmd5hash, normalize_spaces, delcache, delsessioncache, clean_ending, init_cap, starts_with_delete_or_truncate, is_valid_email, check_graphing_request_by_string, is_numeric_column
from dynamic_prompt_injection import get_hints4llm
from semi_trusted_path import auto_certify
from conversation_methods import get_recent_conversations, get_frequent_conversations, submit_conversation_to_agent

config = configparser.RawConfigParser()
config.read('ConfigFile.properties')
logger = setup_logger('nl2sql_app.log')
logger.info("Main application logger initialized")

stylesmall = "<style> table { border-collapse: collapse; width: 100%;} th { text-align: center; padding: 4px;font-family: Arial !important; font-size: 12px !important;} td {text-align: left !important;padding: 4px !important;font-family: Arial !important; font-size: 12px !important;color: black !important;} tr:nth-child(even){background-color: #eee} tr:nth-child(odd){background-color: #fff} th {background-color: #fff;color: black;}</style>"
stylelarge = "<style> table { border-collapse: collapse; width: 100%;} th { text-align: center; padding: 4px;font-family: Arial !important; font-size: 16px !important;} td {text-align: left !important;padding: 4px !important;font-family: Arial !important; font-size: 16px !important;color: black !important;} tr:nth-child(even){background-color: #eee} tr:nth-child(odd){background-color: #fff} th {background-color: #fff;color: black;}</style>"

# global varibales
modified_prompt = ""
df = pd.DataFrame()
column_names = []
fetchstmt = ""

def query(prompt: str, domain: str, usergroup: str, userid: str, session_id:str, followup_flg:str, previous_prompt: str, graphFlag:bool, conversation, reworded: str, user_key, model_id, convo_seq_no):
    #initialize
    (
        is_retry, is_followup, followup_parent_txt, followup_txt, match_status,
        trust_id, is_trusted, is_prompt_equiv, is_template_equiv, is_clarify,
        is_action, action_type, llm_id, user_id, trust_score, user_prompt,
        convo_prompt, convo_id, convo_seq_num, generated_sql, executed_sql,
        db_error_code, db_error_txt, is_authorized, parentid, latency_generate_sql, latency_exec_sql, is_dynamic_instr, is_autocertify, is_parent_corrected, template_id
    ) = initialize_query_variables(model_id, user_key, prompt, reworded, session_id, convo_seq_no)

    logger.debug("*****************query*****************")
    logger.debug(f"""Query function parameters:
    - prompt: {prompt}
    - domain: {domain}
    - userid: {userid}
    - session_id: {session_id}
    - followup_flg: {followup_flg}
    - previous_prompt: {previous_prompt}
    - graphFlag: {graphFlag}
    - reworded: {reworded}
    - user_key: {user_key}
    - model_id: {model_id}
    - convo_seq_no: {convo_seq_no}""")

    idataid = str(uuid.uuid4())
    db_debug = config.get('DatabaseSection', 'database.debug')
    debug_txt = ""
    execution_log_id = 0

    #graphing is handled differently
    if graphFlag:
        is_action,action_type = 1,"GRAPH"
        query_raw = get_chat_cache(session_id + "querycache")
        sql_lineage = ""
        #maybe not needed
        logger.debug(f"looking up the vector db to find a match for: {previous_prompt}")
        trust_id,prompt_lineage,validated_query,match_ratio,match_status = return_validated_sql(previous_prompt)
        trust_score = match_ratio
    else:
        ### conversation ####
        if config.getboolean('FeatureFlags', 'feature.dynamicprompt'):
            logger.debug(f"retrieving hints for dynamic prompt...")
            hints = get_hints4llm(reworded)
            if hints:
                is_dynamic_instr = 1
                logger.debug(f"dynamic prompt to be injected is:\n {hints}")
            logger.debug(f"creating user message with prompt: {reworded}")
            conversation.append(create_user_message(reworded,conversation,domain,hints))
        else:
            logger.debug(f"dynamic prompt is disabled.")
            logger.debug(f"creating user message with: {reworded}")
            conversation.append(create_user_message(reworded,conversation,domain))
        if followup_flg == "F":
            is_followup = 1
            followup_parent_txt = previous_prompt
            followup_txt = reworded
        logger.debug(conversation)
        sql_lineage = ""
        logger.debug(f"looking up the vector db to find a match for: {reworded}")
        trust_id,prompt_lineage,validated_query,match_ratio,match_status = return_validated_sql(reworded)
        trust_score = match_ratio
        logger.debug(f"returned query: {validated_query}" )
        logger.debug(f"match ratio: {match_ratio}")
        logger.debug(f"match status: {match_status}")
        if match_status in ("None Found","VERIFIED-FAILED-NUM-PARAMCHECK","SIMILAR","NA"):
            logger.debug("getting llm sql..." )
            latency_generate_sql_s = time.perf_counter()
            query_raw = get_llm_sql(conversation)
            latency_generate_sql = round(time.perf_counter() - latency_generate_sql_s, 3)
            # initially mark generated and executed SQL to be the same (think it is totally untrusted)
            generated_sql = query_raw
            logger.debug(f"running clean query for:\n{query_raw}")
            executed_sql, fetchstmt = clean_query(query_raw)
            
            # replacing with auto-certify logic
            #equiv_result, equiv_prompt = check_sql_equiv(validated_query, query_raw)
            #logger.debug(f"sql equivalent result: {equiv_result}")
            #sql_diff     = generate_diff_string(validated_query, query_raw)
            #logger.debug(f"sql_diff result is: {sql_diff}")
            #logger.debug(f"trust query:\n{validated_query}")
            #logger.debug(f"llm query:\n{query_raw}")
            #debug_txt = "sql equivalent result:" +  equiv_result + "\n" + "sql_diff result is:   " +  sql_diff + "\n" + "trusted query: " + validated_query + "\n" + "llm query: " + query_raw

            #if equiv_result == "YES" and sql_diff == "=":
            #    is_prompt_equiv = 1
            #    logger.debug("top sql and generated sql are prompt equivalent")
            #if equiv_result == "YES" and sql_diff != "=":
            #    is_template_equiv = 1
                # bug fix
                #generated_sql = validated_query
            #    logger.debug("top sql and generated sql are template equivalent")
            
            # auto-certify logic replacing equivalence logic above
            is_autocertify, is_parent_corrected, template_id = auto_certify(reworded, query_raw, domain)
            logger.debug(f"is_autocertify={is_autocertify}, is_parent_corrected={is_parent_corrected}, template_id={template_id}")
        else:
            logger.debug("this sql is from 100% validated" )
            is_trusted = 1
            query_raw    =     validated_query
            generated_sql =    validated_query
            logger.debug(f"running clean query for:\n{query_raw}")
            executed_sql, fetchstmt = clean_query(query_raw)

    # if the SQL Generator LLM returned -- I do not know -- then we have a problem!!
    if check_substring_single_space(query_raw, "Please clarify."):
        logger.debug(f"Clarification is needed.")
        is_clarify = 1
        executed_sql = ""
        generated_sql = ""
        execution_log_id = persist_log_data("L", llm_id=llm_id, user_id=user_id, trust_id=int(trust_id), trust_score=float(trust_score), user_prompt=user_prompt, convo_prompt=convo_prompt, convo_id=convo_id, convo_seq_num=convo_seq_num, generated_sql=generated_sql, is_trusted=is_trusted, is_prompt_equiv=is_prompt_equiv, is_template_equiv=is_template_equiv, executed_sql=executed_sql, db_error_code=db_error_code, db_error_txt=db_error_txt, is_authorized=is_authorized, is_clarify=is_clarify, is_action=is_action, action_type=action_type, parentid=parentid, latency_generate_sql=latency_generate_sql, latency_exec_sql=latency_exec_sql, is_dynamic_instr=is_dynamic_instr, domain=domain, is_autocertify=is_autocertify, is_parent_corrected=is_parent_corrected, template_id=template_id)
        set_chat_cache(session_id + "lastid",str(execution_log_id))
        ### conversation ####
        conversation.append(create_assistant_message("Please clarify."))
        conversation_obj = pickle.dumps(conversation)
        set_conversation_cache(session_id,conversation_obj)
        return_msg = seek_clarification("Not Applicable", "LLM was not able to generate a SQL",reworded,domain)
        return return_msg

    # clean up the raw query
    logger.debug(f"running clean query for:\n{query_raw}")
    query_clean, fetchstmt = clean_query(query_raw)
    ### conversation ####
    if fetchstmt:
        logger.debug(f"removing fetch statement added by engine and appending query to conversation.")
        conversation.append(create_assistant_message(re.sub(r'\s*SELECT', 'SELECT',remove_limit_fetch(query_clean))))
    else:
        logger.debug(f"appending query to conversation.")
        conversation.append(create_assistant_message(re.sub(r'\s*SELECT', 'SELECT',query_clean)))

    conversation_obj = pickle.dumps(conversation)
    set_conversation_cache(session_id,conversation_obj)

    query_clean = query_clean.replace("\n", " ").replace("\\n", " ").replace(";", "").strip()
    # global dataframe to display data from the database
    databaseexception = False
    rbac_user_id = ""
    if config.get('DatabaseSection', 'database.rbac') == 'Y':
        logger.debug("RBAC is enabled")
        rbac_user_id = userid
    else:
        logger.debug("RBAC is disabled")
    try:
        with get_connection(rbac_user_id,  "" ) as connection:
            query_result_setdateformat = connection.execute(text("alter session set nls_date_format = 'YYYY-MM-DD'"))
            query_clean = remove_quotes(query_clean)
            if starts_with_delete_or_truncate(query_clean):
                usermsg = "Last SQL Operation not permitted"
                ### conversation ####
                logger.debug(f"creating user message with: {usermsg}")
                conversation.append(create_user_message(usermsg,conversation,domain))
                conversation_obj = pickle.dumps(conversation)
                set_conversation_cache(session_id,conversation_obj)
                logger.debug("Last SQL Operation not permitted")
                db_response_code = 400
                db_error_text = "delete or truncate detected"
                execution_log_id = persist_log_data("L", llm_id=llm_id, user_id=user_id, trust_id=int(trust_id), trust_score=float(trust_score), user_prompt=user_prompt, convo_prompt=convo_prompt, convo_id=convo_id, convo_seq_num=convo_seq_num, generated_sql=generated_sql, is_trusted=is_trusted, is_prompt_equiv=is_prompt_equiv, is_template_equiv=is_template_equiv, executed_sql=executed_sql, db_error_code=db_error_code, db_error_txt=db_error_txt, is_authorized=is_authorized, is_clarify=is_clarify, is_action=is_action, action_type=action_type, parentid=parentid, latency_generate_sql=latency_generate_sql, latency_exec_sql=latency_exec_sql, is_dynamic_instr=is_dynamic_instr, domain=domain, is_autocertify=is_autocertify, is_parent_corrected=is_parent_corrected, template_id=template_id)
                return "Operation not permitted. Please check your with your admin."
            try:
                logger.debug("running the sql on database...")
                latency_exec_sql_s = time.perf_counter()
                query_result = connection.execute(text(re.sub(r'\s*SELECT', 'SELECT',query_clean)))
                latency_exec_sql = round(time.perf_counter() - latency_exec_sql_s, 3)
                db_response_code = 200
                db_error_text = "No Error"
                execution_log_id = persist_log_data("L", llm_id=llm_id, user_id=user_id, trust_id=int(trust_id), trust_score=float(trust_score), user_prompt=user_prompt, convo_prompt=convo_prompt, convo_id=convo_id, convo_seq_num=convo_seq_num, generated_sql=generated_sql, is_trusted=is_trusted, is_prompt_equiv=is_prompt_equiv, is_template_equiv=is_template_equiv, executed_sql=executed_sql, db_error_code=db_error_code, db_error_txt=db_error_txt, is_authorized=is_authorized, is_clarify=is_clarify, is_action=is_action, action_type=action_type, parentid=parentid, latency_generate_sql=latency_generate_sql, latency_exec_sql=latency_exec_sql, is_dynamic_instr=is_dynamic_instr, domain=domain, is_autocertify=is_autocertify, is_parent_corrected=is_parent_corrected, template_id=template_id)
                try:
                    if db_debug == "Y":
                        persist_app_debug(execution_log_id,debug_txt)
                except Exception as e:
                    logger.error("extra debugging failed")
                set_chat_cache(session_id + "querycache",query_clean)
                set_chat_cache(session_id, reworded)
                set_chat_cache(session_id + "lastid",str(execution_log_id))
                usermsg = "Great, thanks"
                ### conversation ####
                logger.debug(f"creating user message with: {usermsg}")
                conversation.append(create_user_message(usermsg,conversation,domain))
                conversation_obj = pickle.dumps(conversation)
                set_conversation_cache(session_id,conversation_obj)
            except Exception as e:
                databaseexception = True
                logger.error("Database exception occurred")
                error_code = re.search(r'ORA-\d+', str(e)).group(0) if re.search(r'ORA-\d+', str(e)) else 'Unknown Error Code'
                error_message = str(e)
                db_error_code = error_code
                db_error_txt = error_message
                execution_log_id = persist_log_data("L", llm_id=llm_id, user_id=user_id, trust_id=int(trust_id), trust_score=float(trust_score), user_prompt=user_prompt, convo_prompt=convo_prompt, convo_id=convo_id, convo_seq_num=convo_seq_num, generated_sql=generated_sql, is_trusted=is_trusted, is_prompt_equiv=is_prompt_equiv, is_template_equiv=is_template_equiv, executed_sql=executed_sql, db_error_code=db_error_code, db_error_txt=db_error_txt, is_authorized=is_authorized, is_clarify=is_clarify, is_action=is_action, action_type=action_type, parentid=parentid, latency_generate_sql=latency_generate_sql, latency_exec_sql=latency_exec_sql, is_dynamic_instr=is_dynamic_instr, domain=domain, is_autocertify=is_autocertify, is_parent_corrected=is_parent_corrected, template_id=template_id)
                set_chat_cache(session_id + "lastid",str(execution_log_id))
                usermsg = "last query  caused error code " + error_code + " .Please fix and return a syntactically correct SQL for the user question."
                ### conversation ####
                logger.debug(f"creating user message with: {usermsg}")
                conversation.append(create_user_message(usermsg,conversation,domain))
                conversation_obj = pickle.dumps(conversation)
                set_conversation_cache(session_id,conversation_obj)
                latency_generate_sql_s = time.perf_counter()
                query_raw = get_llm_sql(conversation)
                latency_generate_sql = round(time.perf_counter() - latency_generate_sql_s, 3)
                logger.debug(f"llm SQL after fixing:\n{query_raw}")

                if check_substring_single_space(query_raw, "Please clarify."):
                    ### conversation ####
                    conversation.append(create_assistant_message("Please clarify."))
                    conversation_obj = pickle.dumps(conversation)
                    set_conversation_cache(session_id,conversation_obj)
                    return_msg = seek_clarification("Not Applicable", "LLM was not able to generate a SQL",reworded,domain)
                    return return_msg
                logger.debug(f"running clean query for:\n{query_raw}")
                query_clean, fetchstmt = clean_query(query_raw)
                query_clean = remove_quotes(query_clean)

                if starts_with_delete_or_truncate(query_clean):
                    usermsg = "Last SQL Operation not permitted"
                    logger.debug(f"creating user message with: {usermsg}")
                    conversation.append(create_user_message(usermsg,conversation,domain))
                    conversation_obj = pickle.dumps(conversation)
                    set_conversation_cache(session_id,conversation_obj)
                    return "Operation not permitted. Please check your with your admin."
                else:
                    ### conversation ####
                    conversation.append(create_assistant_message(re.sub(r'\s*SELECT', 'SELECT',query_clean)))
                    conversation_obj = pickle.dumps(conversation)
                    set_conversation_cache(session_id,conversation_obj)
                latency_exec_sql_s = time.perf_counter()
                query_result = connection.execute(text(re.sub(r'\s*SELECT', 'SELECT',query_clean)))
                latency_exec_sql = round(time.perf_counter() - latency_exec_sql_s, 3)
                set_chat_cache(session_id + "querycache",query_clean)
                set_chat_cache(session_id, reworded)
                error_code = 200;
                error_message = "No Error";
                db_error_txt = "** SQL: " + query_clean
                execution_log_id = persist_log_data("R", llm_id=llm_id, user_id=user_id, trust_id=int(trust_id), trust_score=float(trust_score), user_prompt=user_prompt, convo_prompt=convo_prompt, convo_id=convo_id, convo_seq_num=convo_seq_num, generated_sql=generated_sql, is_trusted=is_trusted, is_prompt_equiv=is_prompt_equiv, is_template_equiv=is_template_equiv, executed_sql=executed_sql, db_error_code=db_error_code, db_error_txt=db_error_txt, is_authorized=is_authorized, is_clarify=is_clarify, is_action=is_action, action_type=action_type, parentid=parentid, latency_generate_sql=latency_generate_sql, latency_exec_sql=latency_exec_sql, is_dynamic_instr=is_dynamic_instr, domain=domain, is_autocertify=is_autocertify, is_parent_corrected=is_parent_corrected, template_id=template_id)

            usermsg = "Great, thanks"
            ### conversation ####
            logger.debug(f"creating user message with: {usermsg}")
            conversation.append(create_user_message(usermsg,conversation,domain))
            conversation_obj = pickle.dumps(conversation)
            set_conversation_cache(session_id,conversation_obj)
        if fetchstmt:
            logger.debug(f"removing fetch statement added by engine.")
            iquery = remove_limit_fetch(query_clean)
        else:
            iquery = query_clean
        set_iquery_cache(idataid, iquery)
        logger.debug(f"saved query to cache with idataid: {idataid}\n{iquery}")
        column_names = query_result.keys()
        results = query_result.fetchall()
        list_of_results = [list(row) for row in results]
        converted_list = [tuple(item) for item in list_of_results]
    except Exception as e:
        logger.error("******** final exception **********")
        logger.error(f"{e}")
        usermsg = "Last SQL query returned an error."
        ### conversation ####
        logger.debug(f"creating user message with: {usermsg}")
        conversation.append(create_user_message(usermsg,conversation,domain))
        conversation_obj = pickle.dumps(conversation)
        set_conversation_cache(session_id,conversation_obj)
        return "Database query returned an error. Please try again using a different prompt."

    # populate the global DF
    df = pd.DataFrame(converted_list, columns=column_names)
    df = df.rename(columns=lambda x: format_column_name(x))
    if len(column_names) > 3:
        style = stylesmall
    else:
        style = stylelarge
    fig_json = {}
    gid = str(uuid.uuid4())
    graph_app_url = config.get('vbcs', 'endpoint.url') + config.get('vbcs', 'graph_app.url')
    idata_app_url = config.get('vbcs', 'endpoint.url') + config.get('vbcs', 'idata_app.url')
    oda_flags = []
    if graphFlag:
        logger.debug(f"generating graph...")
        igraph_link_html = ""
        try:
            chrthtml,fig_json  = get_plotly_graph(reworded, df)
            isInteractive = True
        except Exception as e:
            logger.error(f"{e}")
            logger.error(f"Error in get_graph: {e}, falling back to draw_bar_chart...")
            chrthtml = draw_bar_chart(df)
            isInteractive = False
        if isInteractive:    
            set_graph_cache(gid, json.dumps(fig_json))
            logger.debug(f"graph is saved into cache with graphid: {gid}")
            igraph_link_html = f'<table border=2><tr><td><a href="{graph_app_url}?graphId={gid}">View interactive graph</a></td></tr></table>'
        df = df.apply(apply_formatting)
        #df_html = df.to_html(index=False, escape=False).replace('\n', '')
        logger.debug("aligning number columns...")
        numeric_cols = [col for col in df.columns if is_numeric_column(df[col])]
        for col in numeric_cols:
            df[col] = df[col].apply(lambda x: f'<div style="text-align: right;">{x}</div>' if pd.notna(x) else x)
        df_html = df.to_html(index=False, escape=False).replace('\n', '')

        htmldataframe = f"""<html><head>{style}</head>{df_html}<div>{chrthtml}</div>{igraph_link_html}</html>"""
    else:
        df = df.apply(apply_formatting)
        if is_trusted == 1:
            logger.debug(f"marking as a trusted query before returning...")
            trusted_icon, mime_type = get_image("trusted.png")
            trusted_icon_html = f'<img src="data:{mime_type};base64,{trusted_icon}" id="trustedIcon" alt="trusted" title="This query has been certified and can be trusted" width="20" height="20">'
        elif is_autocertify == 1:
            logger.debug(f"marking as a trusted query with auto-certification before returning...")
            trusted_icon, mime_type = get_image("trusted.png")
            trusted_icon_html = f'<img src="data:{mime_type};base64,{trusted_icon}" id="trustedIcon" alt="trusted" title="This query has been certified & can be trusted" width="20" height="20">'
        else:
            logger.debug(f"marking as an untrusted query before returning...")
            trusted_icon, mime_type = get_image("untrusted.png")
            trusted_icon_html = f'<img src="data:{mime_type};base64,{trusted_icon}" id="trustedIcon" alt="untrusted" title="This query is yet to be certified, please use with caution until it is certified by your admin." width="20" height="20">'
        
        record_count_html = ""
        if len(df) > 0:
            record_count_html = f"""<br/>Displaying top {len(df)} record(s) <a href="{idata_app_url}?idataId={idataid}&pPrompt={reworded}">Explore Dataset</a>"""
        else:
            record_count_html = f"<br/>{len(df)} records found."

        #df_html = df.to_html(index=False, escape=False).replace('\n', '')
        logger.debug("aligning number columns...")
        numeric_cols = [col for col in df.columns if is_numeric_column(df[col])]
        for col in numeric_cols:
            df[col] = df[col].apply(lambda x: f'<div style="text-align: right;">{x}</div>' if pd.notna(x) else x)
        df_html = df.to_html(index=False, escape=False).replace('\n', '')

        sqlquery_html = f"""<details><summary>SQL Query</summary>{iquery}</details>"""
        
        explanation_html = ""
        odaflags_html = ""
        explanation = ""
        if config.getboolean('FeatureFlags', 'feature.explain'):
            logger.debug(f"seeking explanation...")
            explanation = seek_explanation(conversation,iquery,domain)
            explanation_html = f"""<details><summary>Explain</summary>{explanation}</details>"""
        else:
            logger.debug(f"explain feature is not enabled!")

        if config.getboolean('FeatureFlags', 'feature.intent'):
            # when explanation feature is disabled but intent is enabled
            if not explanation:
                logger.debug(f"seeking explanation to determine intent...")
                explanation = seek_explanation(conversation, iquery, domain)
            logger.debug(f"seeking intent...")
            intentmatch = seek_intent(conversation, explanation)
            if intentmatch == "NO":
                oda_flags.append("ODACLARIFY")
            if oda_flags:
                flags_str = ", ".join(oda_flags)
                odaflags_html = f"<!-- {flags_str} -->"
        else:
            logger.debug(f"intent feature is not enabled!")

        htmldataframe = f"""<html><head>{style}</head>{df_html}<i>Responding to: {reworded} {trusted_icon_html}</i>{record_count_html}{explanation_html}{sqlquery_html}</html>{odaflags_html}"""

    logger.debug(f"{htmldataframe}")
    return htmldataframe, execution_log_id

app = FastAPI()

@app.post("/")
async def create_item(request: Request):
    response=""
    execution_log_id = 0
    convo_seq_no = 0
    try:
        start_time = time.perf_counter()
        logger.debug("request received from the client...")
        j = await request.body()
        json_post_raw = await request.json()
        json_post = json.dumps(json_post_raw)
        json_post_list = json.loads(json_post)
        question = json_post_list.get('question', "").strip()
        logger.info(f"oda question: {question}")
        oda_sessionid = json_post_list.get('sessionid', "").strip()
        logger.debug(f"oda sessionid: {oda_sessionid}")
        oda_userName = json_post_list.get('userName', "").strip()
        logger.debug(f"oda userName: {oda_userName}")
        oda_domain = json_post_list.get('domain', "").strip()
        logger.debug(f"oda domain: {oda_domain}")
        oda_groupName = json_post_list.get('groupName', "").strip()
        logger.debug(f"oda groupName: {oda_groupName}")

        if not oda_userName or oda_userName == 'anonymous':
            anonymous = config.getboolean('security', 'anonymous.flag')
            if anonymous:
                oda_userName = "anonymous@oracle.com"
                logger.debug(f"Anonymous access enabled. Setting oda_userName to: {oda_userName}")
            else:
                logger.error("Anonymous access is disabled. Returning configuration error.")
                return "User doesn't have access, please contact admin."

        user_id = get_user_id_by_email(oda_userName)
        if user_id == -9 and is_valid_email(oda_userName):
            logger.debug(f"User not found for email: {oda_userName}. Creating a new user...")
            user_id = create_app_user(oda_userName, oda_groupName)
        elif user_id == -9:
            logger.error(f"Invalid email address: {oda_userName}. Cannot create a new user.")
            return "Invalid user email address"

        if user_id == -9:
            logger.error(f"Invalid user, please check your access.")
            return "User request was not processed, please check your access."

        model_id = get_model_id("GEN-PURPOSE-LLM")
        if model_id == -9:
            logger.error(f"Invalid model, please check application config.")
            return "Application config error, please contact your admin."

        logger.debug(f"question:{question}; oda_sessionid:{oda_sessionid}; oda_userName:{oda_userName}; userid:{user_id};")
        if re.sub(r'\s+', ' ', question.strip().lower()) in ["clear all","clear all history","clear all cache","delete all history","delete all cache"]:
            logger.info(f"Deleting cache and returning...")
            delcache()
            return "Done"

        if re.sub(r'\s+', ' ', question.strip().lower()) in ["clear","clear session history","clear session cache","delete session history", "clear history", "delete session cache","delete history", "delete cache"]:
            logger.info(f"Deleting session cache and returning...")
            delsessioncache(oda_sessionid)
            return "Done"
        
        if config.getboolean('FeatureFlags', 'feature.llmgraphcheck'):
            logger.debug(f"LLM-check if it is a graphing request...")
            graphFlg = check_graphing_request(question)
        else:
            logger.debug(f"string-check if it is a graphing request...")
            graphFlg = check_graphing_request_by_string(question)

        if graphFlg and not config.getboolean('FeatureFlags', 'feature.chatgraph'):
            return f"<html><body><p>Please use <b>Explore Dataset</b> option above for interactive graphing.</p></body></html>"

        logger.debug(f"Retrieving chat cache...")
        previous = get_chat_cache(oda_sessionid)
        if previous == " none.":
            logger.debug(f"This is a new conversation.")
            followupFlg = "P"  #parent
            conversation = []
            prompt_conversation = []
            logger.debug(f"chat conversion...")
            reworded, prompt_conversation = chat_conversion(question,prompt_conversation)
            print("reworded\n", reworded)
            logger.debug(f"length of prompt_conversation: {len(prompt_conversation)}")
            prompt_conversation_obj = pickle.dumps(prompt_conversation)
            set_prompt_conversation_cache(oda_sessionid,prompt_conversation_obj)
            set_session_data(oda_sessionid,concat_ids(user_id,model_id,1))
            logger.debug(f"user and model init: {user_id}; {model_id};")
            response, execution_log_id = query(question,oda_domain,oda_groupName,oda_userName,oda_sessionid,followupFlg,previous,graphFlg,conversation,question,user_id,model_id,1)
        else:
            logger.debug(f"This is a followup conversation.")
            followupFlg = "F" #followup
            user_id, model_id, convo_seq_no = separate_ids(get_session_data(oda_sessionid))
            logger.debug(f"seq:{convo_seq_no}; model:{model_id}; user:{user_id};")
            convo_seq_no  = convo_seq_no + 1
            set_session_data(oda_sessionid,concat_ids(user_id,model_id,convo_seq_no))
            if graphFlg:
                logger.debug("retrieving last conversation for graphing request...")
                retrieved_obj = get_conversation_cache(oda_sessionid)
                if retrieved_obj is not None:
                    conversation = pickle.loads(retrieved_obj)
                else:
                    logger.debug("prior conversation not found for graphing request!")
                    conversation = []
                response, execution_log_id = query(question,oda_domain,oda_groupName,oda_userName,oda_sessionid,followupFlg,previous,graphFlg,conversation,question,user_id,model_id,convo_seq_no)
            else:
                logger.debug(f"retrieving conversation object...")
                retrieved_prompt_conversation_obj = get_prompt_conversation_cache(oda_sessionid)
                if retrieved_prompt_conversation_obj is not None:
                    prompt_conversation = pickle.loads(retrieved_prompt_conversation_obj)
                    logger.debug(f"conversation length: {len(prompt_conversation)} \nretrieved_prompt_conversation_obj: {prompt_conversation}")
                else:
                    prompt_conversation = []
                logger.debug(f"chat conversion...")
                reworded, prompt_conversation = chat_conversion(question,prompt_conversation)
                prompt_conversation_obj = pickle.dumps(prompt_conversation)
                set_prompt_conversation_cache(oda_sessionid,prompt_conversation_obj)
                logger.debug(prompt_conversation)
                stripped_llm_response = reworded.lstrip().lower()
                if (stripped_llm_response.startswith("i'm sorry") or stripped_llm_response.startswith("great thank")):
                    logger.debug("******* after reword sorry *******")
                    is_clarify = 1
                    response = reworded
                    execution_log_id = persist_log_data("L", llm_id=model_id, user_id=user_id, trust_id=0, trust_score=0, user_prompt=question, convo_prompt=reworded, convo_id=oda_sessionid, convo_seq_num=convo_seq_no, generated_sql="", is_trusted=0, is_prompt_equiv=0, is_template_equiv=0, executed_sql="", db_error_code="", db_error_txt="", is_authorized=1, is_clarify=1, is_action=0, action_type="", parentid=0, latency_generate_sql=latency_generate_sql, latency_exec_sql=latency_exec_sql, is_dynamic_instr=0, domain=domain)
                else:
                    retrieved_obj = get_conversation_cache(oda_sessionid)
                    if retrieved_obj is not None:
                        conversation = pickle.loads(retrieved_obj)
                    else:
                        logger.debug("******* followup but no obj *******")
                        conversation = []
                    response, execution_log_id = query(question,oda_domain,oda_groupName,oda_userName,oda_sessionid,followupFlg,previous,graphFlg,conversation,reworded,user_id,model_id,convo_seq_no)
    except Exception as e:
        logger.error(f"An internal server error occurred: {e}")
        response = f"An internal server error occurred, please contact administrator."
    total_elapsed_time = round(time.perf_counter() - start_time, 3)
    
    if execution_log_id != 0:
        dummyid = persist_log_data("LU", parentid=execution_log_id, latency_backend=total_elapsed_time)
        logger.debug(f"logged total_elapsed_time {total_elapsed_time} seconds with id: '{execution_log_id}'.")
    else:
        execution_log_id = persist_log_data("L", llm_id=model_id, user_id=user_id,  user_prompt=question, convo_prompt=reworded, convo_id=oda_sessionid, convo_seq_num=convo_seq_no, domain=oda_domain, latency_backend=total_elapsed_time)
        logger.debug(f"logged total_elapsed_time {total_elapsed_time} seconds with id: '{execution_log_id}'.")
    
    logger.info(f"Total request processing time: {total_elapsed_time:.2f} seconds\n\n\n")
    return response

@app.get("/igraph")
@app.get("/igraph/")
async def get_graph(graphId: str, request: Request):
    response=""
    start_time = time.time()
    logger.info("igraph request received...")
    logger.info(f"Received graphId: {graphId}")
    try:
        json_data = get_graph_cache(graphId)
        if json_data:
            try:
                response = json.loads(json_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
                response = f"An internal server error occurred, please contact administrator."
        else:
            response = get_empty_graph()
        logger.debug(f"parsed graph JSON: {json.dumps(response, indent=2)}")
    except Exception as e:
        logger.error(f"An internal server error occurred: {e}")
        response = f"An internal server error occurred, please contact administrator."
    total_elapsed_time = time.time() - start_time
    logger.info(f"Total request processing time: {total_elapsed_time:.2f} seconds\n\n\n")
    return response

@app.get("/getdata")
@app.get("/getdata/")
async def getdata(idataId: str, request: Request, userId: Optional[str] = None):
    df_iquery = pd.DataFrame()
    column_names_iquery = []
    start_time = time.time()
    logger.info("getdata request received...")
    logger.info(f"Received idataId: {idataId}")
    logger.info(f"Received user: {userId}")
    response=""
    logger.debug("reset idata cache...")
    reset_idata_cache(idataId)
    try:
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
                with get_connection(rbac_user_id,  "" ) as connection:
                    query_result_setdateformat = connection.execute(text("alter session set nls_date_format = 'YYYY-MM-DD'"))
                    query_result = connection.execute(text(iquery))
                    column_names_iquery = query_result.keys()
                    results = query_result.fetchall()
                    list_of_results = [list(row) for row in results]
                    converted_list = [tuple(item) for item in list_of_results]
                    df_iquery = pd.DataFrame(converted_list, columns=column_names_iquery)
                    df_iquery = df_iquery.rename(columns=lambda x: format_column_name(x))
                    logger.debug("few rows of data extracted from db...")
                    logger.debug(df_iquery.head())
            except Exception as e:
                logger.error("Database exception occurred")
                logger.error(f"Exception occurred: {e}")
                response = "error occured while retrieving data using interactive query"
            if len(df_iquery) > 0:
                df_iquery = df_iquery.apply(apply_formatting)
                logger.debug("sending idata to redis...")
                set_idata_cache(idataId, "idata", pickle.dumps(df_iquery))
                set_idata_cache(idataId, "isummary", pickle.dumps(""))
                logger.debug(f"reset conversation cache for idataId: {idataId}")
                reset_conversation_cache(idataId)
                json_result = df_iquery.to_json(orient='records', date_format='iso')
                response =  json.loads(json_result)
            else:
                response = {"message": "No data found"}
                logger.info(f"******No data found for the query******")
        else:
            response = {"message": "No data found"}
            logger.info(f"******query not found in cache for {idataId}******")
    except Exception as e:
        logger.error(f"An internal server error occurred: {e}")
        response = f"An internal server error occurred, please contact administrator."
    total_elapsed_time = time.time() - start_time
    logger.info(f"Total request processing time: {total_elapsed_time:.2f} seconds\n\n\n")
    return response

@app.post("/getojet")
@app.post("/getojet/")
async def getOJetData(request: Request):
    try:
        start_time = time.time()
        logger.debug("/getojet request received from the client...")
        j = await request.body()
        json_post_raw = await request.json()
        json_post = json.dumps(json_post_raw)
        json_post_list = json.loads(json_post)

        idataId = json_post_list.get('idataId', "").strip()
        graphType = json_post_list.get('graphType', "").strip()
        xAxis = json_post_list.get('xAxis', "").strip()
        yAxis = json_post_list.get('yAxis', "").strip()
        groupBy = json_post_list.get('groupBy', "").strip()
        parts = []
        if graphType:
            parts.append(f"Let us generate data for {graphType} graph using Oracle JET.")
        if xAxis:
            parts.append(f"with {xAxis} as x-axis")
        if yAxis:
            parts.append(f"{yAxis} as y-axis")
        if groupBy:
            parts.append(f"and {groupBy} as groupby clause")
        prompt = ", ".join(parts).replace(", and", " and")
        logger.debug(f"prompt: {prompt}")
        response = {"message": "No data found"}
        df = pd.DataFrame()
        logger.debug("fetching data from cache..")
        df = pickle.loads(get_idata_cache(idataId, "idata"))
        if len(df) > 0:
            response_json = get_ojet_graph(prompt, df)
            logger.debug("sending igraph to redis...")
            set_idata_cache(idataId, "igraph", pickle.dumps(response_json))
            response = json.loads(response_json)
        else:
            response = {"message": "No data found"}
            logger.info(f"******query not found in cache for {idataId}******")
    except Exception as e:
        logger.error(f"An internal server error occurred: {e}")
        response = f"An internal server error occurred, please contact administrator."

    total_elapsed_time = time.time() - start_time
    logger.debug(f"Total request processing time: {total_elapsed_time:.2f} seconds")
    return JSONResponse(content=response)

@app.post("/iprompt")
async def processInteractivePrompt(request: Request):
    try:
        start_time = time.time()
        logger.debug("/iprompt request received from the client...")
        j = await request.body()
        json_post_raw = await request.json()
        json_post = json.dumps(json_post_raw)
        json_post_list = json.loads(json_post)

        idataId = json_post_list.get('idataId', "").strip()
        logger.debug(f"idataId: {idataId}")
        iPrompt = json_post_list.get('iPrompt', "").strip()
        graph_prompt = "Generate a graph."
        logger.debug(f"prompt: {iPrompt}")
        response = {"message": "No data found"}

        errors = []
        if not idataId:
            errors.append("idataId is required")
        if not iPrompt:
            errors.append("iPrompt is required")

        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Missing required fields",
                    "details": errors
                }
            )
        
        tabData_df = pd.DataFrame()
        next_step = get_idata_step_counter(idataId)+1
        if iPrompt == "RESET":
            logger.debug("resetting conversation, idata and igraph..")
            reset_conversation_cache(idataId)
            reset_idata_cache(idataId)
            logger.debug("getting idata from cache..")
            df_s = get_idata_cache(idataId, "idata")
            tabData_df = pickle.loads(df_s)
            tabData = tabData_df.to_dict(orient="records")
            logger.debug("getting igraph from cache..")
            chartData = json.loads(pickle.loads(get_idata_cache(idataId, "igraph")))
            summary = ""
        else:
            #ipromptType, query_prompt, graph_prompt = classify_iprompt_request(iPrompt)
            #if ipromptType == "graph":
            #    logger.debug("graphing-only request")
            #    df_s = get_idata_cache(idataId, "idata")
            #    tabData_df_raw = pickle.loads(df_s)
            #    tabData_df = tabData_df_raw
            #    tabData_df = tabData_df.apply(apply_formatting)
            #    logger.debug("top 5 rows from cache...")
            #    logger.debug(tabData_df.head())
            #else:
            logger.debug("data processing request")
            tabData_df_raw = processdata(iPrompt, idataId)
            tabData_df = tabData_df_raw
            if isinstance(tabData_df, pd.Series):
                logger.debug("converting series to dataframe")
                tagData_df = tabData_df.to_frame(name=tabData_df.name)
                logger.debug(tabData_df)
            logger.debug("apply_formatting...")
            tabData_df = tabData_df.apply(apply_formatting)
            logger.debug(f"caching the tabData..")
            set_idata_cache(idataId, "idata", pickle.dumps(tabData_df), next_step)
            logger.debug("done with tabData")
        
            tabData = tabData_df.to_dict(orient="records")
            chartData = get_ojet_graph(graph_prompt, tabData_df_raw)
            logger.debug("caching the chartdata...")
            set_idata_cache(idataId, "igraph", pickle.dumps(chartData), next_step)
            #chartData = chartData_df.to_dict(orient="records")
            if isinstance(chartData, str):
                chartData = json.loads(chartData)
            logger.debug("generating summary...")
            summary = get_summary_llm(idataId, iPrompt, len(tabData_df_raw))
            logger.debug("caching the summary...")
            set_idata_cache(idataId, "isummary", pickle.dumps(summary), next_step)
        response = {
            "response": f"{summary}",
            "tabData": tabData,
            "chartType": chartData.get("chartType", ""),
            "chartDesc": chartData.get("chartDesc", ""),
            "xLabel": chartData.get("xLabel", ""),
            "yLabel": chartData.get("yLabel", ""),
            "chartData": chartData.get("data", []),
        }
    except Exception as e:
        logger.error(f"An internal server error occurred: {e}")
        error_json = json.dumps({"response": "Internal error"})
        return Response(content=error_json, media_type="application/json")
    total_elapsed_time = time.time() - start_time
    logger.debug(f"Total request processing time: {total_elapsed_time:.2f} seconds")
    return JSONResponse(content=response)
    #return response

@app.get("/iprompt/data")
async def getipromptdata(idataId: str, request: Request, stepNumber: Optional[int] = 0):
    start_time = time.time()
    logger.debug("GET /iprompt/data request received from the client...")
    logger.debug(f"idataId: {idataId}")
    logger.debug(f"stepNumber: {stepNumber}")
    response = {"message": "No data found"}
    tabData_df = pd.DataFrame()
    logger.debug("fetching idata from cache...")
    tabData_df_raw = get_idata_cache(idataId, "idata", stepNumber)
    tabData_df = pickle.loads(tabData_df_raw)
    tabData_df = tabData_df.apply(apply_formatting)
    logger.debug("top 5 rows from cache...")
    logger.debug(tabData_df.head())
    tabData = tabData_df.to_dict(orient="records")
    logger.debug("fetching igraph from cache...")
    chartData_raw = get_idata_cache(idataId, "igraph", stepNumber)
    chartData = pickle.loads(chartData_raw)
    if isinstance(chartData, str):
        chartData = json.loads(chartData)
    logger.debug("fetching isummary from cache...")
    summary_raw = get_idata_cache(idataId, "isummary", stepNumber)
    summary = pickle.loads(summary_raw)
    response = {
        "response": f"{summary}",
        "tabData": tabData,
        "chartType": chartData.get("chartType", ""),
        "chartDesc": chartData.get("chartDesc", ""),
        "xLabel": chartData.get("xLabel", ""),
        "yLabel": chartData.get("yLabel", ""),
        "chartData": chartData.get("data", []),
    }
    total_elapsed_time = time.time() - start_time
    logger.debug(f"Total request processing time: {total_elapsed_time:.2f} seconds")
    return JSONResponse(content=response)

@app.delete("/iprompt/data")
async def delete_iprompt_data(idataId: str, request: Request, stepNumber: Optional[int] = 0):
    start_time = time.time()
    logger.debug("DELETE /iprompt/data request received from the client...")
    logger.debug(f"idataId: {idataId}")
    logger.debug(f"stepNumber: {stepNumber}")
    response = {"message": "No data found"}
    return {"message": f"Data with idataId={idataId} and stepNumber={stepNumber} deleted successfully"}


@app.post("/iprompt/graph")
async def processInteractiveGraph(request: Request):
    try:
        start_time = time.time()
        logger.debug("/iprompt/graph request received from the client...")
        j = await request.body()
        json_post_raw = await request.json()
        json_post = json.dumps(json_post_raw)
        json_post_list = json.loads(json_post)

        idataId = json_post_list.get('idataId', "").strip()
        logger.debug(f"idataId: {idataId}")
        iGraphPrompt = json_post_list.get('iGraphPrompt', "").strip()
        logger.debug(f"graph prompt: {iGraphPrompt}")
        stepNumber = json_post_list.get('stepNumber')
        logger.debug(f"step number: {stepNumber}")
        response = {"message": "No data found"}

        errors = []
        if not idataId:
            errors.append("idataId is required")
        if not iGraphPrompt:
            errors.append("iGraphPrompt is required")
        try:
            if stepNumber is None or str(stepNumber).strip() == "":
                errors.append("stepNumber is required")
            else:
                stepNumber = int(stepNumber)
                if stepNumber < 0:
                    errors.append("stepNumber must be zero or a positive integer")
        except (ValueError, TypeError):
            errors.append("stepNumber must be an integer")
        logger.debug(f"validated step number: {stepNumber}")

        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Missing required fields",
                    "details": errors
                }
            )

        tabData_df = pd.DataFrame()
        if iGraphPrompt == "RESET":
            logger.debug("getting igraph from cache..")
            chartData = json.loads(pickle.loads(get_idata_cache(idataId, "igraph", stepNumber)))
        else:
            df_s = get_idata_cache(idataId, "idata", stepNumber)
            tabData_df_raw = pickle.loads(df_s)
            tabData_df = tabData_df_raw
            tabData_df = tabData_df.apply(apply_formatting)
            logger.debug("top 5 rows from cache...")
            logger.debug(tabData_df.head())
            chartData = get_ojet_graph(iGraphPrompt, tabData_df_raw)
        if isinstance(chartData, str):
            chartData = json.loads(chartData)
        response = {
            "chartType": chartData.get("chartType", ""),
            "chartDesc": chartData.get("chartDesc", ""),
            "xLabel": chartData.get("xLabel", ""),
            "yLabel": chartData.get("yLabel", ""),
            "chartData": chartData.get("data", []),
        }
    except Exception as e:
        logger.error(f"An internal server error occurred: {e}")
        error_json = json.dumps({"response": "Internal error"})
        return Response(content=error_json, media_type="application/json")
    total_elapsed_time = time.time() - start_time
    logger.debug(f"Total request processing time: {total_elapsed_time:.2f} seconds")
    return JSONResponse(content=response)
    #return response

@app.get("/conversations/recent")
def get_recent(userId: str, request: Request):
    try:
        start_time = time.time()
        logger.debug("/conversations/recent request received from the client...")
        logger.debug(f"userId: {userId}")
        response = {"message": "No data found"}
        recent_prompts = get_recent_conversations(userId)
        if recent_prompts:
            response = [{"id": row[0], "title": row[1]} for row in recent_prompts]
    except Exception as e:
        logger.error(f"Failed to get recent prompts for {userId}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    total_elapsed_time = time.time() - start_time
    logger.debug(f"Total request processing time: {total_elapsed_time:.2f} seconds")
    return response

@app.get("/conversations/frequent")
def get_frequent(userId: str, request: Request):
    try:
        start_time = time.time()
        logger.debug("/conversations/frequent request received from the client...")
        logger.debug(f"userId: {userId}")
        response = {"message": "No data found"}
        frequent_prompts = get_frequent_conversations(userId)
        if frequent_prompts:
            response = [{"id": row[0], "title": row[1]} for row in frequent_prompts]
    except Exception as e:
        logger.error(f"Failed to get frequent prompts for {userId}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    total_elapsed_time = time.time() - start_time
    logger.debug(f"Total request processing time: {total_elapsed_time:.2f} seconds")
    return response

@app.get("/conversations/bookmarks")
def get_bookmarks(userId: str, request: Request):
    return [{
            "id": "conv001",
            "title": "Coming Soon...."
        },
        {
            "id": "conv002",
            "title": "Show vendor name and total amount due"
        },{
            "id": "conv003",
            "title": "Show invoices with total amount due"
        }]

@app.post("/conversations/bookmark")
def bookmark_conversation(request: Request):
    return {"message": "Bookmarked"}

@app.delete("/conversations/bookmark/{id}")
def remove_bookmark(conversationId: str):
    return {"message": f"Removed conversation {id}"}

@app.get("/agent/actions")
def get_agent_actions(userId: str, request: Request):
    return [
        {
            "id": "action000",
            "title": "Coming Soon...."
        },{
            "id": "action001", 
            "title": "Data sync complete"
        },
        {
            "id": "action002", 
            "title": "Report 'Aging Analysis' generated"
        }]

@app.post("/agent/submit")
async def submit_agent_action(request: Request):
    try:
        start_time = time.time()
        logger.debug("/agent/submit request received from the client...")
        j = await request.body()
        json_post_raw = await request.json()
        json_post = json.dumps(json_post_raw)
        json_post_list = json.loads(json_post)

        idataId = json_post_list.get('idataId', "").strip()
        logger.debug(f"idataId: {idataId}")
        prompt = json_post_list.get('prompt', "").strip()
        logger.debug(f"prompt: {prompt}")
        userId = json_post_list.get('userId', "").strip()
        logger.debug(f"userId: {userId}")
        llm_response = submit_conversation_to_agent(userId, idataId, prompt)
        response = {"message": llm_response}
    except Exception as e:
        logger.error(f"Failed to get frequent prompts for {userId}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    total_elapsed_time = time.time() - start_time
    logger.debug(f"Total request processing time: {total_elapsed_time:.2f} seconds")
    return response

@app.post("/v1/feedbackupdown")
async def get_feedback_up_down(request: Request):
    logger.info("thumbs up down request received...")
    j = await request.body()
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    feedbackcode = json_post_list.get('feedbackcode', "")
    oda_sessionid = json_post_list.get('sessionid', "")
    try:
        strid = get_chat_cache(oda_sessionid + "lastid")
        dummyid = persist_log_data("UFT", parentid=int(float(strid.strip())), user_feedback_code=int(feedbackcode.strip()), user_feedback_txt="")
    except Exception as e:
        logger.error(f"An exception occurred /v1/getfeedbackupdown: {e}")
    logger.info("\n\n\n")
    return "Done"

@app.post("/v1/feedbackmessage")
async def get_feedback(request: Request):
    logger.info("feedbackmessage request received")
    j = await request.body()
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    feedback = json_post_list.get('feedback', "")
    logger.debug(f"feedback message received as: {feedback}")
    oda_sessionid = json_post_list.get('sessionid', "")
    try:
        strid = get_chat_cache(oda_sessionid + "lastid")
        dummyid = persist_log_data("UFM", parentid=int(float(strid.strip())), user_feedback_code=0, user_feedback_txt=feedback[:4000])
    except Exception as e:
        logger.error(f"An exception occurred /v1/getfeedbackupdown: {e}")
    logger.info("\n\n\n")
    return "Done"

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, workers=1)
