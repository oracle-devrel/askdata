# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json

from helpers.config_json_helper import config_boostrap as confb
from fastapi.testclient import TestClient

import nl2sql_service

confb.setup()

client = TestClient(nl2sql_service.app)

def test_process_auto_valid():
    response = client.post("/process_auto")
    assert response.status_code == 200
    assert response.json() != None

def test_auto_hist_valid():
    response = client.get("/get_auto_hist")
    assert response.status_code == 200
    assert response.json() != None

def test_process_upload_valid():
    data: dict = None
    with open('test/data/body_upload.json', 'r') as file:
        data = json.load(file)  # Reads the entire content of the file into a string
    print(data)
    response = client.post("/process_upload", json=data)
    assert response.status_code == 200
    assert response.json() != None

def test_upload_hist_valid():
    response = client.get("/get_upload_hist")
    assert response.status_code == 200
    assert response.json() != None

def test_process_sql_valid():
    data: dict = None
    with open('test/data/body_process_sql.json', 'r') as file:
        data = json.load(file)  # Reads the entire content of the file into a string
    print(data)
    response = client.post("/process_sql", json=data)
    assert response.status_code == 200
    assert response.json() != None

def test_get_to_certify_valid():
    response = client.get("/get_to_certify")
    assert response.status_code == 200
    assert response.json() != None

def test_process_stage_valid():
    response = client.post("/process_stage",
                            json=
                            {"data":
                                [
                                    {"id":"5516","pass_fail":"Pass","sql_corrected":""}
                                ]
                            })
    assert response.status_code == 200
    assert response.json() != None

def test_get_staged_valid():
    response = client.get("/get_staged")
    assert response.status_code == 200
    assert response.json() != None

def test_process_unstage_valid():
    response = client.post("/process_unstage",json=
                                    {"id_list":
                                        [1,2,3,4]
                                    }
                            )
    assert response.status_code == 200
    assert response.json() != None

# No limits on local/dev (only when we have a demo environment)
# pytest --capture=no --log-file=output."$(date +'%Y-%m-%d_%H-%M-%S')".log

def test_process_certify_valid():
    response = client.post("/process_certify",
                           json={
                                "data":
                                    [
                                        {"id":"5516",
                                        "prompt_txt":"Show invoice number, amount due and invoice date",
                                        "sql_txt":"",
                                        "sql_corrected":"optional"
                                        },
                                    ],
                                "control": #TODO: move to be central to all pytests
                                    {"config":None,
                                     "test":{
                                            "mode": True,
                                            "out_of_scope":{
                                                    "database": ["insert","update"],
                                                    "llm_ft_dac": ["create_model"]
                                                    }
                                            }
                                    }
                                }
                            )
    #TODO: Pytest output to a file.
    assert response.status_code == 200
    assert response.json() != None