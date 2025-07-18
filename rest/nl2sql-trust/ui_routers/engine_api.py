import warnings
from fastapi import APIRouter
from service_controller import engine_controller as controller

import logging
import constants

logger = logging.getLogger(constants.REST_LAYER)

router = APIRouter()
ctrl: controller = controller()

#Deprecated.
@router.get("/refresh_autofill_cache", deprecated=True)
async def refresh_autofill_cache(previous_last_record_stamp):
    """
    ## REFRESH_AUTOFILL_CACHE FUNCTION                        #
    | Property           |   Description                                      |
    |--------------------|----------------------------------------------------|
    |previous_last_record_stamp  | Last date of the cache refresh                     |
    ``` previous_last_record_stamp example : 20-APR-2025 22:12:45 ```
    """
    logger.info("Refresh autofill engine cache")
    warnings.warn(
        "refresh_autofill_cache is deprecated API and will be removed in a future version.",
        DeprecationWarning, stacklevel=2
    )
    ret= ctrl.refresh_autofill_cache(previous_last_record_stamp=previous_last_record_stamp)
    logger.info(f" in api {ret}")

    return ret