import oci
import configparser
import re
from oci.signer import Signer
import requests
import sseclient
import json
import logging
import os

logger = logging.getLogger("app_logger")
config = configparser.RawConfigParser()
config.read('ConfigFile.properties')

CONFIG_PROFILE = "DEFAULT"
ociconfig = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)
active_endpoint = config.get('OCI', 'serviceendpoint.active')
dac_endpt = ""
compartment_id = ""
ondemand_model_id = ""
dialect = config.get('GenAISQLGenerator', 'sql.dialect')

if active_endpoint == 'DAC':
    endpoint       = config.get('OCI', 'serviceendpoint.dac_url')
    compartment_id = config.get('OCI', 'serviceendpoint.dac_ocid')
    dac_endpt      = config.get('OCI', 'serviceendpoint.dac_endpt')
else:
    endpoint          = config.get('OCI', 'serviceendpoint.url')
    compartment_id    = config.get('OCI', 'serviceendpoint.ocid')
    ondemand_model_id = config.get('OCI', 'serviceendpoint.model')


conversation = []

def get_domain_filename(domain):
    if domain:
        domain_filename = f"{domain.lower()}.sql"
    else:
        domain_filename = config.get('METADATA', 'default')
    return domain_filename

def read_file_to_string(filename):
    # Open the file in read mode and read the contents into a string
    base_path = config.get('METADATA', 'basepath')
    full_path = os.path.join(base_path, filename)
    logger.info(f"Reading metadata from: {full_path}")
    with open(full_path, 'r') as file:
        file_content = file.read()
    return file_content

def create_message(role, text):
    content = oci.generative_ai_inference.models.TextContent()
    content.text = text
    message = oci.generative_ai_inference.models.Message()
    message.role = role
    message.content = [content]
    return message

def ds_llm(messages):
    logger.debug("***************** ds_llm *****************")
    auth = Signer(
            tenancy=ociconfig['tenancy'],
            user=ociconfig['user'],
            fingerprint=ociconfig['fingerprint'],
            private_key_file_location=ociconfig['key_file'],
            pass_phrase=ociconfig['pass_phrase'])
    if isinstance(messages, str):
        # For instruct mode where str will be passed
        transformed_messages = [
            {
                "role": "USER",
                "content": [{"type": "text", "text": messages}]
            }
        ]
    else:
        transformed_messages = [
                {
                    "role": msg.role,
                    "content": [{"type": "text", "text": msg.content[0].text}]
                } for msg in messages
        ]
    logger.debug("transformed_messages:" + json.dumps(transformed_messages, indent=2))
    endpoint = config.get('OCI', 'serviceendpoint.ds_endpt')
    model = config.get('OCI', 'serviceendpoint.ds_model')
    body = {
            "model": model,
            "messages": transformed_messages,
            "max_tokens":500,
            "temperature":0,
            "top_k":50,
            "top_p":0.99,
            "stop":[],
            "frequency_penalty":0,
            "presence_penalty":0
            }
    headers={'Content-Type':'application/json', 'Accept': 'text/event-stream'}
    try:
        #response = requests.post(endpoint, json=body, auth=auth, headers={}).json()
        response = requests.post(endpoint, json=body, auth=auth, stream=True, headers=headers)
        logger.debug("response content:" + response.text)
        response_json = json.loads(response.text)
        response_content = response_json['choices'][0]['message']['content']
        return response_content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error: {e}")
        logger.error(f"Response status code: {response.status_code}")
        logger.error(f"Response content: {response.text}")
        raise

