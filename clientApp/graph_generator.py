# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import oci
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import io
import base64
import configparser
import json
import logging
import simplejson
import pickle
from decimal import Decimal
from llm_handler import create_message, chat_with_llm, chat_instructmode_llm
from helper_methods import set_conversation_cache, get_conversation_cache, set_idata_cache, get_idata_cache, extract_schema, CustomJSONEncoder

logger = logging.getLogger("app_logger")
config = configparser.RawConfigParser()
config.read('ConfigFile.properties')

CONFIG_PROFILE = "DEFAULT"
#ociconfig = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

# try:
#     ociconfig = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)
#     oci.config.validate_config(ociconfig)
# except Exception as e:
#     ociconfig = None 
#     print("Error loading OCI configuration:", e)
#     signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

def extract_python_code(text):
    if not text:
        return None
    pattern = r"```(?:python)?\s*(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    pattern = r"def\s+filterdf\(.*?\):.*"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return None

def get_plotly_graph(user_prompt, df):
    columns = df.columns.tolist()
    df_structure = "{'" + "', '".join(columns) + "'}"
    logger.debug(df_structure)
    graphllm_prompt = (f"{user_prompt}. Provide Python code only in your response to create the graph using Plotly from the following DataFrame structure: {df_structure}."
            "Include all necessary import statements. "
            "Create a method named create_graph that takes a dataframe as input and returns the figure object. "
            "Do not call fig.show() in the function, just return the figure."
            )
    logger.debug(graphllm_prompt)
    llm_response = chat_instructmode_llm(graphllm_prompt)
    generated_code = extract_python_code(llm_response)
    logger.debug(f"Generated Code:\n{generated_code}")
    logger.debug("DataFrame Info:")
    logger.debug(df.info())
    logger.debug("\nDataFrame Head:")
    logger.debug(df.head())
    logger.debug("\nDataFrame Columns:")
    logger.debug(df.columns.tolist())

    # Execute the generated code to create the graph function dynamically
    local_namespace = {}
    exec(generated_code, globals(), local_namespace)
    create_graph = local_namespace.get('create_graph')
    fig = create_graph(df)

    # Save the plot to an image
    img_bytes = fig.to_image(format="png")
    img_str = base64.b64encode(img_bytes).decode('utf-8')

    # Convert the Plotly figure to JSON
    fig_json = json.loads(pio.to_json(fig))

    # Create HTML code to embed the image
    html = f"<img style='display:block;width:125%;height:auto;' src='data:image/png;base64,{img_str}' alt='Chart'>"
    return html, fig_json

def get_graphllm_prompt(user_prompt, df_schema, df_length):
    return rf"""
        User Prompt: {user_prompt} 
        Generate Python code to transform a DataFrame with the following structure: {df_schema} into Oracle JET-compatible format. Total number of records in dataset is {df_length}.
        Determine the appropriate chart type, x-axis, y-axis, and group-by fields based on the first line of this prompt. If there is no explicit ask, use your best judgment based on the DataFrame column names and datatypes provided.
        Create a method named generate_OJetGraph that:
            - Takes a pandas DataFrame as input.
            - Returns the transformed data as a dictionary that is compliant with the Oracle JET chart library structure.
        *Special instructions for bubble and scatter charts:*
            - Always use actual numeric columns from the DataFrame for x and/or z axes.
            - For x-axis: use a numeric column representing a meaningful total.
            - For y-axis: use the count of records per group (not random values).
            - For z-axis (bubble size): use a scaled version of a numeric column (e.g., total divided by 10,000 if necessary).
            - Only generate random values for y-axis if no categorical column or grouping is possible at all (last resort).
        *Instructions:*
            - Include all necessary import statements.
            - Do not generate any method other than generate_OJetGraph.
            - Do not generate print statements, example usage, or additional outputs.
            - Ensure the output dictionary follows this schema:
                df_dict = {{
                    'metadata': {{
                        'chartType': 'bar',
                        'chartDesc': 'Total Amount Due for each Vendor',
                        'xLabel': 'Vendor Name',
                        'yLabel': 'Total Amount Due'
                    }},
                    'dataframes': {{
                        'df_total_amount_due': {{
                            'series_name': 'Total Amount Due',
                            'data': {{
                                'group': [...],
                                'value': [...],
                                'x': [...],
                                'y': [...],
                                'z': [...]
                            }}
                        }}
                    }}
                }}
            - Generate x, y and/or z axes only for scatter or bubble type of charts. 
        *Data type handling:*
            - First, inspect the actual dtype of each column based on the dataframe structure.
            - If a numeric column (float, int) is already correct, do not apply string operations like .str.replace().
            - If a column is string but numeric-looking, clean commas and safely convert to float.
        *Grouping and Counting:*
            - If the grouping column has unique values (1 row per group), set y-axis count = 1.
            - If multiple rows exist per group, set y-axis count = number of rows per group (via groupby().size()).
        Only use random values if absolutely necessary (e.g., if no grouping column is available).
        Provide only the Python function code without explanation or comments.
    """

