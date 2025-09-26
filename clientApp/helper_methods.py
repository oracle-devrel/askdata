# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import configparser
import hashlib
import redis
import re
import os
import base64
import mimetypes
import logging
from logging.handlers import RotatingFileHandler
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime, date
import difflib
import json

logger = logging.getLogger("app_logger")
config = configparser.RawConfigParser()
config.read('ConfigFile.properties')

rediscache = redis.StrictRedis(host=config.get('RedisSection', 'url'), ssl=True, decode_responses=True, port=config.get('RedisSection', 'port'))
rediscache_obj = redis.StrictRedis(host=config.get('RedisSection', 'url'), ssl=True, decode_responses=False, port=config.get('RedisSection', 'port'))
queryttl=2*24*60*60

def setup_logger(log_file_name='application.log'):
    file_level = config.get('Logging', 'file.level', fallback='INFO').upper()
    console_level = config.get('Logging', 'console.level', fallback='INFO').upper()
    log_dir = config.get('Logging', 'logs.path', fallback='./logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_file_name)

    logger = logging.getLogger("app_logger")

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Configure file handler
    file_handler = RotatingFileHandler(log_file_path, maxBytes=0, backupCount=5)  # maxBytes=0 ensures no automatic rotation by size
    file_handler.setLevel(file_level)
    # Rotate at the program start
    if os.path.exists(log_file_path):
        file_handler.doRollover()
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    
    # Formatting
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)  # Root level

    return logger

def initialize_query_variables(model_id, user_key, prompt, reworded, session_id, convo_seq_no):
    is_retry = 0
    is_followup = 0
    followup_parent_txt = ""
    followup_txt = ""
    match_status = ""
    trust_id = 0
    is_trusted = 0
    is_prompt_equiv = 0
    is_template_equiv = 0
    is_clarify = 0
    is_action = 0
    action_type = ""
    llm_id = model_id
    user_id = user_key
    trust_score = 0
    user_prompt = prompt
    convo_prompt = reworded
    convo_id = session_id
    convo_seq_num = convo_seq_no
    generated_sql = ""
    executed_sql = ""
    db_error_code = ""
    db_error_txt = ""
    is_authorized = 1
    parentid = 0
    latency_generate_sql = None
    latency_exec_sql = None
    is_dynamic_instr = 0
    is_autocertify = None
    is_parent_corrected = None 
    template_id = None
    return (
        is_retry, is_followup, followup_parent_txt, followup_txt, match_status,
        trust_id, is_trusted, is_prompt_equiv, is_template_equiv, is_clarify,
        is_action, action_type, llm_id, user_id, trust_score, user_prompt,
        convo_prompt, convo_id, convo_seq_num, generated_sql, executed_sql,
        db_error_code, db_error_txt, is_authorized, parentid, latency_generate_sql, 
        latency_exec_sql, is_dynamic_instr, is_autocertify, is_parent_corrected, template_id
    )

# set chat cache
def set_chat_cache(sid, chat):
    rediscache.set(getmd5hash("sessionid" + sid),chat,ex=queryttl)

# get chat cache
def get_chat_cache(sid):
    chat = rediscache.get(getmd5hash("sessionid" + sid))
    if chat is not None:
        return chat
    else:
        return " none."

# set chat cache
def set_conversation_cache(sid, conversation):
    rediscache_obj.set(getmd5hash("conversation" + sid),conversation,ex=queryttl)

# get chat cache
def get_conversation_cache(sid):
    conversation = rediscache_obj.get(getmd5hash("conversation" + sid))
    return conversation

# reset chat cache
def reset_conversation_cache(sid):
    rediscache_obj.delete(getmd5hash("conversation" + sid))

# set session data
def set_session_data(sid, data):
    rediscache.set(getmd5hash("sessiondata" + sid),data,ex=queryttl)

# get session data
def get_session_data(sid):
    data = rediscache.get(getmd5hash("sessiondata" + sid))
    return data

# get chat cache
def get_prompt_conversation_cache(sid):
    conversation = rediscache_obj.get(getmd5hash("prompt_conversation" + sid))
    return conversation

