# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from fastapi import APIRouter, HTTPException
from service_controller import llm_metrics_controller as controller
from helpers.config_helper import nlp2sql_config as config

import logging
import constants

logger = logging.getLogger(constants.REST_LAYER)

router = APIRouter()
ctrl: controller = controller()

@router.get("/size_trust_library")
async def size_trust_library( ):
    f"""
    The start date is taken from the configuration file as {config.db_config.env_startup_date}.
    """
    return ctrl.size_trust_library( )

@router.get("/percentage_prompts_trust_level")
async def percentage_prompts_trust_level( ):
    f"""
    The start date is taken from the configuration file as {config.db_config.env_startup_date}.
    """
    return ctrl.percentage_prompts_trust_level( )

@router.get("/size_trust_library_source")
async def size_trust_library_source( ):
    f"""
    The start date is taken from the configuration file as {config.db_config.env_startup_date}.
    """
    return ctrl.size_trust_library_source( )

@router.get("/users_number_prompts_trust_level")
async def users_number_prompts_trust_level( ):
    f"""
    The start date is taken from the configuration file as {config.db_config.env_startup_date}.
    """
    return ctrl.users_number_prompts_trust_level( )

@router.get("/users_number_prompts")
async def users_number_prompts( ):
    f"""
    The start date is taken from the configuration file as {config.db_config.env_startup_date}.
    """
    return ctrl.users_number_prompts( )

@router.get("/users_number")
async def users_number( ):
    f"""
    The start date is taken from the configuration file as {config.db_config.env_startup_date}.
    """
    return ctrl.users_number( )

## HOTFIX: 23 April 2025
@router.get("/accuracy_by_trust_level")
async def accuracy_by_trust_level(start_date=None, end_date=None ):
    return ctrl.accuracy_by_trust_level(start_date=start_date,end_date=end_date )

@router.get("/size_trust_library_user_prompts_trust")
async def size_trust_library_user_prompts_trust(start_date=None, end_date=None ):
    return ctrl.size_trust_library_user_prompts_trust(start_date=start_date,end_date=end_date )
##