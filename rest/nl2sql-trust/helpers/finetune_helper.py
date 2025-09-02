# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json
import os
import datetime
from dateutil import parser
import sys
import logging
import time
import oci 
from pathlib import Path
import requests
import constants
import requests
import re
import random

from helpers import util as u
from datetime import datetime

from helpers import database_util as io
from helpers import natural_language_util as nl
from helpers.config_json_helper import config_boostrap as confb, walkback_d

from helpers.oci_helper_json import oci_helper as ocij
from helpers.finetune_db import TrainingDataHistoryDAO, FineTuneEvaluationDAO, FineTuneWorkflowDAO

logger = logging.getLogger(constants.FINETUNE_LAYER)

dummy_mode: bool = False

def evaluate_finetune(workflow_key):
    eval_start_time =  datetime.now()
    finetune_workflow_id = 0
    trust_library_end_date = ""

    def convert_training_filename_to_sysdate(filename):
        tmp = filename.split(".")[0]
        day = tmp.split("_")[-2]
        time = tmp.split("_")[-1]
        dt = datetime.strptime(f"{day} {time}", '%d%b%Y %H%M%S')
        return dt.strftime('%d-%b-%Y %I:%M:%S %p')

    connection = io.db_get_connection()

    # step 1: get workflow key and last date to pull records from trust_library
    # note: this date matches date that training data was created and which was used to fine tune this model being evaluated
    connection = io.db_get_connection()

    #TODO: to update to use parametrize query
    statement = f"""
            select 
            w.id as finetune_workflow_id,
            t.filename as filename
            from finetune_workflow w
            left outer join trainingdata_history t on w.training_data_id = t.id
            where workflow_key = '{workflow_key}'
            """
    result_set = io.db_select(connection, statement)

    finetune_workflow_id = result_set[0][0]
    trust_library_end_date = convert_training_filename_to_sysdate(result_set[0][1])

    logger.info(f"finetune_workflow_id:  {finetune_workflow_id}")
    logger.info(f"trust_library_end_date:  {trust_library_end_date}")

    # step 2: get records from trust library and certify_workflow to run evaluation
    #TODO: to update to use parametrize query
    statement = f"""
                select 
                case
                    when c.pass_fail = 'Pass' then 'regression'
                    when c.pass_fail = 'Fail' then 'corrected'
                end as test_type,
                t.prompt_txt, 
                case
                    when c.pass_fail = 'Pass' then t.sql_txt
                    when c.pass_fail = 'Fail' then c.corrected_sql_txt
                end as trust_sql
                from trust_library t
                left outer join certify_state c on t.certify_state_id = c.id
                where t.certified_date < '{trust_library_end_date}'
                and c.pass_fail is not null
                order by t.id 
            """
    result_set = io.db_select(connection, statement)
    connection.close()

    # step 4: get sql from LLM and see if it matches that in trust library
    logger.info(f"starting service.evaluate_finetune with the result set size: {len(result_set)}")
    if len(result_set) == 0:
        logger.info("No results in evaluate_finetune_results to process")
        return {
            "records requested": 0,
            "records processed": 0
            }

    i = 0
    session = requests.Session()
    url = confb.dconfig["oci"]["engine"]["get_sql_url"]

    # process the resultset to include max number of regression type and max number of corrected types
    result_set_regression = []
    result_set_corrected = []
    for result in result_set:
        if result[0] == "regression":
            result_set_regression.append(result)
        if result[0] == "corrected":
            result_set_corrected.append(result)
    
    logger.debug(f"service.evaluate_finetune: original number of regression cases = {len(result_set_regression)}")
    logger.debug(f"service.evaluate_finetune: original number of corrected cases = {len(result_set_corrected)}")

    #TODO these two values should be in config file
    max_regression = confb.dconfig["oci"]["finetune"].get("max_regression",100)
    max_corrected  = confb.dconfig["oci"]["finetune"].get("max_corrected",100)
    result_set_final = []
    if len(result_set_regression) > max_regression:
        random.shuffle(result_set_regression)
        logger.debug(f"service.evaluate_finetune: number of regression cases reduced to {len(result_set_regression[:max_regression])}")
    result_set_final.extend(result_set_regression[:max_regression])
    
    if len(result_set_corrected) > max_corrected:
        random.shuffle(result_set_corrected)
        logger.debug(f"service.evaluate_finetune: number of regression cases reduced to {len(result_set_regression[:max_corrected])}")
    result_set_final.extend(result_set_corrected[:max_corrected])

    ftwf_dao = FineTuneWorkflowDAO()
    fteval_dao = FineTuneEvaluationDAO()
    wf = ftwf_dao.get_by_key(workflow_key=workflow_key)
    if ("eval_start_time" not in wf or wf["eval_start_time"] is None):
        req={"eval_start_time":eval_start_time}
        ftwf_dao.update(workflow_key=workflow_key,req=req)

    # step 4: get sql from LLM and see if it matches that in trust library.  insert to db
    for result in result_set_final:
        i = i + 1
        item_dict = {}
        item_dict["finetune_workflow_id"] = finetune_workflow_id
        item_dict["eval_category"] = result[0]
        item_dict["prompt_txt"] = result[1]
        item_dict["sql_trust_library"] = u.clean_sql(result[2])
        item_dict["sql_llm_generated"] = ""
        item_dict["is_accurate"] = 0
        item_dict["sql diff"] = ""

        # run prompt against nl2sql llm
        prompt = item_dict["prompt_txt"]

        if ("id" not in wf):
            logger.error(f"workflow {workflow_key} is not found.")
            return {"state":"error","Message":f"workflow {workflow_key} is not found."}
        try:
            logger.debug(f"service.evaluate_finetune: [{i}] dictionary BEFORE llm call: {item_dict}")
            print(f"dictionary BEFORE llm call: {item_dict}")

            # show dealer names and addresses
            item_dict["llm_start_time"] = datetime.now()

            with session.post(url, json={"question": prompt}) as response:
                if response.status_code != 500:
                    logger.info(f"[{i}] {response.text}")
                    r = json.loads(response.text)
                    item_dict["sql_llm_generated"] = u.clean_sql(r.get("query",""))
                    item_dict["llm_end_time"] = datetime.now()
                    item_dict["sql diff"] = nl.generate_diff_string(item_dict["sql_trust_library"], item_dict["sql_llm_generated"])
                    item_dict["is_accurate"] = 1 if item_dict["sql diff"] == "=" else 0
                    item_dict["finetune_workflow_id"] = wf["id"]
                    logger.info(f"dictionary AFTER llm call: {item_dict}")

                    fteval_dao.create(data=item_dict)

                    logger.debug(f"evaluate finetune: [{i}] dictionary AFTER llm call: {item_dict}")

                else:
                    print(f"error with engine service: {url} {response.status_code}")
                    break
        except requests.exceptions.RequestException as e:
            # Catch all request-related exceptions (e.g., network issues, timeouts)
            print(f"An error occurred: {e}")

    logger.debug(f"service.evaluate_finetune completed llm sql generation on {i} requests.")

    eval_end_time = datetime.now()
    logger.debug(f"service.evaluate_finetune updating finetune_workflow: eval_start_time={eval_start_time}, eval_end_time={eval_end_time}")

    if (len(result_set_final) == i):
        req={"eval_end_time":eval_end_time}
        ftwf_dao.update(workflow_key=workflow_key,req=req)

    output = {
        "records requested": len(result_set_final),
        "records processed": i
    }
    logger.info(output)

    return output
    