# set chat cache
def set_prompt_conversation_cache(sid, conversation):
    logger.debug("md5 hash" + getmd5hash("prompt_conversation" + sid))
    rediscache_obj.set(getmd5hash("prompt_conversation" + sid),conversation,ex=queryttl)

# set graph cache
def set_graph_cache(gid, json_data):
    rediscache.set(gid,json_data,ex=queryttl)

# get graph cache
def get_graph_cache(gid):
    return rediscache.get(gid)

# set iquery cache
def set_iquery_cache(idataid, iquery):
    rediscache.set(idataid,iquery,ex=queryttl)

# get iquery cache
def get_iquery_cache(idataid):
    return rediscache.get(idataid)

def get_idata_step_counter(idataid) -> int:
  step = 0
  step_counter_key = f"idata:{idataid}:step_counter"
  current_step = rediscache_obj.get(step_counter_key)
  if current_step is not None:
    step = int(current_step)
  return step

# set idata cache
def set_idata_cache(idataid, dtype, data, step=0):
  step_key = f"idata:{idataid}:{dtype}:{step}"
  latest_key = f"idata:{idataid}:{dtype}:latest"
  history_key = f"idata:{idataid}:{dtype}:history"

  rediscache_obj.set(step_key, data, ex=queryttl)
  rediscache_obj.set(latest_key, data, ex=queryttl)
  if step == 0:
    rediscache.delete(history_key)
  rediscache.rpush(history_key, step_key)
  rediscache.expire(history_key, queryttl)

  rediscache_obj.set(f"idata:{idataid}:step_counter", step)

# get idata cache
def get_idata_cache(idataid, dtype, step=None):
  if step is not None:
    key = f"idata:{idataid}:{dtype}:{step}"
  else:
    key = f"idata:{idataid}:{dtype}:latest"
  data = rediscache_obj.get(key)
  return data

# reset idata cache
def reset_idata_cache(idataid, step=0):
  for dtype in ['idata', 'igraph', 'isummary']:
    step_key = f"idata:{idataid}:{dtype}:{step}"
    latest_key = f"idata:{idataid}:{dtype}:latest"
    history_key = f"idata:{idataid}:{dtype}:history"

    data = rediscache_obj.get(step_key)
    if data:
      rediscache_obj.set(latest_key, data, ex=queryttl)
      rediscache.delete(history_key)
      rediscache.rpush(history_key, step_key)
      rediscache.expire(history_key, queryttl)
      # delete the older entries
      for key_r in rediscache_obj.scan_iter(match=f"idata:{idataid}:{dtype}:*"):
          key = key_r.decode() if isinstance(key_r, bytes) else key_r
          if key.endswith("latest") or key.endswith("history"):
              continue
          try:
              step_num = int(key.rsplit(":", 1)[-1])
              if step_num > step:
                  rediscache_obj.delete(key)
          except ValueError:
              continue

  rediscache_obj.set(f"idata:{idataid}:step_counter", step)

# string utility method
def check_substring_single_space(main_string, sub_string):
    main_string_processed = re.sub(' +', ' ', main_string).strip().lower()
    sub_string_processed = re.sub(' +', ' ', sub_string).strip().lower()
    return sub_string_processed in main_string_processed

# string utility method to format column names
def format_column_name(s):
    if s.casefold() == "index":
        return ""
    if s.startswith("vw"):
        underscore_index = s.find('_')
        modified_string = s[underscore_index+1:].replace('_', ' ') if underscore_index != -1 else s
    else:
        modified_string = s.replace('_', ' ')
    return ' '.join(word.capitalize() for word in modified_string.split())

def getmd5hash(inputstr):
    inputstr = re.sub(' +', ' ',inputstr).strip()
    return hashlib.md5(inputstr.encode('utf-8')).hexdigest()

def normalize_spaces(text):
    """Normalize spaces in the input text."""
    return re.sub(r'\s+', ' ', text).strip()

def delcache():
    logger.debug("deleting cache")
    for key in rediscache.scan_iter():
        rediscache.delete(key)
    return True

