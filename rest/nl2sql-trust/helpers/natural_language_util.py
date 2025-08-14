# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import difflib
import random
import string
from helpers import util as u
import logging
import constants

logger = logging.getLogger(constants.NATURAL_LANGUAGE_LAYER)

SP = " "

# aggregation
agg = ['What is', 'Calculate', 'Find']
agg_max = ['the highest']
agg_min = ['the lowest']
agg_count = ['the number of']
agg_sum = ['the sum of all']
agg_average = ['the average']

agg_max_d = ['the latest']
agg_min_d = ['the earliest']
agg_count_d = ['the number of']

# conditionality
cond_comp = ['equals']
cond_logic = ['and']
cond_date = ['before']

# select
s = ['Tell me', 'Show', 'Find', 'List']
s_all = ["Show each"]
s_max = agg_max
s_min = agg_min
s_count = agg_count
s_sum = agg_sum
s_average = agg_average

# where
w = ['where']

# group by
gb = ["for each", "broken down by", "grouped by"]

# order by
ord = ["sorted", "shown"]
ord_ascdesc = ["ascending", "descending", "from largest to smallest", "from smallest to largest"]

# limit
limit = ["the top 5", "the bottom 10", "the first twenty", "the last two"]

# TODO: ingest above from config file
# ---- do not change below -----


def get_aggr_quant_list():
    agg_functions = ["min", "max", "sum", "average"]
    tmp = []
    for agg_function in agg_functions:
        match agg_function:
            case "min":
                tmp.append(u.get_random(agg_min))
            case "max":
                tmp.append(u.get_random(agg_max))
            case "count":
                tmp.append(u.get_random(agg_count))
            case "sum":
                tmp.append(u.get_random(agg_sum))
            case "average":
                tmp.append(u.get_random(agg_average))
    return tmp

def get_limit_quant_list():
    agg_functions = ["min", "max"]
    tmp = []
    for agg_function in agg_functions:
        match agg_function:
            case "min":
                tmp.append(u.get_random(["the bottom 20", "the lowest ten"]))
            case "max":
                tmp.append(u.get_random(["the top 10", "the highest five"]))
    return tmp

def get_aggr_date_list():
    agg_functions = ["earliest", "latest", "count"]
    tmp = []
    for agg_function in agg_functions:
        match agg_function:
            case "earliest":
                tmp.append(u.get_random(agg_min_d))
            case "latest":
                tmp.append(u.get_random(agg_max_d))
            case "count":
                tmp.append(u.get_random(agg_count_d))
    return tmp

def get_limit_date_list():
    agg_functions = ["earliest", "latest"]
    tmp = []
    for agg_function in agg_functions:
        match agg_function:
            case "earliest":
                tmp.append(u.get_random(["the earliest 20", "the first ten"]))
            case "latest":
                tmp.append(u.get_random(["the latest 20", "the last ten"]))
    return tmp

def generate_nl_prompt_where(where_cols):
    col = u.get_random(where_cols)
    col_type = col["type"]
    domain = u.get_random(col["domain"])
    where = u.get_random(w)
    where_clause = ""

    match col_type:
        case "text":
            where_clause = where + SP + domain + " begins with " + random.choice(string.ascii_letters)

        case "quant":
            tmp = u.get_random(["is more than", "is greater than", "is less than", "equals"])
            tmp2 = u.get_random(["one", "1", "twenty", "20", "five and a half", "5.5"])
            where_clause = where + SP + domain + SP + tmp + SP + tmp2

        case "label":
            where_clause =  where + SP + domain + " is " + random.choice(string.ascii_letters) + random.choice(string.ascii_letters)

        case "date":
            tmp = u.get_random(["is before", "is after", "is"])
            tmp2 = u.get_random(["2024", "May 1 2024", "last Tuesday"])
            where_clause = where + SP + domain + SP + tmp + SP + tmp2

    return where_clause

def generate_nl_prompt_group(group_by_cols):

    col = u.get_random(group_by_cols)
    col_type = col["type"]

    group_clause = ""
    match col_type:
        case "label":
            group_clause = u.get_random(gb) + SP + u.get_random(col["domain"])
        case "date":
            group_clause = u.get_random(gb) + SP + u.get_random(["hour", "day of week", "month", "quarter", "year"])
    return group_clause

def generate_nl_prompt_order(nlb):
    if nlb.order_cols is None:
        return None

    col = u.get_random(nlb.order_cols[0].columns)
    col_type = col["type"]

    sort_order = []
    match col_type:
        case "text":
            sort_order = ["in alphabetically", "in alphabetical order ", "in reverse order"]
        case "quant" | "formula" | "condition":
            sort_order = ["from smallest to largest", "from largest to smallest", "ascending", "descending"]
        case "label":
            sort_order = ["in alphabetical order ", "in reverse alphabetical order"]
        case "date":
            sort_order = ["from earliest to latest", "from latest to earliest"]
        case "primarykey":
            sort_order = ["from smallest to largest", "from largest to smallest", "ascending", "descending"]

    sort_col = ""
    x = nlb.sql_type
    order_clause = None
    match x:
        case x if x.startswith("S_"):
            sort_col = u.get_random(col["domain"])
            order_clause = u.get_random(["sorting by"]) + SP + sort_col + SP + u.get_random(sort_order)
        case x if x.startswith("S.agg_G"):
            order_clause = u.get_random(ord) + SP + u.get_random(sort_order)
        case x if x.startswith("S.c") and "agg" not in x:
            order_clause = u.get_random(ord) + SP + u.get_random(sort_order)
        case x if "_L" in x:
            order_clause = u.get_random(ord) + SP + u.get_random(sort_order)

        # TODO: S.cc. and agg

    return nlb.nl_prompt + SP + order_clause

def generate_diff_string(orig_text, new_text):
    if orig_text == None or new_text == None: 
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