# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import os
import json
import subprocess
import re
import shlex
import time
import random
import ads
import sys
from ads.model.deployment import ModelDeployment

#TODO: Put the environment variables in a config class 
#TODO: Use the authentication information from a config class
#TODO: Transfer the config.json into the /conf subdirectory and rename llm_config.json
#TODO: Replace the prints with loggger.info statements
#TODO: Refactor the script into a class based application
#TODO: use a __main__ entry point

compartment_id=os.environ.get('NB_SESSION_COMPARTMENT_OCID')
print("NB session compartment ocid: ",compartment_id)
json_file_path="cli/config.json"
with open(json_file_path, 'r') as file:
    config = json.load(file)


ERROR_EXIT_CODE="ERROR:ads"


ads.set_debug_mode()
# ads.set_auth("security_token")
ads.set_auth(auth="resource_principal", config={"region": "us-phoenix-1"})

model_deployments=ModelDeployment.list(status="ACTIVE",compartment_id=compartment_id)
print("model_deployments list length: ",len(model_deployments))
print(f"Number of ACTIVE model deployments to be deleted in {compartment_id} : {len(model_deployments)}")
for md in model_deployments:
    current_md = ModelDeployment.from_id(md.id)
    current_md.delete(wait_for_completion=False)

gemma_2b_it_md_id=None
phi3_md_id=None


