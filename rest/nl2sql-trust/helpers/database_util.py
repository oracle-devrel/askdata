# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json

import os
import logging
from datetime import datetime
import concurrent.futures

from helpers.config_json_helper import config_boostrap as confb

from helpers import natural_language_util as nl
from helpers.oci_helper_json import oci_helper as ocij
from helpers.util import format_sql_view as format_sql
from helpers.llm_helper import llm_create_str_embedding
import constants

import oracledb

logger = logging.getLogger(constants.IO_LAYER)

cached_db_pwd = None

# TODO: Not in use
def convert_simple_list_to_json(input_list):
    json_str = "{" + '|'.join([str(elem) for elem in input_list]) + "}"
    return json_str

# TODO: Not in use
def convert_each_row_to_json(input_list):
    json_list = []
    for row in input_list:
        line = "|".join([str(elem) for elem in row])
        line = "{" + line + "}"
        json_list.append(line)

    json_str = "{" + ','.join([str(elem) for elem in json_list]) + "}"
    return json_str

#TODO Not in use
def convert_to_number_str(result_set_count):
    return str(result_set_count[0][0])

def get_sysdate():
    return datetime.now().strftime("%d-%b-%y %I.%M.%S %p")

def db_get_connection( ):
    
    global cached_db_pwd

    wallet = confb.dconfig["database"]["wallet"]
    user = confb.dconfig["database"]["user"]
    dns = confb.dconfig["database"]["dns"]
    pwd = confb.dconfig["database"]["pwd"]

    #wallet = conf.db_config.wallet
    #user = conf.db_config.user
    #dns = conf.db_config.dns
    #pwd = conf.db_config.pwd
    
    if cached_db_pwd is None:
        #cached_db_pwd=oci_helper.vault_get_secret(conf.vault_config.db_secret_ocid)
        
        cached_db_pwd=ocij.vault_get_secret(confb.dconfig["oci"]["vault"]["db_secret_ocid"])
    pwd = cached_db_pwd

    logger.info(f"Connecting to Oracle Database wallet=[{wallet}], user=[{user}], pwd=[{pwd}], dns=[{dns}]")
    logger.info("TNS_ADMIN\n", wallet)
    print("TNS_ADMIN\n", wallet)
    os.environ["TNS_ADMIN"] = wallet
    oracledb.init_oracle_client(config_dir=os.environ["TNS_ADMIN"])
    connection = oracledb.connect(
        user=user,  # Use the username configured in the wallet
        password=pwd,  # This may also be configured in the wallet
        dsn=dns, # This should match the tns entry in the wallet (tnsnames.ora)
        config_dir=os.environ["TNS_ADMIN"]
    )

    return connection

def db_create_default_pool():
    wallet = confb.dconfig["database"]["wallet"]
    user = confb.dconfig["database"]["user"]
    dns = confb.dconfig["database"]["dns"]
    pwd = confb.dconfig["database"]["pwd"]

    #wallet = conf.db_config.wallet
    #user = conf.db_config.user
    #dns = conf.db_config.dns
    #pwd = conf.db_config.pwd

    os.environ["TNS_ADMIN"] = wallet
    oracledb.init_oracle_client(config_dir=os.environ["TNS_ADMIN"])
    pool = oracledb.create_pool(
        user=user,
        password=pwd,
        dsn=dns,  # Data Source Name (TNS)
        min=5,  # Minimum number of connections
        max=20,  # Maximum number of connectionsd
        increment=5  # Number of connections to increment when the pool is exhausted
    )

    # Get the connection pool size (min, max, and current connections)
    print("Pool size details:")
    print(f"Min Connections: {pool.min}")
    print(f"Max Connections: {pool.max}")
    # print(f"Current Connections: {pool.size}")  # Active connections

    # Optional: Retrieve the current connections in the pool
    # print(f"Current available connections: {pool._size()}")

def db_sql_parse(connection, sql):
    logger.info('db sql parse')
    tmp = ""
    with connection.cursor() as cursor:
        try:
            cursor.parse(sql)
        except oracledb.Error as e:
            error_obj, = e.args
            tmp = error_obj.message.split("\n")[0]
        else:
            tmp = "0"
    return tmp


def db_select(connection, select_statement, params=None):
    logger.info(f'running statement {select_statement}')
    print(f'running statement {select_statement}')
    tmp_list = []
    with connection.cursor() as cursor:
        res = cursor.execute(select_statement,params)
        for r in res:
            tmp_list.append(r)
    return tmp_list

def db_file_upload_history(connection,domain):
    #TODO: This uses certify_state 
    logger.info('starting db_file_upload_history')
    sql=f"""
            select to_char(prompt_proc_date, '{confb.dconfig["database"]["datetime_format"]}') as proc_date,
                upload_filename as filename, count(*) as proc_count
                from certify_state
                where prompt_source = :1
                group by prompt_proc_date, upload_filename
                order by prompt_proc_date desc
        """
    sql_ret = db_select(connection=connection, select_statement=sql, params=('upload',))
    lst : list = list()
    for each in sql_ret:
        e ={}
        e["prompt_proc_date"]=each[0]
        e["upload_filename"]=each[1]
        e["proc_count"]=each[2]
        lst.append(e)

    logger.debug(lst)
    logger.debug(f"in db_file_upload_history {len(lst)}")
    return lst


