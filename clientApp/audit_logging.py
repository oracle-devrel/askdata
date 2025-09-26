# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from connect_vector_db import create_db_connection, load_config_db, close_db_connection
import logging

logger = logging.getLogger("app_logger")

# def log_audit_test_insert():
def log_audit_test_insert(CERTIFIED_SCORE, PROMPT_TXT, SQL_QUERY, DB_RESPONSE_CODE, DB_ERR_TEXT, GENERATION_ENGINE_NM, SQL_LINEAGE, PROMPT_LINEAGE):
    connection = None
    cursor = None
    try:
        # Load the database configuration
        config_file = 'ConfigFile.properties'
        #db_config = load_config(config_file)
        db_config = load_config_db('trust', config_file)

        # Create a database connection using the shared function
        connection = create_db_connection(db_config)
        cursor = connection.cursor()

        # Dummy values to test insert
        # EXECUTION_DATE = datetime.datetime.now()
        # CERTIFIED_SCORE = 0.85
        # PROMPT_TXT = "Test prompt for auditing"
        # SQL_QUERY = "SELECT * FROM some_table"
        # DB_RESPONSE_CODE = 200
        # DB_ERR_TEXT = None  # Can also test with some error text, e.g., "Some error occurred"

        insert_sql = """
        INSERT INTO Executed_Prompts (CERTIFIED_SCORE, PROMPT_TXT, SQL_QUERY, DB_RESPONSE_CODE, DB_ERR_TEXT, GENERATION_ENGINE_NM, SQL_LINEAGE, PROMPT_LINEAGE)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
        """
        cursor.execute(insert_sql,
                       (CERTIFIED_SCORE, PROMPT_TXT, SQL_QUERY, DB_RESPONSE_CODE, DB_ERR_TEXT, GENERATION_ENGINE_NM, SQL_LINEAGE, PROMPT_LINEAGE))
        connection.commit()

        logger.debug("Test insert successful.")

    except Exception as e:
        logger.debug(f"Error logging audit data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)