def process_export_jsonl( ):

    connection = io.db_get_connection()
    statement = """
                select prompt_txt, sql_txt from trust_library order by id
                """
    result_set = io.db_select(connection, statement)
    logger.debug("**")
    logger.debug(result_set)

    jsonl_list = []
    file_contents = ""

    for result in result_set:
        user_prompt = result[0]
        sql = result[1]

        response = requests.post(f'{confb.dconfig["oci"]["engine"]["llm_prompt_url"]}', json={"question": user_prompt})
        nl2sql_prompt = response.text.replace("{", "").replace("}", "")
        jsonl_list.append([nl2sql_prompt, sql])

    file_contents = ""

    for jsonl in jsonl_list:
        prompt = jsonl[0].replace('"',"'").replace(chr(10), ' ')
        sql = jsonl[1].replace(chr(10), ' ')
        file_contents += f'{{"prompt":"{prompt}","completion":"{sql};"}}\n'.expandtabs(4)

    logger.debug(file_contents)

    now = datetime.now()
    filename = f'fine_tune_{now.strftime(confb.dconfig["app"]["datetime_format_nospace"])}.jsonl'

    obj_store_dir = os.getenv("NL2SQL_ENV")+"/"+confb.dconfig["oci"]["os"]["finetune"]["os_path"]
    obj_store_filepath = f'{obj_store_dir}{filename}'

    logger.info(f'writing jsonl: {obj_store_filepath}, object size: {sys.getsizeof(file_contents)}')
    local_filename= f'{confb.dconfig["oci"]["os"]["finetune"]["local_path"]}/{filename}'
    local_absolute_fn = Path(local_filename).resolve()
    
    with open(local_filename, 'w') as file:
        file.write(file_contents) 
    # oci_helper.upload(bucket_name=oci_helper.bucket_name, filename=obj_store_filepath, object_body=file_contents)
    logger.info(f'FT: BN={confb.dconfig["oci"]["os"]["finetune"]["bucket"]}, LF={local_absolute_fn}, OSF={obj_store_filepath}')
    ocij.large_upload(bucket_name=confb.dconfig["oci"]["os"]["bucket"], local_filename=local_absolute_fn,os_filename=obj_store_filepath)
    
    if not confb.dconfig["oci"]["finetune"]["keep_local_jsonl"]:
        os.remove(f"{local_absolute_fn}")

    output = {
             "records": len(jsonl_list),
             "path": obj_store_dir,
             "filename": obj_store_filepath
             }
    TrainingDataHistoryDAO().create(record_count=output["records"],path=obj_store_dir, filename = filename)

    logger.info(f" Return of the export_jsonl {output}")
    
    #TODO: SQL Path in the OS of the file, record count, creation time field (process completion) , (in sql)

    return output