def delsessioncache(sid):
    logger.debug("deleting session cache")
    chatkey1 = getmd5hash("sessionid" + sid)
    chatkey2 = getmd5hash("sessionid" + sid + "querycache")
    chatkey3 = getmd5hash("sessionid" + sid + "lastid")
    rediscache.delete(chatkey1)
    rediscache.delete(chatkey2)
    rediscache.delete(chatkey3)
    return True

def clean_ending(sentence):
    sentence = sentence.strip()
    if not sentence.endswith('.'):
        sentence = re.sub(r'[!?;,]+$', '', sentence)  # Remove unwanted punctuation at the end
        sentence += '.'
    return sentence

def init_cap(sentence):
    sentence = sentence.strip()
    if sentence:
        return sentence[0].upper() + sentence[1:]
    return sentence

def starts_with_delete_or_truncate(input_string):
    # Strip leading spaces, tabs, and blanks, then convert to lowercase
    stripped_string = input_string.lstrip().lower()
    # Check if the string starts with "delete" or "truncate"
    return stripped_string.startswith("delete") or stripped_string.startswith("truncate")

def clean_query_demo(text):
    logger.debug("query before ++++")
    logger.debug(text)
    text = extract_sql_code(text)
    text = extract_query(text)
    max_rows = config.get('QueryResult', 'max.resultset')
    str = " ".join(text.replace('\r', ' ').replace('\n', ' ').splitlines())
    cleanstr = str.replace(";", "").replace('"', '').strip()
    # Replace ILIKE with UPPER LIKE
    pattern_ilike = r'(?i)([^\s]+)\s+ilike\s+\'([^\']+)\''
    modified_str = re.sub(pattern_ilike, lambda match: f"UPPER({match.group(1)}) LIKE UPPER('{match.group(2)}')", cleanstr)
    # Patterns for LIMIT and FETCH
    pattern_limit = r"(?i)\bLIMIT\s+(\d+)"
    #pattern_fetch = r"(?i)\bFETCH\s+FIRST\s+\d+\s+ROWS\s+ONLY"
    pattern_fetch = r"(?i)\bFETCH\s+FIRST\b"
    # Search for existing LIMIT or FETCH clauses
    match_limit = re.search(pattern_limit, modified_str)
    match_fetch = re.search(pattern_fetch, modified_str)
    # Handle row limiting clauses
    if match_limit:
        # Replace LIMIT with FETCH FIRST ... ROWS ONLY
        modified_str = re.sub(pattern_limit, f"FETCH FIRST {match_limit.group(1)} ROWS ONLY", modified_str)
    elif not match_fetch:
        # Add FETCH FIRST ... ROWS ONLY if not already present
        modified_str = modified_str.strip() + f" FETCH FIRST {max_rows} ROWS ONLY"
    # Remove any `::FLOAT` casting
    modified_str = modified_str.replace("::FLOAT", "")
    logger.debug("query after +++++++++++++")
    logger.debug(modified_str)
    return modified_str

def clean_query(text):
    fetchstmt = ""
    max_rows = config.get('QueryResult', 'max.resultset')
    str = " ".join(text.replace(r'\r', '  ').replace(r'\n', '  ').replace("```sql", "").replace("`", "").splitlines())
    cleanstr = str.replace(";","")
    cleanstr = cleanstr.replace('"','')
    cleanstr_nospaces = cleanstr.strip()
    # detect ilike
    pattern = r'(?i)([^\s]+)\s+ilike\s+' + r"'([^']+)'"
    # change text
    modified_str = re.sub(pattern, lambda match: f"UPPER({match.group(1)}) LIKE UPPER('{match.group(2)}')", cleanstr_nospaces)

    # Regular expression to find the pattern "LIMIT" followed by spaces and a number
    pattern2 = r"\sLIMIT\s+(\d+)\s*"
    match2 = re.search(pattern2, modified_str)

    pattern3 = r"fetch\s+first\s+\d+\s+row"
    match3 = re.search(pattern3, modified_str, re.IGNORECASE)

    if match2:
        logger.debug("LIMIT clause found, substituting with FETCH...")
        modified_str = re.sub(pattern2, f" fetch first {match2.group(1)} rows only", modified_str)
    else:
        if not match3:
            logger.debug("Appending FETCH clause")
            fetchstmt = " fetch first " + max_rows + " rows only"
            modified_str = modified_str.strip() + fetchstmt

    modified_str = modified_str.replace("::FLOAT","")
    logger.debug(f"clean query...\n{modified_str}")
    return modified_str, fetchstmt

