# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import tempfile
import oci
import os
import logging

import constants
from constants import OCI_CONFIG, OCI_CONFIG_PROFILE, OCI_TIMEOUT_CONFIG

from oci.object_storage import ObjectStorageClient
from oci.object_storage import UploadManager
from oci.object_storage.transfer.constants import MEBIBYTE
from oci.exceptions import ServiceError

logger = logging.getLogger(constants.OCI_LAYER)

class oci_boostrap:
    """
    A helper class is a technically specialized class that is focused on a sole purpose. In this case
    we're hiding the intricacies of connecting/using the OCI resources. 
    The oci helper is a companion class used to handle the requests going to any of the OCI services.

    ## How does this works?

    ### Authentication/Authorization

    The auth/auth is done differently if you are in the cloud or outside of it. The control to know
    in which situation you are is based on the existence of the environment variable 

    ```
    OCI_CLI_AUTH=instance_principal
    ```
    If this variable doesn't exist, we consider that we're out of the cloud.
    
    The auth/auth done from inside of the cloud is controlled by a concept called instance principle.
    In short, the authorized user of the resources is the machine, and no longer a user. This is the 
    response to the need for a system user.
    https://www.ateam-oracle.com/post/calling-oci-cli-using-instance-principal
    """

    object_storage_client = None

    cnx= { # This is required to obtain the first trust_config.json file.
        "auth_mode":os.getenv("NL2SQL_OCI_MODE"),
        "namespace":os.getenv("NL2SQL_OCI_NS"),
        "region": os.getenv('NL2SQL_OCI_REGION','us-chicago-1'),
        "bucket": os.getenv("NL2SQL_OCI_BUCKET")
        }
    
    @classmethod
    def read_oci_client(cls,client):
        """
        Class method <br>
        Creates the OCI Storage client from either config file or from the instance principal.
        """
        if cls.cnx["auth_mode"] == constants.OCI_MODE_INSTANCE:
            cls.config = {}
            if "region" in cls.cnx:
                cls.config["region"]=cls.cnx["region"]
            if "tenancy.ocid" in cls.cnx:
                cls.config["tenancy"]=cls.cnx["tenancy.ocid"]
        else:
            cls.config = oci.config.from_file(OCI_CONFIG, OCI_CONFIG_PROFILE)
            if "region" in cls.cnx:
                cls.config["region"]=cls.cnx["region"]
            if "tenancy.ocid" in cls.cnx:
                cls.config["tenancy"]=cls.cnx["tenancy.ocid"]

        if cls.cnx["auth_mode"] == constants.OCI_MODE_INSTANCE:
            logger.info("Using the instance principle.")
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            return client(config=cls.config, signer=signer, **OCI_TIMEOUT_CONFIG)
        else:
            logger.info("Using the user configuration.")
            return client(config=cls.config, **OCI_TIMEOUT_CONFIG)

    @classmethod
    def read_oci_storage_client(cls):
        """
        Class method <br>
        Creates the OCI Storage client from either config file or from the instance principal.
        """
        cls.object_storage_client : ObjectStorageClient = cls.read_oci_client(ObjectStorageClient)
        return cls.object_storage_client

    @classmethod
    def get_tags(cls):
        """
        oci_helper method <br>
        Used to get tags of an instance.
        """
        if cls.cnx["auth_mode"] == constants.OCI_MODE_INSTANCE:
            cls.config=[]
            if "region" in cls.cnx:
                cls.config["region"]=cls.cnx["region"]
            if "tenancy.ocid" in cls.cnx:
                cls.config["tenancy"]=cls.cnx["tenancy.ocid"]
        else:
            cls.config = oci.config.from_file(OCI_CONFIG, OCI_CONFIG_PROFILE)
            if "region" in cls.cnx:
                cls.config["region"]=cls.cnx["region"]
            if "tenancy.ocid" in cls.cnx:
                cls.config["tenancy"]=cls.cnx["tenancy.ocid"]

        if cls.cnx["auth_mode"] == constants.OCI_MODE_INSTANCE:
            logger.info("Using the instance principle.")
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            compute_client = oci.core.ComputeClient(config=cls.config, signer=signer, **OCI_TIMEOUT_CONFIG)
        else:
            logger.info("Using the user configuration.")
            compute_client = oci.core.ComputeClient(cls.config)

        resource_ocid = "<instance-ocid>"
        resource = compute_client.get_instance(resource_ocid).data
        defined_tags = resource.defined_tags  # System-defined tags
        freeform_tags = resource.freeform_tags  # User-defined tags
        logger.info("Defined Tags:", defined_tags)
        logger.info("Freeform Tags:", freeform_tags)
    
    @classmethod
    def download(cls, file_path, fn):
        """
        Class method <br>
        Downloads the fn (objectname) from the object store to the local or server class path.
        """

        if cls.object_storage_client is None:
            cls.read_oci_storage_client()

        rsp :oci.response.Response = cls.object_storage_client.get_object(
                cls.cnx["namespace"],
                cls.cnx["bucket"],
                f"{file_path}{fn}"
            )
        logger.debug (rsp.data.content)
        return rsp.data.content

    @classmethod
    def upload(cls, bucket_name, filename, object_body):
        """
        Class method <br>
        Upload "small" files to the object store.
        """
        cls.read_oci_storage_client()

        cls.object_storage_client.put_object(
            namespace_name= cls.cnx["namespace"],
            bucket_name=bucket_name,
            object_name=filename,
            put_object_body=object_body
        )

    @classmethod
    def progress_callback(cls, bytes_uploaded):
        """
        Class method <br>
        Tracker used in the large upload method.
        """
        logger.debug("{} additional bytes uploaded".format(bytes_uploaded))

    @classmethod
    def large_upload(cls, bucket_name, local_filename, os_filename):
        """
        Class method <br>
        Multi-part upload used for larger files. It uses the upload manager.
        """
        osc = cls.read_oci_storage_client()

        logger.info(f"Large Upload ns=[{cls.cnx['namespace']}], nb=[{bucket_name}], os=[{os_filename}], lf=[{local_filename}]")
        upload_manager = UploadManager(osc, allow_parallel_uploads=True, parallel_process_count=5)
        part_size=50*MEBIBYTE
        response = upload_manager.upload_file(
            namespace_name=cls.cnx["namespace"],
            bucket_name=bucket_name,
            object_name=os_filename,
            file_path=local_filename,
            part_size=part_size,
            progress_callback=cls.progress_callback)
        
        return response
    
    @classmethod
    def put_os_file(cls,path: str, fn:str, content):
        bucket: str = cls.cnx["bucket"]

        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write(content)
            temp_filename = temp_file.name
            temp_file.close()

            ret= oci_boostrap.large_upload(
                    bucket_name=bucket,
                    local_filename= temp_filename,
                    os_filename=f"{path}{fn}")

            os.remove(temp_filename)

        return ret
    
if __name__ == "__main__":
    logging.getLogger('oci').setLevel(logging.DEBUG)
    oci_boostrap.cnx= { # This is required to obtain the first trust_config.json file.
        "auth_mode":os.getenv("NL2SQL_OCI_MODE"),
        "namespace":os.getenv("NL2SQL_OCI_NS"),
        "region": os.getenv('NL2SQL_OCI_REGION','us-chicago-1'),
        "bucket": os.getenv("NL2SQL_OCI_BUCKET")
        #"tenancy.ocid": "<tenancy-ocid>",
        #"compartment.ocid": "<comp-ocid>",
        #"namespace": "<namespace>"
        }