# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import base64
from pathlib import Path
import tempfile
import oci
import os
import logging
from datetime import datetime, timezone

import constants
from constants import OCI_CONFIG, OCI_CONFIG_PROFILE, OCI_TIMEOUT_CONFIG
from helpers.oci_helper_boostrap import oci_boostrap as bootstrap
from helpers.config_json_helper import config_boostrap as confb

from oci.certificates_management.certificates_management_client import CertificatesManagementClient
from oci.object_storage import ObjectStorageClient
from oci.object_storage import UploadManager
from oci.object_storage.transfer.constants import MEBIBYTE
from oci.exceptions import ServiceError

logger = logging.getLogger(constants.OCI_LAYER)

class oci_helper(bootstrap):
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


    @classmethod
    def read_oci_certificate_management_client(cls): 
        client :CertificatesManagementClient = cls.read_oci_client(CertificatesManagementClient)
        return client

    @classmethod
    def get_llm_inference_client(cls,endpoint):

        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            cls.config={
                        "region": confb.dconfig["oci"]["region"],
                        "tenancy": confb.dconfig["oci"]["tenancy_ocid"]
                        }
        else:
            cls.config = oci.config.from_file(OCI_CONFIG, OCI_CONFIG_PROFILE)
            cls.config["region"]=confb.dconfig["oci"]["region"]
            cls.config["tenancy"]=confb.dconfig["oci"]["tenancy_ocid"]

        generative_ai_inference_client : oci.generative_ai_inference.GenerativeAiClient= None

        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                    config=cls.config,
                    service_endpoint=endpoint,
                    signer=signer,
                    retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
        else:
            generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                    config=cls.config,
                    service_endpoint=endpoint,
                    retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))

        #TODO: Unit test
        return generative_ai_inference_client
    
    @classmethod
    def get_llm_dac_client(cls, endpoint=None):

        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            cls.config={
                        "region": confb.dconfig["oci"]["region"],
                        "tenancy": confb.dconfig["oci"]["tenancy_ocid"]
                        }
        else:
            cls.config = oci.config.from_file(OCI_CONFIG, OCI_CONFIG_PROFILE)
            cls.config["region"]=confb.dconfig["oci"]["region"]
            cls.config["tenancy"]=confb.dconfig["oci"]["tenancy_ocid"]

        generative_ai_client : oci.generative_ai.GenerativeAiClient = None

        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            generative_ai_client = oci.generative_ai.GenerativeAiClient(
                    config=cls.config,
                    service_endpoint=endpoint,
                    signer=signer,
                    retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
        else:
            generative_ai_client = oci.generative_ai.GenerativeAiClient(
                    config=cls.config,
                    service_endpoint=endpoint,
                    retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))

        #TODO: Unit test
        return generative_ai_client
        
    @classmethod
    def download_metadata(cls, fn):
        """
        Class method <br>
        Downloads the fn (objectname) from the object store to the local or server class path.
        """
        # Upload file to OCI Object Storage
        file_path = confb.dconfig["oci"]["os"]["metadata"]["local_path"]
        local_absolute_path = Path(file_path).resolve()

        if cls.object_storage_client is None:
            cls.read_oci_storage_client()

        with open(f"{local_absolute_path}/{fn}", 'wb') as file:
            rsp :oci.response.Response = cls.object_storage_client.get_object(
                    confb.dconfig["oci"]["namespace"],
                    confb.dconfig["oci"]["os"]["bucket"],
                    f'{os.getenv("NL2SQL_ENV")}/{confb.dconfig["oci"]["os"]["metadata"]["os_path"]}{fn}'
                )
            file.write(rsp.data.content) 
        logger.debug(rsp.data.content)
        return rsp.data.content
    
    @classmethod
    def ft_download(cls, local_filename, bucket_name, os_filename):
        """
        Class method <br>
        Download for the finetune. More general should replace the other download.
        """
        # Upload file to OCI Object Storage

        file_path = confb.dconfig["oci"]["os"]["finetune"]["local_path"]
        local_absolute_path = Path(file_path).resolve()

        if cls.object_storage_client is None:
            cls.read_oci_storage_client()

        with open(f"{local_absolute_path}/{local_filename}", 'wb') as file:
            rsp :oci.response.Response = cls.object_storage_client.get_object(
                    confb.dconfig["oci"]["namespace"],
                    bucket_name,
                    os_filename
                )
            file.write(rsp.data.content) 
        logger.debug(rsp.data.content)
        return rsp.data.content

    @classmethod
    def list_objects(cls, bucket, prefix):

        if cls.object_storage_client is None:
            cls.read_oci_storage_client()

        list_objects_response = cls.object_storage_client.list_objects(
                    namespace_name=confb.dconfig["oci"]["namespace"],
                    bucket_name=bucket,
                    prefix=prefix)

        names = []
        for value in list_objects_response.data._objects:
            names.append(value.name)

        return names
    
    @classmethod
    def read_oci_secret_client(cls):
        """
        Class method <br>
        Creates a vault client to read the secrets from the vault associated with the project.
        """
        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            cls.config={
                        "region": confb.dconfig["oci"]["region"],
                        "tenancy": confb.dconfig["oci"]["tenancy_ocid"],
                        "log_requests": True
                        }
        else:
            cls.config = oci.config.from_file(OCI_CONFIG, OCI_CONFIG_PROFILE)
            cls.config["region"]=confb.dconfig["oci"]["region"]
            cls.config["tenancy"]=confb.dconfig["oci"]["tenancy_ocid"]
            cls.config["log_requests"]= True

        cls.vault_client : oci.vault.VaultsClient = None

        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            logger.info("Vault client: Getting instance principle signer")
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            # signer = oci.auth.signers.get_resource_principals_signer()
            cls.vault_client = oci.vault.VaultsClient(config=cls.config, signer=signer)
            cls.secretclient = oci.secrets.SecretsClient(config=cls.config, signer=signer)
        else:
            logger.info("Vault client: Using non-instance mode.")
            cls.vault_client = oci.vault.VaultsClient(cls.config)
            cls.secretclient = oci.secrets.SecretsClient(cls.config)
        return cls.secretclient

    @classmethod
    def vault_get_secret(cls,ocid):
        """
        Class method <br>
        Read a specific secret from the vault (based on the ocid of the secret)
        """

        # Configuration
        client = cls.read_oci_secret_client()
        logger.info("obtained vault client")

        if client is None:
            logger.error("THE CLIENT IS NONE")
        try:
            # Fetch the secret's value from OCI Vault

            secret_response = client.get_secret_bundle(secret_id=ocid)
            secret_value = secret_response.data.secret_bundle_content.content.encode("ascii")
            keybytes = base64.b64decode(secret_value)
            key = keybytes.decode("ascii")            

        except ServiceError as e:
            key=None
            logger.error(f"Error retrieving secret: {e}")

        logger.info(f"Retrieved secret value:{key}")

        return key


