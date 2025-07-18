import oracledb
import pandas as pd
import configparser
import logging

# Configure logging
logging.basicConfig(
    filename='oracle_db.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(config_file: str):
    """
    Load database configuration from a properties file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: Dictionary containing database connection details.
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        db_config = {
            'user': config.get('DEFAULT', 'user'),
            'password': config.get('DEFAULT', 'password'),
            'dsn': config.get('DEFAULT', 'dsn'),
            'wallet_location': config.get('DEFAULT', 'wallet_location'),
            'wallet_password': config.get('DEFAULT', 'wallet_password')
        }
        logging.info('Database configuration loaded successfully.')
        return db_config
    except Exception as e:
        logging.error(f"Failed to load config file: {e}")
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
        logging.info('Connected to Oracle DB successfully.')
        return connection
    except oracledb.DatabaseError as e:
        error, = e.args
        logging.error(f"Oracle Database connection error: {error.message} (Error Code: {error.code})")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during connection: {e}")
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
        db_config = load_config(config_file)

        # Create DB connection
        connection = create_db_connection(db_config)

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            # Define column names based on the table structure
           # column_names = ['prompt', 'query', 'embeddings', 'created_at']

            # Create and return a DataFrame
            df = pd.DataFrame(rows, columns=column_names)
            logging.info(f"{len(df)} rows fetched successfully from the database.")
            return df
    except Exception as e:
        logging.error(f"Failed to fetch data from DB: {e}")
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
        db_config = load_config(config_file)

        # Create DB connection
        connection = create_db_connection(db_config)

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            # Define column names based on the table structure
            #column_names = ['prompt', 'query', 'embeddings', 'created_at']

            # Create and return a DataFrame
            df = pd.DataFrame(rows, columns=column_names)
            logging.info(f"{len(df)} rows fetched successfully from the database.")
            return df
    except Exception as e:
        logging.error(f"Failed to fetch data from DB: {e}")
        raise
    finally:
        if 'connection' in locals():
            close_db_connection(connection)

def update_db(query: str):
    try:
        config_file = 'ConfigFile.properties'
        db_config = load_config(config_file)

        # Create DB connection
        connection = create_db_connection(db_config)

        with connection.cursor() as cursor:
            cursor.execute(query)
            connection.commit()
            logging.info(f"Data update successfully from the database.")
    except Exception as e:
        logging.error(f"Failed to fetch data from DB: {e}")
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
            logging.info('Oracle DB connection closed successfully.')
    except Exception as e:
        logging.error(f"Error closing the connection: {e}")
        raise

# Removed the main function

# If this script is called directly, it will execute the query
if __name__ == '__main__':
    query = """
                SELECT PROMPT_TXT,SQL_QUERY,PROMPT_VECT,CERTIFIED_DATE
                FROM CERTIFIED_PROMPTS
            """
    data = fetch_data_from_db(query)
    print(data.head(1))
