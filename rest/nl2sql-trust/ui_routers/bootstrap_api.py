# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import asyncio
from fastapi import APIRouter, HTTPException
from service_controller import bootstrap_controller as controller
from service_controller import administrative_controller as admin_controller
import logging
import constants

logger = logging.getLogger(constants.REST_LAYER)

router = APIRouter()

ctrl: controller = controller()
admin: admin_controller = admin_controller()

@router.post("/process_auto")
async def process_auto( domain=None):
    """
    Process automatic prompts
    <br><b>Uses the verbose flag for debugging.</b>

    | Parameter| Default | Description  |
    |----------|---------|--------------|
    | Domain   |  None   | Pertinent area of the business. |

    """
    logger.info(f"Calling process prompts")
    ret= admin.read_metadata_os( )
    ret= ctrl.process_auto(domain=domain )
    logger.info(f" in api {ret}")
    return ret

@router.get("/get_auto_hist")
async def get_auto_hist(domain=None ):
    """

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    | Domain   |  None   | Pertinent area of the business. |

    """
    logger.info("Entry in the get auto history")
    ret= ctrl.get_auto_hist(domain=domain)
    logger.info(f" in api {ret}")
    return ret

@router.post("/process_upload")
async def process_upload(jlist: dict,domain=None):
    """
    Process prompts upload

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    | jlist        |  N/A    |  {Filename,Data[{metadata,prompt}]} is the required format.|
    | Domain       |  None   | Pertinent area of the business. |

    <b>jlist example </b>
    ```
    {
    "filename": "test_2.txt",
    "data": [
        {
        "metadata": "",
        "prompt": "list all vendors with past due account payables"
        },
        {
        "metadata": "",
        "prompt": "list all vendors with past due account payables"
        },
        {
        "metadata": "BR",
        "prompt": "list all tardy vendors"
        }
    ]
    }
    ```
    """
    if jlist is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'jlist' parameter. It cannot be null."
        )
        logger.error(f" Missing parameter in api {jlist}")
    elif "filename" not in jlist.keys():
        raise HTTPException(
            status_code=422,
            detail="Missing filename key entry in 'jlist' parameter."
        )
    elif "data" not in jlist.keys():
        raise HTTPException(
            status_code=422,
            detail="Missing data key entry in 'jlist' parameter."
        )

    logger.info(f"Calling process prompts, input ={jlist}")
    ret= ctrl.process_upload(jlist=jlist,domain=domain)
    logger.info(f" in api {ret}")
    return ret

@router.get("/get_upload_hist")
async def get_upload_hist(domain=None):
    """
    Returns the file history of the prompts upload.
    <br> Http GET 
    <br><b>Uses the verbose flag for debugging.</b>

    | Parameter| Default | Description  |
    |----------|---------|--------------|
    | None     |  N/A    |              |
    | Domain   |  None   | Pertinent area of the business. |

    """
    logger.info("Calling file upload history")
    ret= ctrl.get_upload_history(domain=domain )
    logger.info(f" in api {ret}")
    return ret

@router.post("/process_sql" )
async def process_sql(jlist: dict,domain=None ):
#async def process_sql(jlist: dict,multithreaded=None):
    """
    Process the SQL Request that comes in as a json object.
    <br><b>Uses the verbose flag for debugging.</b>

    | Parameter| Default | Description  |
    |----------|---------|-------------|
    | jlist    |  N/A    | SQL Request coming in as a json object.  {"source": "upload"} for test |
    | Domain   |  None   | Pertinent area of the business. |
    
    ``` {"source": "upload"}```

    <b> you do not need to set multithreaded, if you don't use it. Note that this is experimental at this point in time and requires further testing </b>
    
    """

    multithreaded = False
    
    if jlist is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'jlist' parameter. It cannot be null."
        )
    elif "source" not in jlist.keys():
        raise HTTPException(
            status_code=422,
            detail="Missing source key entry in 'jlist' parameter."
        )
    
    logger.info(f"Calling process sql source={jlist}")
    task = asyncio.create_task(ctrl.process_sql(source=jlist, domain=domain, multithreaded=multithreaded))

    # Wait for it only for a limited time
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=150)
        logger.info(f" in api {result}")
        return result
    except asyncio.TimeoutError:
        logger.info("Timeout reached, but sql processing continues in background")
        result= {"status":"running", "message":"Still continuing in the background"}

    
