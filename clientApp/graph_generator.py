# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import oci
import re
import pandas as pd
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
from decimal import Decimal
from llm_handler import create_message, chat_with_llm, chat_instructmode_llm

logger = logging.getLogger("app_logger")
config = configparser.RawConfigParser()
config.read('ConfigFile.properties')

CONFIG_PROFILE = "DEFAULT"
ociconfig = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

def extract_python_code(text):
    pattern = r'```python\s(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return None
    else:
        return matches[0]

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