def chat_with_llm(messages):
    logger.debug("***************** chat_with_llm *****************")
    if active_endpoint == 'DS':
        return ds_llm(messages)
    else:
        generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                config=ociconfig,
                service_endpoint=endpoint,
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10,240)
                )
        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        chat_request = oci.generative_ai_inference.models.GenericChatRequest()
        chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
        chat_request.messages = messages
        chat_request.max_tokens = 600
        chat_request.temperature = 0
        chat_request.frequency_penalty = 0
        chat_request.presence_penalty = 0
        chat_request.top_p = 0.75
        chat_request.top_k = -1
        #chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
        if active_endpoint == 'DAC':
            chat_detail.serving_mode = oci.generative_ai_inference.models.DedicatedServingMode(
                    endpoint_id=dac_endpt
                    )
        else:
            chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
                    model_id=ondemand_model_id
                    )
        chat_detail.chat_request = chat_request
        chat_detail.compartment_id = compartment_id
        return generative_ai_inference_client.chat(chat_detail)

def chat_instructmode_llm(llmqry: str ):
    logger.debug("*****************chat_instructmode_llm**************************")
    if active_endpoint == 'DS':
        return ds_llm(llmqry)
    else:
        generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=ociconfig, service_endpoint=endpoint, retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        content = oci.generative_ai_inference.models.TextContent()
        content.text = llmqry
        message = oci.generative_ai_inference.models.Message()
        message.role = "USER"
        message.content = [content]
        chat_request = oci.generative_ai_inference.models.GenericChatRequest()
        chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
        chat_request.messages = [message]
        chat_request.max_tokens = 600
        chat_request.temperature = 0
        chat_request.frequency_penalty = 0
        chat_request.top_p = 0.75
        chat_request.top_k = -1
        #chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
        if active_endpoint == 'DAC':
            chat_detail.serving_mode = oci.generative_ai_inference.models.DedicatedServingMode(
                    endpoint_id=dac_endpt
                    )
        else:
            chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
                    model_id=ondemand_model_id
                    )
        chat_detail.chat_request = chat_request
        chat_detail.compartment_id = compartment_id
        chat_response = generative_ai_inference_client.chat(chat_detail)
        returnStr = chat_response.data.chat_response.choices[0].message.content[0].text
        # Print result
        logger.debug(f"Response: {returnStr}")
        return returnStr.strip()

def llm_instruction_for_equiv(first, second):
    msg = """
        This is a natural language to sql (nl2sql) prompt: {0}
        This is a second natural language to sql (nl2sql) prompt: {1}
        Each line below represents words that can be considered equivalent
        - invoice, bill, payable
        - days past due, payment delay
        - general ledger, gl
        Above is not an exhaustive list use common sense as necessary.
        Question: will these produce the same sql
        Answer simply as: YES or NO. Do not provide any explanations.
    """
    return msg.format(first, second)

def llm_instruction_seek_clarification(errcode, err,quest,metadata):
    msg = """
        Our NL2SQL tool was presented with the following user question: {0}
        Unfortunately the NL2SQL tool was not able to return data and instead returned the following error:
        error code: {1}
        error text: {2}
        Likely cause of the error is the that the user prompt is ambiguios, it uses custom jargon, it uses custom business rules, it is irrelevant to context the conversation thread or it can't be answered by the fields present in the following metadata:
        {3}
        Instructions:
        - Carefully look at the error message, user question and the metadata and construct a polite response asking the user to clarify.
        - If the likely cause is a missing field in metadata, ambiguous acronym, missing business rule, then point that out.
        - When responding, paraphrase the missing field or ambiguous acronym or missing business rule from user prompt.
        - Do not give out details of available metadata fields.
        - Long responses are unacceptable, keep the response less 23 words.
        - Do not provide a solution.
        - Do do perform any analysis.
        - Answer in a single sentence using professional business language that is pertinent to the provided metadata.
        - For any data deletion or data truncate request, return "operation not allowed"
        - Data removal is never allowed
        Examples:
        User: I want to see data for crazy mountains
        Assistant: To better assist with your query, could you please elaborate what is meant by "crazy mountains"?

        User: I want to see data for truckloads
        Assistant: Apologies, it seems you’re referring to truckloads data, which isn’t available, could you please elaboate?
    """
    return msg.format(errcode, err,quest,metadata)

