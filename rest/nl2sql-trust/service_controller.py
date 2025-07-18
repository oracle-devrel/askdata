import asyncio
import datetime
from dateutil import parser
from io import BytesIO
import json
import os
import re
import concurrent
import time
from dotmap import DotMap
import dotmap
from fastapi import HTTPException
import requests
import logging

import constants
from constants import TEST_DATA_PATH,OS_APEX_EXPORT

from helpers.oci_helper_json import oci_helper as ocij
from helpers.config_json_helper import config_boostrap as confb
from helpers.config_json_helper import walkback


from helpers import util as u
from helpers import database_util as io
from helpers import schema as sc
from helpers import natural_language_util as nl
from helpers import finetune_helper as ft
from helpers import operations_helper as ops
from helpers import trust_metrics as metric
from helpers import engine as eng
from helpers import finetune_db as ftdb

logger = logging.getLogger(constants.SERVICE_LAYER)

class bootstrap_controller:
    process_sql_results = []

    def process_auto(self,domain):
        source = 'auto'
        sorted_list = []

        
        schema = sc.load_schema(f'{constants.CONF_PATH}/{confb.config.oci.os.metadata.file_name}')
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

    def get_auto_hist(self,domain):
        connection = io.db_get_connection()
        ret= io.db_get_auto_hist(connection=connection,domain=domain)
        connection.close()

        output = {"auto_hist": ret}
        logger.debug(output)

        return output
    
    def get_upload_history(self,domain):
        # insert into DB
        connection = io.db_get_connection()
        ret= io.db_file_upload_history(connection,domain=domain)
        connection.close()

        output = {"history": ret}
        logger.debug(output)

        return output
    
    def process_upload(self,jlist,domain):

        upload_list = []
        filename = jlist["filename"]
        for data in jlist["data"]:
            upload_list.append([data["metadata"], filename, data["prompt"]])

        # insert into DB
        connection = io.db_get_connection()
        io.db_insert_process_upload(connection, upload_list,domain=domain)
        connection.close()

        output = {"records": len(upload_list), "filename": filename}
        logger.info(output)

        return output

    def multithreaded_process_one_sql(self,connection,result):

        # run prompt against nl2sql llm
        prompt = result[1]
        url = confb.config.oci.engine.llm_prompt_url
        #url = conf.engine_config.llm_prompt_url
        response = requests.post(url, json={"question": prompt})
        
        logger.debug(response.text)

        r = DotMap(json.loads(response.text))
        sql = u.clean_sql(r.query)

        # run check to see if it parses. if not, E is prepopulated in column for expert to pass/fail in manual workflow (given no E)
        tmp = None
        sql_parse_result = io.db_sql_parse(connection, sql)
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
    
    async def process_sql(self,source,domain, multithreaded:bool= False):
        consecutive_zero_count = 0
        total_requested = 0
        total_processed = 0
        self.process_sql_results = []
        while True:
            result = self.inner_process_sql(source,domain, multithreaded)  # Call the process_sql method
            self.process_sql_results.append(result)

            records_processed = result["records processed"]
            total_processed += records_processed  # Add the processed records to the total
            
            logging.info(f"Records requested: {result['records requested']}, Records processed: {records_processed}")
            
            if total_requested == 0:
                total_requested = result["records requested"]

            if records_processed == 0:
                consecutive_zero_count += 1
            else:
                consecutive_zero_count = 0  # Reset if records were processed
            
            # Exit conditions
            # Stop if 3 consecutive runs have 0 records processed
            if consecutive_zero_count >= 3:
                break
            # Stop of the number of record requested is the same as the number processed.
            if total_processed == result["records requested"]:
                break
            if result["records requested"] == 0:
                break
            
            # Wait for 5 seconds before the next iteration
            # Needs to be configurable
            await asyncio.sleep(5)
        
        logging.debug(self.process_sql_results)

        return {
            "records_requested": total_requested,
            "records_processed": total_processed
        }


    def inner_process_sql(self,source,domain, multithreaded:bool= False):
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
        url = confb.config.oci.engine.get_sql_url
        #url = conf.engine_config.get_sql_url

        for result in result_set:
            i = i + 1
            # run prompt against nl2sql llm
            prompt = result[1]
            try:
                logger.debug(f"inner process sql: [{i}] {prompt}")
                # show dealer names and addresses
                with session.post(url, json={"question": prompt}) as response:
                    if response.status_code != 500:
                        logger.info(f"[{i}] {response.text}")
                        r = DotMap(json.loads(response.text))
                        sql = clean_sql(r.query)
                        # run check to see if it parses. if not, E is prepopulated in column for expert to pass/fail in manual workflow (given no E)
                        tmp = None
                        sql_parse_result = io.db_sql_parse(connection, sql)
                        if sql_parse_result == "0":
                            tmp = ["", ""]
                        else:
                            tmp = ["E", sql_parse_result]
                        
                        row= [str(result[0]), sql, tmp[0], tmp[1]]
                        
                        io.db_update_process_sql_row(connection,row)

                        # row_list.append(row)
                        logger.debug([str(result[0]), result[1], sql, tmp[0], tmp[1]])
                        connection.commit()
                    else:
                        i=i-1 #Remove the last one from the processed count
                        break
            except requests.exceptions.RequestException as e:
                # Catch all request-related exceptions (e.g., network issues, timeouts)
                print(f"An error occurred: {e}")

        session.close()  # Close the session when done
        logger.debug(f"completed parse sql checks on {i} requests.")

        output = {
                    "records requested": len(result_set),
                    "records processed": i
                  }
        logger.info(output)

        return output

    def get_to_certify(self,domain):
        logger.info("starting get to certify")

        connection = io.db_get_connection()
        ret= io.db_get_to_certify(connection,domain)
        connection.close()
        return ret

    def process_stage(self,jlist,domain):

        logger.info("starting stage certify processing")

        # update into DB
        connection = io.db_get_connection()
        io.db_update_save_certify(connection, jlist,domain)
        connection.close()

        output = {"records": len(jlist["data"])}
        logger.info(output)

        return output

    def get_staged(self,domain):
        logger.info("starting get to stage")

        connection = io.db_get_connection()
        ret= io.db_get_staged(connection,domain)
        connection.close()
        return ret

    def process_unstage(self,id_list,domain):

        logger.info("starting unstage certify processing")

        # update into DB
        connection = io.db_get_connection()
        updated_count=io.db_unstage_certify(connection, id_list,domain)
        connection.close()

        output = {
                "records":{
                    "requested" : len(id_list),
                    "updated" : updated_count,
                    }
            }

        logger.info(output)

        return output

    def process_certify(self,data,domain, control=None):
        #TODO: This uses certify_state
        logger.info("starting process certify")

        #Creating a dynamic array of positions for the parameterized query.
        logger.info(data)
        # sql_id_list = ', '.join([f":{i+2}" for i in range(len(id_list))])
        # logger.info(sql_id_list)

        connection = io.db_get_connection()

        # insert into DB
        io.db_process_certify_1(connection, data,domain, control)
        connection.close()

        output = {"records": len(data)}
        logger.info(output)

        return output

