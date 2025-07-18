import json
import dotmap
import oracledb
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

    wallet = confb.config.database.wallet
    user = confb.config.database.user
    dns = confb.config.database.dns
    pwd = confb.config.database.pwd

    #wallet = conf.db_config.wallet
    #user = conf.db_config.user
    #dns = conf.db_config.dns
    #pwd = conf.db_config.pwd
    
    if cached_db_pwd is None:
        #cached_db_pwd=oci_helper.vault_get_secret(conf.vault_config.db_secret_ocid)
        
        cached_db_pwd=ocij.vault_get_secret(confb.config.oci.vault.db_secret_ocid)
    pwd = cached_db_pwd

    logger.info(f"Connecting to Oracle Database wallet=[{wallet}], user=[{user}], pwd=[{pwd}], dns=[{dns}]")
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
    wallet = confb.config.database.wallet
    user = confb.config.database.user
    dns = confb.config.database.dns
    pwd = confb.config.database.pwd

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
            select to_char(prompt_proc_date, '{confb.config.database.datetime_format}') as proc_date,
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

    #TODO: the 2 AUTO_ fields should be renamed in table as PROMPT_METADATA_1 and PROMPT_METADATA_1 ??
    # source set to auto in the service_controller.boostrap_controller.process_auto
    #TODO: This uses certify_state

    prompt_txt = ""
    metadata_1 = "NULL"
    AUTO_SQL_TABLES = "NULL"
    prompt_source=source
    logger.info("Starting db_insert_process_auto")
    insert = f"""
        INSERT INTO certify_state (prompt_proc_date , metadata_1, prompt_txt,prompt_source)
            VALUES (:bdate,:metadata_1,:prompt_txt,:prompt_source)
                """
    logger.debug(f"insert: {insert}")
    with connection.cursor() as cursor:
        date = get_sysdate()
        for row in prompt_list:
            AUTO_SQL_TABLES = row[0]
            metadata_1 = row[1]
            prompt_txt = row[2]
            logger.debug(row)
            logger.debug({"bdate": date, "metadata_1":metadata_1, "prompt_txt":prompt_txt})
            ## Insert test_limit here. (Anytime there is an insert.)
            cursor.execute(insert,{"bdate": date, "metadata_1":metadata_1, "prompt_txt":prompt_txt,"prompt_source":prompt_source})

    connection.commit()
    logger.info("Inserts process auto completed")
    return date

def db_insert_process_upload(connection,  prompt_list,domain):
    #TODO: This uses certify_state

    #TODO: the 2 AUTO_ fields should be renamed in table as PROMPT_METADATA_1 and PROMPT_METADATA_1 ??
    PROMPT = ""
    AUTO_SQL_TAXON = "NULL"
    UPLOAD_FILE_NAME = "NULL"

    logger.info("Starting db_insert_process_auto")
    insert = """
        INSERT INTO certify_state (prompt_proc_date , metadata_1, upload_filename, prompt_txt, prompt_source)
            VALUES (:prompt_proc_date,:metadata_1,:upload_filename, :prompt_txt, 'upload')
                """
    logger.debug(f"insert: {insert}")
    with connection.cursor() as cursor:
        prompt_proc_date = get_sysdate()
        for row in prompt_list:
            AUTO_SQL_TAXON = row[0]
            UPLOAD_FILE_NAME = row[1]
            PROMPT = row[2]
            logger.debug({"prompt_proc_date": prompt_proc_date, "metadata_1":AUTO_SQL_TAXON, "upload_filename":UPLOAD_FILE_NAME, "prompt_txt":PROMPT})
            cursor.execute(insert,{"prompt_proc_date": prompt_proc_date, "metadata_1":AUTO_SQL_TAXON, "upload_filename":UPLOAD_FILE_NAME, "prompt_txt":PROMPT})

    connection.commit()
    logger.info("DB Inserts process upload")
    return prompt_proc_date