def delete_cluster(request):
    if dummy_mode:
        return d_delete_cluster(request=request)
    else:
        return r_delete_cluster(request=request)
    
def d_delete_cluster(request):
    time.sleep(10)
    return request

def r_delete_cluster(request):
    if request is None:
        logger.error("Delete_Finetuning_cluster No request data in r_delete_cluster")
        return
    if "dac_cluster_id" not in request:
        logger.error("Delete_Finetuning_cluster No dac_cluster_id in the request for r_delete_cluster")
        return

    logger.info(f"Delete_Finetuning_cluster ({request['dac_cluster_id']})::Entry")
    generative_ai_client = ocij.get_llm_dac_client( )
    delete_dedicated_ai_cluster_response = generative_ai_client.delete_dedicated_ai_cluster(
        dedicated_ai_cluster_id= request["dac_cluster_id"]
    )
    # Get the data from response
    logger.info(f"Delete_Finetuning_cluster headers {delete_dedicated_ai_cluster_response.headers}")
    logger.info(f"Delete_Finetuning_cluster data {delete_dedicated_ai_cluster_response.data}")
    logger.info("Delete_Finetuning_cluster::Exit")
    return delete_dedicated_ai_cluster_response.data

def get_DAC_info(cluster_id:str = "ocid1.generativeaidedicatedaicluster.oc1.us-chicago-1.amaaaaaawe6j4fqa6hmorui2zxdcrqjljamwjp7u3olbxzwafiohiwqwhsga"):

    logger.info(f"get_DAC_info for {cluster_id}::Entry")
    generative_ai_client = ocij.get_llm_dac_client()
    get_dedicated_ai_cluster_response = generative_ai_client.get_dedicated_ai_cluster(dedicated_ai_cluster_id=cluster_id)
    # Get the data from response
    logger.info(get_dedicated_ai_cluster_response.data)
    x=json.loads(f"{get_dedicated_ai_cluster_response.data}")
    y = x
    if "time_created" in x: y["time_created"] = parser.parse(x["time_created"])
    if "time_updated" in x: y["time_updated"] = parser.parse(x["time_updated"])
    
    return y