def test_process_auto():
    b: bootstrap_controller = bootstrap_controller()
    b.process_auto(domain=None)

def test_get_auto_hist():
    b: bootstrap_controller = bootstrap_controller()
    b.get_auto_hist(domain=None)

def test_get_upload_history():
    b: bootstrap_controller = bootstrap_controller()
    b.get_upload_history(domain=None)

def test_process_upload():
    b: bootstrap_controller = bootstrap_controller()
    with open(f'{TEST_DATA_PATH}/body_upload.json', 'r') as file:
        json_list = json.load(file)  # Reads the entire content of the file into a string
    b.process_upload(jlist=json_list,domain=None)

def test_process_unstage():
    b: bootstrap_controller = bootstrap_controller()
    b.process_unstage([1,2,3], domain=None)


class life_certify_controller:

    def get_certify_lc(self,mode: int,domain):
        logger.info("starting get to stage")
        connection = io.db_get_connection()
        ret= io.db_get_to_certify_lc(connection=connection, mode=mode,domain=domain)
        connection.close()
        return ret

    def get_staged_lc_0(self,input:str,domain):
        connection = io.db_get_connection()
        if input.lower() == "pass":
            return io.db_get_staged_lc_mode_0(connection=connection,domain=domain)
        else:
            return io.db_get_staged_lc_0_failed(connection=connection,domain=domain)

    def get_staged_lc(self,mode:int,domain):
        connection = io.db_get_connection()
        if mode == 0:
            return io.db_get_staged_lc_mode_0(connection=connection,domain=domain)
        elif mode == 1:
            return io.db_get_staged_lc_mode_1(connection=connection,domain=domain)
        elif mode == 2:
            return io.db_get_staged_lc_mode_2(connection=connection,domain=domain)
        else:
            return "Not implemented yet."

    def process_users_lc(self,domain):
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
    lc.get_certify_lc(mode=0,domain=None)
    lc.get_certify_lc(mode=1,domain=None)
    lc.get_certify_lc(mode=2,domain=None)
    #lc.get_certify_lc(mode=3) # Should not work

