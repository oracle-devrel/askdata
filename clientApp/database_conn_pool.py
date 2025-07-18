import configparser
import re
import oracledb
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

logger = logging.getLogger("app_logger")
config = configparser.RawConfigParser()
config.read('ConfigFile.properties')

# Single global engine instance that maintains the connection pool
global_engine = create_engine(
    f'oracle+oracledb://:@',
    connect_args={
        "user": config.get('DatabaseSection', 'database.user'),
        "password": config.get('DatabaseSection', 'database.password'),
        "dsn": config.get('DatabaseSection', 'database.dsn'),
        "config_dir": config.get('DatabaseSection', 'database.config'),
        "wallet_location": config.get('DatabaseSection', 'database.config'),
        "wallet_password": config.get('DatabaseSection', 'database.walletpsswd'),
    },
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

def switch_user(connection, user_id, val1):
    try:
        connection.execute(text("""
            DECLARE
                sessionid raw(16);
            BEGIN
                SYS.DBMS_XS_SESSIONS.CREATE_SESSION('XSGUEST', sessionid);
                SYS.DBMS_XS_SESSIONS.ATTACH_SESSION(sessionid);
                SYS.DBMS_XS_SESSIONS.ASSIGN_USER(:user_id);
                SYS.DBMS_XS_SESSIONS.CREATE_NAMESPACE('ns1');
                SYS.DBMS_XS_SESSIONS.SET_ATTRIBUTE('ns1', 'attr1', :val1);
            END;
        """), {"user_id": user_id, "val1": val1})
    except Exception as e:
        logger.error(f"Error switching session for user {user_id}: {e}")
        connection.invalidate()
        raise

def cleanup_session(connection):
    try:
        connection.execute(text("""
            BEGIN
                SYS.DBMS_XS_SESSIONS.DETACH_SESSION;
            END;
        """))
    except Exception as e:
        logger.error(f"Warning: Session cleanup error: {e}")

@contextmanager
def get_connection(user_id=None, val1=None):
    connection = global_engine.connect()
    session_switched = False
    try:
        connection.execute(text("alter session set nls_date_format = 'YYYY-MM-DD'"))
        if user_id:
            switch_user(connection, user_id,val1)
            session_switched = True
        yield connection
    finally:
        if session_switched:
            cleanup_session(connection)
        connection.close()

def get_pool_status():
    return {
        'pool_size': global_engine.pool.size(),
        'checkedin': global_engine.pool.checkedin(),
        'checkedout': global_engine.pool.checkedout(),
        'overflow': global_engine.pool.overflow()
    }

def dispose_pool():
    global_engine.dispose()
