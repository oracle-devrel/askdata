# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from connect_vector_db import load_config_db, create_db_connection, close_db_connection
from database_conn_pool import get_connection
from generate_embeddings import create_str_embedding, read_file
import configparser
import logging
import oracledb
from sqlalchemy import text
import numpy as np

semantic_config = configparser.RawConfigParser()
semantic_config.read('ConfigFile.properties')
semanticenabled = semantic_config.getboolean('SemanticMatch', 'semantic.enabled')
semanticfetchlimit = int(semantic_config.get('SemanticMatch', 'semantic.fetchlimit'))
semanticadditionalhint = semantic_config.get('SemanticMatch', 'semantic.additionalhint')
sem_search_score_threshold = float(semantic_config.get('SemanticMatch', 'semantic.scorethreshold'))

logger = logging.getLogger("app_logger")

def do_semantic_search(convo_prompt, sem_search_fetch_limit):
    convo_prompt_vector = str(create_str_embedding(convo_prompt)[0])
    results = None
    cursor = None
    config_file = 'ConfigFile.properties'
    #dbconfig = load_config(config_file)
    db_config = load_config_db('trust', config_file)
    vdbconn = create_db_connection(db_config)
    try:
        cursor = vdbconn.cursor()
        #WHERE CERTIFIED_DATE IS NOT NULL
        statement = f"""SELECT COSINE_DISTANCE(prompt_vect, '{convo_prompt_vector}') as v, prompt_txt, sql_txt
                        FROM trust_library
                        WHERE is_corrected = 1
                        ORDER BY v
                        FETCH FIRST {sem_search_fetch_limit} ROWS ONLY"""
        cursor.execute(statement)
        results = cursor.fetchall()
    except Exception as e:
        logger.error(f"SQL error for trust library semi trusted path: {e}")
    return results

def get_hints4llm(convo_prompt):
    inject_str = ""
    matched_results = []
    sem_results = do_semantic_search(convo_prompt, semanticfetchlimit)

    if not semanticenabled:
        logger.debug(f"Semantic Match is not enabled!")
        return inject_str
    
    if not sem_results:
        logger.debug(f"no semantic results found!")
        return inject_str
    else:
        logger.debug(f"{len(sem_results)} semantic results found.")
    
    logger.debug(f"filtering the results over threshold...")
    for item in sem_results:
        logger.debug(f"\n{1 - item[0]}   {item[1]}\n{item[2]}")
        if (1 - item[0]) > sem_search_score_threshold:
            matched_results.append([item[1], item[2]])

    if matched_results:
        logger.debug(f"generating additional hints for semantic results over threshold...")
        inject_str = """ \n    Note: Pay particular attention to these corrected prompt-sql pairs on each line below.\n    {0}\n"""
        inject_str = inject_str.format(semanticadditionalhint)
        for item in matched_results:
            inject_str += f"        -  PROMPT: {item[0]}\tSQL: {item[1]}\n"
        logger.debug(f"{inject_str}")
    return inject_str