def db_insert_process_auto(connection, source, prompt_list):

    prompt_txt = ""
    metadata_1 = "NULL"
    AUTO_SQL_TABLES = "NULL"
    prompt_source = source
    logger.info("Starting db_insert_process_auto")
    insert = f"""
        INSERT INTO certify_state (prompt_proc_date , metadata_1, prompt_txt, prompt_source, prompt_vect)
            VALUES (:bdate, :metadata_1, :prompt_txt, :prompt_source, :prompt_vect)
                """
    logger.debug(f"insert: {insert}")
    with connection.cursor() as cursor:
        date = get_sysdate()
        for row in prompt_list:
            AUTO_SQL_TABLES = row[0]
            metadata_1 = row[1]
            prompt_txt = row[2]
            prompt_vect = llm_create_str_embedding(prompt_txt)
            logger.debug(row)
            logger.debug({"bdate": date, "metadata_1": metadata_1, "prompt_txt": prompt_txt})

            cursor.execute(insert, {"bdate": date, "metadata_1": metadata_1, "prompt_txt": prompt_txt,
                                    "prompt_source": prompt_source, "prompt_vect": json.dumps(prompt_vect)})
            connection.commit()

            id = db_get_latest_id(connection, prompt_source)
            db_check_duplicate_all_types(connection, prompt_vect, id)

        logger.info("Process auto: Insert and duplication check completed")
    return date

def db_insert_process_upload(connection, prompt_list, domain):

    PROMPT = ""
    AUTO_SQL_TAXON = "NULL"
    UPLOAD_FILE_NAME = "NULL"

    logger.info("Starting db_insert_process_auto")
    insert = """
        INSERT INTO certify_state (prompt_proc_date , metadata_1, upload_filename, prompt_txt, prompt_source, prompt_vect)
            VALUES (:prompt_proc_date, :metadata_1,:upload_filename, :prompt_txt, 'upload', :prompt_vect)
                """
    logger.debug(f"insert: {insert}")
    with connection.cursor() as cursor:
        prompt_proc_date = get_sysdate()
        for row in prompt_list:
            AUTO_SQL_TAXON = row[0]
            UPLOAD_FILE_NAME = row[1]
            PROMPT = row[2]
            prompt_vect = llm_create_str_embedding(PROMPT)
            logger.debug({"prompt_proc_date": prompt_proc_date, "metadata_1": AUTO_SQL_TAXON,
                          "upload_filename": UPLOAD_FILE_NAME, "prompt_txt": PROMPT})
            cursor.execute(insert, {"prompt_proc_date": prompt_proc_date, "metadata_1": AUTO_SQL_TAXON,
                                    "upload_filename": UPLOAD_FILE_NAME, "prompt_txt": PROMPT, "prompt_vect": json.dumps(prompt_vect)})
            connection.commit()

            id = db_get_latest_id(connection, 'upload')
            db_check_duplicate_all_types(connection, prompt_vect, id)

    logger.info("Completed db_insert_process_auto")
    return prompt_proc_date

def db_insert_process_user(connection, prompt_source, prompt_list):

    logger.info("Starting db_insert_process_user")
    with connection.cursor() as cursor:
        prompt_proc_date = get_sysdate()
        prompt_source = 'user'

        for row in prompt_list:
            user_src_id = row[0]
            prompt_vect = llm_create_str_embedding(row[1])
            insert = f"""
                INSERT INTO certify_state (prompt_proc_date , user_execution_id, prompt_source, prompt_vect)
                    VALUES (:prompt_proc_date,:user_execution_id,:prompt_source, :prompt_vect)
                        """
            logger.debug(f"insert: {insert}")
            logger.debug({"prompt_proc_date": prompt_proc_date, "user_execution_id": user_src_id,
                          "prompt_source": prompt_source})

            cursor.execute(insert, {"prompt_proc_date": prompt_proc_date, "user_execution_id": user_src_id,
                                    "prompt_source": prompt_source, "prompt_vect": json.dumps(prompt_vect)})

            connection.commit()

            id = db_get_latest_id(connection, prompt_source)
            db_check_duplicate_all_types(connection, prompt_vect, id)


    logger.info("Completed db_insert_process_user")
    return prompt_proc_date

def db_update_process_sql(connection, row_list):

    logger.info("Starting db_update_process_sql")
    #TODO: This uses certify_state

    with connection.cursor() as cursor:
        for row in row_list:
            # sblais: refactored to allow for multi-threading
            db_update_process_sql_row(connection,row)

    connection.commit()
    logger.info("Updates completed")

def db_update_process_sql_row(connection, row):

    logger.debug("Starting db_update_process_sql_row")
    #TODO: This uses certify_state

    date = get_sysdate()
    pass_fail = "NULL"
    parse_error_code = "NULL"
    id = row[0]
    sql = row[1] #.replace("'", "''")
    if row[2] != "":
        pass_fail = row[2]
        parse_error_code = row[3].replace("'", "''")

    with connection.cursor() as cursor:

        update = """
                update certify_state set is_sql_proc = 1, sql_proc_date = :1,
                    sql_txt = :2, pass_fail = :3, parse_error_code = :4
                where id = :5
                """

        logger.debug(f"update: {update}")
        logger.debug((date,sql,pass_fail,parse_error_code,id))
        cursor.execute(update,(date,sql,pass_fail,parse_error_code,id))

    logger.debug("Update completed")

def db_update_executed_prompts_table(connection, resultset):

    logger.info("Starting update: executed_prompts table for executed_prompts")
    with connection.cursor() as cursor:
        for row in resultset:
            ID = row[0]
            update = f"""
                    UPDATE execution_log SET
                    is_cert_processed = :1
                    where ID = :2
                    """
            logger.debug(f"update: {update},{(1,ID)}")
            cursor.execute(update,(1,ID))
            logger.debug("*After update execute")

    connection.commit()
    logger.info("Updates completed")

