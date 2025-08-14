# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from fastapi.testclient import TestClient

import nl2sql_service
from helpers.config_json_helper import config_boostrap as confb
confb.setup()
client = TestClient(nl2sql_service.app)

def test_ops_live_logs_valid():
    response = client.get("/get_live_logs?max_row_count=10")
    assert response.status_code == 200
    assert response.json() != None
