# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import asyncio
import os
from fastapi import APIRouter, HTTPException
import logging
import constants
from service_controller import fine_tune_controller as controller
from service_controller import administrative_controller as admin_controller

from helpers.config_json_helper import config_boostrap as confb

logger = logging.getLogger(constants.REST_LAYER)
router = APIRouter()

ctrl : controller = controller()
admin: admin_controller = admin_controller()

def gatekeeper_attribute(request: dict, attr:str):
    if attr not in request:
        raise HTTPException(
            status_code=422,
            detail=f"Missing '{attr}' parameter. It cannot be null."
        )

def gatekeeper_param(param):
    if param is None or len(param) == 0:
        raise HTTPException(
            status_code=422,
            detail=f"Missing '{param}' parameter. It cannot be null."
        )

@router.post("/process_export_jsonl" , tags=["Finetune"])
async def process_export_jsonl( ):
    """
    Export as a json list the finetune request.
    <br><b>Uses the verbose flag for debugging.</b>

    | Parameter| Default | Description  |
    |----------|---------|--------------|
    | None     |  N/A    |              |

    """
    logger.info("Finetune processor export jsonl")
    ret= ctrl.process_export_jsonl()
    logger.info(f" in api {ret}")
    return ret

@router.get("/get_training_history", tags=["Finetune"])
async def get_training_history(domain=None):
    """
    Get the historical information on the files that are generated to be able
    to finetune llms.

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | N/A               |  N/A    |                 N/A                |

    """
    logger.info("Operations save OS file")
    ret= ctrl.get_trainingdata_history(domain=domain)
    logger.info(f" in api {ret}")
    return ret

@router.get("/get_training_files", tags=["Admin Finetune"])
async def get_training_files( ):
    """
    bucket = nl2sql
    prefix = finetune/jsonl/
    no front slash for the prefix
    """
    logger.info("Operations save OS file")
    filelist= admin.list_os_file(bucket=confb.config.oci.os.bucket,
                           prefix=confb.config.oci.os.finetune.os_path)
    ret =[]
    for each in filelist:
        ret.append(os.path.basename(each))

    logger.info(f" in api {ret}")
    return ret

@router.get("/get_finetune_state", tags=["Finetune"])
async def get_finetune_state(  ):
    """
    Get the current state information about the finetune service.

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | N/A               |  N/A    |                 N/A                |

    """

    return ctrl.get_finetune_state()

@router.get("/get_finetune_evaluation", tags=["Finetune"])
async def get_finetune_evaluation(workflow_key:str):
    """
    Get the current state information about the finetune service.

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """

    return ctrl.get_finetune_evaluation(workflow_key)

@router.patch("/evaluate_finetune", tags=["Finetune"])
async def evaluate_finetune(workflow_key:str):
    """
    Evaluate the finetuning that has been done for the workflow key

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """
    task = asyncio.create_task(ctrl.evaluate_finetune(workflow_key))

    # Wait for it only for a limited time
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=150)
        logger.info(f" in api {result}")
    except asyncio.TimeoutError:
        logger.info("Timeout reached, but evaluate finetune continues in background")
        result= {"status":"running", "message":"Still continuing in the background"}

    return result

@router.get("/get_finetune_history", tags=["Finetune"])
async def get_finetune_history(domain=None ):
    """
    Get the  historical information about the finetune service.

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | N/A               |  N/A    |                 N/A                |

    """

    return ctrl.get_finetune_history(domain=domain)

@router.get("/get_workflow", tags=["Admin Finetune"])
async def get_workflow(workflow_key:str):
    """
    Get the current state information about a specific workflow.

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """
    gatekeeper_param(workflow_key)
    return ctrl.get_workflow(workflow_key=workflow_key)

@router.post("/configure_finetune", tags=["Finetune"])
async def configure_finetune(request:dict, auto_complete:bool=False):
    """
    Configure the finetune cluster.

    | Parameter         | Default |            Description                                          |
    |-------------------|---------|-----------------------------------------------------------------|
    | request           |  N/A    |  configuration information                                      |
    | model_name        |  N/A    |  initial name for the workflow                                  |
    | training_filename |  N/A    |  path of the training data                                      |
    | model_descr       |  N/A    |  model description (optional)                                   |
    | auto_complete     |  False  |  When true, take the workflow the longest it can without user intervention |
    ```
        {"model_name":"",
         "training_filename":"fine_tune_11Apr2025_173806.jsonl",
         "model_descr":""
        }

        {"model_name":"",
         "training_filename":"fine_tune_11Apr2025_173806.jsonl",
         "model_descr":""
        }
        
    ```
    """
    # | config_state      |  N/A    |  State ['empty','cleared', 'set']                               |
    gatekeeper_param(request)
    gatekeeper_attribute(request, attr="model_name")
    gatekeeper_attribute(request, attr="training_filename")
    # gatekeeper_attribute(request, attr="config_state")
    
    #TODO: the model_name must adhere to display name rules of the genai cluster.
    request["workflow_key"]=request["model_name"]
    rsp=ctrl.configure_finetune(request=request)
    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="configure_finetune", workflow_key=rsp["workflow_key"]))
    return rsp

