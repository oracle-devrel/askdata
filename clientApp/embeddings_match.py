# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import pandas as pd
import numpy as np
from generate_embeddings import create_str_embedding, read_file
from connect_vector_db import fetch_data_from_db
import logging

logger = logging.getLogger("app_logger")
def get_prompt_embeds_df(df):
	#df['embeddings'] = df['embeddings'].apply(lambda x: np.array(eval(x))) Commented by saket and added the below line
	# Ensure 'embeddings' is a NumPy array, if it's not already
	df['embeddings'] = df['embeddings'].apply(lambda x: np.array(x) if not isinstance(x, np.ndarray) else x)
	return df

def calculate_similarity(a, b):
  return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def similarity_search_col(input_string, df, top_n=2):
    input_embedding = create_str_embedding(input_string)
    if len(input_embedding) == 1 and isinstance(input_embedding[0], list):
        input_embedding = np.array(input_embedding[0])
    else:
        input_embedding = np.array(input_embedding)
    df['embeddings'] = df['embeddings'].apply(lambda x: np.array(eval(x)))
    similarities = df['embeddings'].apply(lambda x: calculate_similarity(input_embedding, x))
    df['similarity'] = similarities
    sorted_df = df.sort_values(by='similarity', ascending=False)
    top_matches_df = sorted_df.head(5).copy()
    s = input_string[:2]
    logger.debug(top_matches_df)
    top_matches_df["similarity"] = top_matches_df["similarity"].apply(lambda x: float(x[0]) if isinstance(x, np.ndarray) else float(str(x).strip('[]')) if pd.notna(x) else np.nan)
    logger.debug("fix similarity")
    logger.debug(top_matches_df)
    #top_matches_df.loc[:, 'priority'] = top_matches_df['column_name'].apply(lambda x: str(x[0]) if isinstance(x, np.ndarray) else str(x)).apply(lambda x: x.startswith(s))
    top_matches_df.loc[:, 'priority'] = top_matches_df['column_name'].apply(lambda x: str(x)).apply(lambda x: x.startswith(s))
    top_matches_df = top_matches_df.sort_values(by=['priority', 'similarity'], ascending=[False, False])
    # Return the top N rows with the highest similarity
    return top_matches_df.head(top_n)


def find_similarity_search_vdb(input_string, top_n=2):
    # Step 1: Get the embedding for the input string
    input_embedding = create_str_embedding(input_string)
    input_embedding_str = f"'[{', '.join(map(str, input_embedding[0]))}]'"
    query = (
        "SELECT PROMPT_TXT, SQL_TXT, PROMPT_VECT, CERTIFIED_DATE, "
        f"1 - COSINE_DISTANCE(PROMPT_VECT, TO_VECTOR({input_embedding_str})) AS similarity "
        "FROM CERTIFIED_PROMPTS "
        "ORDER BY similarity DESC "
        f"FETCH FIRST {top_n} ROWS ONLY"
    )
    column_names = ['prompt', 'query', 'embeddings', 'created_at', 'similarity']

    return fetch_data_from_db(query, column_names)


def similarity_search(input_string, df, top_n=2):
    input_embedding = create_str_embedding(input_string)
    similarities = df['embeddings'].apply(lambda x: calculate_similarity(input_embedding, x))
    df['similarity'] = similarities
    sorted_df = df.sort_values(by='similarity', ascending=False)
    # Return the top N rows with the highest similarity
    return sorted_df.head(top_n)

def find_top_match(input_string):
    df_s = query_vdb(input_string,1)
    df_s["similarity"] = df_s["similarity"].apply(lambda x: float(x[0]) if isinstance(x, np.ndarray) else float(str(x).strip('[]')) if pd.notna(x) else np.nan)
    return df_s

def query_vdb(input_string, top_n=2):
    # Step 1: Get the embedding for the input string
    input_embedding = create_str_embedding(input_string)
    input_embedding_str = f"'[{', '.join(map(str, input_embedding[0]))}]'"
    query = (
        "SELECT ID, PROMPT_TXT, SQL_TXT, PROMPT_VECT, CERTIFIED_DATE, "
        f"1 - COSINE_DISTANCE(PROMPT_VECT, TO_VECTOR({input_embedding_str})) AS similarity "
        "FROM TRUST_LIBRARY "
        "ORDER BY similarity DESC "
        f"FETCH FIRST {top_n} ROWS ONLY"
    )
    column_names = ['id', 'prompt', 'query', 'embeddings', 'created_at', 'similarity']

    return fetch_data_from_db(query, column_names)

def find_similar_prompts(input_string):
    query = """
                  SELECT PROMPT_TXT,SQL_TXT,PROMPT_VECT,CERTIFIED_DATE
                FROM TRUST_LIBRARY
              """
    column_names = ['prompt', 'query', 'embeddings', 'created_at']
    df = fetch_data_from_db(query,column_names)
    logger.debug(df.head(1))
    #  df = read_vector_db()
    df_e = get_prompt_embeds_df(df)
    # calculating  similarity using python commented by Saket
    #df_s = similarity_search(input_string, df_e, 1)
    #calculating similarity using vector db saket
    df_s = find_similarity_search_vdb(input_string,1)
    #df_s["similarity"] = df_s["similarity"].apply(lambda x: float(x[0]) if isinstance(x, np.ndarray) else float(str(x).strip('[]')))
    df_s["similarity"] = df_s["similarity"].apply(lambda x: float(x[0]) if isinstance(x, np.ndarray) else float(str(x).strip('[]')) if pd.notna(x) else np.nan)
    return df_s

def find_similar_columns(input_string, embeds_path):
    df = read_file(embeds_path)
    df_e = get_prompt_embeds_df(df)
    df_s = similarity_search_col(input_string, df_e, 1)
    #df_s["similarity"] = df_s["similarity"].apply(lambda x: float(x[0]) if isinstance(x, np.ndarray) else float(str(x).strip('[]')))
    df_s["similarity"] = df_s["similarity"].apply(lambda x: float(x[0]) if isinstance(x, np.ndarray) else float(str(x).strip('[]')) if pd.notna(x) else np.nan)
    return df_s
