import oracledb
import os
import logging

from helpers.config_json_helper import config_boostrap as confb

from helpers import database_util as db

import constants
import oracledb


logger = logging.getLogger(constants.IO_LAYER)
logging.basicConfig(level=logging.DEBUG)
confb.setup()

def test_connection( ):
    """
    This is meant to test the database connection using the wallet configuration. 
    by default it is using the local configuration.
    """    
    # Configure the TNS_ADMIN environment variable to use the Oracle wallet

    # Connection details - your ADW DB URL, username, and service name
    wallet = confb.config.database.wallet
    user = confb.config.database.user
    dns = confb.config.database.dns
    pwd = confb.config.database.pwd

    os.environ["TNS_ADMIN"] = wallet
    oracledb.init_oracle_client(config_dir=os.environ["TNS_ADMIN"])
    connection = oracledb.connect(
        user=user,  # Use the username configured in the wallet
        password=pwd,  # This may also be configured in the wallet
        dsn=dns # This should match the tns entry in the wallet (tnsnames.ora)
    )
    #"""

    # Example query
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM dual")

    for row in cursor:
        logger.debug(row)

    # Close the connection
    cursor.close()
    connection.close()

def db_get_database_active_connections():
    wallet = confb.config.database.wallet
    user = confb.config.database.user
    dns = confb.config.database.dns
    pwd = confb.config.database.pwd
    os.environ["TNS_ADMIN"] = wallet
    oracledb.init_oracle_client(config_dir=os.environ["TNS_ADMIN"])
    connection = oracledb.connect(
        user=user,  # Use the username configured in the wallet
        password=pwd,  # This may also be configured in the wallet
        dsn=dns # This should match the tns entry in the wallet (tnsnames.ora)
    )
    #"""

    # Example query
    cursor = connection.cursor()
    cursor.execute("""
                SELECT count(*) 
                FROM v$session 
                WHERE status = 'ACTIVE'
                """)
    for row in cursor:
        logger.debug(row)
    # Close the connection
    cursor.close()
    connection.close()

def test_file_upload_history():
    db.db_file_upload_history(connection=db.db_get_connection(),domain=None)

def test_get_upload_hist():
    db.db_get_auto_hist(connection=db.db_get_connection(),domain=None)

def test_db_get_to_certify():
    db.db_get_to_certify(connection=db.db_get_connection(),domain=None)

def test_db_get_staged():
    db.db_get_staged(connection=db.db_get_connection(),domain=None)

def test_db_get_staged_lc():
    db.db_get_staged_lc_0_failed(connection=db.db_get_connection(),domain=None)
    db.db_get_staged_lc_mode_0(connection=db.db_get_connection(),domain=None)
    db.db_get_staged_lc_mode_1(connection=db.db_get_connection(),domain=None)
    db.db_get_staged_lc_mode_2(connection=db.db_get_connection(),domain=None)

def test_db_get_to_certify_lc():
    db.db_get_to_certify_lc(connection=db.db_get_connection(),mode=0,domain=None)
    db.db_get_to_certify_lc(connection=db.db_get_connection(),mode=1,domain=None)
    db.db_get_to_certify_lc(connection=db.db_get_connection(),mode=2,domain=None)

def test_db_process_certify_1():

    record_list = [
                    {"id":"5516",
                    "prompt_txt":"Show invoice number, 'amount' due and invoice date",
                    "sql_txt":"",
                    "sql_corrected":"optional"
                    },
                ]

    control = {"control":None,
                    "test":{
                        "mode": True,
                        "out_of_scope":{
                                "database": ["insert","update"]
                                }
                        }
                }


    db.db_process_certify_1(db.db_get_connection(), record_list, control=control,domain=None)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(constants.REST_LAYER)
    db_get_database_active_connections()
    