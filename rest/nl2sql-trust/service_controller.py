# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import asyncio
import datetime
from dateutil import parser
from io import BytesIO
import json
import os
import re
import concurrent
import time
from fastapi import HTTPException
import requests
import logging

import constants
from constants import TEST_DATA_PATH,OS_APEX_EXPORT

from helpers.oci_helper_json import oci_helper as ocij
from helpers.config_json_helper import config_boostrap as confb
from helpers.config_json_helper import walkback_d


from helpers import util as u
from helpers import database_util as io
from helpers import schema as sc
from helpers import natural_language_util as nl
from helpers import operations_helper as ops
from helpers import trust_metrics as metric
from helpers import engine as eng
from helpers import llm_helper as llm

logger = logging.getLogger(constants.SERVICE_LAYER)

class bootstrap_controller:
    process_sql_results = []

    def process_auto(self,domain):
        source = 'auto'
        sorted_list = []

        
        schema = sc.load_schema(f'{constants.CONF_PATH}/{confb.dconfig["oci"]["os"]["metadata"]["file_name"]}')
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

    # def multithreaded_process_one_sql(self,connection,result):

    #     # run prompt against nl2sql llm
    #     prompt = result[1]
    #     url = confb.dconfig["oci"]["engine"]["llm_prompt_url"]
    #     #url = conf.engine_config.llm_prompt_url
    #     response = requests.post(url, json={"question": prompt})
        
    #     logger.debug(response.text)

    #     r : dict = json.loads(response.text)
    #     sql = u.clean_sql(sql=r.get("query",""))

    #     # run check to see if it parses. if not, E is prepopulated in column for expert to pass/fail in manual workflow (given no E)
    #     tmp = None
    #     sql_parse_result = io.db_sql_parse(connection, sql)
    #     if sql_parse_result == "0":
    #         tmp = ["", ""]
    #     else:
    #         tmp = ["E", sql_parse_result]
    #     row =[str(result[0]), sql, tmp[0], tmp[1]]

    #     logger.debug(row)
    #     logger.debug("completed parse sql checks")

    #     # update db
    #     logger.debug("Starting updates")
    #     # db(N)
    #     io.db_update_process_sql_row(connection, row)

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
        url = confb.dconfig["oci"]["engine"]["get_sql_url"]
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
                        r :dict = json.loads(response.text)
                        sql = clean_sql(sql=r.get("query",""))
                        # run check to see if it parses. if not, E is prepopulated in column for expert to pass/fail in manual workflow (given no E)
                        tmp = None
                        parse_sql: bool = confb.dconfig.get("oci",False).get("engine",False).get("sqlparse",False).get("enable",False)
                        tmp = ["", ""]
                        if parse_sql:
                            sql_parse_result = io.db_sql_parse(connection, sql)
                            if sql_parse_result != "0":
                                tmp = ["E", sql_parse_result]
                        # sql_parse_result = io.db_sql_parse(connection, sql)
                        # if sql_parse_result == "0":
                        #     tmp = ["", ""]
                        # else:
                        #     tmp = ["E", sql_parse_result]
                        
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
        io.db_process_certify(connection=connection, record_list=data, control=control, domain=domain)
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

    def process_users_lc(self, domain):
        source = 'users'
        connection = io.db_get_connection()

        ## id, execution_date, certified_score, prompt_tx, prompt_lineage, sql_query, sql_lineage, db_err_text, gen_engine_nm, fb
        statement = """
                    select id, 
                    (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt
                    from execution_log e
                    where is_cert_processed = 0
                    and (is_trusted = 0 or (is_trusted = 1 and (user_feedback_code = -1 or db_error_code is not null)))   
                    and is_authorized = 1   
                    and is_clarify = 0   
                    and is_action = 0
                    and (is_autocertify is null or is_autocertify = 0)
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
    
    def process_users_autocertify(self, domain):
        connection = io.db_get_connection()

        ## 1: get autocertify records to process to certify_state and trust_library
        statement = f""" select 
                            id as user_execution_id,
                            (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt
                        from execution_log e
                        where is_autocertify = 1 
                            and is_cert_processed = 0
                            and is_authorized = 1 
                            and is_clarify = 0 
                            and is_action = 0
                        order by id asc """

        result_set = io.db_select(connection, statement)
        rlen = len(result_set)

        # 2: insert into certify state table
        io.db_insert_process_user_autocertify(connection, result_set)

        # 3: update executed table with id
        io.db_update_executed_prompts_table(connection, result_set)

        output = {"records certify_state": rlen}
        logger.info(output)

        # 4: insert into trust library table and update certify state table
        statement = f"""select 
                        c.id,
                        (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt,
                        e.generated_sql as sql_txt,
                        e.is_parent_corrected,
                        e.template_id,
                        e.user_feedback_code,
                        e.db_error_code
                    from certify_state c
                        join execution_log e on e.id = c.user_execution_id
                    where e.is_autocertify = 1
                        and c.is_cert_proc = 0
                        and e.user_feedback_code != -1
                        and e.db_error_code is null
                    order by c.id asc """

        result_set = io.db_select(connection, statement)
        rlen = len(result_set)

        io.db_process_certify_autocertify(connection, result_set)

        connection.close()

        output = {"records": rlen}
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

class administrative_controller:
    def read_config(self):
        output = confb.read_config(os.getenv('NL2SQL_ENV'))
        return output
    
    def reset_config_from_file(self):
        output = "TO BE REDONE" #TODO
        return output

    def read_metadata_os(self):
        print("Administrative_Processor::read_metadata_os")
        output = self.read_metadata_os_fn(confb.dconfig["oci"]["os"]["metadata"]["file_name"])
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

    # this is a batch update of null duplicate flags for prompts that are waiting to be certified
    # main goal is to run operationally/manually when needed .. primarily when environment is updated to
    # 'prevent-duplicates' capability.  This updates existing data for this capability
    def update_certify_queue_null_duplicate_flags(self, mode):
        logger.info(f"Start bulk update for certify queue for duplicates in trust_library or certify_queue.")
        logger.info(f"mode: {mode}")

        in_string = ""
        match mode:
            case "bootstrap":
                in_string = "'auto', 'upload'"
            case "user":
                in_string = "'user'"
            case _:
                in_string = None
        
        if in_string is None:
            logger.error(f"Mode {mode} not recognized")
            logger.info('{"records": -1}')
            return {"records": -1}
        
        id = 0
        select_cert_queue = f"""
                    select id, prompt_vect
                    from certify_state
                    where prompt_source in ({in_string})
                        and prompt_vect is not null
                        and is_cert_proc = 0
                        and duplicated_tbl_name is null
                    order by id asc
                """

        connection = io.db_get_connection()
        result_set = io.db_select(connection, select_cert_queue)

        logger.info(f"Number of candidate records to possibly update: {len(result_set)}")

        update_count = 0
        row_dict = None
        for row in result_set:
            id = row[0]
            certify_prompt_vect = list(row[1])

            row_dict = io.db_check_duplicate_all_types(connection, certify_prompt_vect, id)

            if row_dict is not None and row_dict["is_duplicate"]:
                update_count += 1

        logger.info(f"Update completed.  Number of records updated: {update_count}")
        connection.close()

        output = {"records": update_count}
        return output






    # this is a batch update of null prompt_vectors in certify_state
    # main goal is to run operationally/manually when needed .. primarily when environment is updated to
    # 'prevent-duplicates' capability.  This updates existing data for this capability
    def update_certify_state_null_prompt_vects(self, mode):
        logger.info(f"Start bulk update for certify_state when prompt_vect is null")
        logger.info(f"mode: {mode}")

        select = ""
        match mode:
            case "bootstrap":
                select = f"""
                            select id, prompt_txt
                            from certify_state
                            where prompt_source in ('auto', 'upload')
                            and prompt_vect is null
                            order by id asc
                        """
            case "user":
                select = f"""
                            select c.id as id,
                                (case when e.convo_seq_num = 1 then e.user_prompt else e.convo_prompt end) prompt_txt
                            from certify_state c 
                                join execution_log e on e.id = c.user_execution_id
                            where prompt_source = 'user'
                                and prompt_vect is null
                            order by id asc
                            """
            case _:
                select = None

        if select is None:
            logger.error(f"Mode {mode} not recognized")
            logger.info('{"records": -1}')
            return {"records": -1}
        
        connection = io.db_get_connection()
        result_set = io.db_select(connection, select)

        logger.info(f"Number of records to update: {len(result_set)}")

        update_count = 0
        try:
            for row in result_set:
                id = row[0]
                prompt = row[1]
                vector = llm.llm_create_str_embedding(prompt)
                vector = json.dumps(vector)

                logger.debug(f"Update prompt_vect: {id}\t{prompt}")
                with connection.cursor() as cursor:
                    update = f"""update certify_state set
                                prompt_vect = :1
                                where id = :2
                        """
                    cursor.execute(update, (vector, id))
                    connection.commit()
                    update_count += 1
        except:
            pass

        logger.info(f"Update completed.  Number of records updated: {update_count}")
        connection.close()

        output = {"records": update_count}
        return output

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
    
    def accuracy_cumulative(self, start_date=None, end_date=None, domain=None):
        logger.info("Service_Helper::Accuracy Cumulative")
        return metric.accuracy_cumulative(start_date=start_date, end_date=end_date,domain=domain)

class engine_controller:
    def refresh_autofill_cache(self,previous_last_record_stamp):
        logger.info("Engine_Helper::refresh_autofill_cache")
        return eng.refresh_autofill_cache(previous_last_record_stamp=previous_last_record_stamp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(constants.REST_LAYER)
    confb.setup()