def runtest_certificate_management( ):
    """
    """
    client = oci_helper.read_oci_certificate_management_client()

    # Send the request to service, some parameters are not required, see API
    # doc for more info
    validity=oci.certificates_management.models.Validity(
        time_of_validity_not_after=datetime.strptime("2026-03-14T00:00:00.000Z","%Y-%m-%dT%H:%M:%S.%fZ"),
        time_of_validity_not_before=datetime.strptime("2025-02-12T18:45:00.000Z","%Y-%m-%dT%H:%M:%S.%fZ"))
    
    """subject=oci.certificates_management.models.CertificateSubject(
        common_name="ca-test-dev-1",
        domain_component="nl2sql",
        distinguished_name_qualifier=None, # "EXAMPLE-distinguishedNameQualifier-Value",
        generation_qualifier=None, # "EXAMPLE-generationQualifier-Value",
        pseudonym="",
        given_name="John",
        surname="Doe",
        title="Developer",
        initials="JDD",
        serial_number=None,
        street="street name",
        locality_name="Dallas",
        state_or_province_name="TX",
        country="US",
        organization="Cloud",
        organizational_unit="<unit>",
        user_id="<user-id>")
    """
    subject=oci.certificates_management.models.CertificateSubject(
        common_name="www.example.com"
    )

    certificate_authority_config=oci.certificates_management.models.CreateRootCaByGeneratingInternallyConfigDetails(
        config_type="ROOT_CA_GENERATED_INTERNALLY",
        subject=subject,
        #version_name="0.1",
        #validity=validity,
        signing_algorithm="SHA256_WITH_RSA")

    """
    certificate_authority_rules = oci.certificates_management.models.CertificateAuthorityRule()
            advance_renewal_period= "P30D",
            renewal_interval= "P3650D",
            rule_type= "CERTIFICATE_AUTHORITY_RENEWAL_RULE")
    """
    
    certificate_authority_rule_1 = oci.certificates_management.models.CertificateAuthorityIssuanceExpiryRule(
            rule_type="CERTIFICATE_AUTHORITY_ISSUANCE_EXPIRY_RULE",
            leaf_certificate_max_validity_duration="P90D",
            certificate_authority_max_validity_duration="P3650D")

    certificate_revocation_list_details=oci.certificates_management.models.CertificateRevocationListDetails(
        object_storage_config=oci.certificates_management.models.ObjectStorageBucketConfigDetails(
            object_storage_bucket_name="EXAMPLE-objectStorageBucketName-Value",
            object_storage_object_name_format="EXAMPLE-objectStorageObjectNameFormat-Value",
            object_storage_namespace="EXAMPLE-objectStorageNamespace-Value"),
        custom_formatted_urls=["EXAMPLE--Value"])

    create_certificate_authority_details=oci.certificates_management.models.CreateCertificateAuthorityDetails(
        name="name",
        description="Certificate Authority for development for NL2SQL",
        compartment_id="<comp-id>",
        kms_key_id="<comp-id>",
        certificate_authority_config=certificate_authority_config,
        certificate_authority_rules=[certificate_authority_rule_1],
        freeform_tags={'NL2SQLEnv': 'dev'},
        #certificate_revocation_list_details=None,
        #defined_tags=None
        )
    
    create_certificate_authority_response = client.create_certificate_authority(
        create_certificate_authority_details=create_certificate_authority_details,
        opc_request_id=None,
        opc_retry_token=None)
    
    # Get the data from response
    print(create_certificate_authority_response.data)
    
