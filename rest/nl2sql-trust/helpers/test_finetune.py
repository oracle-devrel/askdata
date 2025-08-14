# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import logging

import constants
from helpers import finetune_helper as ft
from helpers import finetune_db as fdb
from helpers.config_json_helper import config_boostrap as confb

confb.setup()
logger = logging.getLogger(constants.FINETUNE_LAYER)

def test_finetune_valid( ):
    # Test a valid prompt (non-empty)
    result = ft.process_export_jsonl()
    assert result != None

def test_latest_model( ):
    # Test a valid prompt (non-empty)
    result = fdb.test_model_usage()
    assert result != None