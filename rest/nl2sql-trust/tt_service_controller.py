import configparser
from io import BytesIO
import json
import os
import re
import concurrent
from dotmap import DotMap
import requests
import logging

import constants
from constants import SCHEMA_FILE, TEST_DATA_PATH,OS_APEX_EXPORT

from helpers.oci_helper import oci_helper as ocih
from helpers.config_helper import nlp2sql_config as conf

from helpers import util as u
from helpers import database_util as io
from helpers import schema as sc
from helpers import natural_language_util as nl
from helpers import finetune_helper as ft
from helpers import operations_helper as ops
from helpers import trust_metrics as metric

logger = logging.getLogger(constants.SERVICE_LAYER)
conf.read_configuration(suffix=os.getenv("NL2SQL_ENV"))

class bootstrap_controller:
        
    def process_auto(self):
        source = 'auto'
        sorted_list = []

        
        schema = sc.load_schema(f'{constants.CONF_PATH}/{constants.SCHEMA_FILE}')
        SP = " "


        def generate_select(table):

            table_used = table["name"]

            # select all including limit
            sql_type = "S"
            prompt = u.get_first(nl.s_all) + SP + u.get_first(table["domain"])
            sorted_list.append([table_used, sql_type, prompt])

            sql_type += "_L"
            limit_list = ["the first twenty", "the last two"]
            for limit in limit_list:
                prompt = u.get_first(nl.s) + SP + limit + SP + u.get_first(table["domain"])
                sorted_list.append([table_used, sql_type, prompt])

            # select all count
            sql_type = "Saq"
            prompt = (u.get_first(nl.agg) + SP +
                    u.get_first(nl.agg_count) + u.get_first([" rows of", " records of"]) + SP +
                    u.get_first(table["domain"]))
            sorted_list.append([table_used, sql_type, prompt])

            # select single columns
            sql_type = "S.c"
            for column in sc.get_columns(table):
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(["each"]) + SP +
                        u.get_first(column["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

            # select multiple columns
            sql_type = "S.c*"
            columns = sc.get_columns(table)
            if len(columns) == 2:
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(["each"]) + SP +
                        u.get_first(columns[0]["domain"]) + " and " + u.get_first(columns[1]["domain"]))
                sorted_list.append([table_used, sql_type, prompt])
            if len(columns) > 2:
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(["each"]) + SP +
                        u.get_first(columns[0]["domain"]) + ", " + u.get_first(columns[1]["domain"]) + " and " + u.get_first(columns[2]["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

            # select single aggregation (quantity) including limit
            sql_type = "S.caq"
            columns = sc.get_cols_by_type(table["columns"], "quant")
            if len(columns) > 0:
                column = columns[0]
                for nl_agg in nl.get_aggr_quant_list():
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_agg + SP +
                            u.get_first(column["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

                sql_type += "_L"
                for nl_lim in nl.get_limit_quant_list():
                    column = u.get_first(columns)
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_lim + SP +
                            u.get_first(column["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

            # select count of single label
            sql_type = "S.cal"
            columns = sc.get_cols_by_type(table["columns"], "label")
            if len(columns) > 0:
                column = columns[0]
                prompt = (u.get_first(nl.agg) + SP +
                        u.get_first(nl.agg_count) + SP +
                        u.get_first(column["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

            # select aggregation (date) including limit
            sql_type = "S.cad"
            columns = sc.get_cols_by_type(table["columns"], "date")
            if len(columns) > 0:
                column = columns[0]
                for nl_agg in nl.get_aggr_date_list():
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_agg + SP +
                            u.get_first(column["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

                sql_type += "_L"
                for nl_lim in nl.get_limit_date_list():
                    column = u.get_first(columns)
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_lim + SP +
                            u.get_first(column["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

            # select single business rule
            sql_type = "S.b"
            brs = sc.get_bus_rules(table)
            for br in brs:
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(['the']) + SP +
                        u.get_first(br["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

            # select multiple business rules
            sql_type = "S.b*"
            brs = sc.get_bus_rules(table)
            if len(brs) == 2:
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(["each"]) + SP +
                        u.get_first(brs[0]["domain"]) + " and " + u.get_first(brs[1]["domain"]))
                sorted_list.append([table_used, sql_type, prompt])
            if len(brs) > 2:
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(["each"]) + SP +
                        u.get_first(brs[0]["domain"]) + ", " + u.get_first(brs[1]["domain"]) + " and " + u.get_first(brs[2]["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

            # select single aggregation on business rule (quantity)
            sql_type = "S.baq"
            brs = sc.get_bus_rules_by_type(table, "quant")
            if len(brs) > 0:
                br = brs[0]
                for nl_agg in nl.get_aggr_quant_list():
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_agg + SP +
                            u.get_first(br["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

                sql_type += "_L"
                for nl_lim in nl.get_limit_quant_list():
                    column = u.get_first(columns)
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_lim + SP +
                            u.get_first(br["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

            # select count on business rule (label)
            sql_type = "S.bal"
            brs = sc.get_bus_rules_by_type(table, "label")
            if len(brs) > 0:
                br = brs[0]
                prompt = (u.get_first(nl.agg) + SP +
                        u.get_first(nl.agg_count) + SP +
                        u.get_first(br["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

            # select single aggregation on business rule (date)
            sql_type = "S.bad"
            brs = sc.get_bus_rules_by_type(table, "date")
            if len(brs) > 0:
                br = brs[0]
                for nl_agg in nl.get_aggr_date_list():
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_agg + SP +
                            u.get_first(br["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

                sql_type += "_L"
                for nl_lim in nl.get_limit_date_list():
                    column = u.get_first(columns)
                    prompt = (u.get_first(nl.agg) + SP +
                            nl_lim + SP +
                            u.get_first(br["domain"]))
                    sorted_list.append([table_used, sql_type, prompt])

            # select multiple columns and business rules
            sql_type = "S.(cb)*"
            cols = sc.get_columns(table)
            brs = sc.get_bus_rules(table)
            if len(cols) > 0 and len(brs) > 0:
                col = u.get_first(cols)
                br = u.get_first(brs)
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(["each"]) + SP +
                        u.get_first(col["domain"]) + " and " + u.get_first(br["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

                col = u.get_first(cols)
                br = u.get_first(brs)
                prompt = (u.get_first(nl.s) + SP +
                        u.get_first(["each"]) + SP +
                        u.get_first(br["domain"]) + " and " + u.get_first(col["domain"]))
                sorted_list.append([table_used, sql_type, prompt])

        def generate_join(tables):

            tables_used = tables[0]["name"] + '-' + tables[1]["name"]

            primary_cols = tables[0]["columns"]
            foreign_cols = tables[1]["columns"]

            sql_type = "J.c2"
            primary_col = u.get_first(primary_cols)
            foreign_col = u.get_first(foreign_cols)
            prompt = ("Show the" + SP + u.get_first(foreign_col["domain"]) +
                    " for all " + u.get_first(tables[0]["domain"]))
            sorted_list.append([tables_used, sql_type, prompt])

            sql_type = "J.c1.c2"
            prompt = ("Show the" + SP + u.get_first(primary_col["domain"]) + " and " + u.get_first(foreign_col["domain"]) +
                    " for all " + u.get_first(tables[0]["domain"]))
            sorted_list.append([tables_used, sql_type, prompt])

            #TODO: needs to be generecized
            sql_type = "J.c1aq.c2al"
            primary_col_quant = u.get_first(sc.get_cols_by_type(primary_cols, "quant"))
            foreign_col_label = u.get_first(sc.get_cols_by_type(foreign_cols, "label"))
            prompt = ("Show the average" + SP + u.get_first(primary_col_quant["domain"]) + " and the number of " + u.get_first(foreign_col_label["domain"]) +
                    " for all " + u.get_first(tables[0]["domain"]))
            sorted_list.append([tables_used, sql_type, prompt])


        def generate_where(row):
            if row[1].startswith("S"):
                sql_type = row[1] + "_W"
                table_name = row[0]
                table = sc.get_table_by_name(schema, table_name)
                where_cols = sc.get_cols_with_domain(table["columns"])
                prompt = row[2] + SP + nl.generate_nl_prompt_where(where_cols)
                sorted_list.append([row[0], sql_type, prompt])

            if row[1].startswith("J"):
                table_names = row[0].split("-")
                i = 1
                for table_name in table_names:
                    sql_type = row[1] + "_W" + str(i)
                    table = sc.get_table_by_name(schema, table_name)
                    where_cols = sc.get_cols_with_domain(table["columns"])
                    prompt = row[2] + SP + nl.generate_nl_prompt_where(where_cols)
                    sorted_list.append([row[0], sql_type, prompt])
                    i += i


        def generate_group_by(row):
            if row[1].startswith("S"):
                sql_type = row[1] + "_G"
                table_name = row[0]
                table = sc.get_table_by_name(schema, table_name)
                group_cols = sc.get_group_by_columns(table["columns"])
                prompt = row[2] + SP + nl.generate_nl_prompt_group(group_cols)
                sorted_list.append([row[0], sql_type, prompt])

            if row[1].startswith("J"):
                table_names = row[0].split("-")
                i = 1
                for table_name in table_names:
                    sql_type = row[1] + "_G" + str(i)
                    table = sc.get_table_by_name(schema, table_name)
                    group_cols = sc.get_group_by_columns(table["columns"])
                    prompt = row[2] + SP + nl.generate_nl_prompt_group(group_cols)
                    sorted_list.append([row[0], sql_type, prompt])
                    i += i


        # create select prompts
        for table in schema['tables']:
            # use only tables that associate to domain entities
            if "domain" in table.keys():
                generate_select(table)

        # generate join prompts
        for table_pair in sc.get_join_tables(schema):
            generate_join(table_pair)


        # generate where prompts
        previous_list = sorted_list.copy()
        for row in previous_list:
            generate_where(row)

        # generate group by prompts
        previous_list = sorted_list.copy()
        for row in previous_list:
            generate_group_by(row)

        # order it by table sql
        sorted_list = u.sort_result(sorted_list)

        ######## filter list ##############################################
        filtered_list = []
        current_taxon = ""

        for item in sorted_list:
            taxon = item[1]
            if taxon == 'S.c' or taxon != current_taxon:
                filtered_list.append(item)
            current_taxon = taxon

        ##################################################################


        # insert into DB
        connection = io.db_get_connection()
        io.db_insert_process_auto(connection, source, filtered_list)
        connection.close()

        output = {"records": len(filtered_list)}
        logger.info(output)

        return output

    def get_auto_hist(self):
        connection = io.db_get_connection()
        ret= io.db_get_auto_hist(connection=connection)
        connection.close()

        output = {"auto_hist": ret}
        logger.debug(output)

        return output
    
    def get_upload_history(self):
        # insert into DB
        connection = io.db_get_connection()
        ret= io.db_file_upload_history(connection)
        connection.close()

        output = {"history": ret}
        logger.debug(output)

        return output
    
    def process_upload(self,jlist):

        upload_list = []
        filename = jlist["filename"]
        for data in jlist["data"]:
            upload_list.append([data["metadata"], filename, data["prompt"]])

        # insert into DB
        connection = io.db_get_connection()
        io.db_insert_process_upload(connection, upload_list)
        connection.close()

        output = {"records": len(upload_list), "filename": filename}
        logger.info(output)

        return output

    def multithreaded_process_one_sql(self,connection,result):
        def clean_sql(sql):
            tmp = sql.replace("\\n", " ").replace('"', '').replace(';', '').strip()
            tmp = re.sub(r'\s+', ' ', tmp)
            tmp = tmp.split("This")[0]
            return tmp

        # run prompt against nl2sql llm
        prompt = result[1]
        url = conf.ai_config.engine_nl2sql_url
        response = requests.post(url, json={"question": prompt})
        
        logger.debug(response.text)

        r = DotMap(json.loads(response.text))
        sql = clean_sql(r.query)

        # run check to see if it parses. if not, E is prepopulated in column for expert to pass/fail in manual workflow (given no E)
        tmp = None
        sql_parse_result = "0" #io.db_sql_parse(connection, sql)
        if sql_parse_result == "0":
            tmp = ["", ""]
        else:
            tmp = ["E", sql_parse_result]
        row =[str(result[0]), sql, tmp[0], tmp[1]]

        logger.debug(row)
        logger.debug("completed parse sql checks")

        # update db
        logger.debug("Starting updates")
        # db(N)
        io.db_update_process_sql_row(connection, row)

    def multithreaded_process_sql(self,source):
        prompt_source = source["source"]
        connection = io.db_get_connection()
        statement = """
                    select id, prompt_txt from certify_state
                        where is_sql_proc = 0
                        and prompt_source = :1
                        order by id
                    """
        # DB(N)
        result_set = io.db_select(connection, statement,params=(prompt_source,))

        logger.info(f"m:starting nl2sql with parse check {len(result_set)} ")
        row_list = []
        # llm(N/max_workers)
        connection = io.db_get_connection()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.multithreaded_process_one_sql,(connection,result_set))

        connection.commit()
        connection.close()
        logger.debug("Updates completed")

        output = {"records": len(row_list)}
        logger.info(output)

        return output

    def process_sql(self,source,multithreaded:bool= False):
        
        if multithreaded:
            return self.multithreaded_process_sql(source=source)
            
        prompt_source = source["source"]
        connection = io.db_get_connection()
        statement = """
                    select id, prompt_txt from certify_state
                        where is_sql_proc = 0
                        and prompt_source = :1
                        order by id
                    """
        # DB(N)
        result_set = io.db_select(connection, statement,params=(prompt_source,))

        def clean_sql(sql):
            tmp = sql.replace("\\n", " ").replace('"', '').replace(';', '').strip()
            tmp = re.sub(r'\s+', ' ', tmp)
            tmp = tmp.split("This")[0]
            return tmp

        logger.info(f"starting service.process_sql with the result set size: {len(result_set)}")
        row_list = []
        # llm(N)
        if len(result_set)==0:
            logger.info("No results in process_sql to process from the certify_state")
        i = 0
        session = requests.Session()
        url = conf.ai_config.engine_nl2sql_url 

        for result in result_set:
            i = i + 1
            # run prompt against nl2sql llm
            prompt = result[1]
            try:
                with session.post(url, json={"question": prompt})as response:
                    if response.status_code != 500:
                        logger.info(f"[{i}] {response.text}")
                        r = DotMap(json.loads(response.text))
                        sql = clean_sql(r.query)
                        # run check to see if it parses. if not, E is prepopulated in column for expert to pass/fail in manual workflow (given no E)
                        tmp = None
                        sql_parse_result = "0" #io.db_sql_parse(connection, sql)
                        if sql_parse_result == "0":
                            tmp = ["", ""]
                        else:
                            tmp = ["E", sql_parse_result]
                        
                        row= [str(result[0]), sql, tmp[0], tmp[1]]
                        
                        io.db_update_process_sql_row(connection,row)

                        # row_list.append(row)
                        logger.debug([str(result[0]), result[1], sql, tmp[0], tmp[1]])
                    else:
                        break
            except requests.exceptions.RequestException as e:
                # Catch all request-related exceptions (e.g., network issues, timeouts)
                print(f"An error occurred: {e}")

        connection.commit()
        session.close()  # Close the session when done
        logger.debug(f"completed parse sql checks on {i} requests.")

        output = {
                    "records requested": len(result_set),
                    "records processed": i
                  }
        logger.info(output)

        return output

    def get_to_certify(self):
        logger.info("starting get to certify")

        connection = io.db_get_connection()
        ret= io.db_get_to_certify(connection)
        connection.close()
        return ret

    def process_stage(self,jlist):

        logger.info("starting stage certify processing")

        # update into DB
        connection = io.db_get_connection()
        io.db_update_save_certify(connection, jlist)
        connection.close()

        output = {"records": len(jlist["data"])}
        logger.info(output)

        return output

    def get_staged(self):
        logger.info("starting get to stage")

        connection = io.db_get_connection()
        ret= io.db_get_staged(connection)
        connection.close()
        return ret

    def process_unstage(self,id_list):

        logger.info("starting unstage certify processing")

        # update into DB
        connection = io.db_get_connection()
        updated_count=io.db_unstage_certify(connection, id_list)
        connection.close()

        output = {
                "records":{
                    "requested" : len(id_list),
                    "updated" : updated_count,
                    }
            }

        logger.info(output)

        return output

    def process_certify(self,data,control=None):
        #TODO: This uses certify_state
        logger.info("starting process certify")

        #Creating a dynamic array of positions for the parameterized query.
        logger.info(data)
        # sql_id_list = ', '.join([f":{i+2}" for i in range(len(id_list))])
        # logger.info(sql_id_list)

        connection = io.db_get_connection()

        # insert into DB
        io.db_process_certify_1(connection, data,control)
        connection.close()

        output = {"records": len(data)}
        logger.info(output)

        return output

def test_process_auto():
    b: bootstrap_controller = bootstrap_controller()
    b.process_auto()

def test_get_auto_hist():
    b: bootstrap_controller = bootstrap_controller()
    b.get_auto_hist()

def test_get_upload_history():
    b: bootstrap_controller = bootstrap_controller()
    b.get_upload_history()

def test_process_upload():
    b: bootstrap_controller = bootstrap_controller()
    with open(f'{TEST_DATA_PATH}/body_upload.json', 'r') as file:
        json_list = json.load(file)  # Reads the entire content of the file into a string
    b.process_upload(jlist=json_list)

def test_process_unstage():
    b: bootstrap_controller = bootstrap_controller()
    b.process_unstage([1,2,3])


class life_certify_controller:

    def get_certify_lc(self,mode: int):
        logger.info("starting get to stage")
        connection = io.db_get_connection()
        ret= io.db_get_to_certify_lc(connection=connection, mode=mode)
        connection.close()
        return ret

    def get_staged_lc_0(self,input:str):
        connection = io.db_get_connection()
        if input.lower() == "pass":
            return io.db_get_staged_lc_mode_0(connection=connection)
        else:
            return io.db_get_staged_lc_0_failed(connection=connection)

    def get_staged_lc(self,mode:int):
        connection = io.db_get_connection()
        if mode == 0:
            return io.db_get_staged_lc_mode_0(connection=connection)
        elif mode == 1:
            return io.db_get_staged_lc_mode_1(connection=connection)
        elif mode == 2:
            return io.db_get_staged_lc_mode_2(connection=connection)
        else:
            return "Not implemented yet."

    def process_users_lc(self):
        source = 'users'
        connection = io.db_get_connection()

        ## id, execution_date, certified_score, prompt_tx, prompt_lineage, sql_query, sql_lineage, db_err_text, gen_engine_nm, fb
        statement = """
                    select id 
                    from execution_log
                    where is_cert_processed = 0
                    and (is_trusted = 0 or (is_trusted = 1 and (user_feedback_code = -1 or db_error_code is not null)))   
                    and is_authorized = 1   
                    and is_clarify = 0   
                    and is_action = 0
                    order by id
                    """
        result_set = io.db_select(connection, statement)
        rlen = len(result_set)
        # insert into DB
        io.db_insert_process_user(connection, source, result_set)

        # update executed table with id
        io.db_update_executed_prompts_table(connection, result_set)

        connection.close()

        output = {"records": rlen}
        logger.info(output)

        return output

    def process_users(self):
        source = 'users'
        connection = io.db_get_connection()

        ## id, execution_date, certified_score, prompt_tx, prompt_lineage, sql_query, sql_lineage, db_err_text, gen_engine_nm, fb
        statement = f""" select id 
            from execution_log
            where is_cert_processed = 0
            and (is_trusted = 0 or (is_trusted = 1 and (user_feedback_code = -1 or db_error_code is not null)))   
            and is_authorized = 1   
            and is_clarify = 0   
            and is_action = 0
            order by id
            """

        result_set = io.db_select(connection, statement)

        # insert into DB
        io.db_insert_process_user(connection, source, result_set)

        # update executed table with id
        io.db_update_executed_prompts_table(connection, result_set)

        connection.close()

        output = {"records": len(result_set)}
        logger.info(output)

        return output

    
def test_get_certify_lc():
    lc: life_certify_controller = life_certify_controller()
    lc.get_certify_lc(mode=0)
    lc.get_certify_lc(mode=1)
    lc.get_certify_lc(mode=2)
    #lc.get_certify_lc(mode=3) # Should not work

def test_get_staged_lc():
    lc: life_certify_controller = life_certify_controller()
    lc.get_staged_lc(mode=0)
    lc.get_staged_lc(mode=1)
    lc.get_staged_lc(mode=2)
    #lc.get_staged_lc(mode=3) # Should not work

def test_process_users_lc():
    lc: life_certify_controller = life_certify_controller()
    lc.process_users_lc()

def test_process_users():
    lc: life_certify_controller = life_certify_controller()
    lc.process_users()

class trust_ops_controller:
    def get_live_logs(self,max_row_count:int=1000):
        return ops.ops_live_logs(max_row_count=max_row_count)
    
def test_get_live_logs( ):
    ops: trust_ops_controller = trust_ops_controller()
    ops.get_live_logs()

class fine_tune_controller:

    def process_export_jsonl(self):
        output = ft.process_export_jsonl( )
        return output
    
def test_process_export_jsonl():
    ft: fine_tune_controller = fine_tune_controller()
    ft.process_export_jsonl()

class administrative_controller:
    def read_config(self):
        output = conf.dict_value()
        return output
    
    def reset_config_from_file(self):
        conf.read_configuration(conf.rest_config.location)
        output = conf.dict_value()
        return output

    def read_metadata_os(self):
        print("Administrative_Processor::read_metadata_os")
        output = self.read_metadata_os_fn(SCHEMA_FILE)
        return output

    def get_os_file(self, fn:str ):
        path: str = f"{conf.installation}/{OS_APEX_EXPORT}"
        output = ocih.download(file_path=path,fn=fn)
        return output
        
    def put_os_file(self, fn:str, content):
        path: str = f"{conf.installation}/{OS_APEX_EXPORT}"
        output = ocih.put_os_file(path=path, fn=fn, content=content)
        return output

    def read_metadata_os_fn(self,fn:str):
        logger.info("Service_Helper::read_metadata_os")
        return json.load(BytesIO(ocih.download_metadata(fn=fn)))
    
def test_finetune():
    pass

class llm_metrics_controller:
    def size_trust_library(self):
        logger.info("Service_Helper::size_trust_library")
        return metric.size_trust_library()

    def percentage_prompts_trust_level(self):
        logger.info("Service_Helper::percentage_prompts_trust_level")
        return metric.percentage_prompts_trust_level()

    def size_trust_library_source(self):
        logger.info("Service_Helper::size_trust_library")
        return metric.size_trust_library_source()
    
    def users_number_prompts_trust_level(self):
        logger.info("Service_Helper::users_number_prompts_trust_level")
        return metric.users_number_prompts_trust_level()

    def users_number_prompts(self):
        logger.info("Service_Helper::users_number_prompts")
        return metric.users_number_prompts()
    
    def users_number(self):
        logger.info("Service_Helper::users_number")
        return metric.users_number()

## HOTFIX: 23 April 2025
    def accuracy_by_trust_level(self, start_date, end_date):
        logger.info("Service_Helper::accuracy_by_trust_level")
        return metric.accuracy_by_trust_level(start_date=start_date, end_date=end_date)

    def size_trust_library_user_prompts_trust(self, start_date, end_date):
        logger.info("Service_Helper::size_trust_library_user_prompts_trust")
        return metric.size_trust_library_user_prompts_trust(start_date=start_date, end_date=end_date)
##

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(constants.REST_LAYER)
    conf.read_configuration(suffix=os.getenv("NL2SQL_ENV"))
