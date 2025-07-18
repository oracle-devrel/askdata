import json
import logging
import os
import constants
from helpers.llm_helper import query_oci_llama_DAC, greg_query_oci_llama_DAC, llm_create_str_embedding
from helpers.config_json_helper import config_boostrap as confb
confb.setup()

logger = logging.getLogger(constants.FINETUNE_LAYER)

logging.basicConfig(level=logging.DEBUG)

def test_dac_llm():
    ret = query_oci_llama_DAC(llm_prompt="Show all invoices")
    logger.debug(ret)

def test_llm_embeddings():
    ret = llm_create_str_embedding(input_str="Show all invoices")
    logger.debug(ret)