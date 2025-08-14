# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import logging
import os
import pickle
from sentence_transformers import SentenceTransformer
import re

# get package root directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_embeddings(emb_path: str, save_emb: bool = True) -> tuple[dict, dict]:
    """
    For each db, generate embeddings for all of the column names and descriptions
    """
    encoder = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2", device="cpu"
    )
    emb = {}
    csv_descriptions = {}
    glossary_emb = {}
    with open('/home/ubuntu/metadata.sql') as f:
        lines = f.readlines()
    lines_lcase = [x.lower().strip() for x in lines]
    varcharpattern = r'varchar2\(\d+\)'
    tablename =""
    db_name = "schemaname"
    column_descriptions = []
    column_descriptions_typed = []

    for i in lines_lcase:
        if i.startswith('--') or len(i) == 0 or i.startswith(');'):
            continue
        if i.startswith('create') :
            words = i.split()
            tablename = words[2]
            #print(tablename)
        else:
            if ',' in i:
               parts = i.split(',')
               column_name, data_type = parts[0].split()
               data_type = re.sub(varcharpattern, 'text', data_type).replace('number','bigint')
               column_description = parts[1].strip().lstrip('--').rstrip('.')
               #print(tablename+'.' + column_name +',' + data_type + ',' + column_description)
            else:
                index_of_dash = i.find("--")
                column_name, data_type = i[:index_of_dash].split()
                data_type = re.sub(varcharpattern, 'text', data_type)
                column_description = i[index_of_dash:].lstrip('- ').rstrip('.').replace('number','bigint')
                #print(tablename+'.' + column_name +',' + data_type + ',' + column_description)
            col_str = (
                tablename
                + "."
                + column_name
                + ": "
                + column_description
            )
            col_str_typed = (
                tablename
                + "."
                + column_name
                + ","
                + data_type
                + ","
                + column_description
            )
            column_descriptions.append(col_str)
            column_descriptions_typed.append(col_str_typed)
        column_emb = encoder.encode(column_descriptions, convert_to_tensor=True)
        emb[db_name] = column_emb
        csv_descriptions[db_name] = column_descriptions_typed
        glossary = []
        if len(glossary) > 0:
            glossary_embeddings = encoder.encode(glossary, convert_to_tensor=True)
        else:
            glossary_embeddings = []
        glossary_emb[db_name] = glossary_embeddings
    if save_emb:
        # get directory of emb_path and create if it doesn't exist
        emb_dir = os.path.dirname(emb_path)
        if not os.path.exists(emb_dir):
            os.makedirs(emb_dir)
        with open(emb_path, "wb") as f:
            pickle.dump((emb, csv_descriptions, glossary_emb), f)
            logging.info(f"Saved embeddings to file {emb_path}")
    return emb, csv_descriptions, glossary_emb

def clean_glossary(glossary: str) -> list[str]:
    """
    Clean glossary by removing number bullets and periods, and making sure every line starts with a dash bullet.
    """
    if glossary == "":
        return []
    glossary = glossary.split("\n")
    # remove empty strings
    glossary = list(filter(None, glossary))
    cleaned = []
    for line in glossary:
        # remove number bullets and periods
        line = re.sub(r"^\d+\.?\s?", "", line)
        # make sure every line starts with a dash bullet if it does not already
        line = re.sub(r"^(?!-)", "- ", line)
        cleaned.append(line)
    glossary = cleaned
    return glossary

def load_embeddings(emb_path: str) -> tuple[dict, dict]:
    """
    Load embeddings from file if they exist, otherwise generate them and save them.
    """
    if os.path.isfile(emb_path):
        logging.info(f"Loading embeddings from file {emb_path}")
        with open(emb_path, "rb") as f:
            emb, csv_descriptions, glossary_emb = pickle.load(f)
        return emb, csv_descriptions, glossary_emb
    else:
        logging.info(f"Embeddings file {emb_path} does not exist.")
        emb, csv_descriptions, glossary_emb = generate_embeddings(emb_path)
        return emb, csv_descriptions, glossary_emb


# entity types: list of (column, type, description) tuples
# note that these are spacy types https://spacy.io/usage/linguistic-features#named-entities
# we can add more types if we want, but PERSON, GPE, ORG should be
# sufficient for most use cases.
# also note that DATE and TIME are not included because they are usually
# retrievable from the top k embedding search due to the limited list of nouns
# NOT USED
columns_ner = {
    "schemaname": {
        "PERSON": [
            "dummy_tbl.biller,text,person responsible for issuing invoices",
        ],
        "ORG": [
            "dummy_tbl.company_id,text,company id",
        ],
        "MONEY": [
            "dummy_tbl.itd_tot_rev,bigint,total revenue inception to date",
        ],
        "DATE": [
            "dummy_tbl.gl_period,text,time period for general ledger entries",
        ],
        "LOC": [
            "dummy_tbl.project_location,text,location of the project",
        ],
        "QUANTITY": [
            "dummy_tbl.ptd_lbr_hrs,bigint,period-to-date labor hours",
        ],
        "PCT": [
            "dummy_tbl.cst_pct_complete,bigint,percentage of project cost completion",
        ],
    },
}
columns_join = {
    "schemaname": {
        ("company_lkp" , "dummy_tbl", ): [("company_lkp.company_id" , "dummy_tbl.company_id" )],
    },
}