def extract_sql_code(text):
    import re
    pattern = r"```sql(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return text  # Return original text if no SQL blocks are found
    # Combine SQL blocks into a single string without adding new lines
    sql_code = " ".join(match.strip() for match in matches)
    return sql_code

def extract_query(sql_text):
    # Case-insensitive regex to match 'select' and capture text until the next ';' or end of string
    match = re.search(r'(select\b.*?)(;|$)', sql_text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def remove_limit_fetch(query):
    pattern = r'\s*(LIMIT\s+\d+|FETCH\s+(FIRST|NEXT)\s+\d+\s+(ROW|ROWS)\s+(ONLY)|TOP\s+\d+)'
    return re.sub(pattern, '', query, flags=re.IGNORECASE)

def get_image(image_name):
    current_directory = os.path.dirname(__file__)
    image_path = os.path.join(current_directory, image_name)
    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        return base64_image, mime_type
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{image_name}' does not exist in {current_directory}.")
    except Exception as e:
        raise Exception(f"An error occurred while processing the image: {e}")

def remove_quotes(s):
    if s.startswith("'\"") and s.endswith("\"'"):
        return s[2:-2]
    return s

# Takes a df column and returns True if it contains Integer or Float type of data
def is_numeric_column(series):
    # remove commas
    series = series.astype(str).str.replace(',', '', regex=False)
    # return False if the column is blank
    non_null_count = series.dropna().shape[0]
    if non_null_count == 0:
        return False
    try:
        # convert to numeric, string values would become NaN
        numeric_series = pd.to_numeric(series, errors='coerce')
        numeric_count = numeric_series.dropna().shape[0]
        # return True if atleast 80% of the values are converted
        if numeric_count / non_null_count >= 0.8:
            return True
        else:
            return False
    except:
        return False

def convert_to_numeric_if_possible(df):
    for col in df.select_dtypes(include=['object']).columns:
        logger.debug(col)
        try:
            df[col] = pd.to_numeric(df[col], errors='raise')
        except Exception as e:
            logger.error(e)
            continue
    return df

def draw_bar_chart(df_input):
    logger.debug("***** inside draw_bar_chart *****")
    df_input = convert_to_numeric_if_possible(df_input)
    logger.debug(df_input.dtypes)
    df=df_input.copy()

    # Automatically detect categorical and numerical columns
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    numerical_columns = df.select_dtypes(include=['number']).columns

    if len(categorical_columns) == 0 or len(numerical_columns) == 0:
        raise ValueError("DataFrame must have at least one categorical column and one numerical column")

    if (len(numerical_columns) > 2):
        df = df.iloc[:7, :]
    else:
        df = df.iloc[:15, :]

    # Assuming the first categorical column for x-axis
    x_col = categorical_columns[0]

    logger.debug("one")
    scale_columns=True
    if scale_columns:
        #scaler = MinMaxScaler()
        #df[numerical_columns] = scaler.fit_transform(df[numerical_columns])
        flattened_data = df[numerical_columns].values.flatten()
        # Perform Min-Max Scaling on the flattened data
        min_val = np.min(flattened_data)
        max_val = np.max(flattened_data)
        scaled_data = (flattened_data - min_val) / (max_val - min_val)
        # Reshape the scaled data back to original DataFrame shape
        df[numerical_columns] = pd.DataFrame(scaled_data.reshape(df[numerical_columns].shape), columns=df[numerical_columns].columns)

    # Plot the bar chart with all numerical columns
    df.plot(kind='bar', x=x_col, y=numerical_columns, colormap='viridis')

    # Add labels and title
    plt.xlabel(x_col)
    plt.ylabel(', '.join(numerical_columns))
    plt.title('Bar Chart of Numerical Columns by ' + x_col)

    logger.debug("two")
    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)

    # Convert the BytesIO object to a base64 string
    img_str = base64.b64encode(buf.read()).decode('utf-8')

    # Create HTML code to embed the image
    html = f"<img style='display:block;width:400px;height:400px;' src='data:image/png;base64,{img_str}' alt='Chart'>"
    logger.debug("three")
    logger.debug(html)
    return html

