# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json
import os
from fastapi.testclient import TestClient
from helpers.config_json_helper import config_boostrap as confb

import nl2sql_service

client = TestClient(nl2sql_service.app)
#from helpers.config_json_helper import config_boostrap as confb
confb.setup()

def test_read_metadata_objectstore_valid():
    response = client.get("/admin_read_metadata_os")
    assert response.status_code == 200
    assert response.json() != None