def create_finetune_DAC(request):
    if dummy_mode:
        return d_create_finetune_DAC(request=request)
    else:
        return r_create_finetune_DAC(request=request)
    
def d_create_finetune_DAC(request):
    time.sleep(10)
    req ={
        "dac_created_time":datetime.datetime.now(),
        "dac_lifecycle_state": "Created",
        "dac_cluster_id": "ocid_cluster_id",
        "dac_error_dtls": None,
        "dac_unit_count": confb.dconfig["oci"]["finetune"]["unit_count"],
        "dac_unit_shape": confb.dconfig["oci"]["finetune"]["unit_shape"],
        "dac_started_time": None
        }
    return req

def r_create_finetune_DAC(request):
    """
    oci generative-ai dedicated-ai-cluster create \
        --compartment-id ocid1.compartment.oc1..aaaaaaaachueq7lxeibh64towzx5zqa4r7yljyve6zyy4yzbckynucyr3jpq \
        --type FINE_TUNING --unit-count 2 --unit-shape LARGE_GENERIC --display-name test_02    
    """
    #--- CREATE DEDICATED AI CLUSTER for FINETUNING
    # Send the request to service, some parameters are not required, see API
    # doc for more info

    logger.info(f"Create_Finetuning_cluster::Entry {request}")
    print(f"Create_Finetuning_cluster::Entry {request}")
    generative_ai_client = ocij.get_llm_dac_client( )
    ret = {}
    try:
        create_dedicated_ai_cluster_response = generative_ai_client.create_dedicated_ai_cluster(
            create_dedicated_ai_cluster_details=oci.generative_ai.models.CreateDedicatedAiClusterDetails(
                display_name=request.get("workflow_key",""),
                type="FINE_TUNING",
                compartment_id=walkback_d(confb.dconfig["oci"]["ai"],"compartment_ocid"),
                freeform_tags={'NL2SQL_Env': os.getenv("NL2SQL_ENV")},
                unit_count=request.get("unit_count",""),
                unit_shape=request.get("unit_shape","")
        )
        )

        # Get the data from response
        logger.info("Create_Finetuning_cluster::AfterTheCreation")
        logger.debug(create_dedicated_ai_cluster_response.data)
        dac = json.loads(f"{create_dedicated_ai_cluster_response.data}")
        
        # The following must adhere to the finetune_workflow table column names.

        # "dac_error_dtls": dac.dac_error_dtls,
        # "dac_started_time": dac.dac_started_time

        ret ={
            "dac_created_time":parser.parse(dac.get("time_created","")),
            "dac_lifecycle_state": dac.get("lifecycle_state",""),
            "dac_cluster_id": dac.get("id",""),
            "dac_unit_count": dac.get("unit_count",""),
            "dac_unit_shape": dac.get("unit_shape",""),
            "dac_submit_time":datetime.datetime.now()
            }
    except oci.exceptions.ServiceError as x:
        ret ={
            "dac_error_dtls": x.message,
            }

    logger.info(f"create_finetune_DAC return : {ret}")
    return ret

def create_model_details(request):
    if dummy_mode:
        return d_create_model_details(request=request)
    else:
        return r_create_model_details(request=request)

def d_create_model_details(request):
    time.sleep(10)
    return request

