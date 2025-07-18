from fastapi import APIRouter, HTTPException
from service_controller import life_certify_controller as controller
from service_controller import administrative_controller as admin_controller

import logging
import constants

logger = logging.getLogger(constants.REST_LAYER)

router = APIRouter()
ctrl: controller = controller()
admin: admin_controller = admin_controller()

@router.post("/process_user_lc")
async def process_user_lc(domain=None ):
    """
    Process automatic prompts
    <br><b>Uses the verbose flag for debugging.</b>

    | Parameter| Default | Description  |
    |----------|---------|--------------|
    | Domain   |  None   | Pertinent area of the business. |

    """
    logger.info(f"Calling process prompts")
    ret= admin.read_metadata_os( )
    ret= ctrl.process_users_lc(domain=domain )
    logger.info(f" in api {ret}")
    return ret

@router.get("/get_to_certify_lc")
async def get_to_certify_lc(mode:int,domain=None):
    """

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    |   mode       |         | [0,1,2]      |

    """
    if mode is None:
        raise HTTPException(
            status_code=422,
            detail="Missing mode parameter. It cannot be null, it must be 0, 1 or 2."
        )
    if mode not in (0,1,2):
        raise HTTPException(
            status_code=422,
            detail="Wrong value in the  mode parameter. It cannot be null, it must be 0, 1 or 2."
        )

    logger.info("Get to certify LC")
    ret= ctrl.get_certify_lc(mode=mode,domain=domain)
    logger.info(f" in api {ret}")
    return ret

@router.get("/get_staged_lc_0")
async def get_staged_lc_0(input:str,domain=None):
    """

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    |   input      |         | [pass/fail]  |

    """
    if input is None:
        raise HTTPException(
            status_code=422,
            detail="Missing mode parameter. It cannot be null, it must be 0, 1 or 2."
        )
    logger.info("Config reset from file")
    ret= ctrl.get_staged_lc_0(input=input,domain=domain)

    logger.info(f" in api {ret}")
    return ret

@router.get("/get_staged_lc")
async def get_staged_lc(mode:int,domain=None):
    """

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    |   mode       |         | [1,2]      |

    """
    if mode is None:
        raise HTTPException(
            status_code=422,
            detail="Missing mode parameter. It cannot be null, it must be 1 or 2."
        )
    logger.info("Config reset from file")
    ret= ctrl.get_staged_lc(mode=mode, domain=domain)

    logger.info(f" in api {ret}")
    return ret