def llm_instruction_forsql_equiv(first, second):
    msg = """
        Below are two sql statements:
        SQL statement 1: {0}
        SQL statement 2: {1}

        Instructions:
        Tell me if these two sql statements are have the same sql structure.
        For this to be true, each of the following must be true
        - SELECT clause: aggregations must be identical
        - WHERE clause: the columns in the where clause must be the same
        - WHERE clause: ignore difference if due to value of number, date or text
        - WHERE clause: ignore differences in alias names
        - WHERE clause: the number of where clauses must be equal except when comparing ranges of the same column
        - FROM clause: must be identical
        - GROUP BY: must be identical
        - ORDER BY:ascending and descending must be identical
        - FETCH or LIMIT: ignore this difference

        Answer only: YES or NO and do not provide explanations.
    """
    return msg.format(first, second)

def followup_prompt(userprompt: str):
    msg = """ I am starting a natural language to sql (NL2SQL) dialogue.
    The user's natural language prompt is: {0}

    If this is the first message in the chat history, please answer: {0}

    If this is not the first message in the chat history, use the provided followup to return a reworded NL2SQL prompt that closely represents the followup.
    Instructions:
    - Do not provide any explanation. Never return SQL.  Simply return a concise business pertinent NL2SQL prompt.
    - If the followup creates ambiguity simply answer: I'm sorry, could you state this more clearly
    - If the user prompt is just appreciation or greeting with no questhion simply answer: Great thank you, how can I assist further
    - If the user prompt just negative comment with no questhion simply answer: I'm sorry, could you state this more clearly
    """
    return msg.format(userprompt)

def get_sql_prompt(metadata,question,dialect):
    prmpt = """
    Using the METADATA and the INSTRUCTIONS provided, create a SQL query for the user prompt given below.
    User prompt: {1}

    Your query should be syntactically correct sql in {2} dialect.

    INSTRUCTIONS:
       -   If what the prompt is asking for does not clearly relate to the below metadata tables or columns or to the below business rules, do not generate a SQL query.  Instead answer: 'Please clarify.'
        -  Use column names from the metadata below with no exceptions.
        -  Do not provide any explanations. Only output query.
        -  Make the query explict and readable.  Use table aliases
        -  Return a minimal number of columns that are relevant to the prompt and meaningful to the business user
        -  Do not aggregate unless the prompt specifies
        -  For aggregation(s) in the select clause, only group by column(s) used for the aggregation(s)
        -  For dates in the where clause, use equality instead of ranges when possible and use 'extract' instead of 'to_date'
        -  For dates in the where clause, specify the date as a number and do not derive from current date if possible
        -  For numbers or dates in the where clause, specify ranges if possible and do not use 'between'
        -  Avoid using Primary keys or Join keys in the select clause if possible
        -  Do not order by unless the user prompt specifies

    Business Rules:
        -  critical invoice: amount due is > $1000 and days past due > 7

    METADATA:
    {0}
    """
    prmpt = prmpt.format(metadata,question,dialect)
    #logger.debug(prmpt)
    return prmpt

def seek_explanation(convoprompt,sql,domain):
    # excluding metadata 
    #metadata  = get_domain_filename(domain)
    #schemaddl = read_file_to_string(metadata)
    #msg = llm_seek_explanation(convoprompt,sql,schemaddl)
    msg = llm_seek_explanation(convoprompt,sql)
    str = chat_instructmode_llm(msg)
    return str.strip()

def llm_seek_explanation(convoprompt,sql):
    msg = """
        You need to look at the provided SQL, user prompt, and then provide a clear concise business explanation of what the SQL does.
        Make sure there are no LLM halucinations.
        Instructions:
        - Explanation must be brief and not more than 2 sentences.
        - Use respectful business language.
        - Explanation is intended for non technical users, hence use business descriptions of tables and columns.
        User prompt: {0}
        SQL: {1}
    """
    return msg.format(convoprompt,sql)