def get_ojet_graph(user_prompt, df):
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return json.dumps({
            "chartType": "",
            "chartDesc": "No data available",
            "xLabel": "",
            "yLabel": "",
            "data": []
        }, indent=2)
    df_schema = extract_schema(df)
    graphllm_prompt = get_graphllm_prompt(user_prompt, df_schema, len(df))
    logger.debug(f"calling llm with prompt:\n{graphllm_prompt}")
    llm_response = chat_instructmode_llm(graphllm_prompt)
    generated_code = extract_python_code(llm_response)
    logger.debug(f"Generated Code is:\n{generated_code}")
    local_namespace = {}
    try:
        exec(generated_code, globals(), local_namespace)
        generate_OJetGraph = local_namespace.get('generate_OJetGraph')
        ojet_df = generate_OJetGraph(df)
        logger.debug("executed generate_OJetGraph() generated by LLM")
        logger.debug(f"ojet_df is:\n{ojet_df}")
    except Exception as e:
        logger.error(f"Error executing generated code: {e}")
        return json.dumps({"error": "Failed to generate chart"}, indent=2)
    ojet_json = convert_ojet_df_to_json(ojet_df)
    ojet_json_str = json.dumps(ojet_json, cls=CustomJSONEncoder, indent=2)
    logger.debug(f"ojet_json_str is:\n{ojet_json_str}")
    return ojet_json_str

def convert_ojet_df_to_json(df_dict):
    metadata = df_dict.get('metadata', {})
    chartType = metadata.get('chartType', '')
    chartDesc = metadata.get('chartDesc', '')
    xLabel = metadata.get('xLabel', '')
    yLabel = metadata.get('yLabel', '')

    json_data = {
        "chartType": chartType,
        "chartDesc": chartDesc,
        "xLabel": xLabel,
        "yLabel": yLabel,
        "data": []
    }

    # Process each dataframe
    for df_key, df_info in df_dict.get('dataframes', {}).items():    
        series_name = df_info.get('series_name', '')
        data_structure = df_info.get('data', {})
        data_points = []
        if data_structure.get('x') and data_structure.get('y') and len(data_structure['x']) > 0 and len(data_structure['y']) > 0:
            x_values = data_structure.get('x', [])
            y_values = data_structure.get('y', [])
            z_values = data_structure.get('z', [])
            group_values = data_structure.get('group', [])

            for i in range(len(x_values)):
                point = {
                        "group": group_values[i] if group_values else series_name,
                        "x": x_values[i],
                        "y": y_values[i]
                }
                if z_values and i < len(z_values):
                    point["z"] = z_values[i]
                data_points.append(point)
        else:
            groups = data_structure.get('group', [])
            values = data_structure.get('value', [])

            for i in range(len(groups)):
                point = {
                    "series": series_name,
                    "group": groups[i],
                    "value": values[i]
                }
                data_points.append(point)

        # Add this series to the JSON data
        json_data["data"].append({
            "series": series_name,
            "data": data_points
        })
    return json_data

def get_initial_prompt(df_structure, prompt):
    msg = rf"""
        You are provided a pandas DataFrame with the following structure: {df_structure}.
        Your task is to generate python code that can be used to manipulate DataFrame to fulfill user request.
        User Request: {prompt}
        **Instructions:**
            - Define a single function `filterdf`. Do not generate any method other than filterdf.
            - filterdf should take in a single parameter of the type pandas DataFrame and should return a pandas DataFrame.
            - Identify numeric columns by header name and always sanitize numeric columns (remove commas, convert to float).
            - Ensure code handles string-formatted numbers safely.
            - Use OOB pandas functionality as much as possible.
            - Never return SQL.
            - Provide support for multi-turn conversations. Maintain and update understanding of the DataFrame structure across user messages.
            - Only return the Python code. No explanations, no comments.
        """
    return msg

def create_conversation_message(prompt,conversation,role):
    logger.debug("appending message to conversation...")
    message = create_message(role, prompt)
    conversation.append(message)
    return conversation

def get_summary_prompt(conversation, user_prompt, df_length):
    msg = f"""
        Look at the Conversation and provide a clear concise business summary of all the messages from the conversation.

        Instructions:
        - Consider only the USER messages from the conversation and summarize into a concise business summary.
        - Just summarize the actions but don't include phrases like "User requests to" or "Here is a summary".
        - Do not include any hallucinated or inferred actions.
        - Use clear, non-technical language appropriate for business users.
        - Do not mention the operations performed or refer to any Python code, functions, or data structures like 'DataFrame'.
        
        Conversation:
        {conversation}

        Number of Records: {df_length}
        
    """
    return msg