@router.get("/get_to_certify")
async def get_to_certify(domain=None ):
    """
    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    | Domain       |  None   | Pertinent area of the business. |

    """
    logger.info("Operations read OS file")
    ret= ctrl.get_to_certify(domain=domain)
    logger.info(f" in api {ret}")
    return ret

@router.post("/process_stage")
async def process_stage(jlist: dict,domain=None):
    """
    Stage the request for certification that comes in as a json object.
    <br>

    | Parameter| Default | Description  |
    |----------|---------|--------------|
    | jlist    |  N/A    |              |
    | Domain   |  None   | Pertinent area of the business. |
    ```
    {"data":[{"id":"5516","pass_fail":"Pass","sql_corrected":""}]}
    ```
    """
    if jlist is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'jlist' parameter. It cannot be null."
        )
    if "data" not in jlist.keys():
        raise HTTPException(
            status_code=422,
            detail="Missing 'data' key parameter. It cannot be absent."
        )

    for each in jlist["data"]:
        if "id" in each:
            id = each["id"]
            if id is None:
                raise HTTPException(
                    status_code=422,
                    detail="Missing and 'id' value in the data structure"
                )
        else:
            raise HTTPException(
                status_code=422,
                detail="Missing and 'id' value in the data structure")

        if "pass_fail" in each:
            pass_fail = each['pass_fail']
            if pass_fail is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Missing 'pass_fail' value parameter for id[{id}]. It cannot be absent."
                )
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Missing 'pass_fail' value parameter for id[{id}]. It cannot be absent."
            )

    logger.info("Calling stage certify source={jlist}")
    ret= ctrl.process_stage(jlist=jlist,domain=domain)
    logger.info(f" in api {ret}")
    return ret

@router.get("/get_staged")
async def get_staged(domain=None ):
    """
    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    | Domain       |  None   | Pertinent area of the business. |

    """
    logger.info("calling get staged.")
    return ctrl.get_staged(domain=domain)

@router.post("/process_unstage")
async def process_unstage(req: dict,domain=None ):
    """
    Unstage the request from certification that comes in as a json object.
    <br><b>Uses the verbose flag for debugging.</b>

    | Parameter| Default | Description  |
    |----------|---------|-------------|
    | req      |  N/A    | The request container. Expected {"id_list":[1,2,3,4,...]}  |
    | Domain   |  None   | Pertinent area of the business. |

    <b>Example</b>
    ```
    { "id_list":[1,2,3,4]}
    ```
    """

    if req is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'req' parameter. It cannot be null. expected format: {\"id_list\":[1,2,3,4,...]}}"
        )

    if "id_list" not in req:
        raise HTTPException(
            status_code=422,
            detail="Missing 'id_list' parameter. It cannot be null. expected format: {\"id_list\":[1,2,3,4,...]}"
        )
    id_list = req["id_list"]
    logger.info("Calling unstage certify source={id_list}")
    ret= ctrl.process_unstage(id_list=id_list,domain=domain)
    logger.info(f" in api {ret}")
    return ret
 
@router.post("/process_certify")
async def process_certify(req:dict,domain=None):
    """
    Process the staged request for certification.
    <br><b>Uses the verbose flag for debugging.</b>

    | Parameter| Default | Description  |
    |----------|---------|--------------|
    | req      |  N/A    |  The request container.|
    | Domain   |  None   | Pertinent area of the business. |
    <b>Example</b>
    ```
    {"id_list":[1,2,3,4]}
    {"data":[{"id":"5516","prompt_txt":"","sql_txt":"","sql_corrected":"optional"}]}
    ```
    """
    if req is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'req' parameter. It cannot be null. expected format: {\"id_list\":[1,2,3,4,...]}}"
        )

    if "data" not in req:
        raise HTTPException(
            status_code=422,
            detail="Missing 'data' parameter. It cannot be null. expected format: {'data':[{'id':'','prompt_txt':'','sql_txt':'','sql_corrected':'optional'}]}"
        )

    logger.info(req)
    logger.info("Calling process certify")
    if ("control" not in req):
        ret= ctrl.process_certify(data=req["data"],domain=domain)
    else:
        ret= ctrl.process_certify(data=req["data"],control = req["control"],domain=domain)
        
    logger.info(f" in api {ret}")
    return ret
