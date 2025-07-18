from fastapi import APIRouter
from service_controller import trust_ops_controller as controller
import logging
import constants

logger = logging.getLogger(constants.REST_LAYER)

ctrl : controller = controller()

router = APIRouter()

@router.get("/get_live_logs")
async def get_live_logs(max_row_count:int=1000, domain=None):
    """
    Getting the live logs for operations. <br>
    <u> Should we provide a form of pagination? </u>
    <br><b>Uses the verbose flag for debugging.</b>

    |   Parameter       |  Default |                    Description                |
    |-------------------|----------|-----------------------------------------------|
    | max_row_count     |  1000    | Maximum number of rows to return              |

    """
    if (max_row_count <=0 ):
        return {"record List":[]}
    
    logger.info("Operations Live Logs")
    ret= ctrl.get_live_logs(max_row_count=max_row_count,domain=domain)
    logger.debug(f" in api {ret}")
    return ret