def runtest_certificate( ):
    """
    """
    client = oci_helper.read_oci_certificate_management_client()

    create_certificate_response = client.create_certificate(
        create_certificate_details=oci.certificates_management.models.CreateCertificateDetails(
            name="EXAMPLE-name-Value",
            compartment_id="<comp-id>",
            certificate_config=oci.certificates_management.models.CreateCertificateByImportingConfigDetails(
                config_type="IMPORTED",
                cert_chain_pem="EXAMPLE-certChainPem-Value",
                private_key_pem="EXAMPLE-privateKeyPem-Value",
                certificate_pem="EXAMPLE-certificatePem-Value",
                version_name="EXAMPLE-versionName-Value",
                private_key_pem_passphrase="EXAMPLE-privateKeyPemPassphrase-Value"),
            description="EXAMPLE-description-Value",
            certificate_rules=[
                oci.certificates_management.models.CertificateRenewalRule(
                        rule_type="CERTIFICATE_RENEWAL_RULE",
                        renewal_interval="EXAMPLE-renewalInterval-Value",
                        advance_renewal_period="EXAMPLE-advanceRenewalPeriod-Value")],
            freeform_tags={ 'nl2sqlenv': 'dev'},
            defined_tags=None),
        opc_request_id="JUF1TGSMIK01R1NTAXLN<unique_ID>",
        opc_retry_token="EXAMPLE-opcRetryToken-Value")

    # Get the data from response
    print(create_certificate_response.data)

