# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from connect_vector_db import fetch_data_from_db
from llm_handler import evaluate_equivalence_prompt, chat_instructmode_llm
from database_ops import persist_log_data
from generate_embeddings import create_str_embedding
import configparser
import logging
import numpy as np
import pandas as pd
import re

semantic_config = configparser.RawConfigParser()
semantic_config.read('ConfigFile.properties')
semanticenabled = semantic_config.getboolean('SemanticMatch', 'semantic.enabled')

logger = logging.getLogger("app_logger")

def auto_certify(user_prompt, user_sql, domain):
    if not semantic_config.getboolean('SemiTrustedPath', 'semitrusted.enabled'):
        logger.debug("sql auto-certification is disabled!")
        return None, None, None
    
    logger.debug("auto certifying the sql...")
    fetch_limit = semantic_config.get('SemiTrustedPath', 'semitrusted.fetchlimit')
    df = get_top_semantic_match(user_prompt, fetch_limit)
    df_eqv = find_equivalent_record(user_prompt, user_sql, df, domain)
    
    if df_eqv is None:
        logger.debug("no equivalent match to be updated!")
        return None, None, None

    is_autocertify = 1
    logger.debug(f"equivalent_record:\n {df_eqv}")
    is_parent_corrected = int(df_eqv["is_corrected"]) if pd.notna(df_eqv["is_corrected"]) else None
    template_id = int(df_eqv["template_id"]) if pd.notna(df_eqv["template_id"]) else None
    return is_autocertify, is_parent_corrected, template_id

def get_top_semantic_match(input_string, top_n=3):
    input_embedding = create_str_embedding(input_string)
    input_embedding_str = f"'[{', '.join(map(str, input_embedding[0]))}]'"
    query = (
        "SELECT ID, TEMPLATE_ID, PROMPT_TXT, SQL_TXT, IS_CORRECTED, "
        f"1 - COSINE_DISTANCE(PROMPT_VECT, TO_VECTOR({input_embedding_str})) AS similarity "
        "FROM TRUST_LIBRARY "
        "WHERE TEMPLATE_ID = CERTIFY_STATE_ID AND (IS_DEPRECATED IS NULL OR IS_DEPRECATED=0)"
        "ORDER BY similarity DESC, ID DESC "
        f"FETCH FIRST {top_n} ROWS ONLY"
    )
    column_names = ['id', 'template_id', 'prompt', 'query', 'is_corrected',  'similarity']
    df = fetch_data_from_db(query, column_names)
    # cleanup similarity column
    if not df.empty:
        df["similarity"] = df["similarity"].apply(lambda x: float(x[0]) if isinstance(x, np.ndarray) else float(str(x).strip('[]')) if pd.notna(x) else np.nan)

    logger.debug(f"top records based on semantic search: \n {df}")
    return df

def find_equivalent_record(user_prompt, user_sql, df, domain):
    if df.empty:
        print("No records found.")
        return None
    df['llm_equivalent'] = "NO"

    #for idx, row in df.iterrows():
    #    llm_prompt = evaluate_equivalence_prompt(user_prompt, user_sql, row['prompt'], row['query'])
    #    logger.debug(f"equivalence prompt: {llm_prompt}")
    #    llm_response = chat_instructmode_llm(llm_prompt).strip().upper()
    #    df.at[idx, 'llm_equivalent'] = llm_response
    
    llm_prompt = evaluate_equivalence_prompt(user_prompt, user_sql, df, domain)
    logger.debug(f"equivalence prompt: {llm_prompt}")
    llm_response = chat_instructmode_llm(llm_prompt)
    num_candidates = len(df)
    llm_results = parse_llm_response(llm_response, num_candidates)
    df['prompt_equivalent'] = [r[0] for r in llm_results]
    df['sql_equivalent'] = [r[1] for r in llm_results]
    df['llm_equivalent'] = df.apply(lambda row: "YES" if row['prompt_equivalent'] == "YES" and row['sql_equivalent'] == "YES" else "NO", axis=1)

    equivalent_df = df[df['llm_equivalent'] == "YES"]
    logger.debug(f"records that are equivalent:\n {equivalent_df}")
    if equivalent_df.empty:
        logger.debug("No equivalent records found by LLM.")
        return None

    best_match_row = equivalent_df.loc[equivalent_df['similarity'].idxmax()]
    return best_match_row

def parse_llm_response(response, num_candidates):
    results = [("NO", "NO")] * num_candidates
    for line in response.splitlines():
        m = re.match(r"(\d+)\.\s*(YES|NO)\s*\|\s*(YES|NO)", line.strip(), re.IGNORECASE)
        if m:
            idx = int(m.group(1)) - 1
            prompt_answer = m.group(2).upper()
            sql_answer = m.group(3).upper()
            if 0 <= idx < num_candidates:
                results[idx] = (prompt_answer, sql_answer)
    return results

