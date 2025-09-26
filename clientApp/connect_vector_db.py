# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import oracledb
import pandas as pd
import configparser
import logging

import oci
import base64
from oci.secrets import SecretsClient

logger = logging.getLogger("app_logger")


api_config = None

def initialize_api_config(profile: str): 
    try:
        api_config = oci.config.from_file(profile_name=profile)
        return api_config
    except Exception as e:
        logger.error(f"Failed to load api key. Loading instance principal")
        print("Failed to load api key. Loading instance principal")

        return None # function should check if api_config is none, then initialize instance principal
        

def get_password(secret_id: str): 
    """
    Get password for given secret ocid.

    Args:
        secret_id: str: secret ocid in vault.

    Returns:
        password: secret password.
    """
    # Get secret from vault 
    initialize_api_config("DEFAULT")
    if api_config is not None: # if api key exists
        secrets_client = SecretsClient(api_config)

        password = secrets_client.get_secret_bundle(secret_id).data
        base64pw = password.secret_bundle_content.content
        decoded_pw = base64.b64decode(base64pw).decode('utf-8')
        return decoded_pw
    else: # use instance principal
        try: 
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            secrets_client = SecretsClient(
                        config = {},
                        signer = signer,
                    )
            password = secrets_client.get_secret_bundle(secret_id).data
            base64pw = password.secret_bundle_content.content
            decoded_pw = base64.b64decode(base64pw).decode('utf-8')
            return decoded_pw
        except Exception as e:
            logger.error(f"Failed to initialize secret client: {e}")
            print("Failed to initialize secret client")
            raise
        