@router.get("/configure_finetune_update", tags=["Admin Finetune"])
async def configure_finetune_update(workflow_key):
    """
    After the configure finetune is done, this gets the database information.

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |
    """
    gatekeeper_param(workflow_key)

    rsp=ctrl.get_workflow(workflow_key=workflow_key)
    return rsp

@router.patch("/clear_configure_finetune", tags=["Finetune"])
async def clear_configure_finetune(workflow_key:str):
    """
    Clear the configure finetune information.
    Will not be cleared when ... (if the resources have been allocated?)

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """
    gatekeeper_param(workflow_key)

    return ctrl.clear_finetune(workflow_key=workflow_key)

@router.patch("/ignore_deployment", tags=["Finetune"])
async def ignore_deployment(workflow_key:str):
    """
    Clear the configure finetune information.
    Will not be cleared when ... (if the resources have been allocated?)

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """
    gatekeeper_param(workflow_key)

    return ctrl.ignore_deployment(workflow_key=workflow_key)

@router.post("/create_finetune_DAC", tags=["Admin Finetune"])
async def create_finetune_DAC(workflow_key:str, auto_complete:bool=False):
    """
    Creates the DAC for fine-tuning. Can be integrated with auto-complete.

    | Parameter         | Default |            Description                                          |
    |-------------------|---------|-----------------------------------------------------------------|
    | key               |  N/A    |  key information for the database.                              |
    | auto_complete     |  False  |  when true, take the workflow the longest it can without user intervention |

    """
    
    gatekeeper_param(workflow_key)

    task = asyncio.create_task(ctrl.create_finetune_DAC(workflow_key=workflow_key))

    # Wait for it only for a limited time
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=15)
    except asyncio.TimeoutError:
        logging.info("Timeout reached, but creating the cluster continues in background")
        result= {"Status":"running", "message":"Still continuing in the background"}
        return result
    
    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="create_finetune_DAC_update", workflow_key=workflow_key))

    return result 

@router.post("/run_finetune", tags=["Finetune"])
async def run_finetune(workflow_key:str):
    """
    Run finetune complete sequence. including the remaining steps (auto-complete assumed)

    | Parameter         | Default |            Description                                          |
    |-------------------|---------|-----------------------------------------------------------------|
    | key               |  N/A    |  key information for the database.                              |

    """
    auto_complete:bool=True
    gatekeeper_param(workflow_key)

    task = asyncio.create_task(ctrl.create_finetune_DAC(workflow_key=workflow_key))

    # Wait for it only for a limited time
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=15)
    except asyncio.TimeoutError:
        logging.info("Timeout reached, but creating the cluster continues in background")
        result= {"Status":"running", "message":"Still continuing in the background"}
        return result
    
    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="create_finetune_DAC_update", workflow_key=workflow_key))

    return result 

@router.get("/create_finetune_DAC_update" , tags=["Admin Finetune"])
async def create_finetune_DAC_update(workflow_key, auto_complete:bool = False):
    """
    Return the current status of the DAC Creation.

    | Parameter         | Default |            Description                                          |
    |-------------------|---------|-----------------------------------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow                                    |
    | auto_complete     |  False  |  when true, take the workflow the longest it can without user intervention |
    """
    gatekeeper_param(workflow_key)

    rsp= ctrl.create_finetune_DAC_update(workflow_key=workflow_key)
    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="create_finetune_DAC_update", workflow_key=rsp["workflow_key"]))
    return rsp

