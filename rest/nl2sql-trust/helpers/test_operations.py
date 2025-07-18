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