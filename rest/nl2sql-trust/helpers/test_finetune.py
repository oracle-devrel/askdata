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