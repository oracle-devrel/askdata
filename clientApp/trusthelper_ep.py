# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import re
import configparser
from fastapi import FastAPI, Request
from fastapi.responses import Response
import uvicorn, json, datetime
from get_top_match import return_validated_sql
from llm_handler import create_user_message, create_assistant_message, chat_conversion,get_llm_sql, check_sql_equiv, get_prompt_equiv, seek_clarification, check_graphing_request, read_file_to_string, get_sql_prompt
import difflib
from database_ops   import get_user_id_by_email, get_model_id, persist_log_data, log_user_action,persist_app_debug
from helper_methods import setup_logger, remove_limit_fetch, generate_diff_string, check_substrings_in_string, clean_query, remove_quotes, starts_with_delete_or_truncate
from database_conn_pool import get_connection
from sqlalchemy import text
from dynamic_prompt_injection import get_hints4llm

config = configparser.RawConfigParser()
config.read('ConfigFile.properties')
logger = setup_logger('trusthelper_ep.log')
logger.info("Main application logger initialized")

# global varibales
modified_prompt = ""
column_names = []
fetchstmt = ""
app = FastAPI()

@app.post("/getprompt")
async def getprompt(request: Request):
    logger.debug("request received from the client")
    j = await request.body()
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    question = json_post_list.get('question')
    logger.info("question:"+question)
    prmpt = re.sub(r'(?<=\.)Payables\s*$', '', question)
    metadata  = config.get('METADATA', 'schema.ddl')
    schemaddl = read_file_to_string(metadata)
    dialect = config.get('GenAISQLGenerator', 'sql.dialect')
    hints = ""
    if config.getboolean('FeatureFlags', 'feature.dynamicprompt'):
        logger.debug(f"retrieving hints for dynamic prompt...")
        hints = get_hints4llm(prmpt)
        if hints:
            logger.debug(f"dynamic prompt to be injected is:\n {hints}")
    sqlprompt = get_sql_prompt(schemaddl,prmpt,dialect,hints)
    return Response(content=sqlprompt, media_type="text/plain")

@app.post("/getsql")
async def getsql(request: Request):
    logger.debug("request received from the client")
    j = await request.body()
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    question = json_post_list.get('question', "").strip()
    logger.info("question:"+question)
    oda_domain = json_post_list.get('domain', "payables").strip()
    logger.debug(f"oda domain: {oda_domain}")
    if question and question.strip():
        model_id = get_model_id("GEN-PURPOSE-LLM")
        conversation = []
        prompt_conversation = []
        reworded, prompt_conversation = chat_conversion(question,prompt_conversation)
        conversation.append(create_user_message(reworded,conversation,oda_domain))
        sql_lineage = ""
        trust_id,prompt_lineage,validated_query, match_ratio, match_status = return_validated_sql(reworded)
        trust_score = match_ratio
        if match_status in ("None Found","VERIFIED-FAILED-NUM-PARAMCHECK","SIMILAR","NA"):
            logger.debug("getting llm sql" )
            query_raw = get_llm_sql(conversation)
            # initially mark generated and executed SQL to be the same (think it is totally untrusted)
            generated_sql = query_raw
            executed_sql, fetchstmt = clean_query(query_raw)
            equiv_result, equiv_prompt = check_sql_equiv(validated_query, query_raw)
            logger.debug("sql equivalent result:" +  equiv_result)
            sql_diff     = generate_diff_string(validated_query, query_raw)
            logger.debug("sql_diff result is:   " +  sql_diff)
            logger.debug("**** trust query ***********")
            logger.debug(validated_query)
            logger.debug("**** llm query ************")
            logger.debug(query_raw)
            logger.debug("**********************")
            debug_txt = "sql equivalent result:" +  equiv_result + "\n" + "sql_diff result is:   " +  sql_diff + "\n" + "trusted query: " + validated_query + "\n" + "llm query: " + query_raw

            if equiv_result == "YES" and sql_diff == "=":
                is_prompt_equiv = 1
                logger.debug("top sql and generated sql are prompt equivalent")
            if equiv_result == "YES" and sql_diff != "=":
                is_template_equiv = 1
                generated_sql = validated_query
                logger.debug("top sql and generated sql are template equivalent")
        else:
            logger.debug("this sql is from 100% validated" )
            is_trusted = 1
            query_raw    =     validated_query
            generated_sql =    validated_query
            executed_sql, fetchstmt = clean_query(query_raw)
            logger.debug(query_raw)
        # clean up the raw query
        query_clean, fetchstmt = clean_query(query_raw)
        logger.debug("*** clean *****")
        query_clean = query_clean.replace("\n", " ").replace("\\n", " ").replace(";", "").strip()
        query_clean = remove_quotes(query_clean)
        logger.debug(query_clean)
        if fetchstmt:
            query_clean = remove_limit_fetch(query_clean)
        response_data = {
                "query": query_clean
                #"match_status": match_status,
                #"trust_score": float(trust_score)
                }
        return Response(content=json.dumps(response_data), media_type="application/json")
    else:
        return Response(content="Invalid Prompt Question!", media_type="text/plain")


