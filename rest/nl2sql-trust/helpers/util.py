import random
import re

def get_first(list):
    return list[0]

def get_random(list):
    return list[random.randint(0, len(list) - 1)]

def clean_sql(sql):
    tmp = sql.replace("\\n", " ").replace('"', '').replace(';', '').strip()
    tmp = re.sub(r'\s+', ' ', tmp)
    return tmp
    
def sort_result(rows):
    sql_type_prefix_set = []
    table_set = []

    tmp_list = []

    # create ordered sets
    for row in rows:
        tmp_table = row[0]
        tmp_prefix = row[1].split("_")[0]   #TODO: use process_file before input so split is not needed
        if tmp_table not in table_set:
            table_set.append(tmp_table)
        if tmp_prefix not in sql_type_prefix_set:
            sql_type_prefix_set.append(tmp_prefix)

    # order the input
    for t in table_set:
        for s in sql_type_prefix_set:
            for row in rows:
                if row[0] == t and row[1].split("_")[0] == s:
                    tmp_list.append(row)

    return tmp_list


#Precursor to clean_sql.
def format_sql_view(sql_str):
    #Check if string is empty
    if sql_str is None:
      return None
    if sql_str == 'null':
       return None
    if len(sql_str) == 0:
       return None
    
    return clean_sql(sql_str)