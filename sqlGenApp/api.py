# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM, pipeline
import argparse
from fastapi import FastAPI, Request
import uvicorn, json, datetime
import sqlparse
import os
import re

def generate_prompt(question, prompt_file="prompt_sql.md", metadata_file="metadata.sql"):
    current_directory = os.getcwd()
    file_path = os.path.join(current_directory, prompt_file)
    with open(file_path, "r") as f:
        promptinput = f.read()
    #with open(metadata_file, "r") as f:
    #    table_metadata_string = f.read()
    import pruning as prn
    table_metadata_string = prn.get_metadata_str(question)
    substrings1 = ["top","highest", "greatest", "largest"]
    if any(substr1 in question.lower() for substr1 in substrings1):
        question = question + ". order by descending"
    substrings2 = ["bottom","lowest", "least"]
    if any(substr2 in question.lower() for substr2 in substrings2):
        question = question + ". make sure to order by ascending"
    promptinput = promptinput.format(
        user_question=question, table_metadata_string=table_metadata_string
    )
    print("question  \n" + promptinput)
    print("metadata:  \n" + table_metadata_string)
    return promptinput

def generate_query(question):
    updated_prompt = generate_prompt(question=question)
    #updated_prompt = prompt.format(question=question)
    inputs = tokenizer(updated_prompt, return_tensors="pt").to("cuda")
    generated_ids = model.generate(
        **inputs,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        max_new_tokens=400,
        do_sample=False,
        num_beams=1,
    )
    outputs = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    # empty cache so that you do generate more results w/o memory crashing
    return sqlparse.format(outputs[0].split("[SQL]")[-1], reindent=True)


app = FastAPI()


@app.post("/")
async def create_item(request: Request):
    response = "hello world"
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    question = json_post_list.get('question')
    text = generate_query(question)
    cleaned_text1 = re.sub(r'[\n\t]|\\n', ' ', text)
    cleaned_text2 = cleaned_text1.replace("[/SQL]","")
    cleaned_text3 = cleaned_text2.strip('"')
    cleaned_text4 = cleaned_text3.strip(' ')
    print("query  \n" + cleaned_text4)
    return cleaned_text4


if __name__ == '__main__':
    torch.cuda.is_available()
    available_memory = torch.cuda.get_device_properties(0).total_memory
    print(available_memory)
    #model_name = "defog/sqlcoder-7b-2"
    model_name = "Phind/Phind-CodeLlama-34B-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if available_memory > 15e9:
        # if you have atleast 15GB of GPU memory, run load the model in float16
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto",
            use_cache=True,
        )
    else:
        # else, load in 8 bits – this is a bit slower
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            # torch_dtype=torch.float16,
            load_in_8bit=True,
            device_map="auto",
            use_cache=True,
        )
    uvicorn.run(app, host='0.0.0.0', port=8000, workers=1)