def db_update_save_certify(connection, json,domain):
    #TODO: This uses certify_state

    #{"data":[{"id":"5516","pass_fail":"Pass","sql_corrected":""}]} 
    logger.info("Starting db_update_save_certify")
    with connection.cursor() as cursor:
        for data in json["data"]:
            id = data["id"]
            pass_fail = data['pass_fail']
            sql_corrected = "NULL" if (data['sql_corrected'] == "" or data['sql_corrected'] == None) else data['sql_corrected']
            logger.debug(f"db_update_save_certify.0.0 {data['sql_corrected']}")
            logger.debug(f"db_update_save_certify.0.1 {sql_corrected}")
            update = """
                    update certify_state set
                        is_staged_proc = :1,
                        pass_fail = :2,
                        corrected_sql_txt = :3
                    where id = :4
                    """
            logger.debug(f"update: {update} {(1,pass_fail,sql_corrected,id)}")
            cursor.execute(update,(1,pass_fail,sql_corrected,id))

    connection.commit()
    logger.info("Updates completed")

def db_unstage_certify(connection, id_list: list,domain):
     #TODO: This uses certify_state

    logger.info("Starting db_unstage_certify")

    rows_affected=0

    with connection.cursor() as cursor:

        # id_list = [1, 2, 3, 4]  Example list of integers

        #Creating a dynamic array of positions for the parameterized query.
        sql_id_list = ', '.join([f":{i+2}" for i in range(len(id_list))]) 
        logger.info(sql_id_list)

        update = f"""
                update certify_state set
                    is_staged_proc = :1
                where id in ({sql_id_list})
                """
        logger.debug(f"update: {update} {[0]+id_list}")
        cursor.execute(update, [0]+id_list )

        rows_affected = cursor.rowcount

    connection.commit()
    logger.info(f"Updates completed on {rows_affected} from a request of {len(id_list)}")
    
    if rows_affected is None:
        rows_affected=0

    return rows_affected

# GK 07-2025 @autocertify CHANGED
def db_process_certify(connection, record_list, control, domain):

    # DEPENDENCIES: This uses certify_state
    # NOTE: This doesn't work with a parametrized query because of the list being passed. sblais - 11Feb2025

    logger.info(f"Starting insert: db_process_certify {len(record_list)}")
    certified_date = get_sysdate()
    with connection.cursor() as cursor:
        # id, metadata_1, prompt_txt, sql_txt, sql_corrected
        for row in record_list:
            logger.debug("**************************")
            logger.debug(row)
            certify_state_id = row["id"]
            prompt_txt = row["prompt_txt"]  # Can not be None
            prompt_vct = llm_create_str_embedding(prompt_txt)
            is_corrected = 0
            sql_txt = ""

            logger.debug(f"db_process_certify start: keys = {row.keys()}")
            logger.debug(f"db_process_certify: prompt = {row['prompt_txt']}")
            logger.debug(f"db_process_certify: sql = {row['sql_txt']}")
            if "sql_corrected" not in row.keys():
                sql_txt = row["sql_txt"]
                logger.debug(f"db_process_certify: no corrected sql")
            else:
                if (row["sql_corrected"] is None or row["sql_corrected"] == "" or row["sql_corrected"] == "NULL"):
                    sql_txt = row["sql_txt"]
                    logger.debug(f"db_process_certify: no corrected sql")

                # sql has been corrected by expert
                else:
                    sql_txt = row["sql_corrected"]
                    is_corrected = 1
                    logger.debug(f"db_process_certify: sql has been corrected and this will be inserted")
                    logger.debug(f"db_process_certify: corrected sql = {sql_txt}")

                    # deprecate existing (duplicate) in trust library  when sql is corrected
                    # this clears the duplicate allowing new insert with same prompt and corrected sql
                    res_dict = db_check_duplicate(connection, prompt_vct, "trust_library", certify_state_id)
                    if res_dict["is_duplicate"]:
                        deprecate_in_trust_library(connection, res_dict["template_id"])

            # check for duplicate in trust library and do not insert if so
            if is_corrected == 0:
                res_dict = db_check_duplicate(connection, prompt_vct, "trust_library", certify_state_id)
                if res_dict["is_duplicate"]:
                    logger.debug(f"NOT inserting to trust_library c_s id={certify_state_id}: duplicate entry in trust_library with t_l id: {res_dict['duplicated_id']}")
                    continue

            if sql_txt is not None and len(sql_txt) > 0:
                insert = f"""
                            insert into trust_library (certified_date, certify_state_id, prompt_txt, prompt_vect, sql_txt, is_corrected, template_id)
                            values (:certified_date,  :certify_state_id, :prompt_txt, :prompt_vct, :sql_txt,  :is_corrected, :template_id)
                            """

                logger.debug(f"insert: {insert}")
                # Insert limit_test here. If true, then make a logging statement that the sql is not run.
                if control and control["test"]["mode"] and "insert" in control["test"]["out_of_scope"]["database"]:
                    logger.info("The insert into trust_library is not being executed")
                else:
                    # cursor.execute(insert)
                    logger.info("Doing the insert")
                    i = {
                        "certified_date": certified_date,
                        "certify_state_id": certify_state_id,
                        "prompt_txt": prompt_txt,
                        "prompt_vct": json.dumps(prompt_vct),
                        "sql_txt": sql_txt,
                        "is_corrected": is_corrected,
                        "template_id": certify_state_id}
                    logger.debug(f"inserting: {i}")

                    n = cursor.execute(insert, i)
                    logger.info(f"DB return after updating the trust_library: {n}")

    connection.commit()

    logger.debug("Starting update: certify_state table")
    with connection.cursor() as cursor:
        date = get_sysdate()
        for row in record_list:
            ID = row["id"]
            update = """
                        UPDATE certify_state SET
                        is_cert_proc = 1,  cert_proc_date = :1
                        where ID = :2
                        """

            logger.debug(f"update: {update}")
            if control and control["test"]["mode"] and "update" in  control["test"]["out_of_scope"]["database"]:
                logger.info(f"The update {(date, ID)} into certify_state is not being executed")
            else:
                logger.debug(f"updating: is_cert_proc = 1,  cert_proc_date = {date}, id = {ID}")
                cursor.execute(update,(date,ID))

    connection.commit()
    logger.info("processing completed")