def run_command(command_string,**kwargs):
    if kwargs:
        command_string=command_string.format(**kwargs)
    print(f"Running command: {command_string}")
    command_string = shlex.split(command_string)
    result = subprocess.run(command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    return output

def update_test_result(result, test_name, err):
    result[test_name]=True if 'ERROR' not in err else False

def print_summary(test_suite, result_array):
    print("Test results summary")
    for test in test_suite.items():
        if result_array[test[0]]:
            print(f"{test[0]}: PASSED ✅")
        else:
            print(f"{test[0]}: FAILED ❌")

def get_id(output):
    match = re.search(r'(?<!_)id["\']?\s*[:=]\s*["\']?([^"\'}]+)["\']?', output)
    if match:
        id = match.group(1)
        print(f"Extracted ID: {id}")
        return id
    else:
        print("ID not found in the output.")

def get_md_state(output):
    match = re.search(r"['\"]?state['\"]?\s*[:=]\s*['\"]?([^'\"}]+)['\"]?", output)
    if match:
        state = match.group(1)
        return state
    else:
        print("State not found in the output.")

def get_eval_state(output):
    match = re.search(r"['\"]?lifecycle_state['\"]?\s*[:=]\s*['\"]?([^'\"}]+)['\"]?", output)
    if match:
        state = match.group(1)
        return state
    else:
        print("Eval lifecycle_state not found in the output.")

def get_ft_status(output):
    match = re.search(r"['\"]?lifecycle_state['\"]?\s*[:=]\s*['\"]?([^'\"}]+)['\"]?", output)
    if match:
        state = match.group(1)
        return state
    else:
        print("lifecycle_state not found in the output.")

def exponential_backoff(base_delay, max_delay):
    delay = base_delay
    while True:
        yield delay
        delay = min(max_delay, delay * 2 + random.uniform(0, 1))

def poll_ft_status(id):
    backoff_generator=exponential_backoff(base_delay=5,max_delay=60)
    status=None
    while status not in ['ACTIVE','FAILED']:
        try:
            get_ft_response=run_command(f'ads aqua model get {id}')
            status=get_ft_status(get_ft_response)
            if status not in ['ACTIVE','FAILED']:
                print(f"Current status: {status}. Polling again...")
                time.sleep(next(backoff_generator))
            else:
                print(f"Terminal status: {status}")
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(next(backoff_generator))
    return status

def poll_md_status(id):
    backoff_generator = exponential_backoff(base_delay=5, max_delay=60)
    status = None

    while status not in ["ACTIVE", "FAILED"]:
        try:
            get_md_response = run_command(f'ads aqua deployment get {id}')
            status = get_md_state(get_md_response)

            if status not in ["ACTIVE", "FAILED"]:
                print(f"Current status: {status}. Polling again...")
                time.sleep(next(backoff_generator))
            else:
                print(f"Terminal status: {status}")

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(next(backoff_generator))
    return status

def poll_eval_status(id):
    backoff_generator = exponential_backoff(base_delay=5, max_delay=60)
    status = None

    while status not in ["SUCCEEDED", "FAILED"]:
        try:
            get_eval_response = run_command(f'ads aqua evaluation get {id}')
            status = get_eval_state(get_eval_response)
            if status not in ["SUCCEEDED", "FAILED"]:
                print(f"Current status: {status}. Polling again...")
                time.sleep(next(backoff_generator))
            else:
                print(f"Terminal status: {status}")

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(next(backoff_generator))
    return status

SERVICE_MODELS_LIST = "SERVICE_MODELS_LIST"
AQUA_MODEL_DEPLOYMENT_LIST = "AQUA_MODEL_DEPLOYMENT_LIST"
AQUA_EVAL_LIST = "AQUA_EVAL_LIST"

REGISTER_DEFOG_SQLCODER_2_7B_HF="REGISTER_DEFOG_SQLCODER_2_7B_HF"
DEPLOY_DEFOG_SQLCODER_2_7B_HF="DEPLOY_DEFOG_SQLCODER_2_7B_HF"
FINE_TUNE_SQLCODER_7b_MODEL="FINE_TUNE_SQLCODER_7b_MODEL"
EVALUATE_SQLCODER_7b_GGUF="EVALUATE_SQLCODER_7b_GGUF"

test_suite={
    SERVICE_MODELS_LIST:"ads aqua model list",

    AQUA_MODEL_DEPLOYMENT_LIST:"ads aqua deployment list",

    AQUA_EVAL_LIST:"ads aqua evaluation list",

    REGISTER_DEFOG_SQLCODER_2_7B_HF: f"ads aqua model register --model defog/sqlcoder-7b-2-hf --os_path {config['register-model-bucket-output-location']} --download_from_hf True --inference-container odsc-vllm-serving --compartment_id {compartment_id}",

    DEPLOY_DEFOG_SQLCODER_2_7B_HF:"ads aqua deployment create --model-id {sqlcoder_7b_hf_id} --instance-shape {instance_shape} --display-name {display_name}",

    FINE_TUNE_SQLCODER_7b_MODEL:f"ads aqua fine_tuning create --ft_source_id {config['sqlcoder-7b-2-hf']} --ft_name sqlcoder-7b-2-hf-FT --dataset_path {config['ft-dataset-path']} --report-path {config['ft-report-path']} --ft_parameters '{{\"epochs\": 5, \"learning_rate\": 0.0002}}' --shape_name VM.GPU.A10.1 --replica 1 --validation_set_size 0.4 --experiment-name aqua_test_experiment_ft",

    EVALUATE_SQLCODER_7b_GGUF: "ads aqua evaluation create  --evaluation_source_id {evaluation_source_id} --evaluation_name {evaluation_name} --dataset_path {dataset_path} --report_path {report_path} --model-parameters '{{\"max_tokens\":500,\"temperature\":0.5,\"top_p\":0.99,\"top_k\":50}}' --shape_name VM.Standard.E4.Flex --block_storage_size 50 --metrics '[{{\"name\":\"bertscore\",\"args\":{{}}}}, {{\"name\":\"rouge\",\"args\":{{}}}}]' --experiment-name {experiment_name}"
}

result_array={
    SERVICE_MODELS_LIST:False,
    AQUA_MODEL_DEPLOYMENT_LIST:False,
    AQUA_EVAL_LIST:False,
    REGISTER_DEFOG_SQLCODER_2_7B_HF:False,
    DEPLOY_DEFOG_SQLCODER_2_7B_HF:False,
    FINE_TUNE_SQLCODER_7b_MODEL:False,
    EVALUATE_SQLCODER_7b_GGUF:False,
}


# Listing response tests
output=run_command(test_suite[SERVICE_MODELS_LIST])
update_test_result(result_array,SERVICE_MODELS_LIST,output)
output=run_command(test_suite[AQUA_MODEL_DEPLOYMENT_LIST])
update_test_result(result_array,AQUA_MODEL_DEPLOYMENT_LIST,output)
output=run_command(test_suite[AQUA_EVAL_LIST])
update_test_result(result_array,AQUA_EVAL_LIST,output)

# Register defog/sqlcoder-7b-2-hf
output=run_command(test_suite[REGISTER_DEFOG_SQLCODER_2_7B_HF])
update_test_result(result_array,REGISTER_DEFOG_SQLCODER_2_7B_HF,output)
sqlcoder_7b_hf_id=get_id(output)

# Deploy defog/sqlcoder-7b-2-hf
if sqlcoder_7b_hf_id:
    output=run_command(test_suite[DEPLOY_DEFOG_SQLCODER_2_7B_HF],
                       sqlcoder_7b_hf_id=sqlcoder_7b_hf_id,
                       instance_shape="VM.GPU.A10.1",
                       display_name="automated-test-sqlcoder-7b-2-hf-md")
    if ERROR_EXIT_CODE in output:
        update_test_result(result_array,DEPLOY_DEFOG_SQLCODER_2_7B_HF,'ERROR')
    else:
        sqlcoder_7b_2_hf_md=get_id(output)
        status=poll_md_status(sqlcoder_7b_2_hf_md)
        if status in ["ACTIVE","FAILED"]:
            update_test_result(result_array,DEPLOY_DEFOG_SQLCODER_2_7B_HF, '' if status=='ACTIVE' else 'ERROR')

# Fine tune defog/sqlcoder-7b-2-hf model
output=run_command(test_suite[FINE_TUNE_SQLCODER_7b_MODEL])
if ERROR_EXIT_CODE in output:
    print("Some Error occurred while finetuning sqlcoder-7b-2 model: ",output)
    update_test_result(result_array,FINE_TUNE_SQLCODER_7b_MODEL,'ERROR')
else:
    sqlcoder_7b_2_ft_id=get_id(output)
    status=poll_ft_status(sqlcoder_7b_2_ft_id)
    if status in ["ACTIVE", "FAILED"]:
        update_test_result(result_array,FINE_TUNE_SQLCODER_7b_MODEL,'' if status=='ACTIVE' else 'ERROR')

# Run evaluation for defog/sqlcoder-7b-2-hf MD
if sqlcoder_7b_2_ft_id:
    output=run_command(test_suite[EVALUATE_SQLCODER_7b_GGUF],
                       evaluation_source_id=sqlcoder_7b_2_ft_id,
                       evaluation_name="automated_test_sqlcoder_7b_2_ft_id_eval",
                       dataset_path=config['eval-dataset-path'],
                       report_path=config['eval-report-path'],
                       experiment_name=config['experiment'])
    if ERROR_EXIT_CODE in output:
        print("Error in running evaluation for sqlcoder_7b_2_ft_id model deployment: ", output)
        update_test_result(result_array,EVALUATE_SQLCODER_7b_GGUF,'ERROR')
    else:
        sqlcoder_7b_2_gguf_eval_id=get_id(output)
        status=poll_eval_status(sqlcoder_7b_2_gguf_eval_id)
        if status in ["SUCCEEDED", "FAILED"]:
            update_test_result(result_array,EVALUATE_SQLCODER_7b_GGUF,'' if status == 'SUCCEEDED' else 'ERROR')

# Print test summary
print_summary(test_suite,result_array)

if any(not value for value in result_array.values()):
    print("Error: Some test(s) did not run successfully.")
    sys.exit(1)