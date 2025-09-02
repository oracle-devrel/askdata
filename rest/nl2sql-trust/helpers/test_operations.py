# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json
import logging
import constants

from helpers.config_json_helper import config_boostrap as configb

from helpers.operations_helper import ops_live_logs

logger = logging.getLogger(constants.OPERATION_LAYER)
logging.basicConfig(level=logging.DEBUG)
configb.setup()

def test_ops_live_logs():
    json_data=ops_live_logs(10)
    
    json_formatted_str = json.dumps(f"{json_data}", indent=4)
    logger.debug(json_formatted_str)