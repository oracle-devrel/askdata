import os
import uuid
import re
import configparser
import requests
import redis
from sqlalchemy import create_engine
import json
import pandas as pd
from decimal import Decimal
from sqlalchemy import text
import hashlib
import argparse
from fastapi import FastAPI, Request
import uvicorn, json, datetime
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import re
import concurrent.futures
from datetime import datetime, timedelta
import math
from embeddings_match import find_similar_prompts, find_similar_columns, find_top_match
import logging

logger = logging.getLogger("app_logger")
config = configparser.RawConfigParser()
config.read('ConfigFile.properties')

ocillm = config.get('OCI', 'serviceendpoint.llm_name')

def read_file_to_string(filename='metadata.sql'):
    # Open the file in read mode and read the contents into a string
    with open(filename, 'r') as file:
        file_content = file.read()
    return file_content

# Perfect matches must have same numbers if in the numeric form
# No numeric values return true
def compare_perfect_matches(string1, string2):
    pattern = r'(?<!\d)\b\d+\b(?!\d)'
    numbers1 = re.findall(pattern, string1)
    numbers2 = re.findall(pattern, string2)
    # If both lists of numbers are empty, return True
    if not numbers1 and not numbers2:
        return True
    return numbers1 == numbers2

def round_to_one(number):
    return 1 if number >= 0.99 else number

def return_validated_sql(prmpt):
    similarity_threshold = config.get('METADATA', 'librarymatch.threshold')
    similarity_threshold_upper = config.get('METADATA', 'librarymatch.upperthreshold')
    df_s = find_top_match(prmpt)
    df_s = df_s.iloc[0]

    # If df_s is a DataFrame
    if isinstance(df_s, pd.DataFrame):
      logger.debug(f"Columns in df_s: {df_s.columns.tolist()}")
      #logger.debug("Data in df_s:", df_s.head())  # Print first few rows
    else:
    # If it's a Series
      logger.debug(f"Index in df_s: {df_s.index.tolist()}")
      #logger.debug(f"Data in df_s: {df_s.tolist()}")

    top_prmpt = df_s["prompt"]
    top_query = df_s["query"]
    top_s_pct = df_s["similarity"]
    top_row_id = df_s["id"]
    logger.debug(f"top prompt: {top_prmpt}")
    logger.debug(f"top query: \n{top_query}")
    logger.debug(f"top similarity: {top_s_pct}")
    if top_s_pct is None or (isinstance(top_s_pct, float) and math.isnan(top_s_pct)):
        return 0,"None Found","None Found", 0, "None Found"
    elif round_to_one(top_s_pct) >= float(similarity_threshold_upper):
        logger.debug("perfect match: " + str(top_s_pct))
        if compare_perfect_matches(prmpt,top_prmpt):
            return top_row_id,top_prmpt,top_query, top_s_pct,"VERIFIED"
        else:
            logger.debug("requesting llm adjustments despite perfect match:")
            return top_row_id,top_prmpt,top_query, top_s_pct,"VERIFIED-FAILED-NUM-PARAMCHECK"
    elif round_to_one(top_s_pct) > float(similarity_threshold): #Scenario 2
        return top_row_id,top_prmpt,top_query, top_s_pct,"SIMILAR"
    else:
        return top_row_id,top_prmpt,"No match", top_s_pct,"NA"


def parse_select_query(sql):
    match = re.search(r"(?i)(select\s+.*?)(;|```|$)", sql, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "SQL not found"
