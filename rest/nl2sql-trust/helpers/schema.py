import json
from helpers import util as u


def load_schema(path_to_schema):
    with open(path_to_schema) as f:
        schema = json.load(f)
        print("loaded: " + path_to_schema)
        return schema


def get_cols_by_type(columns, col_type):
    tmp = []
    for col in columns:
        if col["type"] == col_type:
            tmp.append(col)
    return tmp


def get_cols_with_domain(columns):
    tmp = []
    for col in columns:
        if "domain" in col.keys():
            tmp.append(col)
    return tmp


def get_col_domains_by_type(columns, col_type):
    cols = get_cols_by_type(columns, col_type)
    tmp = []
    for col in cols:
        tmp.append(u.get_random(col["domain"]))
    return tmp


def get_col_names_by_type(columns, col_type):
    cols = get_cols_by_type(columns, col_type)
    tmp = []
    for col in cols:
        tmp.append(col["name"])
    return tmp


def get_table_by_name(schema, table_name):
    for table in schema["tables"]:
        if table["name"] == table_name:
            return table


def get_column_by_name(schema, table_name, column_name):
    table = get_table_by_name(schema, table_name)
    for col in table["columns"]:
        if col["name"] == column_name:
            return col


def get_group_by_columns(columns):
    tmp = []
    type_list = ["label", "date"]
    for col in columns:
        if col["type"] in type_list:
            tmp.append(col)
    return tmp


# TODO: deprecate
def xxxxget_bus_rules_by_type(bus_rules, bus_rule_type):
    tmp = []
    for br in bus_rules:
        if br["type"] == bus_rule_type:
            tmp.append(br)
    return tmp

def get_bus_rules_by_type(table, bus_rule_type):
    tmp = []
    if "business-rules" in table.keys():
        for br in table["business-rules"]:
            if br["type"] == bus_rule_type:
                tmp.append(br)
    return tmp

def get_bus_rules(table):
    tmp = []
    if "business-rules" in table.keys():
        for br in table["business-rules"]:
            tmp.append(br)
    return tmp

def get_columns(table):
    tmp = []
    for column in table['columns']:
        if 'domain' in column.keys():
                tmp.append(column)
    return tmp


def get_tables_with_col_type(schema, col_type):
    tables = []
    for table in schema["tables"]:
        tmp = get_cols_by_type(table["columns"], col_type)
        if len(tmp) > 0:
            tables.append(table)
    return tables


def get_join_tables(schema):
    # TODO generate 3 or more joins
    join_tables = []

    # get all tables that have one or more foreign keys (ie can be joined to)
    fk_tables = get_tables_with_col_type(schema, "foreignkey")

    # iterate tables with foreign keys and find the primary keys of other tables to join to
    for fk_table in fk_tables:
        for table in schema["tables"]:

            # iterate all the foreign keys in a single table
            fk_cols = get_cols_by_type(fk_table["columns"], "foreignkey")
            for fk_col in fk_cols:

                # find the primary key to join the table
                join_col = get_cols_by_type(table["columns"], "primarykey")

                if len(join_col) > 0 and join_col[0]["name"] == fk_col["name"]:
                    join_tables.append([fk_table, table])
    return join_tables

