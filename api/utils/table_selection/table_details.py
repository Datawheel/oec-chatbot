import json
from typing import List, Tuple
import re


table_details = {}
with open("data/tables.json", "r") as f:
    table_details = json.load(f)


def extract_text_from_markdown(text):
    """
    Extracts any sub-string enclosed within backticks in a string.
    """
    regex = r"`([\s\S]+?)`"
    matches = re.findall(regex, text)

    if matches:
        extracted_text = matches[0]
    else:
        extracted_text = text

    return extracted_text


def get_table_names() -> List[str]:
    """
    Gets table names.
    """
    return [table["name"] for table in table_details["tables"]]


def get_table_schemas(table_names: List[str] = None) -> Tuple[str, str]:
    """
    Returns table name, columns and description. Also returns any custom type and valid values for a column (enums).
    """
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
                    enums_str_set.add(extract_text_from_markdown(column['description']))
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

    return enums_description + "\n\n" + tables_description
    #return tables_description, enums_description


def get_minimal_table_schemas(scope="USA") -> str:
    
    tables_list = []

    tables_list = table_details["tables"]

    tables_str_list = []
    for table in tables_list:
        tables_str = f"table name: {table['name']}\n"
        tables_str += f"table description: {table['description']}\n"
        tables_str_list.append(tables_str)

    tables_description = "\n\n".join(tables_str_list)

    # return tables_description
    return tables_description
