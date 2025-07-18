import logging
import constants

from helpers.config_json_helper import config_boostrap as configb
from helpers import trust_metrics as m

logger = logging.getLogger(constants.METRICS_LAYER)
configb.setup()

def test_size_trust_library_valid( ):
    # Test a valid prompt (non-empty)
    result = m.size_trust_library( )
    assert result != None

def test_percentage_prompts_trust_level_valid( ):
    # Test a valid prompt (non-empty)
    result = m.percentage_prompts_trust_level( )
    assert result != None

def test_size_trust_library_source_valid( ):
    # Test a valid prompt (non-empty)
    result = m.size_trust_library()
    assert result != None

def test_users_number_prompts_trust_level_valid( ):
    # Test a valid prompt (non-empty)
    result = m.users_number_prompts_trust_level()
    assert result != None

def test_users_number_prompts_valid( ):
    # Test a valid prompt (non-empty)
    result = m.users_number_prompts()
    assert result != None

def test_users_number_valid( ):
    # Test a valid prompt (non-empty)
    result = m.users_number()
    assert result != None

def test_accuracy_by_trust_level_valid():
    # Test a valid prompt (non-empty)
    m.set_globals()
    result = m.accuracy_by_trust_level()
    assert result != None

def test_size_trust_library_user_prompts_trust_valid():
    # Test a valid prompt (non-empty)
    result = m.size_trust_library_user_prompts_trust()
    assert result != None