def is_integer(value):
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return value.is_integer()
    try:
        return float(value).is_integer()
    except ValueError:
        return False

def is_numeric(value):
    if value is None:
       return "Null"
    if isinstance(value, (pd.Period, pd.Timestamp, datetime, date)):
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def format_number(value):
    if value is None:
        return "Null"
    elif is_integer(value):
        return f"{int(float(value)):,}"
    else:
        return f"{float(value):,.2f}"

def format_date(value):
    if pd.isnull(value):
        return "Null"
    if isinstance(value, pd.Period):
        return str(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime('%Y-%m-%d')
    return value

def apply_formatting(col):
    exclude_suffixes = ('id', 'code', 'cd','number')
    if not col.name.lower().endswith(exclude_suffixes):
        return col.apply(lambda x: format_number(x) if is_numeric(x) else format_date(x))
    else:
        return col

def extract_schema(df, max_rows=5):
    def normalize_type(val):
        if pd.isna(val):
            return None
        elif isinstance(val, (datetime, pd.Timestamp)):
            return "datetime"
        elif isinstance(val, date):
            return "date"
        elif isinstance(val, dict):
            return "dict"
        elif isinstance(val, list):
            return "list"
        else:
            return type(val).__name__

    def merge_keys(dicts):
        keys = set()
        for d in dicts:
            if isinstance(d, dict):
                keys.update(d.keys())
        return list(keys)

    def flatten_schema(schema, parent_key=''):
        flat_schema = {}
        for key, value in schema.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict) and value.get("type") == "dict":
                nested = value.get("keys", {})
                nested_flat = flatten_schema(nested, full_key)
                flat_schema.update(nested_flat)
            else:
                flat_schema[full_key] = value.get("type", "unknown")
        return flat_schema

    if df.empty or df.shape[1] == 0:
        return {}

    schema = {}
    for col in df.columns:
        sample_values = df[col].head(max_rows).tolist()
        non_na_values = [val for val in sample_values if not pd.isna(val)]

        if not non_na_values:
            schema[col] = {"type": "unknown"}
            continue

        if any(isinstance(val, dict) for val in non_na_values):
            nested_dicts = [val for val in non_na_values if isinstance(val, dict)]
            nested_keys = merge_keys(nested_dicts)
            nested_schema = {}

            for k in nested_keys:
                inner_vals = [d.get(k, None) for d in nested_dicts]
                inner_types = set(normalize_type(v) for v in inner_vals if v is not None)
                nested_schema[k] = {"type": list(inner_types) or ["unknown"]}

            schema[col] = {
                "type": "dict",
                "keys": nested_schema
            }
        else:
            inferred_types = set(normalize_type(val) for val in non_na_values if val is not None)
            schema[col] = {
                "type": list(inferred_types) or ["unknown"]
            }

    flattened_schema = flatten_schema(schema)
    return flattened_schema