def db_get_auto_hist(connection,domain):
    #TODO: This uses certify_state
    logger.info("Starting db_get_auto_hist")
    rows_affected=0
    lst : list = list()

    with connection.cursor() as cursor:

        sql =f""" select to_char(prompt_proc_date, '{confb.dconfig["database"]["datetime_format"]}') as proc_date, count(*) as proc_count 
                from certify_state 
                where prompt_source = 'auto' 
                and prompt_proc_date = (
                    select max(prompt_proc_date) from certify_state where prompt_source = 'auto') 
                group by prompt_proc_date
                """

        logger.debug(f"select: {sql}")
        # cursor.execute(sql )

        sql_ret = db_select(connection=connection, select_statement=sql)
        logger.debug(sql_ret)

        for each in sql_ret:
            e ={}
            e["prod_date"]=each[0]
            e["proc_count"]=each[1]
            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_auto_hist completed with {rows_affected} returned")
    
    return lst

def db_get_corrected_sql(connection):
    #TODO: This uses certify_state
    logger.info("Starting db_corrected_sql")
    lst : list

    with connection.cursor() as cursor:
        sql =f""" select to_char(t.certified_date, '{confb.dconfig["database"]["datetime_format"]}') as corrected_date,
                 t.certify_state_id as id, c.prompt_source as source, t.prompt_txt as prompt, 
                 (case c.prompt_source when 'user' then e.generated_sql else c.sql_txt end) orig_sql,
                  c.corrected_sql_txt as corrected_sql
                from trust_library t
                    join certify_state c on t.certify_state_id = c.id
                    left outer join  execution_log e on c.user_execution_id = e.id
                where c.is_cert_proc = 1
                    and c.corrected_sql_txt is not null and c.corrected_sql_txt !='NULL'
                    order by corrected_date desc
              """

        logger.debug(f"select: {sql}")
        rows=cursor.execute(sql)

        logger.debug(rows)

        column_names = [col[0].lower() for col in cursor.description]
        lst= [dict(zip(column_names, row)) for row in rows]
        for each in lst:
            each["orig_sql"] = format_sql(each["orig_sql"])
            each["corrected_sql"] = format_sql(each["corrected_sql"])

    connection.commit()
    logger.debug(lst)
    logger.info(f"select db_corrected_sql completed with {len(lst)} returned")
    
    return lst


def db_get_to_certify(connection, domain):
    logger.info("Starting db_get_to_certify")
    rows_affected = 0
    lst: list = list()

    sql = f""" select id as id,
                to_char(prompt_proc_date, '{confb.dconfig["database"]["datetime_format"]}') as proc_date, 
                prompt_source as prompt_source,
                metadata_1 as meta,
                prompt_txt as prompt_txt, 
                sql_txt as sql_txt,
                parse_error_code as parse_error
            from certify_state
            where is_sql_proc = 1
                and is_staged_proc = 0
                and is_cert_proc = 0
                and (prompt_source = 'auto' or prompt_source = 'upload')
                and duplicated_tbl_name is null
            order by id desc
            """

    with connection.cursor() as cursor:
        logger.debug(f"select: {sql}")
        cursor.execute(sql)

        sql_ret = db_select(connection=connection, select_statement=sql)
        logger.debug(sql_ret)

        for each in sql_ret:
            e = {}
            e["id"] = each[0]
            e["proc_date"] = each[1]
            e["proc_source"] = each[2]
            e["meta"] = each[3]
            e["prompt_txt"] = each[4]
            e["sql_txt"] = format_sql(each[5])
            e["parse_error_code"] = each[6]
            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_to_certify completed with {rows_affected} returned")

    return lst

def db_get_staged(connection,domain) :
    #TODO: This uses certify_state
    logger.info("Starting db_get_staged")
    rows_affected=0
    lst : list = list()

    with connection.cursor() as cursor:

        sql =f""" select id as id,
                to_char(prompt_proc_date, '{confb.dconfig["database"]["datetime_format"]}') as proc_date, 
                prompt_source as prompt_source,
                metadata_1 as meta,
                prompt_txt as prompt_txt, 
                sql_txt as sql_txt,
                pass_fail as pass_fail,
                corrected_sql_txt as corrected_sql_txt,
                parse_error_code as parse_error
            from certify_state
            where is_sql_proc = 1
                and is_staged_proc = 1
                and is_cert_proc = 0
                and (prompt_source = 'auto' or prompt_source = 'upload')
            order by id desc
                """
        
        logger.debug(f"select: {sql}")
        cursor.execute(sql )

        sql_ret = db_select(connection=connection, select_statement=sql)
        logger.debug(sql_ret)

        for each in sql_ret:
            e ={}
            e["id"]=each[0]
            e["proc_date"]=each[1]
            e["proc_source"]=each[2]
            e["meta"]=each[3]
            e["prompt_txt"]=each[4]
            e["sql_txt"]=format_sql(each[5])
            e["pass_fail"]=each[6]
            e["corrected_sql_text"]=each[7]
            e["parse_error_code"]=each[8]
            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_staged completed with {rows_affected} returned")
    
    return lst