def r_create_model_details(request):
    logger.info(f"Create_Model_Details::Entry {request}")

    #--- CREATE MODEL DETAILS
    ret = {}
    try:
        generative_ai_client = ocij.get_llm_dac_client( )

        create_model_response = generative_ai_client.create_model(
            create_model_details=oci.generative_ai.models.CreateModelDetails(
                compartment_id=request.get("compartment_ocid", ""),
                base_model_id=request.get("ft_base_model_ocid", ""),
                fine_tune_details=oci.generative_ai.models.FineTuneDetails(
                    training_dataset=oci.generative_ai.models.ObjectStorageDataset(
                        dataset_type=request.get("dataset_type", ""),
                        namespace_name=request.get("namespace", ""),
                        bucket_name=request.get("bucket", ""),
                        object_name=request.get("object_name", ""),
                    ),
                    dedicated_ai_cluster_id=request.get("cluster_ocid", ""),
                    training_config=oci.generative_ai.models.TFewTrainingConfig(
                        training_config_type=request.get("training_type", ""),
                    )
                )
            )
        )


        # Get the data from response
        logger.info(create_model_response.data)
        ft = json.loads(f"{create_model_response.data}")
        
        # The following must adhere to the finetune_workflow table column names.

        # "ft_error_dtls": ft.dac_error_dtls,
        # "ft_started_time": ft.dac_started_time

        ret ={
            "ft_created_time":parser.parse(ft.time_created),
            "ft_lifecycle_state": ft.lifecycle_state,
            "ft_base_model_id": ft.base_model_id,
            "ft_result_model_id": ft.id,
            "ft_type": ft.type,
            "ft_version": ft.version,
            "ft_submit_time":datetime.datetime.now()
            }
    except oci.exceptions.ServiceError as x:
        logger.error("*****************************")
        logger.error("*****************************")
        logger.error("*****************************")
        logger.error(x)
        ret ={
            "ft_submit_time":datetime.datetime.now(),
            "ft_error_dtls": x.message
            }
    return ret

def get_model_info(model_id):
    #get status of model creation - Gets information about a custom model.
    if model_id is None:
        return None
    
    generative_ai_client = ocij.get_llm_dac_client( )
    get_model_response = generative_ai_client.get_model(model_id=model_id)

    logger.info(get_model_response.data)
    x=json.loads(f"{get_model_response.data}")
    y = x
    if "time_created" in x: y["time_created"] = parser.parse(x["time_created"])
    if "time_updated" in x: y["time_updated"] = parser.parse(x["time_updated"])
    
    return y

def create_hosting_DAC(request=
        {
        "compartment_ocid":"<comp-ocid>",
        "display_name":"Endpoint-OracleAskData",
        "cluster_type":"HOSTING",
        "unit_count":1,
        "unit_shape":"LARGE_GENERIC"
        }
    ):
    if dummy_mode:
        return d_create_hosting_DAC(request=request)
    else:
        return r_create_hosting_DAC(request=request)

def d_create_hosting_DAC(request):
    time.sleep(10)
    return request

def r_create_hosting_DAC(request):
    """
    oci generative-ai dedicated-ai-cluster create \
        --compartment-id ocid1.compartment.oc1..xxx \
        --type HOSTING --unit-count 1 --unit-shape LARGE_GENERIC --display-name test_02    
    """
    #--- CREATE DEDICATED AI CLUSTER for FINETUNING
    # Send the request to service, some parameters are not required, see API
    # doc for more info


    logger.info(f"Create_hosting_DAC::Entry {request}")
    print(f"Create_hosting_DAC::Entry {request}")
    generative_ai_client = ocij.get_llm_dac_client( )
    ret = {}
    try:
        create_dedicated_ai_cluster_response = generative_ai_client.create_dedicated_ai_cluster(
            create_dedicated_ai_cluster_details=oci.generative_ai.models.CreateDedicatedAiClusterDetails(
                display_name=request.get("workflow_key",""),
                type="HOSTING",
                compartment_id=walkback_d(confb.dconfig["oci"]["ai"],"compartment_ocid"),
                freeform_tags={'NL2SQL_Env': os.getenv("NL2SQL_ENV")},
                unit_count=request.get("unit_count",""),
                unit_shape=request.get("unit_shape",""))
        )

        # Get the data from response
        logger.info("Create_Hosting_DAC::AfterTheCreation")
        logger.debug(create_dedicated_ai_cluster_response.data)
        dac = json.loads(f"{create_dedicated_ai_cluster_response.data}")
        
        # The following must adhere to the finetune_workflow table column names.

        # "dac_error_dtls": dac.dac_error_dtls,
        # "dac_started_time": dac.dac_started_time

        ret ={
            "dac_created_time":parser.parse(dac.get("time_created","")),
            "dac_lifecycle_state": dac.get("lifecycle_state",""),
            "dac_cluster_id": dac.get("id",""),
            "dac_unit_count": dac.get("unit_count",""),
            "dac_unit_shape": dac.get("unit_shape",""),
            "dac_submit_time":datetime.datetime.now()
            }
    except oci.exceptions.ServiceError as x:
        ret ={
            "dac_error_dtls": x.message,
            }

    logger.info(f"create_finetune_DAC return : {ret}")
    return ret