def seek_intent(convoprompt,explanation):
    msg = llm_seek_intent(convoprompt,explanation)
    str = chat_instructmode_llm(msg)
    return str.strip(" \t\n.")

def llm_seek_intent(convoprompt,explanation):
    msg = """
        You are responsible for analyzing the explanation produced by a LLM to double check that if it actually answers user's query.
        You need to look at the provided user prompt, explanation and then determine if the intent of explanation matches to user prompt. 
        Make sure there are no LLM halucinations.
        Instructions:
        - If the intent of the user prompt matches intent of your explanation then return YES.
        - If the intent of the user prompt does not match the intent of your explanation then return NO.
        - Your response must be 'YES' or 'NO'
        User prompt: {0}
        Explanation: {1}
    """
    return msg.format(convoprompt,explanation)

def chat_conversion(msg, prompt_conversation):
    if len(prompt_conversation) == 0:
        msg = followup_prompt(msg)
        user_message = create_message("USER", msg)
    else:
        user_message = create_message("USER", msg)
    prompt_conversation.append(user_message)
    response = chat_with_llm(prompt_conversation)
    if active_endpoint == 'DS':
        assistant_response = create_message("ASSISTANT", response)
        prompt_conversation.append(assistant_response)
        logger.debug("reworded prompt: " +response)
        return response, prompt_conversation
    else:
        response_content = response.data.chat_response.choices[0].message.content[0].text
        assistant_response = create_message("ASSISTANT", response_content)
        prompt_conversation.append(assistant_response)
        logger.debug("reworded prompt: " + response_content)
        return response_content, prompt_conversation

def create_user_message(prmpt,conversation,domain):
    if len(conversation) == 0:
        metadata  = get_domain_filename(domain)
        logger.debug(f"Domain filename is: {metadata}")
        schemaddl = read_file_to_string(metadata)
        sqlprompt = get_sql_prompt(schemaddl,prmpt,dialect)
        user_message = create_message("USER", sqlprompt)
    else:
        user_message = create_message("USER", prmpt)
    return user_message

def create_assistant_message(prmpt):
    assistant_message = create_message("ASSISTANT", prmpt)
    return assistant_message

def get_llm_sql(conversation):
    response = chat_with_llm(conversation)
    if active_endpoint == 'DS':
        #response_json = json.loads(response.text)
        #response_json['choices'][0]['message']['content']
        parse_output = parse_select_query(response)
    else:
        parse_output = parse_select_query(response.data.chat_response.choices[0].message.content[0].text)
    if parse_output ==  "SQL not found":
        return "Please clarify."
    else:
        return parse_output

def check_sql_equiv(first, second):
    msg = llm_instruction_forsql_equiv(first, second)
    str = chat_instructmode_llm(msg)
    return str.strip().upper(), msg

def get_prompt_equiv(first, second):
    msg = llm_instruction_for_equiv(first, second)
    str = chat_instructmode_llm(msg)
    return str.strip().upper()

def seek_clarification(errcode,err,quest,domain):
    metadata  = get_domain_filename(domain)
    schemaddl = read_file_to_string(metadata)
    msg = llm_instruction_seek_clarification(errcode,err,quest,schemaddl)
    str = chat_instructmode_llm(msg)
    return str.strip()

def check_graphing_request(prompt: str):
    msg = """
    ## Instructions
    Below is a request posted by the user. Figure out if the request is to make a graph. The request must contain the word 'graph' or 'chart'. If it is a graphing request then return YES otherwise return NO.
    {0}
    """
    msg = msg.format(prompt)
    ret = chat_instructmode_llm(msg)
    if ret.upper() == 'YES':
        return True
    else:
        return False

def parse_select_query(sql):
    match = re.search(r"(?i)(select\s+.*?)(;|```|$)", sql, re.DOTALL)
    if match:
        return match.group(1).strip()
    logger.debug("SQL not found")
    return "SQL not found"