def db_get_to_certify_lc(connection, mode: int, domain):
    # TODO: This uses certify_state
    logger.info("Starting db_get_to_certify_lc")
    rows_affected = 0
    lst: list = list()
    mode_lst = []

    mode_lst.insert(0, f""" select c.id as id,
                    to_char(e.execution_date, '{confb.dconfig["database"]["datetime_format"]}') as exec_date,
                    (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
                    e.generated_sql as sql_txt,
                    round(e.trust_score, 2) as score,
                    t.prompt_txt as trust_prompt_txt,
                    t.sql_txt as trust_sql_txt
                from certify_state c 
                    join execution_log e on e.id = c.user_execution_id
                    join trust_library t on t.id = e.trust_id
                where is_staged_proc = 0 
                    and is_cert_proc = 0
                    and (e.is_prompt_equiv = 1 or e.is_template_equiv = 1) 
                    and e.user_feedback_code != -1
                    and db_error_code  is null
                    and prompt_source = 'user'
                    and duplicated_tbl_name is null
                order by id desc
                """)

    # id, exec_date,prompt_txt, sql_txt, trust_level, error_code
    mode_lst.insert(1, f""" select c.id as id,
                    to_char(e.execution_date, '{confb.dconfig["database"]["datetime_format"]}') as exec_date,
                    (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
                    e.generated_sql as sql_txt,
                    (case when e.is_trusted = 1 then 'T' when e.is_autocertify = 1 then 'Ta' else 'U' end) trust_level,
                    (case when e.db_error_code is null then '' else  e.db_error_code end) error_code
                from certify_state c 
                    join execution_log e on e.id = c.user_execution_id
                where is_staged_proc = 0 
                    and is_cert_proc = 0
                    and (e.is_trusted = 0 or db_error_code is not null)
                    and e.user_feedback_code != -1
                    and prompt_source = 'user'
                    and duplicated_tbl_name is null
                order by id desc """)

                # GK: removed for autocertify: -- and ((e.is_prompt_equiv = 0 and e.is_template_equiv = 0) or (db_error_code is not null))

    # id, exec_date, email, feedback, prompt_txt, sql_txt,trust_level, authorized, error_code
    mode_lst.insert(2, f""" select  c.id as id,
                    to_char(e.execution_date, '{confb.dconfig["database"]["datetime_format"]}') as exec_date,
                    a.email_address as email,
                    e.user_feedback_txt as feedback,
                    (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
                    e.generated_sql as sql_txt,
                    (case when e.is_trusted = 1 then 'T' when e.is_autocertify = 1 then 'Ta' else 'U' end) trust_level,
                    (case when e.is_authorized = 0 then 'false' else 'true' end) authorized,
                    (case when e.db_error_code is null then '' else  e.db_error_code end) error_code
                from certify_state c 
                    join execution_log e on e.id = c.user_execution_id
                    join app_users a on a.id = e.user_id
                where is_staged_proc = 0 
                    and is_cert_proc = 0 
                    and e.user_feedback_code = -1
                    and prompt_source in ('user', 'user-autocertify')
                order by id desc
                """)
                # GK: removed for autocertify: -- and ((e.is_prompt_equiv = 0 and e.is_template_equiv = 0) or (db_error_code is not null))

    with connection.cursor() as cursor:
        sql = mode_lst[mode]

        logger.debug(f"select: {sql}")
        cursor.execute(sql)

        sql_ret = db_select(connection=connection, select_statement=sql)
        # logger.debug(sql_ret)

        for each in sql_ret:
            e = {}
            # id, exec_date,prompt_txt, sql_txt, score, trust_prompt_txt, trust_sql_txt
            if (mode == 0):
                e["id"] = each[0]
                e["exec_date"] = each[1]
                e["prompt_txt"] = each[2]
                e["sql_txt"] = format_sql(each[3])
                e["score"] = each[4]
                e["trust_prompt_txt"] = each[5]
                e["trust_sql_txt"] = format_sql(each[6])
                # calculated fields
                e["prompt_diff"] = nl.generate_diff_string(e["trust_prompt_txt"], e["prompt_txt"])
                e["sql_diff"] = nl.generate_diff_string(e["trust_sql_txt"], e["sql_txt"])

            # id, exec_date,prompt_txt, sql_txt, trust_level, error_code
            elif (mode == 1):
                e["id"] = each[0]
                e["exec_date"] = each[1]
                e["prompt_txt"] = each[2]
                e["sql_txt"] = format_sql(each[3])
                e["trust_level"] = each[4]
                e["error_code"] = each[5]

            # id, exec_date, email, feedback, prompt_txt, sql_txt,trust_level, authorized, error_code
            elif (mode == 2):
                e["id"] = each[0]
                e["exec_date"] = each[1]
                e["email"] = each[2]
                e["feedback"] = each[3]
                e["prompt_txt"] = each[4]
                e["sql_txt"] = format_sql(each[5])
                e["trust_level"] = each[6]
                e["authorized"] = each[7]
                e["error_code"] = each[8]

            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    # logger.debug(lst)
    logger.info(f"select get_to_certified_lc completed with {rows_affected} returned")

    return lst

