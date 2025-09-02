# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import warnings
from fastapi import APIRouter, HTTPException
from service_controller import llm_metrics_controller as controller

import logging
import constants

logger = logging.getLogger(constants.REST_LAYER)

router = APIRouter()
ctrl: controller = controller()

def metric_gatekeeper(start_date,end_date):
    if start_date is None:
        raise HTTPException(
            status_code=422,
            detail="Missing the start_date."
        )
    elif end_date is None:
        raise HTTPException(
            status_code=422,
            detail="Missing stop_date"
        )

@router.get("/get_corrected_sql")
async def get_corrected_sql():
    """
    Returns the corrected sql list.
    <br> Http GET 
    | Parameter| Default | Description  |
    |----------|---------|--------------|
    | None     |  N/A    |              |

    """
    logger.info("Calling get corrected sql")
    ret= ctrl.get_corrected_sql()
    logger.info(f" in api {ret}")
    return ret

@router.get("/size_trust_library")
async def size_trust_library(start_date=None, end_date=None, domain=None):
    return ctrl.size_trust_library(start_date=start_date,end_date=end_date, domain=domain )

@router.get("/percentage_prompts_trust_level")
async def percentage_prompts_trust_level(start_date=None, end_date=None, domain=None ):
    return ctrl.percentage_prompts_trust_level(start_date=start_date,end_date=end_date, domain=domain  )

@router.get("/size_trust_library_source")
async def size_trust_library_source(start_date=None, end_date=None, domain=None ):
    return ctrl.size_trust_library_source(start_date=start_date,end_date=end_date, domain=domain )

@router.get("/users_number_prompts_trust_level")
async def users_number_prompts_trust_level(start_date=None, end_date=None, domain=None ):
    return ctrl.users_number_prompts_trust_level(start_date=start_date,end_date=end_date, domain=domain )

@router.get("/users_number_prompts")
async def users_number_prompts(start_date=None, end_date=None, domain=None ):
    return ctrl.users_number_prompts(start_date=start_date,end_date=end_date, domain=domain )

@router.get("/users_number")
async def users_number(start_date=None, end_date=None, domain=None ):
    return ctrl.users_number(start_date=start_date,end_date=end_date, domain=domain )

@router.get("/size_trust_library_user_prompts_trust")
async def size_trust_library_user_prompts_trust(start_date=None, end_date=None, domain=None ):
    return ctrl.size_trust_library_user_prompts_trust(start_date=start_date,end_date=end_date, domain=domain  )

@router.get("/accuracy_semitrusted", deprecated=True)
async def accuracy_semitrusted(start_date=None, end_date=None, domain=None ):
    warnings.warn(
        "accuracy_semitrusted is deprecated API and will be removed in a future version.",
        DeprecationWarning, stacklevel=2
    )
    return ctrl.accuracy_semitrusted(start_date=start_date,end_date=end_date, domain=domain )

@router.get("/accuracy_untrusted", deprecated=True)
async def accuracy_untrusted(start_date=None, end_date=None, domain=None ):
    warnings.warn(
        "accuracy_untrusted is deprecated API and will be removed in a future version.",
        DeprecationWarning, stacklevel=2
    )
    return ctrl.accuracy_untrusted(start_date=start_date,end_date=end_date, domain=domain  )

@router.get("/accuracy_by_trust_level")
async def accuracy_by_trust_level(start_date, end_date, domain=None):
    metric_gatekeeper(start_date=start_date, end_date=end_date)
    return ctrl.accuracy_by_trust_level(start_date=start_date,end_date=end_date, domain=domain  )

@router.get("/accuracy_by_week")
async def accuracy_by_week(start_date=None, end_date=None, domain=None):
    metric_gatekeeper(start_date=start_date, end_date=end_date)
    return ctrl. accuracy_by_week(start_date=start_date,end_date=end_date, domain=domain)


@router.get("/accuracy_cumulative")
async def accuracy_cumulative(start_date=None, end_date=None, domain=None):
    metric_gatekeeper(start_date=start_date, end_date=end_date)
    return ctrl.accuracy_cumulative(start_date=start_date,end_date=end_date, domain=domain)