def db_insert_process_user(connection, prompt_source, prompt_list):
    #TODO: This uses certify_state

    logger.info("Starting db_insert_process_user")
    with connection.cursor() as cursor:
        prompt_proc_date = get_sysdate()
        prompt_source='user'
        for row in prompt_list:
            user_src_id = row[0]
            insert = f"""
                INSERT INTO certify_state (prompt_proc_date , user_execution_id, prompt_source)
                    VALUES (:prompt_proc_date,:user_execution_id,:prompt_source)
                        """
            logger.debug(f"insert: {insert}")
            logger.debug({"prompt_proc_date": prompt_proc_date, "user_execution_id":user_src_id, "prompt_source":prompt_source})
            
            cursor.execute(insert,{"prompt_proc_date": prompt_proc_date, "user_execution_id":user_src_id, "prompt_source":prompt_source})

    connection.commit()
    logger.info("DB Inserts process user completed")
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

def db_process_certify_1(connection, record_list, control,domain):
    ctrl = dotmap.DotMap(control)
    #DEPENDENCIES: This uses certify_state
    #NOTE: This doesn't work with a parametrized query because of the list being passed. sblais - 11Feb2025

    logger.info(f"Starting insert: db_process_certify {len(record_list)}")
    certified_date = get_sysdate()
    with connection.cursor() as cursor:
        # id, metadata_1, prompt_txt, sql_txt, sql_corrected
        for row in record_list:
            logger.debug("**************************")
            logger.debug(row)
            logger.debug("**************************")
            certify_state_id = row["id"]
            prompt_txt = row["prompt_txt"] # Can not be None
            prompt_vct = llm_create_str_embedding(prompt_txt)
            logger.debug(f"db_process_certify_1.1 sql_txt: {row['sql_txt']}")
            if "sql_corrected" not in row.keys():
                logger.debug(f"db_process_certify_1.1.1 keys={row.keys()}")
                sql_txt = row["sql_txt"]
            else:
                sql_txt = row["sql_txt"] if (row["sql_corrected"] is None or row["sql_corrected"] == "") else row["sql_corrected"]
                logger.debug(f"db_process_certify_1.2 sql_txt:  {sql_txt}")
                logger.debug(f"db_process_certify_1.3 sql_corrected {row['sql_corrected']}")
            
            # logging.info(f"process_certify prompt vector {prompt_vct}")
            if sql_txt is not None and len(sql_txt) > 0:
                # TO DO Implement parametrized SQL.
                insert = f"""
                            insert into trust_library (certified_date, certify_state_id, prompt_txt, prompt_vect, sql_txt)
                            values (:certified_date,  :certify_state_id, :prompt_txt, :prompt_vct, :sql_txt )
                            """
                
                logger.debug(f"insert: {insert}")
                # Insert limit_test here. If true, then make a logging statement that the sql is not run.
                if ctrl.test.mode and "insert" in  ctrl.test.out_of_scope.database:
                    logger.info("The insert into trust_library is not being executed")
                else:
                    # cursor.execute(insert)
                    logger.info("Doing the insert)")
                    n= cursor.execute(insert,{
                            "certified_date":certified_date,
                            "certify_state_id":certify_state_id,
                            "prompt_txt":prompt_txt,
                            "prompt_vct":json.dumps(prompt_vct),
                            "sql_txt":sql_txt})
                    logger.info(f"DB return after updating the trust_library: {n}")

    connection.commit()

    logger.debug("Starting update: certify_state table")
    with connection.cursor() as cursor:
        date = get_sysdate()
        for row in record_list:
            ID = row["id"]
            # TODO parameterised sql
            update = """
                        UPDATE certify_state SET
                        is_cert_proc = 1,  cert_proc_date = :1
                        where ID = :2
                        """

            logger.debug(f"update: {update}")
            if ctrl.test.mode and "update" in  ctrl.test.out_of_scope.database:
                logger.info(f"The update {(date,ID)} into certify_state is not being executed")
            else:
                cursor.execute(update,(date,ID))

    connection.commit()
    logger.info("processing completed")