# TODO: route to appropriate type of db
@app.post("/testsql")
async def testsql(request: Request):
    logger.debug("request received for testing sql")
    j = await request.body()
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)

    # TODO: what does the input format look like
    query = json_post_list.get('sql', "").strip()
    logger.info("query:"+query)
    #oda_domain = json_post_list.get('domain', "payables").strip()
    #logger.debug(f"oda domain: {oda_domain}")

    #TODO: make/find right config stuff
    # would one deployment potentially go against multiple source dbs
    db_type = "oracle" #config.get("DATABASE",type)
    if db_type == "oracle":
        response = test_against_oracle(query)
    elif db_type == "snowflake":
        response = test_against_snowflake(query) # TODO implement later
    else:
        response = {"errorcode": "server error", "errortext" : "no db configured", "success": False}
    
    logger.debug(response)
    #{"errorcode": "", "errortext" : "", "success": true} -- success
    #{"errorcode": "ORA-23838", "errortext" : "table or view does not exist", "success": false}
    return Response(content=json.dumps(response), media_type="application/json")

def test_against_snowflake(query):
    return {"errorcode": "None", "errortext" : "snowflake not implemented", "success": False}

# TODO: does this function already exist?
def test_against_oracle(query):

    # TODO: other function has these inputs. where should we get the necessary ones
    # prompt: str, domain: str, usergroup: str, userid: str, session_id:str, followup_flg:str, previous_prompt: str, graphFlag:bool, conversation, reworded: str, user_key, model_id, convo_seq_no
    userid = "temp"
    rbac_user_id = ""
    if config.get('DatabaseSection', 'database.rbac') == 'Y':
        logger.debug("RBAC is enabled")
        rbac_user_id = userid

    try:
        logger.debug("opening db connection")
        with get_connection(rbac_user_id,  "" ) as connection:
            logger.debug("connection open, setting session date format")
            query_result_setdateformat = connection.execute(text("alter session set nls_date_format = 'YYYY-MM-DD'"))
            query_clean = remove_quotes(query) # TODO: figure out where query is in input

            if starts_with_delete_or_truncate(query_clean):
                error_code = "No-op"
                error_text = "Last SQL Operation not permitted: delete or truncate detected"
                return {"errorcode": error_code, "errortext" : error_text, "success": False}
            # TODO: should we add an additional check to make sure it's a select statement?

            #TODO: if we have an Oracle versions before 12c, we would need to use ROWNUM
            # SELECT * FROM (your_query) WHERE ROWNUM = 1;
            # TODO: should we check and remove semicolon from end of statement? what other formatting options do we need?
            test_query = query_clean + " FETCH FIRST 1 ROWS ONLY"

            logger.debug(f"formatted test query: {test_query}")
            try:
                query_result = connection.execute(text(re.sub(r'\s*SELECT', 'SELECT',test_query)))

                logger.debug(f"Query Response:")
                # Fetch rows in batches and print them
                batch_size = 50
                while True:
                    rows = query_result.fetchmany(batch_size)
                    if not rows:
                        break
                    for row in rows:
                        logger.debug(row)
                #logger.debug(f"Query Result: {query_result}")
                return {"errorcode": "", "errortext" : "", "success": True}

            except Exception as e:

                logger.error("Database exception occurred")

                error_code = re.search(r'ORA-\d+', str(e)).group(0) if re.search(r'ORA-\d+', str(e)) else 'Unknown Error Code'
                error_text = str(e)
                logger.debug(f"error code: {error_code}")
                logger.debug(f"error message: {error_text}")

                return {"errorcode": error_code, "errortext" : error_text, "success": False}

    except Exception as e:
        logger.error(f"error connecting to the database: {e}")
        return {"errorcode": "error connecting to the database", "errortext" : str(e), "success": False}


    

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001, workers=1)
