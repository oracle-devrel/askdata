# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import logging
import constants
import oci
from helpers.oci_helper_json import oci_helper as ocij

from helpers.config_json_helper import config_boostrap as confb

logger = logging.getLogger(constants.IO_LAYER)

def llm_create_str_embedding(input_str):
    if (input_str is None):
        logger.error("llm_create_str_embedding(input_str) input string should not be none")
        return None;

    logger.info(f"llm_create_str_embedding getting embedding: {input_str}")
    inputs = [input_str]

    embed_text_detail = oci.generative_ai_inference.models.EmbedTextDetails()
    embed_text_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=confb.dconfig["oci"]["ai"]["model_embed"])
    embed_text_detail.inputs = inputs
    embed_text_detail.truncate = "NONE"
    embed_text_detail.compartment_id = confb.dconfig["oci"]["compartment_ocid"]

    embed_text_response = ocij.get_llm_inference_client(endpoint=None).embed_text(embed_text_detail)
    (embd) = embed_text_response.data.embeddings
    return embd[0]

def query_oci_llama_DAC(llm_prompt):
    # llm_prompt test.1 ="Show all invoices"

    # Service endpoint
    # endpoint = confb.dconfig["oci"]["ai"]["genai_dac_endpoint"]
    endpointmodel = confb.dconfig["oci"]["ai"]["dac_endpoint_model"]
    # endpointmodel =  "ocid1.generativeaiendpoint.oc1.us-chicago-1.xxx"
    generative_ai_inference_client = ocij.get_llm_inference_client(endpoint=None)

    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    content = oci.generative_ai_inference.models.TextContent()
    content.text = llm_prompt
    message = oci.generative_ai_inference.models.Message()
    message.role = "USER"
    message.content = [content]
    chat_request = oci.generative_ai_inference.models.GenericChatRequest()
    chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
    chat_request.messages = [message]
    chat_request.max_tokens = 600
    chat_request.temperature = 0
    chat_request.frequency_penalty = 0
    chat_request.top_p = 0.5
    chat_request.top_k = -1
    # chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=endpointmodel)
    chat_detail.serving_mode = oci.generative_ai_inference.models.DedicatedServingMode(endpoint_id=endpointmodel)
    chat_detail.chat_request = chat_request
    chat_detail.compartment_id = confb.dconfig["oci"]["compartment_ocid"]
    chat_response = generative_ai_inference_client.chat(chat_detail)
    returnStr = chat_response.data.chat_response.choices[0].message.content[0].text
    return returnStr.strip()

def greg_query_oci_llama_DAC(llm_prompt):
    compartment_id = "<comp-id>"
    CONFIG_PROFILE = "DEFAULT"
    ociconfig = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)
    # Service endpoint
    endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
    endpointmodel =  "ocid1.generativeaiendpoint.oc1.us-chicago-1.xxx"
    
    generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=ociconfig,
                                                                                             service_endpoint=endpoint,
                                                                                             retry_strategy=oci.retry.NoneRetryStrategy(),
                                                                                             timeout=(10, 240))
    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    content = oci.generative_ai_inference.models.TextContent()
    content.text = llm_prompt
    message = oci.generative_ai_inference.models.Message()
    message.role = "USER"
    message.content = [content]
    chat_request = oci.generative_ai_inference.models.GenericChatRequest()
    chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
    chat_request.messages = [message]
    chat_request.max_tokens = 600
    chat_request.temperature = 0
    chat_request.frequency_penalty = 0
    chat_request.top_p = 0.5
    chat_request.top_k = -1
    #chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=endpointmodel)
    chat_detail.serving_mode = oci.generative_ai_inference.models.DedicatedServingMode(endpoint_id=
                "ocid1.generativeaiendpoint.oc1.us-chicago-1.xxx")
    chat_detail.chat_request = chat_request
    chat_detail.compartment_id = compartment_id
    chat_response = generative_ai_inference_client.chat(chat_detail)
    returnStr = chat_response.data.chat_response.choices[0].message.content[0].text
    return returnStr.strip()