def load_config_db(database: str, config_file: str):
    """
    Load database configuration 'database' (trust or client db) from a properties file or vault if properties file is incomplete.

    Args:
        database (str): Database being used, 'client' or 'trust'
        config_file (str): Path to the configuration file.

    Returns:
        dict: Dictionary containing database connection details.
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
             
        # Check if password exists in config, else check if password secret exists, else inform user 
        if database == "trust" and config.has_option('DEFAULT', 'password') and config.get('DEFAULT', 'password') is not None: 
        
            db_config = {
                'user': config.get('DEFAULT', 'user'),
                'password': config.get('DEFAULT', 'password'),
                'dsn': config.get('DEFAULT', 'dsn'),
                'wallet_location': config.get('DEFAULT', 'wallet_location'),
                'wallet_password': config.get('DEFAULT', 'wallet_password')
            }
            logger.debug('Database configuration loaded successfully.')
            print("database config loaded successfully", config.get('DEFAULT', 'wallet_location'))

            return db_config
    
        elif database == "trust" and config.has_option('DEFAULT', 'password_secret') and config.get('DEFAULT', 'password_secret') is not None:
            try: 
                password_secret = config.get('DEFAULT', 'password_secret')
                password = get_password(password_secret)

                db_config = {
                    'user': config.get('DEFAULT', 'user'),
                    'password': password,
                    'dsn': config.get('DEFAULT', 'dsn'),
                    'wallet_location': config.get('DEFAULT', 'wallet_location'),
                    'wallet_password': config.get('DEFAULT', 'wallet_password')
                }
                return db_config 
            except Exception as e:
                logger.error(f"Failed to load password secret: {e}")
                print("Failed to load password secret from config")
                raise
        elif database == "client" and config.has_option('DatabaseSection', 'database.password') and config.get('DatabaseSection', 'database.password') is not None: 
            db_config = {
                'user': config.get('DatabaseSection', 'database.user'),
                'password': config.get('DatabaseSection', 'database.password'),
                'dsn': config.get('DatabaseSection', 'database.dsn'),
                "config_dir": config.get('DatabaseSection', 'database.config'),
                'wallet_location': config.get('DatabaseSection', 'database.config'),
                'wallet_password': config.get('DatabaseSection', 'database.walletpsswd')
            }
            logger.debug('Client Database configuration loaded successfully from password.')
            print("database config loaded successfully", config.get('DatabaseSection', 'database.config'))

            return db_config
        elif database == "client" and config.has_option('DatabaseSection', 'database.password_secret') and config.get('DatabaseSection', 'database.password_secret') is not None:
            try: 
                password_secret = config.get('DatabaseSection', 'database.password_secret')
                password = get_password(password_secret)

                db_config = {
                    'user': config.get('DatabaseSection', 'database.user'),
                    'password': password,
                    'dsn': config.get('DatabaseSection', 'database.dsn'),
                    "config_dir": config.get('DatabaseSection', 'database.config'),
                    'wallet_location': config.get('DatabaseSection', 'database.config'),
                    'wallet_password': config.get('DatabaseSection', 'database.walletpsswd')
                }

                logger.debug('Client Database configuration loaded successfully from vault.')
                return db_config 
            except Exception as e:
                logger.error(f"Failed to load password secret: {e}")
                print("Failed to load password secret from config")
                raise
        else: 
            logger.debug('Please provide database password or secret.')
            print("Please provide database password or secret.")
            
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        print("Failed to load config file.")
        raise

def create_db_connection(db_config: dict):
    """
    Establish connection to Oracle DB using provided configuration.

    Args:
        db_config (dict): Dictionary containing DB connection details.

    Returns:
        connection: Oracle database connection object.
    """
    try:
        connection = oracledb.connect(
            config_dir=db_config['wallet_location'],  # Assuming config_dir is the same as wallet_location
            user=db_config['user'],
            password=db_config['password'],
            dsn=db_config['dsn'],
            wallet_location=db_config['wallet_location'],
            wallet_password=db_config['wallet_password']
        )
        logger.debug('Connected to Oracle DB successfully.')
        return connection
    except oracledb.DatabaseError as e:
        error, = e.args
        logger.error(f"Oracle Database connection error: {error.message} (Error Code: {error.code})")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during connection: {e}")
        raise

def fetch_data_from_db(query: str,column_names):
    """
    Fetch data from Oracle DB.

    Args:
        query (str): SQL query to execute.

    Returns:
        DataFrame: Pandas DataFrame containing the fetched data.
    """
    try:
        config_file = 'ConfigFile.properties'
        #db_config = load_config(config_file)
        db_config = load_config_db('trust', config_file)

        # Create DB connection
        connection = create_db_connection(db_config)

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            # Define column names based on the table structure
           # column_names = ['prompt', 'query', 'embeddings', 'created_at']

            # Create and return a DataFrame
            df = pd.DataFrame(rows, columns=column_names)
            logger.debug(f"{len(df)} rows fetched successfully from the database.")
            return df
    except Exception as e:
        logger.error(f"Failed to fetch data from DB: {e}")
        raise
    finally:
        if 'connection' in locals():
            close_db_connection(connection)

def fetch_data_from_db_col(query: str,column_names):
    """
    Fetch data from Oracle DB.

    Args:
        query (str): SQL query to execute.

    Returns:
        DataFrame: Pandas DataFrame containing the fetched data.
    """
    try:
        config_file = 'ConfigFile.properties'
        #db_config = load_config(config_file)
        db_config = load_config_db('trust', config_file)

        # Create DB connection
        connection = create_db_connection(db_config)

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            # Define column names based on the table structure
            #column_names = ['prompt', 'query', 'embeddings', 'created_at']

            # Create and return a DataFrame
            df = pd.DataFrame(rows, columns=column_names)
            logger.debug(f"{len(df)} rows fetched successfully from the database.")
            return df
    except Exception as e:
        logger.error(f"Failed to fetch data from DB: {e}")
        raise
    finally:
        if 'connection' in locals():
            close_db_connection(connection)

def update_db(query: str):
    try:
        config_file = 'ConfigFile.properties'
        #db_config = load_config(config_file)
        db_config = load_config_db('trust', config_file)

        # Create DB connection
        connection = create_db_connection(db_config)

        with connection.cursor() as cursor:
            cursor.execute(query)
            connection.commit()
            logger.debug(f"Data update successfully from the database.")
    except Exception as e:
        logger.error(f"Failed to fetch data from DB: {e}")
        raise
    finally:
        if 'connection' in locals():
            close_db_connection(connection)

def close_db_connection(connection):
    """
    Safely close the Oracle DB connection.

    Args:
        connection: Oracle database connection object.
    """
    try:
        if connection:
            connection.close()
            logger.debug('Oracle DB connection closed successfully.')
    except Exception as e:
        logger.error(f"Error closing the connection: {e}")
        raise

# Removed the main function

# If this script is called directly, it will execute the query
if __name__ == '__main__':
    query = """
                SELECT PROMPT_TXT,SQL_QUERY,PROMPT_VECT,CERTIFIED_DATE
                FROM CERTIFIED_PROMPTS
            """
    # query = """
    #             SELECT * FROM VENDORS
    #         """
    
    # Define column names based on the table structure
    column_names = ['prompt', 'query', 'embeddings', 'created_at']
    #column_names = ['VENDOR_ID', 'VENDOR_NAME', 'VENDOR_SITE_DETAILS']
    data = fetch_data_from_db(query, column_names)
    print(data.head(1))
