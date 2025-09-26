# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

# This assumes that the application is ran from the rest directory.

REST_LAYER: str ="n2sql_rest"
CONFIG_LAYER: str ="n2sql_rest"
FINETUNE_LAYER: str ="n2sql_rest"
IO_LAYER: str ="n2sql_rest"
NATURAL_LANGUAGE_LAYER: str ="n2sql_rest"
OCI_LAYER: str ="n2sql_rest"
OPERATION_LAYER: str ="n2sql_rest"
SERVICE_LAYER: str ="n2sql_rest"
UTIL_LAYER: str ="n2sql_rest"
METRICS_LAYER: str ="n2sql_rest"
ENGINE_LAYER: str ="n2sql_rest"

CONF_PATH: str = "conf"
CONFIG_FILE_PATH: str =f"{CONF_PATH}/ConfigFile_"
CONFIG_FILE_SUFFIX: str = ".properties"
TEST_DATA_PATH: str = "test/data"
NL2SQL_MODES: str = ["demo","dev","local"]
NL2SQL_MODE_DEFAULT="local"
OS_APEX_EXPORT="apex_exports/"
OCI_CONFIG:str="~/.oci/config"
OCI_CONFIG_PROFILE = "DEFAULT"
OCI_MODE_INSTANCE="instance"
OCI_MODE_USER="user"
OCI_MODE_TOKEN="token"
OCI_TIMEOUT_CONFIG = {
    'connect_timeout': 300,  # 5 minutes for establishing connection
    'read_timeout': 6000      # 10 minutes for reading the response
}
MODEL_PURPOSE="GEN-PURPOSE-LLM"