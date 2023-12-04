import json
from typing import List, Tuple
import re

from os import getenv
from utils.preprocessors.text import extract_text_from_markdown_single_backticks

TABLES_PATH = getenv('TABLES_PATH')

def load_tables_json(TABLES_PATH):
    table_details = {}
    with open(TABLES_PATH, "r") as f:
        table_details = json.load(f)

    return table_details


def get_table_names() -> List[str]:
    """
    Gets table names.
    """
    table_details = load_tables_json(TABLES_PATH)
    return [table["name"] for table in table_details["tables"]]


def get_table_api_base(table_name):
    table_details = load_tables_json(TABLES_PATH)
    tables = table_details.get("tables", [])

    for table in tables:
        if table.get("name") == table_name:
            return table.get("api")
    
    return None


def get_drilldown_levels(table_name, variable_name):
    table_details = load_tables_json(TABLES_PATH)
    for table in table_details.get("tables", []):
        if table["name"] == table_name:
            for column in table.get("columns", []):
                if column["name"] == variable_name and "levels" in column:
                    return column["levels"]
    return None


def get_table_schemas(table_names: List[str] = None) -> Tuple[str, str]:
    """
    Returns table name, columns and description. Also returns any custom type and valid values for a column (enums).
    """
    table_details = load_tables_json(TABLES_PATH)

    enums_list = []
    tables_list = []
    
    enums_list = table_details.get("enums", [])
    if table_names:
        for table in table_details['tables']:
            if table['name'] in table_names:
                tables_list.append(table)
    else:
        tables_list = table_details["tables"]

    enums_str_set = set()
    tables_str_list = []

    for table in tables_list: 
        tables_str = f"table name: {table['name']}\n"
        tables_str += f"table description: {table['description']}\n"
        columns_str_list = []
        for column in table['columns']:
            if column.get('description'):
                columns_str_list.append(f"{column['name']} [{column['type']}] ({column['description']})")
                if 'enums' in column['description']:
                    enums_str_set.add(extract_text_from_markdown_single_backticks(column['description']))
            else:
                columns_str_list.append(f"{column['name']} [{column['type']}]")
        tables_str += f"table columns: {', '.join(columns_str_list)}\n"
        tables_str_list.append(tables_str)
    tables_description = "\n\n".join(tables_str_list)

    enums_str_list = []
    for custom_type_str in enums_str_set:
        custom_type = next((t for t in enums_list if t["type"] == custom_type_str), None)
        if custom_type:
            enums_str = f"custom type: {custom_type['type']}\n"
            enums_str += f"valid values: {', '.join(custom_type['valid_values'])}\n"
            enums_str_list.append(enums_str)
    enums_description = "\n\n".join(enums_str_list)

    return tables_description
    #return tables_description, enums_description

#def get_minimal_table_schemas() -> str: