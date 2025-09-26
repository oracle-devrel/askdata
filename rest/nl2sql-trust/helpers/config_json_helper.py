# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import json
import logging
import os
import constants
import zipfile

from helpers.oci_helper_boostrap import oci_boostrap as ocib
from helpers.file_overwrite import copy_template_to_destination

logger = logging.getLogger(constants.CONFIG_LAYER)


def walkback_d(child: dict, attr: str, parent_key: str = 'p'):
    """
    Walk up the parent hierarchy to find an attribute in nested dictionaries.
    
    Args:
        child: Current dictionary to search in
        attr: Attribute name to search for
        parent_key: Key name that contains the parent reference (default: 'p')
    
    Returns:
        The value if found, None otherwise
    """
    x = child.get(attr)
    i = 0  # max depth 20. Avoid infinite loop
    
    while (x is None or (isinstance(x, (list, dict, str)) and len(x) == 0)) and i < 20:
        # Check if parent exists and is not empty
        parent :dict = child.get(parent_key)
        if not parent or (isinstance(parent, str) and len(parent) == 0):
            break
        
        child = parent
        x = child.get(attr)
        i = i + 1
    
    if i == 20:
        logging.error(f"Possible problem with the code structure, while searching for the attribute [{attr}]")
    
    return x

def test_climb():
    base={"oci":
            {
            "namespace":"A",
            "os":{
                "metadata":{
                        "os_path":"D",
                        "local_path":"E"
                        }
                }
            },
            "database": { # Database details need to be replaced here
                "wallet": "",
                "user": "",
                "pwd": "",
                "dns": "",
                "datetime_format": "DD-MON-YYYY hh24:mi:ss",
                "date_format": "DD-MON-YYYY"
            }
        }
    
    base["oci"]["os"]["p"] = base["oci"]
    base["oci"]["os"]["metadata"]["p"] = base["oci"]["os"]

    print("base----------")
    print(base)
    print("base.oci.ns----------")
    print(base["oci"]["namespace"])
    print(walkback_d(base["oci"],"namespace"))
    print("base.oci.os.ns----------")
    print(walkback_d(base["oci"]["os"],"namespace"))

class  config_boostrap:

    @classmethod
    def read_config(cls,environment) -> dict: 
        c = None
        try:
            c = json.loads(ocib.download(file_path=f'{environment}/config/',fn='trust_config.json'))
            logger.info(f"Using configuration file os://{environment}/config/trust_config.json")
            with open("./conf/trust_config.json", 'w') as json_file:
                json.dump(c, json_file, indent=4)         
            logger.debug(c)
        except FileNotFoundError as fe:
            logger.error(f"Error: The file at os://{environment}/config/trust_config.json was not found.")
            raise fe
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

        c["oci"] |= ocib.cnx

        return c

    @classmethod
    def read_file_and_trace(cls, environment):
        logger.info("bootstrap read_file_and_trace")
        try:
            cls.configuration = ocib.download(file_path=f'{environment}/config/',fn='trust_config.json')
            logger.info(f"Using configuration file(2) os://{environment}/config/trust_config.json")
            logger.debug(cls.configuration)
        except FileNotFoundError:
            logger.error(f"Error: The file at os://{environment}/config/trust_config.json was not found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    @classmethod
    def read_configuration(cls, environment:str):
        """
        Class method <br>
        Reads the configuration file into local attributes. At this time, once read, they are not updated even if the file is changed.
        """
        cls.dconfig : dict= cls.read_config(environment=environment)
        cls.dconfig["oci"]["engine"]["p"] = cls.dconfig["oci"]
        cls.dconfig["oci"]["ai"]["p"] = cls.dconfig["oci"]
        cls.dconfig["oci"]["vault"]["p"] = cls.dconfig["oci"]
        cls.dconfig["oci"]["os"]["p"] = cls.dconfig["oci"]
        cls.dconfig["oci"]["os"]["metadata"]["p"] = cls.dconfig["oci"]["os"]
        
    @classmethod
    def trace(cls):
        logger.info(json.dumps(cls.dconfig,indent=1))


    @classmethod
    def get_wallet(cls,environment):
        c = None
        try:
            c = ocib.download(file_path=f'{environment}/',fn=cls.dconfig["database"]["os_wallet"])
            with open('./wallet.zip', 'wb') as zip_file:
                zip_file.write(c)
            with zipfile.ZipFile('./wallet.zip', 'r') as zip_ref:
                zip_ref.extractall(cls.dconfig["database"]["wallet"])
            copy_template_to_destination(template_dir="conf/dbwallet", destination_dir=cls.dconfig["database"]["wallet"])
        except Exception as e:
            logger.error(f"An error occurred: {e}")

        return
    
    @classmethod
    def setup(cls):
        """
            export NL2SQL_ENV=<username> ;
            export NL2SQL_MODE=user ;
            export NL2SQL_OCI_NS=<your-tenancy-namespace> ;
            export NL2SQL_OCI_BUCKET=<bucketname> ;
        """
        cls.cnx = {
                "auth_mode":os.getenv('NL2SQL_OCI_MODE'),
                "namespace": os.getenv('NL2SQL_OCI_NS'),
                "region": os.getenv('NL2SQL_OCI_REGION','us-chicago-1'),
                "bucket": os.getenv('NL2SQL_OCI_BUCKET')
                }
        logger.info(cls.cnx)
        cls.read_configuration(environment=os.getenv('NL2SQL_ENV'))    # db_get_auto_hist(connection=db_get_connection())
        config_boostrap.get_wallet(environment=os.getenv('NL2SQL_ENV'))

def test_1():
    logging.basicConfig(level=logging.DEBUG)
    print("running config_helper (boostrap) main")
    config_boostrap.setup()

    #config_boostrap.trace()
    #logger.info(f"engine : {config_boostrap.dconfig["oci"]["engine"]["get_sql_url"]}")
    #logger.info(f"database : {config_boostrap.dconfig["database"]["wallet"]}")
    #logger.info(f"metrics : {config_boostrap.dconfig["metrics"]["start_date"]}")
    logger.info("***************************")
    #logger.info(f"engine : {config_boostrap.dconfig["oci"]["engine"]["region"]}")
    logger.info(f'engine : {config_boostrap.dconfig["oci"]["namespace"]}')
    logger.info(f'monitoring namespace : {config_boostrap.dconfig["oci"]["monitoring"]["namespace"]}')
    logger.info(f'telemetry endpoint : {config_boostrap.dconfig["oci"]["monitoring"]["telemetry"]}')

def test_2():
    test_climb()

if __name__ == "__main__":
    test_2()
    