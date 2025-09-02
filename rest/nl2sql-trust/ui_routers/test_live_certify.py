# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from fastapi.testclient import TestClient
from helpers.config_json_helper import config_boostrap as confb

import nl2sql_service

confb.setup()

client = TestClient(nl2sql_service.app)

def test_process_user_lc_valid():
    response = client.post("/process_user_lc")
    assert response.status_code == 200
    assert response.json() != None

def test_get_to_certify_lc_valid():
    response = client.get("/get_to_certify_lc", params={"mode":0})
    assert response.status_code == 200
    assert response.json() != None
    response = client.get("/get_to_certify_lc", params={"mode":1})
    assert response.status_code == 200
    assert response.json() != None
    response = client.get("/get_to_certify_lc", params={"mode":2})
    assert response.status_code == 200
    assert response.json() != None

def test_get_staged_lc_valid():
    response = client.get("/get_staged_lc_0", params={"input":"fail"})
    assert response.status_code == 200
    assert response.json() != None
    response = client.get("/get_staged_lc_0", params={"input":"pass"})
    assert response.status_code == 200
    assert response.json() != None
    response = client.get("/get_staged_lc", params={"mode":0})
    assert response.status_code == 200
    assert response.json() != None
    response = client.get("/get_staged_lc", params={"mode":1})
    assert response.status_code == 200
    assert response.json() != None
    response = client.get("/get_staged_lc", params={"mode":2})
    assert response.status_code == 200
    assert response.json() != None