def db_get_staged_lc_0_failed(connection,domain):
    logger.info("Starting db_get_staged_lc_0_failed")
    rows_affected=0
    lst : list = list()
    #id, exec_date, pass_fail, prompt_txt, sql_txt, corrected_sql_txt, score,trust_prompt_txt,trust_sql_txt

    stmt=f"""
        select c.id as id,
                    to_char(execution_date, '{confb.dconfig["database"]["datetime_format"]}') as exec_date,
                    c.pass_fail as pass_fail,
                    (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
                    e.generated_sql as sql_txt,
                    c.corrected_sql_txt as corrected_sql_txt,
                    e.trust_score as score,
                    t.prompt_txt as trust_prompt_txt,
                    t.sql_txt as trust_sql_txt
                from certify_state c 
                    join execution_log e on e.id = c.user_execution_id
                    join trust_library t on t.id = e.trust_id
                where is_staged_proc = 1 
                    and is_cert_proc = 0
                    and (e.is_prompt_equiv = 1 or e.is_template_equiv = 1)
                    and e.user_feedback_code != -1
                    and db_error_code is null
                    and prompt_source = 'user'
                    and pass_fail = 'Fail'
                order by id desc
            """  
    with connection.cursor() as cursor:
        
        logger.debug(f"select: {stmt}")
        cursor.execute(stmt)

        sql_ret = db_select(connection=connection, select_statement=stmt)
        logger.debug(sql_ret)

        for each in sql_ret:
            e ={}
            #id, exec_date, pass_fail, prompt_txt, sql_txt, corrected_sql_txt, score,trust_prompt_txt,trust_sql_txt
            e["id"]=each[0]
            e["exec_date"]=each[1]
            e["pass_fail"]=each[2]
            e["prompt_txt"]=each[3]
            e["sql_txt"]=format_sql(each[4])
            e["corrected_sql_txt"]=format_sql(each[5])
            e["score"]=each[6]
            e["trust_prompt_txt"]=each[7]
            e["trust_sql_txt"]=format_sql(each[8])
            e["prompt_diff"] = nl.generate_diff_string(each[7], each[3])
            e["sql_diff"] = nl.generate_diff_string(each[8], each[4])
            # prompt_diff = nl.generate_diff_string(trust_prompt_txt, prompt_txt)
            # sql_diff = nl.generate_diff_string(trust_sql_txt, sql_txt)

            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_staged_lc_0_fail completed with {rows_affected} returned")
    
    return lst

def db_get_staged_lc_mode_0(connection,domain) :
    logger.info("Starting db_get_staged_lc_mode_0")
    rows_affected=0
    lst : list = list()
    #id, exec_date, promp_txt,sql_txt, score,trust_prompt_txt,trust_sql_txt
    #e.user_prompt
    #e.convo_prompt
    #e.generated_sql
    #t.prompt_txt
    #t.sql_txt

    stmt=f""" select c.id as id,
            to_char(execution_date, '{confb.dconfig["database"]["datetime_format"]}') as exec_date,
            c.pass_fail as pass_fail,
            (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
            e.generated_sql as sql_txt,
            e.trust_score as score,
            t.prompt_txt as trust_prompt_txt,
            t.sql_txt as trust_sql_txt
        from certify_state c 
            join execution_log e on e.id = c.user_execution_id
            join trust_library t on t.id = e.trust_id
        where is_staged_proc = 1 
            and is_cert_proc = 0
            and (e.is_prompt_equiv = 1 or e.is_template_equiv = 1)
            and e.user_feedback_code != -1
            and db_error_code is null
            and prompt_source = 'user'
            and pass_fail = 'Pass'
        order by id desc
            """  
    with connection.cursor() as cursor:
        
        logger.debug(f"select: {stmt}")
        cursor.execute(stmt)

        sql_ret = db_select(connection=connection, select_statement=stmt)
        logger.debug(sql_ret)

        for each in sql_ret:
            e ={}
            #id, exec_date, promp_txt,sql_txt, score,trust_prompt_txt,trust_sql_txt
            e["id"]=each[0]
            e["exec_date"]=each[1]
            e["pass_fail"]=each[2]
            e["prompt_txt"]=each[3]
            e["sql_txt"]=format_sql(each[4])
            e["score"]=each[5]
            e["trust_prompt_txt"]=each[6]
            e["trust_sql_txt"]=format_sql(each[7])
            e["prompt_diff"] = nl.generate_diff_string(each[6], each[3])
            e["sql_diff"] = nl.generate_diff_string(each[7], each[4])
            # prompt_diff = nl.generate_diff_string(trust_prompt_txt, prompt_txt)
            # sql_diff = nl.generate_diff_string(trust_sql_txt, sql_txt)

            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_staged_lc_mode_0 completed with {rows_affected} returned")
    
    return lst

def db_get_staged_lc_mode_1(connection,domain) :
    #TODO: This uses certify_state
    logger.info("Starting db_get_staged_lc_mode_1")
    rows_affected=0
    lst : list = list()
    #id, exec_date, prompt_txt, sql_txt, corrected_sql, trust_level, error_code
    #e.user_prompt
    #e.convo_prompt
    #e.generated_sql
    #c.corrected_sql_txt

    stmt=f""" select c.id as id,
            to_char(execution_date, '{confb.dconfig["database"]["datetime_format"]}') as exec_date,
            c.pass_fail as pass_fail,
            (case 
                when e.convo_seq_num = 1 then e.user_prompt
                else e.convo_prompt
                end) prompt_txt,
            e.generated_sql as sql_txt, 
            c.corrected_sql_txt as corrected_sql,
            (case 
                when is_action = 0 and is_trusted = 1 then 'T' 
                when (is_action = 0 and (is_prompt_equiv = 1 or is_template_equiv = 1)) then 'S' 
                when is_action = 0 and is_trusted = 0 then 'U' 
                end) trust_level,
            (case 
                when e.db_error_code is null 
                then ' ' 
                else  e.db_error_code 
                end) error_code
        from certify_state c 
            join execution_log e on e.id = c.user_execution_id
            join app_users a on a.id = e.user_id
        where
            is_staged_proc = 1  
            and is_cert_proc = 0
            and e.user_feedback_code != -1    
            and (        
            -- untrusted        
            (e.is_prompt_equiv = 0 and e.is_template_equiv = 0) or                     

            -- semi-trusted but set as fail in semi-trusted certify flow        
            ((e.is_prompt_equiv = 1 or e.is_template_equiv = 1) and pass_fail = 'F') or                      

            -- any time there is a db error        
            db_error_code is not null    
            )     

            and e.user_feedback_code != -1    
            and prompt_source = 'user'
        order by id desc"""
    
    with connection.cursor() as cursor:
        
        logger.debug(f"select: {stmt}")
        cursor.execute(stmt)

        sql_ret = db_select(connection=connection, select_statement=stmt)
        logger.debug(sql_ret)
    #id, exec_date, prompt_txt, sql_txt, corrected_sql, trust_level, error_code

        for each in sql_ret:
            e ={}
            e["id"]=each[0]
            e["exec_date"]=each[1]
            e["pass_fail"]=each[2]
            e["prompt_txt"]=each[3]
            e["sql_txt"]=format_sql(each[4])
            e["corrected_sql"]=format_sql(each[5])
            e["trust_level"]=each[6]
            e["error_code"]=each[7]

            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_staged_lc_mode_1 completed with {rows_affected} returned")
    
    return lst

