# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import logging
import pytest
import constants

from helpers import engine as e
from helpers.config_json_helper import config_boostrap as confb

confb.setup()

logger = logging.getLogger(constants.ENGINE_LAYER)


@pytest.mark.skip(reason="Deprecated")
def test_refresh_autofill_cache( ):
    # Test a valid prompt (non-empty)
    result = e.refresh_autofill_cache(previous_last_record_stamp=None)
    assert result != None

@pytest.mark.skip(reason="Deprecated")
def test_refresh_autofill_cache( ):
    # Test a valid prompt (non-empty)
    result = e.refresh_autofill_cache(previous_last_record_stamp=None)
    assert result != None