def get_summary_llm(idataId, user_prompt, df_length):
    conversation = []
    retrieved_obj = get_conversation_cache(idataId)
    if retrieved_obj is not None:
        conversation = pickle.loads(retrieved_obj)
    logger.debug(f"conversation: \n{conversation}")
    msg = get_summary_prompt(conversation, user_prompt, df_length)
    str = chat_instructmode_llm(msg)
    return str.strip()

def processdata(user_prompt, idataId):
    conversation = []
    retrieved_obj = get_conversation_cache(idataId)
    if retrieved_obj is not None:
        conversation = pickle.loads(retrieved_obj)
    else:
        logger.debug("prior conversation not found for drill down request!")
        conversation = []
    df = pd.DataFrame()
    logger.debug("fetching data from cache..")
    df_s = get_idata_cache(idataId, "idata")
    df = pickle.loads(df_s)
    logger.debug("top 5 rows from cache...")
    logger.debug(df.head())
    logger.info(f"extracting schema from dataframe...")
    df_schema = extract_schema(df)
    
    if len(conversation) == 0:
        logger.debug("creating the first prompt for drill-down")
        prompt = get_initial_prompt(df_schema,user_prompt)
        conversation = create_conversation_message(prompt,conversation,"USER")
    else:
        user_prompt = f"{user_prompt}. You are given a pandas DataFrame with the following structure:{df_schema}."
        conversation = create_conversation_message(user_prompt,conversation,"USER")
    logger.debug("adding conversation to cache..")
    conversation_obj = pickle.dumps(conversation)
    set_conversation_cache(idataId,conversation_obj)
    logger.debug(conversation)
    logger.debug("calling llm with conversation...")
    response = chat_with_llm(conversation)
    generated_code = extract_python_code(response)
    logger.debug("Adding generated code as assistant message to the conversation...")
    conversation = create_conversation_message(generated_code,conversation,"ASSISTANT")
    logger.debug("adding conversation to cache..")
    conversation_obj = pickle.dumps(conversation)
    set_conversation_cache(idataId,conversation_obj)
    logger.debug(conversation)
    logger.debug(f"Generated Code:\n{generated_code}")

    local_namespace = {}
    try:
        logger.debug("executing the code as the first attempt...")
        exec(generated_code, globals(), local_namespace)
        filterdf = local_namespace.get('filterdf')
        df_data = filterdf(df)
    except Exception as e:
        error_message = f"Error in generated code: {str(e)}\nErroneous Code:\n{generated_code}"
        correction_prompt = f"Generated code failed with runtime error below, please regenerate the python code satisfying the user query. {error_message}"
        logger.debug(f"correction_prompt: {correction_prompt}")
        conversation = create_conversation_message(correction_prompt,conversation,"USER")
        logger.debug("adding conversation with correction prompt to cache..")
        conversation_obj = pickle.dumps(conversation)
        set_conversation_cache(idataId,conversation_obj)
        logger.debug("calling llm with correction prompt...")
        response = chat_with_llm(conversation)
        corrected_code = extract_python_code(response)
        logger.debug("Adding corrected code as assistant message to the conversation...")
        conversation = create_conversation_message(corrected_code,conversation,"ASSISTANT")
        logger.debug("adding conversation to cache..")
        conversation_obj = pickle.dumps(conversation)
        set_conversation_cache(idataId,conversation_obj)
        logger.debug(f"corrected_code: {corrected_code}")
        try:
            logger.debug("executing the code as the second attempt...")
            exec(corrected_code, globals(), local_namespace)
            filterdf = local_namespace.get('filterdf')
            df_data = filterdf(df)
        except Exception as final_error:
            logger.error(f"Critical error after correction: {final_error}")
            return {"error": "Failed to process data after correction attempt"}
    logger.debug(df_data)
    return df_data
    
def get_empty_graph():
    fig = go.Figure()

    fig.add_annotation(
        text="No Data to Display",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=25, color="crimson"),
        align="center"
    )

    # Update layout to remove axes visibility
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    # Convert the figure to JSON
    fig_json = pio.to_json(fig)

    # Load JSON into a Python dictionary
    fig_json_data = json.loads(fig_json)
    return fig_json_data

if __name__ == "__main__":
    input_prompt = (
            "Provide Python code only in your response to create a line graph using Plotly from the following DataFrame structure: {'Vendor Name', 'Total', 'Invoice Amount'}."
            "Include all necessary import statements. "
            "Create a method named create_graph that takes a dataframe as input and returns the figure object. "
            "Do not call fig.show() in the function, just return the figure."
            )
    df = pd.DataFrame({
        'Vendor Name': ['Vendor A', 'Vendor B', 'Vendor C', 'Vendor D'],
        'Total': [1000, 2000, 3000, 4000],
        'Invoice Amount': [800, 1800, 2800, 3800]
    })
    img_str = generate_graph(input_prompt, df)
    html_img_tag = f"<img style='display:block;width:400px;height:400px;' src='data:image/png;base64,{img_str}' alt='Chart'>"

