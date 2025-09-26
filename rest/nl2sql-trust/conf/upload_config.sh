# Copyright (c) 2025, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

echo "Uploading trust_config.json to ${TENANCY_NAMESPACE}:${NL2SQL_OCI_BUCKET}/${NL2SQL_ENV}/config/trust_config.json"
oci os object --auth instance_principal put -ns ${TENANCY_NAMESPACE} -bn ${NL2SQL_OCI_BUCKET} --storage-tier InfrequentAccess --file trust_config.json --name ${NL2SQL_ENV}/config/trust_config.json