def db_get_staged_lc_mode_2(connection,domain) :
    #TODO: This uses certify_state
    logger.info("Starting db_get_staged_lc_mode_2")
    rows_affected=0
    lst : list = list()
    #id, exec_date,email,feedback,prompt_txt,sql_txt,corrected_sql,trust_level,authorized,error_code
    #e.user_prompt
    #e.convo_prompt
    #e.generated_sq
    # c.corrected_sql_txt

    stmt=f"""select 
            c.id as id,
            to_char(execution_date, '{confb.dconfig["database"]["datetime_format"]}') as exec_date,
            c.pass_fail as pass_fail,
            a.email_address as email,
            e.user_feedback_txt as feedback,
            (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
            e.generated_sql as sql_txt,
            c.corrected_sql_txt as corrected_sql,
            (case when e.is_trusted = 1 then 'T' when e.is_autocertify = 1 then 'Ta' else 'U' end) trust_level,
            (case when e.is_authorized = 0 then 'false' else 'true' end) authorized,
            (case when e.db_error_code is null then '' else  e.db_error_code end) error_code
        from certify_state c 
            join execution_log e on e.id = c.user_execution_id
            join app_users a on a.id = e.user_id
        where is_staged_proc = 1 
            and is_cert_proc = 0
            and ((e.is_prompt_equiv = 0 and e.is_template_equiv = 0) or (db_error_code is not null))
            and e.user_feedback_code = -1
            and prompt_source in ('user', 'user-autocertify')
        order by id desc
            """
    
    with connection.cursor() as cursor:
        
        logger.debug(f"select: {stmt}")
        cursor.execute(stmt)

        sql_ret = db_select(connection=connection, select_statement=stmt)
        logger.debug(sql_ret)

        #id, exec_date,email,feedback,prompt_txt,sql_txt,corrected_sql,trust_level,authorized,error_code
        for each in sql_ret:
            e ={}
            e["id"]=each[0]
            e["exec_date"]=each[1]
            e["pass_fail"]=each[2]
            e["email"]=each[3]
            e["feedback"]=each[4]
            e["prompt_txt"]=each[5]
            e["sql_txt"]=format_sql(each[6])
            e["corrected_sql"]=format_sql(each[7])
            e["trust_level"]=each[8]
            e["authorized"]=each[9]
            e["error_code"]=each[10]
            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_staged_lc_mode_2 completed with {rows_affected} returned")
    
    return lst


#########################################################################################################################
# AUTOCERTIFY PROCESS
#########################################################################################################################


# GK 07-2025 @autocertify new
def db_insert_process_user_autocertify(connection, prompt_list):

    logger.info(f"Starting db_insert_process_user_autocertify {len(prompt_list)}")
    with connection.cursor() as cursor:
        prompt_proc_date = get_sysdate()
        prompt_source ='user-autocertify'
        for row in prompt_list:
            user_execution_id = row[0]
            prompt_vect = llm_create_str_embedding(row[1])
            insert = f"""
                INSERT INTO certify_state (prompt_proc_date , user_execution_id, prompt_source, prompt_vect)
                    VALUES (:prompt_proc_date,:user_execution_id,:prompt_source, :prompt_vect)
                        """
            logger.debug(f"insert: {insert}")
            logger.debug({"prompt_proc_date": prompt_proc_date, "user_execution_id" :user_execution_id, "prompt_source" :prompt_source})

            cursor.execute(insert, {"prompt_proc_date": prompt_proc_date, "user_execution_id": user_execution_id, "prompt_source": prompt_source, "prompt_vect": json.dumps(prompt_vect)})

            connection.commit()

            id = db_get_latest_id(connection, prompt_source)
            db_check_duplicate_all_types(connection, prompt_vect, id)


    logger.info("Completed db_insert_process_user_autocertify")
    return prompt_proc_date