def extract_schema_old(df, max_rows=5):
    def flatten_schema(nested_schema, parent_key=''):
        flat_schema = {}
        for key, value in nested_schema.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if value.get("type") == "dict" and "keys" in value:
                for subkey in value["keys"]:
                    flat_schema[f"{full_key}.{subkey}"] = "unknown"
            else:
                flat_schema[full_key] = value["type"]
        return flat_schema

    schema = {}
    for col in df.columns:
        sample_values = df[col].head(max_rows).tolist()
        sample_values = ['' if pd.isna(val) else val for val in sample_values]
        sample_type = set(type(val).__name__ for val in sample_values)

        if any(isinstance(val, dict) for val in sample_values):
            # Handle nested dictionaries
            nested_keys = set()
            for val in sample_values:
                if isinstance(val, dict):
                    nested_keys.update(val.keys())
            schema[col] = {
                "type": "dict",
                "keys": list(nested_keys)
            }
        else:
            schema[col] = {
                "type": list(sample_type)
            }

    # Flatten the schema before returning
    flattened_schema = flatten_schema(schema)
    return flattened_schema

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Period):
            return str(obj)
        if isinstance(obj, (pd.Timestamp, datetime, date)):
            return obj.strftime('%Y-%m-%d')
        return super().default(obj)

def preprocess_for_llm(df):
    df = df.copy()

    # Convert object columns with dictionaries to JSON strings
    for col in df.select_dtypes(include='object').columns:
        if df[col].apply(lambda x: isinstance(x, dict)).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, default=str) if isinstance(x, dict) else x)

    # Convert datetime columns to ISO format strings
    for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
        df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000') if pd.notnull(x) else '1900-01-01T00:00:00.000')

    # Try to convert numeric-looking object columns to numbers
    for col in df.columns:
        if df[col].dtype == 'object':
            sample_vals = df[col].dropna().astype(str).head(10).tolist()

            # If it looks like numbers with commas, attempt to clean and convert
            if any(',' in val for val in sample_vals):
                cleaned = df[col].astype(str).str.replace(',', '', regex=False)
                numeric = pd.to_numeric(cleaned, errors='coerce')

                # Only replace if conversion makes sense
                if numeric.notnull().sum() > 0:
                    df[col] = numeric
                    continue  # Skip string casting below

            # If not converting, ensure strings
            df[col] = df[col].astype(str)

    # Convert float columns that are all integers to int safely
    for col in df.select_dtypes(include='float').columns:
        non_na = df[col].dropna()
        if not non_na.empty and np.all(np.mod(non_na, 1) == 0):
            df[col] = df[col].fillna(0).astype(int)

    # Final cleanup: ensure all object columns are strings
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str)

    return df
    
def check_substrings_in_string(substrings, string_to_check):
    substring_list = [s.strip() for s in substrings.split(',')]
    for substring in substring_list:
        if substring in string_to_check:
            return True
    return False

def concat_ids(user_id, model_no, convo_seq_num):
    return f"{user_id}|{model_no}|{convo_seq_num}"

def separate_ids(combined_string):
    logger.debug(f"combined_string is: {combined_string}")
    try:
        user_id_str, model_no_str, convo_seq_num_str = combined_string.split('|')
        return int(user_id_str),int(model_no_str),int(convo_seq_num_str)
    except (ValueError, AttributeError) as e:
        logger.error(f"Error separating string: {e}")
        return None

def generate_diff_string(orig_text, new_text):
    if orig_text is None or new_text is None:
        return ""
    orig_list = orig_text.replace(',', '').split()
    new_list = new_text.replace(',', '').split()

    d = difflib.Differ()
    diff = d.compare(orig_list, new_list)
    added_list = []
    removed_list = []
    for ele in difflib.ndiff(orig_list, new_list):
        if ele.startswith("+ "):
            added_list.append(ele.replace("+ ", ""))
        elif ele.startswith("-"):
            removed_list.append(ele.replace("- ", ""))

    for added in added_list:
        if added in removed_list:
            added_list.remove(added)
            removed_list.remove(added)

    for removed in removed_list:
        if removed in added_list:
            added_list.remove(removed)
            removed_list.remove(removed)

    ret_string = f'{" ".join(removed_list)} -> {" ".join(added_list)}'
    if ret_string.strip() == '->':
        ret_string = '='

    return ret_string

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def check_graphing_request_by_string(prompt: str):
    keywords = ['graph', 'chart', 'plot']
    prompt_lower = prompt.lower()
    found = False
    for keyword in keywords:
        if keyword in prompt_lower:
            found = True
            break
    logger.debug(f"Response: {found}")
    if found:
        return True
    else:
        return False