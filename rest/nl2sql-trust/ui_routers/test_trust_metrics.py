# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from fastapi.testclient import TestClient
from helpers.config_json_helper import config_boostrap as confb
from helpers import trust_metrics

import nl2sql_service

confb.setup()
trust_metrics.set_globals()

client = TestClient(nl2sql_service.app)

def test_size_trust_library_valid():
    response = client.get("/size_trust_library")
    assert response.status_code == 200
    assert response.json() != None

def test_percentage_prompts_trust_level_valid():
    response = client.get("/percentage_prompts_trust_level")
    assert response.status_code == 200
    assert response.json() != None

def test_size_trust_library_source_valid():
    response = client.get("/size_trust_library_source")
    assert response.status_code == 200
    assert response.json() != None

def test_users_number_prompts_trust_level_valid():
    response = client.get("/users_number_prompts_trust_level")
    assert response.status_code == 200
    assert response.json() != None

def test_users_number_prompts_valid():
    response = client.get("/users_number_prompts")
    assert response.status_code == 200
    assert response.json() != None

def test_users_number_valid():
    response = client.get("/users_number")
    assert response.status_code == 200
    assert response.json() != None

def test_accuracy_by_trust_level_valid():
    response = client.get("/accuracy_by_trust_level")
    assert response.status_code == 200
    assert response.json() != None

def test_size_trust_library_user_prompts_trust_valid():
    response = client.get("/size_trust_library_user_prompts_trust")
    assert response.status_code == 200
    assert response.json() != None