class SimpleOCIMonitoring(bootstrap):
    """Simple OCI monitoring client"""

    def __init__(self):
        # Load configuration from Terraform
        
        # Initialize OCI client
        self.oci_config=None
        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            self.oci_config={
                        "region": confb.dconfig["oci"]["region"],
                        "tenancy": confb.dconfig["oci"]["tenancy_ocid"],
                        "log_requests": True
                        }
        else:
            self.oci_config = oci.config.from_file(OCI_CONFIG, OCI_CONFIG_PROFILE)
            self.oci_config["region"]=confb.dconfig["oci"]["region"]
            self.oci_config["tenancy"]=confb.dconfig["oci"]["tenancy_ocid"]
            self.oci_config["log_requests"]= True


        if confb.dconfig["oci"]["auth_mode"] == constants.OCI_MODE_INSTANCE:
            logger.info("Monitor client: Getting instance principle signer")
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            self.monitoring_client = oci.monitoring.MonitoringClient(self.oci_config, service_endpoint=confb.dconfig["oci"]["monitoring"]["telemetry"],signer=signer)
        else:
            logger.info("Monitor client: Getting user")
            self.monitoring_client = oci.monitoring.MonitoringClient(self.oci_config, service_endpoint=confb.dconfig["oci"]["monitoring"]["telemetry"])
            
    def send_unable_to_certify_event(self, app_name, error_message="Certificate validation failed"):
        """Send unableToCertify event"""
        try:
            # Prepare metric data
            metric_data = oci.monitoring.models.MetricDataDetails(
                namespace= confb.dconfig["oci"]["monitoring"]["namespace"],
                compartment_id= confb.dconfig["oci"]["compartment_ocid"],
                name="unable_to_certify_event",
                dimensions={
                    "applicationName": app_name,
                    "eventType": "unableToCertify",
                    "severity": "CRITICAL"
                },
                datapoints=[
                    oci.monitoring.models.Datapoint(
                        timestamp=datetime.now(timezone.utc),
                        value=1.0,
                        count=1
                    )
                ]
            )
            
            # Send the event
            response = self.monitoring_client.post_metric_data(
                post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                    metric_data=[metric_data]
                )
            )
            
            if response.status == 200:
                print(f"✓ Successfully sent unableToCertify event for {app_name}")
                print(f"  Error: {error_message}")
                return True
            else:
                print(f"✗ Failed to send event. Status: {response.status}")
                return False
                
        except Exception as e:
            print(f"✗ Error sending event: {e}")
            return False
    
    def send_app_error_event(self, app_name, error_count=1):
        """Send application error event"""
        try:
            metric_data = oci.monitoring.models.MetricDataDetails(
                namespace=confb.dconfig["oci"]["monitoring"]["namespace"],
                compartment_id=confb.dconfig["oci"]["compartment_ocid"],
                name="application_error_event",
                dimensions={
                    "applicationName": app_name,
                    "eventType": "applicationError",
                    "severity": "WARNING"
                },
                datapoints=[
                    oci.monitoring.models.Datapoint(
                        timestamp=datetime.now(timezone.utc),
                        value=float(error_count),
                        count=1
                    )
                ]
            )
            
            response = self.monitoring_client.post_metric_data(
                post_metric_data_details=oci.monitoring.models.PostMetricDataDetails(
                    metric_data=[metric_data]
                )
            )
            
            if response.status == 200:
                print(f"✓ Successfully sent {error_count} application error event(s) for {app_name}")
                return True
            else:
                print(f"✗ Failed to send error event. Status: {response.status}")
                return False
                
        except Exception as e:
            print(f"✗ Error sending error event: {e}")
            return False

def monitoring_main():
    """Example usage"""
    print("=== Simple OCI Monitoring Test ===")
    
    try:
        # Initialize monitoring
        monitor = SimpleOCIMonitoring()
        
        # Test 1: Send unableToCertify event
        print("\n1. Testing unableToCertify event...")
        success1 = monitor.send_unable_to_certify_event(
            app_name="TrustService",
            error_message="Unable to certify"
        )
        
        # Test 2: Send application error events
        print("\n2. Testing application error events...")
        success2 = monitor.send_app_error_event(
            app_name="TrustService Issue",
            error_count=3
        )
        
        # Summary
        print(f"\n=== Test Results ===")
        print(f"UnableToCertify event: {'✓ SUCCESS' if success1 else '✗ FAILED'}")
        print(f"Application error events: {'✓ SUCCESS' if success2 else '✗ FAILED'}")
        
        if success1 or success2:
            print(f"\nCheck your email for alerts!")
            print("Note: Alarms may take 1-2 minutes to trigger notifications")
        
    except Exception as e:
        print(f"✗ Application error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    logging.getLogger('oci').setLevel(logging.DEBUG)
    confb.setup()
    #runtest_certificate_management()
    monitoring_main()