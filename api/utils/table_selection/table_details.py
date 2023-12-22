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
            for column in table.get("variables", []):
                if column["name"] == variable_name and "hierarchies" in column:
                    return column["hierarchies"]
    return None


def get_table_schemas(table_names: List[str] = None) -> Tuple[str, str]:
    """
    Returns table name, columns and description. Also returns any custom type and valid values for a column (enums).
    """
    table_details = load_tables_json(TABLES_PATH)

    tables_list = []
    
    if table_names:
        for table in table_details['tables']:
            if table['name'] in table_names:
                tables_list.append(table)
    else:
        tables_list = table_details["tables"]

    tables_str_list = []

    for table in tables_list: 
        tables_str = f"table name: {table['name']}\n"
        tables_str += f"table description: {table['description']}\n"

        dimensions_str_list = []
        for dimension in table['variables']:
            if dimension.get('description'):
                dimensions_str_list.append(f"{dimension['name']} ({dimension['description']})")
            else:
                dimensions_str_list.append(f"{dimension['name']}")
        
        measures_str_list = []
        for measure in table['measures']:
            if measure.get('description'):
                measures_str_list.append(f"{measure['name']} ({measure['description']})")
            else:
                measures_str_list.append(f"{measure['name']}")

        tables_str += f"table dimensions: {', '.join(dimensions_str_list)}\n"
        tables_str += f"table measures: {', '.join(measures_str_list)}\n"
        tables_str_list.append(tables_str)
    tables_description = "\n\n".join(tables_str_list)

    return tables_description
    #return tables_description, enums_description

#def get_minimal_table_schemas() -> str:


def get_table_columns(table_names: List[str] = None) -> Tuple[str, str]:
    """
    Returns table name, columns and description. Also returns any custom type and valid values for a column (enums).
    """
    table_details = load_tables_json(TABLES_PATH)

    tables_list = []
    
    if table_names:
        for table in table_details['tables']:
            if table['name'] in table_names:
                tables_list.append(table)
    else:
        tables_list = table_details["tables"]

    tables_str_list = []

    for table in tables_list: 
        tables_str = f"table name: {table['name']}\n"
        tables_str += f"table description: {table['description']}\n"

        dimensions_str_list = []
        for dimension in table['variables']:
            if dimension.get('description'):
                dimensions_str_list.append(f"\n{dimension['name']} ({dimension['description']}) [Parent dimension: {dimension['parent dimension']}]")
            else:
                dimensions_str_list.append(f"\n{dimension['name']} [Parent dimension: {dimension['parent dimension']}]")
        
        measures_str_list = []
        for measure in table['measures']:
            if measure.get('description'):
                measures_str_list.append(f"\n{measure['name']} ({measure['description']})")
            else:
                measures_str_list.append(f"\n{measure['name']}")

        tables_str += f"Variables: {' '.join(dimensions_str_list)}\n\n"
        tables_str += f"Measures: {' '.join(measures_str_list)}\n\n"
        tables_str_list.append(tables_str)
    tables_description = "\n\n".join(tables_str_list)

    return tables_description