def db_process_certify_2(connection, data):
    #TODO: This uses certify_state

    logger.info(f"Starting insert: db_process_certify {len(data)}")
    certified_date = get_sysdate()
    with connection.cursor() as cursor:
        insert = """
                    insert into trust_library (certified_date, certify_state_id, prompt_txt, prompt_vect, sql_txt)
                    values (:certified_date, :certify_state_id, :prompt_txt, :prompt_vct , :sql_txt )
                    """
        update = """cert_proc_date
                    UPDATE certify_state SET
                    is_cert_proc = 1, cert_proc_date = :certified_date
                    where ID = :certify_state_id
                    """

        logger.debug(f"insert: {insert}")
        logger.debug(f"update: {update}")
        
        for each in data:
            logger.debug("**************************")
            logger.debug(each) 
            logger.debug("**************************")
            prompt_vct = llm_create_str_embedding(each["prompt_txt"])

            if ("sql_corrected" in each):
                if ((each["sql_corrected"] == "") or (each["sql_corrected"] is None )):
                    pass
                else:
                    each["sql_txt"]=each["sql_corrected"]
            
            each["certified_date"]=certified_date
            each["certify_state_id"]=each["id"]

            i = {
                "certified_date":each["certified_date"],
                "certify_state_id":each["certify_state_id"],
                "prompt_txt":each["prompt_txt"],
                "prompt_vct":json.dumps(prompt_vct),
                "sql_txt":each["sql_txt"]
                }
            logger.debug(f"insert: {i}")
            cursor.execute(insert, i)

            u = {"certified_date":each["certified_date"],
                 "certify_state_id":each["certify_state_id"]
                }
            logger.debug(f"update: {u}")
            cursor.execute(update, u)

    connection.commit()

    logger.info("processing completed")


def db_get_auto_hist(connection,domain):
    #TODO: This uses certify_state
    logger.info("Starting db_get_auto_hist")
    rows_affected=0
    lst : list = list()

    with connection.cursor() as cursor:

        sql =f""" select to_char(prompt_proc_date, '{confb.config.database.datetime_format}') as proc_date, count(*) as proc_count 
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
        sql =f""" select to_char(t.certified_date, '{confb.config.database.datetime_format}') as corrected_date,
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


def db_get_to_certify(connection,domain) :
    logger.info("Starting db_get_to_certify")
    rows_affected=0
    lst : list = list()

    sql =f""" select id as id,
                to_char(prompt_proc_date, '{confb.config.database.datetime_format}') as proc_date, 
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
            order by id desc
            """

    with connection.cursor() as cursor:

        logger.debug(f"select: {sql}")
        cursor.execute(sql )

        sql_ret = db_select(connection=connection, select_statement=sql)
        logger.debug(sql_ret)

        for each in sql_ret:
            e ={}
            e["id"]=each[0]
            e["proc_date"]=each[1]
            # e["proc_count"]=each[2]
            e["proc_source"]=each[2]
            e["meta"]=each[3]
            e["prompt_txt"]=each[4]
            e["sql_txt"]=format_sql(each[5])
            e["parse_error_code"]=each[6]
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
                to_char(prompt_proc_date, '{confb.config.database.datetime_format}') as proc_date, 
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


