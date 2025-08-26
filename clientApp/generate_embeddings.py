# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import pandas as pd
import oci
import re
import configparser
import logging

logger = logging.getLogger("app_logger")
config = configparser.RawConfigParser()
config.read('ConfigFile.properties')

def create_str_embedding(input_str: str ):
    compartment_id = config.get('OCI', 'serviceendpoint.ocid')
    CONFIG_PROFILE = "DEFAULT"
    ociconfig = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)
    # Service endpoint
    endpoint = config.get('OCI', 'serviceendpoint.url')
    #endpoint="https://inference.generativeai.sa-saopaulo-1.oci.oraclecloud.com"

    generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=ociconfig, service_endpoint=endpoint, retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
    inputs = [input_str]
    embed_text_detail = oci.generative_ai_inference.models.EmbedTextDetails()
    embed_text_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="cohere.embed-english-v3.0")
    embed_text_detail.inputs = inputs
    embed_text_detail.truncate = "NONE"
    embed_text_detail.compartment_id = compartment_id
    embed_text_response = generative_ai_inference_client.embed_text(embed_text_detail)
    (embd) = embed_text_response.data.embeddings
    return embd

def read_file(filepath):
    df = pd.read_excel(filepath)
    return df

def create_emdbeddings_list(df,col_to_embd):
    if col_to_embd not in df.columns:
        raise ValueError("The " + col_to_embd + " column is missing from the spreadsheet.")
    df['embeddings'] = df[col_to_embd].apply(create_str_embedding)
    df['embeddings'] = df['embeddings'].apply(lambda x: x[0] if isinstance(x, list) and len(x) == 1 else x)
    return df

def save_embeddings(filepath, df):
    df.to_excel(filepath, index=False)

import openpyxl

def create_column_embd(metadatafile,column_embd_file):
    # Create a new workbook and select the active worksheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Processed Data"
    sheet.append(['column_name', 'column_metadata'])

    # Open the text file and read its content
    with open(metadatafile, 'r') as file:
        lines = file.readlines()

    # Ignore the first and last lines
    if len(lines) > 2:  # Ensure there are at least 3 lines to ignore the first and last
        lines = lines[1:-1]

    # Process each line, extracting the first word and the full line
    for line in lines:
        words = line.strip().split()
        if words:
            first_word = words[0]
            sheet.append([first_word, line.strip()])

    # Save the workbook as an Excel file
    output_filename = column_embd_file
    workbook.save(output_filename)
    logger.debug(f"Data has been written to {output_filename}")
    df = read_file(output_filename)
    logger.debug("read file")
    df = create_emdbeddings_list(df,'column_name')
    logger.debug("ready to save file")
    save_embeddings(output_filename,df)



def create_column_embd_new(metadatafile, column_embd_file):
    # Create a new workbook and select the active worksheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Processed Data"
    sheet.append(['table_name', 'column_name', 'column_metadata'])  # Add headers

    table_name = None  # To track the current table being processed

    with open(metadatafile, 'r') as file:
        for line in file:
            # Trim leading and trailing spaces/tabs, normalize spaces, convert to lowercase
            normalized_line = " ".join(line.strip().split()).lower()

            # Skip blank lines and comments
            if not normalized_line or normalized_line.startswith("--"):
                continue

            # Check for table creation
            if normalized_line.startswith("create table"):
                # Extract table name (case-sensitive from original line)
                table_name = line.strip().split()[2].replace("(", "").strip().lower()
                continue

            # Skip line with contents ");"
            if normalized_line == ");":
                continue

            # Extract column definitions
            if table_name:
                column_parts = line.strip().split()
                if column_parts:  # Ensure there are parts to parse
                    # First word is the column name
                    column_name = column_parts[0].strip().replace(",", "").replace(")", "").lower()

                    # Extract metadata/comment if available by looking backward for "--"
                    if "--" in line:
                        column_metadata = line[line.index("--") + 2:].strip().lower()
                    else:
                        column_metadata = ""

                    # Append table name, column name, and column metadata to the spreadsheet
                    sheet.append([table_name, column_name, column_metadata])

    # Save the workbook
    workbook.save(column_embd_file)
    logger.debug(f"Data has been written to {column_embd_file}")
    df = read_file(column_embd_file)
    logger.debug("read file")
    df = create_emdbeddings_list(df,'column_name')
    logger.debug("ready to save file")
    save_embeddings(column_embd_file,df)

def create_prompt_embd(input_file):
    df = read_file(input_file)
    df = create_emdbeddings_list(df,'prompt')
    save_embeddings(input_file,df)


if __name__ == "__main__":
    metadatafile = config.get('METADATA', 'schema.ddl')
    embdgs = config.get('METADATA', 'file.embdgs')
    col_embdgs = config.get('METADATA', 'file.col_embdgs')
    #create_prompt_embd(embdgs)
    create_column_embd_new(metadatafile,col_embdgs)
#    input_file = 'prompt_lib.xlsx'  # Replace with your file path
#    df = read_file(input_file)
#    df = create_emdbeddings_list(df,'prompt')
#    save_embeddings(input_file,df)