# GK 07-2025 @autocertify NEW
def db_process_certify_autocertify(connection, data):

    logger.info(f"Starting insert: db_process_certify_autocertify {len(data)}")
    certified_date = get_sysdate()
    with connection.cursor() as cursor:
        insert = """
                    insert into trust_library (certified_date, certify_state_id, prompt_txt, prompt_vect, sql_txt, is_corrected, template_id)
                    values (:certified_date, :certify_state_id, :prompt_txt, :prompt_vct, :sql_txt, :is_corrected, :template_id)
                    """

        update = """UPDATE certify_state SET
                    is_cert_proc = 1, cert_proc_date = :certified_date
                    where ID = :certify_state_id
                    """

        logger.debug(f"update: {update}")

        for each in data:
            logger.debug("**************************")
            logger.debug(f"insert: {insert}")
            logger.debug(each)
            prompt_txt = each[1]
            prompt_vct = llm_create_str_embedding(prompt_txt)

            i = {
                "certified_date": certified_date,
                "certify_state_id": each[0],
                "prompt_txt": each[1],
                "prompt_vct": json.dumps(prompt_vct),
                "sql_txt": each[2],
                "is_corrected": each[3],
                "template_id": each[4]
            }

            # check for duplicate in trust library and do not insert if so
            res_dict = db_check_duplicate(connection, i["prompt_vct"], "trust_library", i["certify_state_id"])
            if res_dict["is_duplicate"]:
                logger.debug(f"NOT inserting to trust_library c_s id={each[0]}: duplicate entry in trust_library with t_l id: {res_dict['duplicated_id']}")
                continue


            logger.debug(f"insert: {i}")
            cursor.execute(insert, i)

            u = {"certified_date": i["certified_date"],
                 "certify_state_id": i["certify_state_id"],
                 }
            logger.debug(f"update: {update}")
            logger.debug(f"update: {u}")
            cursor.execute(update, u)

    connection.commit()

    logger.info("processing completed")

def db_get_latest_id(connection, prompt_source):
    statement = f"select max(id) from certify_state where prompt_source = '{prompt_source}'"
    result = db_select(connection, statement)
    return result[0][0]



def db_check_duplicate_all_types(connection, user_prompt_vector, id):
    row_dict = None
    for table in ["trust_library", "certify_state"]:
        logger.info(f"Checking if prompt is already in {table}: certify_state_id =  {id}")
        row_dict = db_check_duplicate(connection, user_prompt_vector, table, id)

        logger.debug(f"row_dict {row_dict}")

        if row_dict["is_duplicate"]:
            break

    return row_dict


def db_check_duplicate(connection, user_prompt_vector, table, id):
    logger.info(f" Starting duplicate check on {table} for certify_state_id={id}")
    logger.debug(f"Vector length={len(user_prompt_vector)}")

    res_dict = {"certify_id": id, "duplicated_table": table, "is_duplicate": False, "duplicated_id": -1, "template_id": -1}
    statement = ""
    match table:
        case "trust_library":
            statement = f"""
                SELECT COSINE_DISTANCE(prompt_vect, '{user_prompt_vector}') as v, id, prompt_txt, template_id  
                FROM trust_library 
                WHERE is_deprecated is null  or is_deprecated = 0 
                ORDER BY v FETCH EXACT FIRST 1 ROWS ONLY"""
        case "certify_state":
            statement = f"""
                SELECT COSINE_DISTANCE(prompt_vect, '{user_prompt_vector}') as v, id, prompt_txt  
                FROM certify_state 
                WHERE duplicated_tbl_name is null 
                and id < {id}
                ORDER BY v FETCH EXACT FIRST 1 ROWS ONLY"""
        case _:
            statement = None

    if statement is None:
        logger.error(f"Table {table} not recognized")
        # logger.info('{"records": -1}')
        return None

    # logger.info(f"Statement {statement}")

    with connection.cursor() as cursor:

        cursor.execute(statement)
        result = cursor.fetchall()
        if result is None or len(result) == 0:
            logger.info(f"No resultset returned for {res_dict}")
            return res_dict
        # logger.info(f"Results {result}")

        # normalize to 0-1 range
        normalized_score = round(1 - result[0][0], 2)

        if normalized_score == 1.00:
            res_dict["is_duplicate"] = True
            res_dict["duplicated_id"] = result[0][1]
            if result and len(result[0]) > 3 and result[0][3] is not None:
                res_dict["template_id"] = result[0][3]
            else:
                res_dict["template_id"] = res_dict["duplicated_id"] 
            db_update_certify_state_duplication_flags(connection, res_dict, id)

    logger.debug(f"Results : {res_dict}")
    logger.info(f" Completed duplicate check on {table} for certify_state_id={id}")

    return res_dict


def db_update_certify_state_duplication_flags(connection, row_dict, id):
    # This is NOT a batch update but rather a single row
    duplicate_table = row_dict["duplicated_table"]
    duplicated_id = row_dict["duplicated_id"]
    id = row_dict["certify_id"]

    logger.info("Starting update: db_update_certify_state_duplication_flags")
    with connection.cursor() as cursor:
        update = f"""
                UPDATE certify_state SET
                duplicated_tbl_name = :1,
                duplicated_id = :2
                where ID = :3
                """

        logger.debug(f"update: {update},{(duplicate_table, duplicated_id, id)}")
        cursor.execute(update, (duplicate_table, duplicated_id, id))
        connection.commit()
        logger.debug("*After update execute")

    logger.info("Completed: db_update_certify_state_duplication_flags")

# deprecates all entries in trust_library with same template_id
# (ie parent and children that were autocertied against the parent
def deprecate_in_trust_library(connection, template_id):
    is_deprecated = 1
    deprecated_date = get_sysdate()

    logger.info("Starting update: deprecate_in_trust_library ")
    with connection.cursor() as cursor:
        update = f"""UPDATE trust_library set
                            is_deprecated = :1,
                            deprecation_date = :2
                            where template_id  = :3
                """

        logger.debug(f"{update}")
        logger.debug(f"update: {update},{(is_deprecated, deprecated_date, template_id)}")
        cursor.execute(update, (is_deprecated, deprecated_date, template_id))
        connection.commit()
        logger.debug("*After update execute")

    logger.info("Completed: deprecate_in_trust_library")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(constants.REST_LAYER)
    confb.setup()
    # db_file_upload_history(connection=db_get_connection())