@router.post("/runonly_finetune", tags=["Admin Finetune"])
async def runonly_finetune(workflow_key:str, auto_complete:bool=False):
    """
    Execute the finetune action.

    | Parameter         | Default |            Description                                          |
    |-------------------|---------|-----------------------------------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow                                    |
    | auto_complete     |  False  |  When true, take the workflow the longest it can without user intervention |

    """
    gatekeeper_param(workflow_key)
    logger.info(f"run_finetune_api({workflow_key}) auto_complete={auto_complete}")

    task = asyncio.create_task(ctrl.run_finetune(workflow_key=workflow_key))

    # Wait for it only for a limited time
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=10)
    except asyncio.TimeoutError:
        logger.info("Timeout reached, but finetune processing continues in background")
        result= {"status":"running", "message":"Still continuing in the background"}

    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="run_finetune_update", workflow_key=workflow_key))

    return result

@router.get("/run_finetune_update", tags=["Admin Finetune"])
async def run_finetune_update(workflow_key, auto_complete:bool=False):
    """
    Return the status of the DAC Creation.

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |
    """
    gatekeeper_param(workflow_key)

    rsp= ctrl.run_finetune_update(workflow_key=workflow_key)
    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="run_finetune_update", workflow_key=rsp["workflow_key"]))
    return rsp


    """
@router.post("/create_hosting_DAC")
async def create_hosting_DAC(workflow_key:str, auto_complete:bool = False):
    Create the finetune DAC

    | Parameter         | Default |            Description                                          |
    |-------------------|---------|-----------------------------------------------------------------|
    | key               |  N/A    |  key information for the database.                              |

    gatekeeper_param(workflow_key)

    task = asyncio.create_task(ctrl.create_hosting_DAC(workflow_key=workflow_key))

    # Wait for it only for a limited time
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=15)
    except asyncio.TimeoutError:
        logging.info("Timeout reached, but creating the cluster continues in background")
        result= {"Status":"running", "message":"Still continuing in the background"}
        return result
    
    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="create_hosting_DAC_update", workflow_key=workflow_key))

    return result 
    """


    """
@router.get("/create_hosting_DAC_update")
async def create_hosting_DAC_update(workflow_key, auto_complete:bool = False):
    Return the status of the DAC Creation.

    | Parameter         | Default |            Description                                          |
    |-------------------|---------|-----------------------------------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow                                    |
    | auto_complete     |  False  |  take the workflow the longest it can without user intervention |
    gatekeeper_param(workflow_key)

    rsp= ctrl.create_hosting_DAC_update(workflow_key=workflow_key)
    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="create_hosting_DAC_update", workflow_key=rsp["workflow_key"]))
    return rsp
    """

@router.post("/deploy_finetune_model", tags=["Finetune"])
async def deploy_finetune_model(workflow_key:str, auto_complete:bool = False ):
    """
    Deploy a finetune model

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """
    gatekeeper_param(workflow_key)
    return ctrl.deploy_finetune_model(workflow_key=workflow_key)

@router.post("/deploy_finetune_model_update", tags=["Admin Finetune"])
async def deploy_finetune_model_update(workflow_key:str, auto_complete:bool=False ):
    """
    Check the current status on the deployment of  a finetune model

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """
    gatekeeper_param(workflow_key)
    return ctrl.deploy_finetune_model_update(workflow_key=workflow_key)

@router.delete("/destroy_finetune_DAC", tags=["Admin Finetune"])
async def destroy_finetune_DAC(workflow_key:str, auto_complete:bool=False ):
    """
    Destroy a finetune DAC

    | Parameter         | Default |            Description             |
    |-------------------|---------|------------------------------------|
    | workflow_key      |  N/A    |  Unique key for the workflow       |

    """
    gatekeeper_param(workflow_key)

    task = asyncio.create_task(ctrl.destroy_finetune_DAC(workflow_key=workflow_key))

    # Wait for it only for a limited time
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=10)
    except asyncio.TimeoutError:
        logger.info("Timeout reached, but destroy finetune DAC processing continues in background")
        result= {"status":"running", "message":"Still continuing in the background"}

    if auto_complete:
        asyncio.create_task(ctrl.auto_complete(step="destroy_finetune_DAC_update", workflow_key=workflow_key))

    return result

@router.get("/get_destroy_cluster_info", tags=["Admin Finetune"])
async def get_destroy_cluster_DAC_update(workflow_key:str):
    """
    Get the current information of a destroyed cluster.

    | Parameter| Default |            Description             |
    |----------|---------|------------------------------------|
    | workflow_key      |  N/A    |  key information for the database. |

    """
    gatekeeper_param(workflow_key)
    return ctrl.destroy_finetune_DAC_update(workflow_key=workflow_key)