def create_endpoint(request=
        {
        "compartment_ocid":"<comp-ocid>",
        "model_ocid":"ocid1.generativeaimodel.oc1.us-chicago-1.xxx",
        "cluster_ocid":"ocid1.generativeaidedicatedaicluster.oc1.us-chicago-1.xxx"
        }
        ):
    if dummy_mode:
        return d_create_endpoint(request=request)
    else:
        return r_create_endpoint(request=request)

def d_create_endpoint(request):
    time.sleep(10)
    return request

def r_create_endpoint(request):
    logger.info("Create_Endpoint::Entry")
    #--- CREATE ENDPOINT DETAILS
    generative_ai_client = ocij.get_llm_dac_client( )
    create_endpoint_response = generative_ai_client.create_endpoint(
        create_endpoint_details=oci.generative_ai.models.CreateEndpointDetails(
            compartment_id=request.get("compartment_ocid",""),
            model_id=request.get("model_ocid",""),
            dedicated_ai_cluster_id=request.get("cluster_ocid","")))

    # Get the data from response
    logger.info(create_endpoint_response.data)
    return create_endpoint_response.data


def test_create_real_DAC():
    req = {
            "workflow_key":"test_key_01_1",
            "unit_count":2,
            "unit_shape":"LARGE_GENERIC"
        }    

    r_create_finetune_DAC(request=req)

def test_create_model():

    req = {
        "compartment_ocid":walkback_d(confb.dconfig["oci"]["ai"],"compartment_ocid"),
        "ft_base_model_ocid":confb.dconfig["oci"]["finetune"]["base_model_id"],
        "dataset_type":confb.dconfig["oci"]["finetune"]["dataset_type"],
        "namespace": confb.dconfig["oci"]["namespace"],
        "bucket": walkback_d(confb.dconfig["oci"]["os"]["finetune"],"bucket"),
        "object_name":os.getenv("NL2SQL_ENV","nothing")+"/"+confb.dconfig["oci"]["os"]["finetune"]["os_path"]+"fine_tune_11Apr2025_173806.jsonl",
        "cluster_ocid":"<cluster-id>",
        "training_type":confb.dconfig["oci"]["finetune"]["training_dataset"]["training_config_type"]
        }
    
    r_create_model_details(request=req)

def test_get_model_info():

    get_model_info(model_id=confb.dconfig["oci"]["finetune"]["base_model_id"])

def test_DAC_return():
    ret = {
    "compartment_id": "ocid1.compartment.oc1..xxx",
    "defined_tags": {
        "Oracle-Tags": {
        "CreatedBy": "",
        "CreatedOn": ""
        }
    },
    "display_name": "Key150_15Apr2025_131134",
    "freeform_tags": {
        "NL2SQL_Env": "xxx"
    },
    "id": "ocid1.generativeaidedicatedaicluster.oc1.us-chicago-1.xxx",
    "lifecycle_details": "Creating",
    "lifecycle_state": "CREATING",
    "system_tags": {},
    "time_created": "",
    "time_updated": "",
    "type": "FINE_TUNING",
    "unit_count": 2,
    "unit_shape": "LARGE_GENERIC"
    }

    print(ret)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG, force=True)
    confb.setup()
    #test_create_model()
    test_get_model_info()
    test_DAC_return()