def test_get_staged_lc():
    lc: life_certify_controller = life_certify_controller()
    lc.get_staged_lc(mode=0,domain=None)
    lc.get_staged_lc(mode=1,domain=None,)
    lc.get_staged_lc(mode=2,domain=None)
    #lc.get_staged_lc(mode=3) # Should not work

def test_process_users_lc():
    lc: life_certify_controller = life_certify_controller()
    lc.process_users_lc(domain=None)

def test_process_users():
    lc: life_certify_controller = life_certify_controller()
    lc.process_users()

class trust_ops_controller:
    def get_live_logs(self,max_row_count:int=1000,domain=None):
        return ops.ops_live_logs(max_row_count=max_row_count,domain=domain)
    
def test_get_live_logs( ):
    ops: trust_ops_controller = trust_ops_controller()
    ops.get_live_logs( )

class fine_tune_controller:
    
    ftdb_dao : ftdb.FineTuneWorkflowDAO = ftdb.FineTuneWorkflowDAO( )
    ftcfg_dao : ftdb.FineTuneConfigDAO = ftdb.FineTuneConfigDAO( )
    model_dao : ftdb.ModelUsageDAO = ftdb.ModelUsageDAO( )
    td_hist_dao:ftdb.TrainingDataHistoryDAO= ftdb.TrainingDataHistoryDAO()
    eval_dao: ftdb.FineTuneEvaluationDAO = ftdb.FineTuneEvaluationDAO()


    async def auto_complete(self, step, workflow_key:str):
        """
        step is the last step that was done. This is because if the step can 
        return some data it will, but the remainder of the step must complete.
        """
        Done :bool = False
        delay=10 # seconds
        while not Done:
            match step:
                case "configure_finetune":
                    step="create_finetune_DAC"

                case "create_finetune_DAC":
                    logger.info("Run create finetune DAC for {workflow_key} is starting.")
                    rsp= await self.create_finetune_DAC(workflow_key=workflow_key)
                    if ("dac_error_dtls" in rsp and rsp["dac_error_dtls"] is not None and len(rsp["dac_error_dtls"]) > 0):
                        step="error"
                    elif rsp["dac_lifecycle_state"].lower() == "creating":
                        step="create_finetune_DAC_update"

                case "create_finetune_DAC_update":
                    logger.info("Run create finetune DAC update for {workflow_key} is starting.")
                    timeout=3600 # one hour
                    rsp= {"dac_lifecycle_state":'creating'}
                    while rsp["dac_lifecycle_state"].lower() != "active" and timeout > 0:
                        timeout = timeout - delay
                        await asyncio.sleep(delay)
                        rsp=self.create_finetune_DAC_update(workflow_key=workflow_key)
                        if ("dac_error_dtls" in rsp and rsp["dac_error_dtls"] is not None and len(rsp["dac_error_dtls"]) > 0):
                            step="error"
                            timeout = 0
                    if rsp["dac_lifecycle_state"].lower() == "active":
                        step="run_finetune"
                    else:
                        step="error"

                case "run_finetune":
                    logger.info("Run finetune for {workflow_key} is starting.")
                    rsp=await self.run_finetune(workflow_key=workflow_key)
                    if ("ft_error_dtls" in rsp and rsp["ft_error_dtls"] is not None and len(rsp["ft_error_dtls"]) > 0):
                        step="error"
                    elif rsp["ft_lifecycle_state"].lower() == "creating":
                        step="run_finetune_update"

                case "run_finetune_update":
                    logger.info("Run finetune update for {workflow_key} is starting.")
                    timeout=3600*3 # three hours
                    rsp={"ft_lifecycle_state":'creating'}
                    while rsp["ft_lifecycle_state"].lower() != "active" and timeout > 0:
                        timeout = timeout - delay
                        await asyncio.sleep(delay)
                        rsp=self.run_finetune_update(workflow_key=workflow_key)
                        if ("ft_error_dtls" in rsp and rsp["ft_error_dtls"] is not None and len(rsp["ft_error_dtls"]) > 0):
                            step="error"
                            timeout = 0

                    if rsp["ft_lifecycle_state"].lower() == "active":
                        step="destroy_finetune_DAC"
                    else:
                        step="error"

                case "destroy_finetune_DAC":
                    logger.info("Run destroy_finetune_DAC for {workflow_key} is starting.")
                    rsp=await self.destroy_finetune_DAC(workflow_key=workflow_key)
                    if ("ft_error_dtls" in rsp and rsp["ft_error_dtls"] is not None and len(rsp["ft_error_dtls"]) > 0):
                        step="error"
                    else:
                        step="destroy_finetune_DAC_update"

                case "destroy_finetune_DAC_update":
                    logger.info("Run destroy finetune DAC update for {workflow_key} is starting.")
                    timeout=3600 # one hour
                    rsp= {"dac_lifecycle_state":'deleting'}
                    while rsp["dac_lifecycle_state"].lower() != "deleted" and timeout > 0:
                        timeout = timeout - delay
                        await asyncio.sleep(delay)
                        rsp=self.destroy_finetune_DAC_update(workflow_key=workflow_key)
                        if ("dac_error_dtls" in rsp and rsp["dac_error_dtls"] is not None and len(rsp["dac_error_dtls"]) > 0):
                            step="error"
                            timeout = 0
                    if rsp["dac_lifecycle_state"].lower() == "deleted":
                        step="done"
                        Done=True
                    else:
                        step="error"
                        Done=False

                case "error":
                    logger.error("The auto complete process for {workflow_key} is completed in error.")
                    Done = True

                case "done":
                    Done=True
                case _:
                    logger.error(f" {step} is unknown")

    def configure_finetune(self,request:dict):
        """
        Step 1.0
        """

        now = datetime.datetime.now()
        h = self.td_hist_dao.read_by_filename(filename=request["training_filename"])
        logger.info(f"fine_tune_controller.configure_finetune {h}")

        if h is None:
            raise HTTPException(status_code=422,detail=f"1-The training filename {request['training_filename']} is not in the history table.")
        if "id" not in h:
            raise HTTPException(status_code=422,detail=f"2-The training filename {request['training_filename']} is not in the history table.")
        
        request["training_data_id"] = h["id"]
        request["config_submit_time"]=request.get("config_submit_time",datetime.datetime.now())
        request["config_state"]="set"
        request["unit_count"]=request.get("unit_count",confb.config.oci.finetune.unit_count)
        request["unit_shape"]=request.get("unit_shape",confb.config.oci.finetune.unit_shape)
        request["workflow_key"] = f"{request['workflow_key']}_{now.strftime(confb.config.app.datetime_format_nospace)}"
        workflow_key = self.ftdb_dao.create(request)
        inserted = self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        inserted["training_data_file"]=request["training_filename"]
        return inserted

    def get_finetune_state(self):
        ret= self.ftdb_dao.get_finetune_state()
        ft = self.ftdb_dao.get_by_key(ret["workflow_key"])
        if "dac_submit_time" in ft and ft["dac_submit_time"] is not None:
            elapsed = datetime.datetime.now()-ft["dac_submit_time"]
            hours, remainder = divmod(elapsed.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            # Format for the elapsed time: hr:min:sec
            ret["elapsed_time"] = formatted
        else:
            ret["elapsed_time"] = "Not submitted yet."
        return ret
    
    async def evaluate_finetune(self,workflow_key:str):
        consecutive_zero_count = 0
        total_requested = 0
        total_processed = 0
        records_processed = 0
        evaluation_results = []
        while True:
            result = self._inner_evaluate_finetune(workflow_key=workflow_key)
            if result is not None:
                evaluation_results.append(result)

                records_processed = result["records processed"]
                total_processed += records_processed  # Add the processed records to the total
                
                logging.info(f"Records requested: {result['records requested']}, Records processed: {records_processed}")
                
                if total_requested == 0:
                    total_requested = result["records requested"]

            if records_processed == 0:
                consecutive_zero_count += 1
            else:
                consecutive_zero_count = 0  # Reset if records were processed
            
            # Exit conditions
            # Stop if 3 consecutive runs have 0 records processed
            if consecutive_zero_count >= 3:
                break
            # Stop of the number of record requested is the same as the number processed.
            if total_processed == total_requested:
                break
            if total_requested == 0:
                break            
            # Wait for 5 seconds before the next iteration
            # Needs to be configurable
            await asyncio.sleep(5)

        logging.debug(evaluation_results)

        return {
            "records_requested": total_requested,
            "records_processed": total_processed
        }

    def _inner_evaluate_finetune(self,workflow_key:str):
        ret= ft.evaluate_finetune(workflow_key=workflow_key)
        return ret

    def get_finetune_evaluation(self,workflow_key:str):
        ret= self.ftdb_dao.get_evaluate_finetune(workflow_key=workflow_key)
        return ret

    def get_finetune_history(self,domain):
        return self.ftdb_dao.get_finetune_history(domain)
    
    def get_workflow(self, workflow_key):
        ret= self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        ret["training_data"]= self.td_hist_dao.read_by_id(ret["training_data_id"])
        return ret

    def get_training_data(self,worflow_key):
        """
        Step 1.2
        """
        pass

    def clear_finetune(self,workflow_key):
        """
        Step 1.1
        """
        return self.ftdb_dao.update(workflow_key=workflow_key, req={"config_state":"cleared"})

    def ignore_deployment(self,workflow_key):
        """
        Step 1.1
        """
        return self.ftdb_dao.update(workflow_key=workflow_key, req={"deploy_state":"ignore"})

    def process_export_jsonl(self):
        output = ft.process_export_jsonl( )
        return output
    
    async def create_finetune_DAC(self,workflow_key: str):
        """
        Step 1.3
        """

        request = {"workflow_key":workflow_key}

        if "compartment_ocid" not in request:
            request["compartment_ocid"]=walkback(confb.config.oci.os.finetune,"compartment_ocid")

        db_response = self.ftdb_dao.get_by_key(workflow_key=workflow_key)

        dac_answer = ft.create_finetune_DAC(request=request | db_response)

        if "dac_error_dtls" not in dac_answer:
            dac : DotMap = DotMap(dac_answer)

            # "dac_started_time": dac.dac_started_time
                    
            self.ftdb_dao.update(
                workflow_key=workflow_key,
                req ={
                    "dac_submit_time": dac.dac_submit_time,
                    "dac_created_time":dac.dac_created_time,
                    "dac_lifecycle_state": dac.dac_lifecycle_state,
                    "dac_cluster_id": dac.dac_cluster_id,
                    "dac_unit_count": dac.dac_unit_count,
                    "dac_unit_shape": dac.dac_unit_shape,
                    "dac_error_dtls": ""
                    })
        else:
            req = {
                "dac_error_dtls": dac_answer["dac_error_dtls"]
            }
            self.ftdb_dao.update(workflow_key=workflow_key, req=req)
        
        return self.ftdb_dao.get_by_key(workflow_key=workflow_key)

    def create_finetune_DAC_update(self,workflow_key):
        state= self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        if "dac_cluster_id" in state and state["dac_cluster_id"] is not None and len(state["dac_cluster_id"]) > 0:
            info = ft.get_DAC_info(cluster_id=state["dac_cluster_id"])
            if "dac_error_dtls" not in info:
                req = {
                    "dac_unit_count": info["unit_count"],
                    "dac_unit_shape": info["unit_shape"],
                    "dac_lifecycle_state": info["lifecycle_state"],
                    "dac_error_dtls": ""

                }

                if info["lifecycle_state"] == "ACTIVE":
                    req["dac_started_time"] = info["time_updated"]

                if info["lifecycle_state"] == "CREATING":
                    req["dac_created_time"] = info["time_updated"]

            else:
                req = {
                    "dac_error_dtls": info["dac_error_dtls"]
                }

            self.ftdb_dao.update(workflow_key=workflow_key, req=req)
            return self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        
        return {"Error":"DAC_CLUSTER_ID not set in the database."}

    async def run_finetune(self,workflow_key: str):
        """
        Step 1.4
        """
        db_response = self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        db_response["training"] = self.td_hist_dao.read_by_id(db_response["training_data_id"])
        d = db_response["training"]
        if not d["path"].endswith("/"):
            db_response["training_data_path"] = d["path"]+"/"+d["filename"]
        else:
            db_response["training_data_path"] = d["path"]+d["filename"]

        fn_workflow = dotmap.DotMap(db_response)
        logging.info(fn_workflow)

        #1. Preconditions check
        if len(fn_workflow.dac_cluster_id) == 0:
            raise HTTPException(
                status_code=409,
                detail={
                        "status": "error",
                        "message": f"The {workflow_key} DAC ocid is not available for the requested operation."
                        }

            )
        if fn_workflow.dac_lifecycle_state.lower() != 'active':
            raise HTTPException(
                status_code=409,
                detail={
                        "status": "error",
                        "message": f"The {workflow_key} DAC is not in a proper state [{fn_workflow.dac_lifecycle_state.lower()}] for the requested operation."
                        }

            )
        if len(fn_workflow.get("training_data_path","")) == 0:
            raise HTTPException(
                status_code=409,
                detail={
                        "status": "error",
                        "message": f"The training data path is not set for the requested operation on the {workflow_key} DAC."
                        }
            )
        
        #3. Make the call to create the model on the available cluster
        req={
             "compartment_ocid": walkback(confb.config.oci.finetune,"compartment_ocid"),
             "ft_base_model_ocid": confb.config.oci.finetune.base_model_id,
             "dataset_type": confb.config.oci.finetune.dataset_type,
             "namespace":walkback(confb.config.oci.finetune,"namespace"),
             "bucket": walkback(confb.config.oci.os.finetune,"bucket"),
             "object_name": fn_workflow.training_data_path,
             "cluster_ocid": fn_workflow.dac_cluster_id,
             "training_type": confb.config.oci.finetune.training_dataset.training_config_type
        } 
        logger.info(f"Model Creation Request: {req}")
        rsp=ft.create_model_details(request=req)
        if "ft_error_dtls" not in rsp:
            rsp["ft_error_dtls"]=""

        self.ftdb_dao.update(workflow_key=workflow_key, req=rsp)
        return self.ftdb_dao.get_by_key(workflow_key=workflow_key)
    
    def run_finetune_update(self,workflow_key):
        state= self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        if "ft_result_model_id" in state and state["ft_result_model_id"] is not None and len(state["ft_result_model_id"]) > 0:
            info = ft.get_model_info(model_id=state["ft_result_model_id"])
            if "ft_error_dtls" not in info:
                req = {
                    "ft_lifecycle_state": info["lifecycle_state"],
                    "ft_base_model_id": info["base_model_id"],
                    "ft_type": info["type"],
                    "ft_version": info["version"],
                    "dac_error_dtls": ""
                }
                if info["lifecycle_state"] == "ACTIVE":
                    req["ft_started_time"] = info["time_updated"]
                    req["ft_completion_time"] = info["time_updated"]

                if info["lifecycle_state"] == "CREATING":
                    req["ft_created_time"] = info["time_updated"]
            else:
                req = {
                    "ft_error_dtls": info["ft_error_dtls"]
                }

            self.ftdb_dao.update(workflow_key=workflow_key, req=req)
            return self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        else:
            return {"Error":"ft_result_model_id not set in the database."}


    async def destroy_finetune_DAC(self,workflow_key: str):
        """
        Step 5 ?
        """
        logger.info(f"destroy_finetune_DAC(workflow_key={workflow_key}) Entry")
        request = self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        if request is None:
            return
        ret= ft.delete_cluster(request=request)
        logger.info(f"destroy_finetune_DAC(workflow_key={workflow_key}) getting state information")
        ret= ft.get_DAC_info(cluster_id=request["dac_cluster_id"])
        if ret is not None:
            request["dac_lifecycle_state"]=ret["lifecycle_state"]
            request["dac_destroy_time"]=datetime.datetime.now()            
            self.ftdb_dao.update(workflow_key=workflow_key, req=request)
        logger.info(f"destroy_finetune_DAC(workflow_key={workflow_key}) Exit")
        return request

    def destroy_finetune_DAC_update(self,workflow_key):
        state= self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        if "dac_cluster_id" in state and state["dac_cluster_id"] is not None and len(state["dac_cluster_id"]) > 0:
            info = ft.get_DAC_info(cluster_id=state["dac_cluster_id"])
            if "dac_error_dtls" not in info:
                req = {
                    "dac_lifecycle_state": info["lifecycle_state"],
                    "dac_error_dtls": ""
                }

                if info["lifecycle_state"] == "DELETED":
                    req["dac_destroy_time"] = info["time_updated"]
                    logger.info(f" {workflow_key} finetune cluster deleted.")
            else:
                req = {
                    "dac_error_dtls": info["dac_error_dtls"]
                }

            self.ftdb_dao.update(workflow_key=workflow_key, req=req)
            return self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        
        return {"Error":"DAC_CLUSTER_ID not set in the database."}


    async def create_hosting_DAC(self,workflow_key: str):
        """
        Step 2.1
        """

        request = {"workflow_key":workflow_key}

        if "compartment_ocid" not in request:
            request["compartment_ocid"]=walkback(confb.config.oci.os.finetune,"compartment_ocid")

        model = self.model_dao.select_purpose(model_purpose="GEN-PURPOSE-LLM")
        db_response = self.ftdb_dao.get_by_key(workflow_key=workflow_key)

        dac_answer = ft.create_hosting_DAC(request=request | db_response)

        dac : DotMap = DotMap(dac_answer)
        if "dac_error_dtls" not in dac_answer:

            # "dac_started_time": dac.dac_started_time            
            model_usage_data={
                "workflow_id": db_response["id"],
                "dac_submit_time": dac.get("dac_submit_time",datetime.datetime.now()),
                "dac_created_time":dac.get("dac_created_time",None),
                "dac_lifecycle_state": dac.get("dac_lifecycle_state",None),
                "dac_cluster_id": dac.get("dac_cluster_id",None),
                "dac_unit_count": dac.get("dac_unit_count",None),
                "dac_unit_shape": dac.get("dac_unit_shape",None),
                "dac_error_dtls": "",
                "model_name_version": model["model_name_version"]+"_"+db_response["ft_version"],
                "model_purpose": model["model_purpose"]
                }
        else:
            model_usage_data={
                "workflow_id": db_response["id"],
                "dac_submit_time": dac.get("dac_submit_time",datetime.datetime.now()),
                "dac_error_dtls": dac_answer["dac_error_dtls"],
                "model_name_version": model["model_name_version"]+"_"+db_response["ft_version"]
                }
        self.model_dao.create(model_usage_data=model_usage_data)
        
        return model_usage_data

    def create_hosting_DAC_update(self,workflow_key):
        wf= self.ftdb_dao.get_by_key(workflow_key=workflow_key)
        model=self.model_dao.select_workflow(workflow_id=wf["id"])

        if model is None:
            return {"dac_error_dtls":"The model has not been registered yet."}

        if "dac_cluster_id" in model and model["dac_cluster_id"] is not None and len(model["dac_cluster_id"]) > 0:
            info = ft.get_DAC_info(cluster_id=model["dac_cluster_id"])
            if "dac_error_dtls" not in info:
                req = {
                    "dac_unit_count": info["unit_count"],
                    "dac_unit_shape": info["unit_shape"],
                    "dac_lifecycle_state": info["lifecycle_state"],
                    "dac_error_dtls": ""
                }

                if info["lifecycle_state"] == "ACTIVE":
                    req["dac_started_time"] = info["time_updated"]

                if info["lifecycle_state"] == "CREATING":
                    req["dac_created_time"] = info["time_updated"]

            else:
                req = {
                    "dac_error_dtls": info["dac_error_dtls"]
                }

            self.model_dao.update(model_usage_data=model)
            return model
        
        return {"Error":"HOSTING DAC_CLUSTER_ID not set in the database."}

    def deploy_finetune_model(self, workflow_key:str):
        """
        1. No update in the finetune workflow table
        2. Updates in the model usage table
        2.0 Read the old newest row (MODEL_PURPOSE='GEN_PURPOSE_LLM')
        2.1 Create new row (set workflow.id, ft_result_model_id, ft_version)
        2.1.0 Set the newest row of (MODEL_PURPOSE,MODEL_SRC,MODEL_NAME,DAC_CLUSTER_ID) from the old row
        2.1.1 Set the usage_start as now
        2.1.2 Set the endpoint_ocid as endpoint_ocid
        2.2 In the old rows (MODEL_PURPOSE='GEN_PURPOSE_LLM') where the usage stop is null
        2.2.1 set the usage stop to now
        """

        ft_data = self.ftdb_dao.get_by_key(workflow_key=workflow_key)

        old_model = self.model_dao.select_purpose(model_purpose="GEN-PURPOSE-LLM")
        old_model["usage_stop"]=datetime.datetime.now()
        
        req = {}
        req["compartment_ocid"]=confb.config.oci.compartment_ocid
        req["model_ocid"]=ft_data["ft_result_model_id"]
        req["cluster_ocid"]=old_model["dac_cluster_ocid"]

        ft.create_endpoint(request=req)

        new_model= {
                "model_purpose":"GEN-PURPOSE-LLM",
                "model_name": old_model["model_name"],
                "model_src":old_model["model_src"],
                "usage_start":datetime.datetime.now(),
                "usage_stop": None,
                "workflow_id": ft["id"],
                "endpoint_ocid": "Not a real one",
                "version":ft["ft_version"],
                "dac_cluster_ocid":old_model["dac_cluster_ocid"]
                }
        self.model_dao.create(model_usage_data=new_model)
        self.model_dao.update(model_usage_id=old_model["id"],model_usage_data=old_model)
        self.model_dao.close()

    def deploy_finetune_model_update(self, workflow_key:str):
        # TODO update the model_usage when the new endpoint is life.
        pass

    def get_trainingdata_history(self,domain):
        dao: ftdb.TrainingDataHistoryDAO = ftdb.TrainingDataHistoryDAO()
        data = dao.read_all(domain)
        return data

def test_process_export_jsonl():
    ft: fine_tune_controller = fine_tune_controller()
    ft.process_export_jsonl()

class administrative_controller:
    def read_config(self):
        output = confb.read_config(os.getenv('NL2SQL_ENV'))
        return output
    
    def reset_config_from_file(self):
        output = "TO BE REDONE" #TODO
        return output

    def read_metadata_os(self):
        print("Administrative_Processor::read_metadata_os")
        output = self.read_metadata_os_fn(confb.config.oci.os.metadata.file_name)
        return output

    def get_os_file(self, fn:str ):
        path: str = f"{os.getenv('NL2SQL_ENV')}/{OS_APEX_EXPORT}"
        output = ocij.download(file_path=path,fn=fn)
        return output
        
    def list_os_file(self, bucket :str, prefix:str  ):
        output = ocij.list_objects(bucket=bucket, prefix=f"{os.getenv('NL2SQL_ENV')}/{prefix}")
        return output

    def put_os_file(self, fn:str, content):
        path: str = f"{os.getenv('NL2SQL_ENV')}/{OS_APEX_EXPORT}"
        output = ocij.put_os_file(path=path, fn=fn, content=content)
        return output

    def read_metadata_os_fn(self,fn:str):
        logger.info("Service_Helper::read_metadata_os")
        return json.load(BytesIO(ocij.download_metadata(fn=fn)))
        
class llm_metrics_controller:
    def get_corrected_sql(self):
        connection = io.db_get_connection()
        ret= io.db_get_corrected_sql(connection=connection)
        connection.close()

        output = {"corrected_sql": ret}
        logger.debug(output)

        return output

    def size_trust_library(self,start_date,end_date,domain):
        logger.info("Service_Helper::size_trust_library")
        return metric.size_trust_library(start_date=start_date,end_date=end_date,domain=domain)

    def percentage_prompts_trust_level(self,start_date,end_date,domain):
        logger.info("Service_Helper::percentage_prompts_trust_level")
        return metric.percentage_prompts_trust_level(start_date=start_date,end_date=end_date,domain=domain)

    def size_trust_library_source(self,start_date,end_date,domain):
        logger.info("Service_Helper::size_trust_library")
        return metric.size_trust_library_source(start_date=start_date,end_date=end_date,domain=domain)
    
    def users_number_prompts_trust_level(self,start_date,end_date,domain):
        logger.info("Service_Helper::users_number_prompts_trust_level")
        return metric.users_number_prompts_trust_level(start_date=start_date,end_date=end_date,domain=domain)

    def users_number_prompts(self,start_date,end_date,domain):
        logger.info("Service_Helper::users_number_prompts")
        return metric.users_number_prompts(start_date=start_date,end_date=end_date,domain=domain)
    
    def users_number(self,start_date,end_date,domain):
        logger.info("Service_Helper::users_number")
        return metric.users_number(start_date=start_date,end_date=end_date,domain=domain)
    
    def accuracy_semitrusted(self,start_date,end_date,domain):
        logger.info("Service_Helper::users_number")
        return metric.accuracy_semitrusted(start_date=start_date,end_date=end_date,domain=domain)

    def accuracy_untrusted(self,start_date,end_date,domain):
        logger.info("Service_Helper::accuracy_untrusted")
        return metric.accuracy_untrusted(start_date=start_date,end_date=end_date,domain=domain)

    def accuracy_by_trust_level(self, start_date, end_date,domain):
        logger.info("Service_Helper::accuracy_by_trust_level")
        return metric.accuracy_by_trust_level(start_date=start_date, end_date=end_date, domain=domain)

    def size_trust_library_user_prompts_trust(self, start_date, end_date,domain):
        logger.info("Service_Helper::size_trust_library_user_prompts_trust")
        return metric.size_trust_library_user_prompts_trust(start_date=start_date, end_date=end_date,domain=domain)

class engine_controller:
    def refresh_autofill_cache(self,previous_last_record_stamp):
        logger.info("Engine_Helper::refresh_autofill_cache")
        return eng.refresh_autofill_cache(previous_last_record_stamp=previous_last_record_stamp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(constants.REST_LAYER)
    confb.setup()