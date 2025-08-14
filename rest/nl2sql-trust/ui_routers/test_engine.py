# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import datetime
import pytest
from fastapi.testclient import TestClient
from helpers.config_json_helper import config_boostrap as confb

import nl2sql_service
confb.setup()

client = TestClient(nl2sql_service.app)

@pytest.mark.skip(reason="Deprecated")
def test_refresh_autofill_cache_valid():
    start=datetime.datetime.strftime(datetime.datetime(2025, 1, 1), "%d-%b-%Y %H:%M:%S")
    response = client.get("/refresh_autofill_cache",
                            params=
                                {
                                    "previous_last_record_stamp":start
                                }
                            )

    assert response.status_code == 200
    assert response.json() != None