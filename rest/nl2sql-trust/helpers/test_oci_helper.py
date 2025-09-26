# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import base64
import uuid
import os
import logging

import oci
import pytest

import constants
from constants import OCI_CONFIG, OCI_CONFIG_PROFILE, OCI_TIMEOUT_CONFIG
from helpers.oci_helper_boostrap import oci_boostrap as ocib
from helpers.config_json_helper import config_boostrap as confb

from helpers.oci_helper_json import oci_helper as ocij


confb.setup()

logger = logging.getLogger(constants.OCI_LAYER)

def test_vault():
    """
    module method <br>
    Used to test the vault interaction.
    """
    logging.getLogger('oci').setLevel(logging.DEBUG)
    logging.info(f"db secret = {confb.dconfig["oci"]["vault"]["db_secret_ocid"]}")
    ocij.vault_get_secret(confb.dconfig["oci"]["vault"]["db_secret_ocid"])

def test_os():
    """
    module method <br>
    Used to test the object store interaction.
    """
    logging.getLogger('oci').setLevel(logging.DEBUG)
    ocij.read_oci_storage_client()
    c=ocij.download_metadata(fn=confb.dconfig["oci"]["os"]["metadata"]["file_name"])
    logging.info(c)
    ocij.upload(bucket_name=confb.dconfig["oci"]["os"]["bucket"],
                      filename=f"test_{str(uuid.uuid4())}.json",
                      object_body=c)

@pytest.mark.skip(reason="get_tags() not in oci_json_helper")
def test_tags():
    """
    module method <br>
    Used to test the vault interaction.
    """
    #conf.read_file_and_trace(suffix="local")
    ocij.get_tags()

@pytest.mark.skip(reason="Not in policies")
def test_regions():
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    identity_client = oci.identity.IdentityClient(config={}, signer=signer)
    regions = identity_client.list_regions()
    print(regions.data)

def test_vaults():
    config ={
            "region":confb.dconfig["oci"]["vault"]["region"],
            "tenancy":confb.dconfig["oci"]["tenancy_ocid"]
            }
    logging.getLogger('oci').setLevel(logging.DEBUG)
    ocid=confb.dconfig["oci"]["vault"]["db_secret_ocid"]
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    client = oci.secrets.SecretsClient(config=config, signer=signer)
    secret_response = client.get_secret_bundle(secret_id=ocid)
    secret_value = secret_response.data.secret_bundle_content.content.encode("ascii")
    keybytes = base64.b64decode(secret_value)
    key = keybytes.decode("ascii")   

    print(key)