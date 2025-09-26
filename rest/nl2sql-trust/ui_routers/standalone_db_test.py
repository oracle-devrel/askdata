# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from helpers.config_json_helper import config_boostrap as confb
confb.setup()
wallet = confb.dconfig["database"]["wallet"]
import os
os.environ["TNS_ADMIN"] = wallet
import oracledb
oracledb.init_oracle_client()

dsn = confb.dconfig["database"]["dns"]
user = confb.dconfig["database"]["user"]
pwd = confb.dconfig["database"]["pwd"]
print("Connecting using DSN:", dsn)
print("TNS_ADMIN is:", os.environ.get("TNS_ADMIN"))
print("Files in TNS_ADMIN:", os.listdir(wallet))

connection = oracledb.connect(
    user=user,
    password=pwd,
    dsn=dsn
)
print("Connection successful!")