def db_get_to_certify_lc(connection, mode: int,domain) :
    #TODO: This uses certify_state
    logger.info("Starting db_get_to_certify_lc")
    rows_affected=0
    lst : list = list()
    mode_lst = []

    mode_lst.insert(0, f""" select c.id as id,
                    to_char(e.execution_date, '{confb.config.database.datetime_format}') as exec_date,
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
                order by id desc
                """)
    
    # id, exec_date,prompt_txt, sql_txt, trust_level, error_code
    mode_lst.insert(1,f""" select c.id as id,
                    to_char(e.execution_date, '{confb.config.database.datetime_format}') as exec_date,
                    (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
                    e.generated_sql as sql_txt,
                    (case when e.is_prompt_equiv = 1 or e.is_template_equiv = 1 then 'S' else 'U' end) trust_level,
                    (case when e.db_error_code is null then '' else  e.db_error_code end) error_code
                from certify_state c 
                    join execution_log e on e.id = c.user_execution_id
                where is_staged_proc = 0 
                    and is_cert_proc = 0
                    and ((e.is_prompt_equiv = 0 and e.is_template_equiv = 0) or (db_error_code is not null))
                    and e.user_feedback_code != -1
                    and prompt_source = 'user'
                order by id desc """)

    #id, exec_date, email, feedback, prompt_txt, sql_txt,trust_level, authorized, error_code
    mode_lst.insert(2,f""" select  c.id as id,
                    to_char(e.execution_date, '{confb.config.database.datetime_format}') as exec_date,
                    a.email_address as email,
                    e.user_feedback_txt as feedback,
                    (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
                    e.generated_sql as sql_txt,
                    (case when e.is_trusted = 1 then 'T' when (e.is_prompt_equiv = 1 or e.is_template_equiv = 1) then 'S' else 'U' end) trust_level,
                    (case when e.is_authorized = 0 then 'false' else 'true' end) authorized,
                    (case when e.db_error_code is null then '' else  e.db_error_code end) error_code
                from certify_state c 
                    join execution_log e on e.id = c.user_execution_id
                    join app_users a on a.id = e.user_id
                where is_staged_proc = 0 
                    and is_cert_proc = 0
                    and ((e.is_prompt_equiv = 0 and e.is_template_equiv = 0) or (db_error_code is not null))
                    and e.user_feedback_code = -1
                    and prompt_source = 'user'
                order by id desc
                """)
    
    with connection.cursor() as cursor:
        sql = mode_lst[mode]
        
        logger.debug(f"select: {sql}")
        cursor.execute(sql )

        sql_ret = db_select(connection=connection, select_statement=sql)
        logger.debug(sql_ret)

        for each in sql_ret:
            e ={}
            # id, exec_date,prompt_txt, sql_txt, score, trust_prompt_txt, trust_sql_txt
            if (mode ==0):
                e["id"]=each[0]
                e["exec_date"]=each[1]
                e["prompt_txt"]=each[2]
                e["sql_txt"]=format_sql(each[3])
                e["score"]=each[4]
                e["trust_prompt_txt"]=each[5]
                e["trust_sql_txt"]=format_sql(each[6])
                # calculated fields
                e["prompt_diff"]= nl.generate_diff_string(e["trust_prompt_txt"], e["prompt_txt"])
                e["sql_diff"] = nl.generate_diff_string(e["trust_sql_txt"], e["sql_txt"])

            # id, exec_date,prompt_txt, sql_txt, trust_level, error_code
            elif (mode == 1):
                e["id"]=each[0]
                e["exec_date"]=each[1]
                e["prompt_txt"]=each[2]
                e["sql_txt"]=format_sql(each[3])
                e["trust_level"]=each[4]
                e["error_code"]=each[5]

            #id, exec_date, email, feedback, prompt_txt, sql_txt,trust_level, authorized, error_code
            elif (mode == 2):
                e["id"]=each[0]
                e["exec_date"]=each[1]
                e["email"]=each[2]
                e["feedback"]=each[3]
                e["prompt_txt"]=each[4]
                e["sql_txt"]=format_sql(each[5])
                e["trust_level"]=each[6]
                e["authorized"]=each[7]
                e["error_code"]=each[8]
            
            lst.append(e)

        rows_affected = cursor.rowcount

    connection.commit()
    logger.debug(lst)
    logger.info(f"select get_to_certified_lc completed with {rows_affected} returned")
    
    return lst

def db_get_staged_lc_0_failed(connection,domain):
    logger.info("Starting db_get_staged_lc_0_failed")
    rows_affected=0
    lst : list = list()
    #id, exec_date, pass_fail, prompt_txt, sql_txt, corrected_sql_txt, score,trust_prompt_txt,trust_sql_txt

    stmt=f"""
        select c.id as id,
                    to_char(execution_date, '{confb.config.database.datetime_format}') as exec_date,
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
            to_char(execution_date, '{confb.config.database.datetime_format}') as exec_date,
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
            to_char(execution_date, '{confb.config.database.datetime_format}') as exec_date,
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
            to_char(execution_date, '{confb.config.database.datetime_format}') as exec_date,
            c.pass_fail as pass_fail,
            a.email_address as email,
            e.user_feedback_txt as feedback,
            (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
            e.generated_sql as sql_txt,
            c.corrected_sql_txt as corrected_sql,
            (case when e.is_trusted = 1 then 'T' when (e.is_prompt_equiv = 1 or e.is_template_equiv = 1) then 'S' else 'U' end) trust_level,
            (case when e.is_authorized = 0 then 'false' else 'true' end) authorized,
            (case when e.db_error_code is null then '' else  e.db_error_code end) error_code
        from certify_state c 
            join execution_log e on e.id = c.user_execution_id
            join app_users a on a.id = e.user_id
        where is_staged_proc = 1 
            and is_cert_proc = 0
            and ((e.is_prompt_equiv = 0 and e.is_template_equiv = 0) or (db_error_code is not null))
            and e.user_feedback_code = -1
            and prompt_source = 'user'
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(constants.REST_LAYER)
    confb.setup()
    # db_file_upload_history(connection=db_get_connection())
