import json
import random
import string
import time
from datetime import datetime

from config import LOGS_TABLE_NAME, POSTGRES_ENGINE, SCHEMA_LOGS
from utils.functions import calculate_total_cost, dict_to_tuple, keys_to_tuple
from sqlalchemy import text


def generate_custom_id() -> str:
    """
    Generates a custom ID.

    Returns:
        str: The generated custom ID.
    """
    timestamp = str(int(time.time()))
    random_numbers = "00" + "".join(random.choices(string.digits, k=4))  # Generate 4 random digits

    return f"{timestamp}{random_numbers}"


def create_table(table: dict) -> None:
    """
    Creates a table if it doesn't exist for the requested configuration.

    Args:
        table (dict): contain the following entries:
            - "schema": table schema name
            - "name": table name
            - "columns": dict of columns with the shape: "COLUMN_NAME": "COLUMN_TYPE"
    """
    # we think there's a better aproach to create the .sql statement for creating the table,
    # for security reasons f functions are not recommended
    schema_query = text(f"CREATE SCHEMA IF NOT EXISTS {table['schema']}")
    table_query = text(f"CREATE TABLE IF NOT EXISTS {table['schema']}.{table['name']} ({dict_to_tuple(table['columns'])})")

    with POSTGRES_ENGINE.connect() as conn:
        conn.execute(schema_query)
        conn.execute(table_query)
        conn.commit()
        conn.close()


def insert_logs(table: dict, values: dict) -> None:
    """
    Insert the required logs from an API call into the respective database.

    Args:
        natural_language_query (str): The user's natural language query.
        api_url (str): The URL of the API endpoint.
        response (str): The response from the API.
        drilldowns (set): The set of drilldowns used in the API call.
        measures (set): The set of measures used in the API call.
        cuts (dict): The cuts used in the API call.
        cube: The cube used in the API call.
        start_time (float): The start time of the API call.
        tokens (dict): The tokens used in the API call.

    Returns:
        dict: A dictionary indicating the status of the operation.
    """
    # Check if values have the same columns as the table columns

    # Create table if it doesn't exists
    create_table(table=table)

    # Assign a query-id to the request
    values.update({"query_id": generate_custom_id()})

    # Assign creation time to the values dict
    creation_time = datetime.now()
    values.update({"created_on": creation_time})

    # Assign token costs in to the values dict
    costs = calculate_total_cost(values["total_tokens"])
    values.update({"total_tokens": costs["tokens"], "total_cost": costs["cost"]})

    # Insert logs in to the database
    # create function that creates :query_id, :query..........
    insert_query = text(f"""
        INSERT INTO {table['schema']}.{table['name']} {keys_to_tuple(table['columns'])}
        VALUES ('{values['query_id']}', '{values['question']}', '{values['api_url']}', '{values['response']}', '{values['cube']}', '{values['drilldowns']}', '{values['measures']}', '{values['cuts']}', '{values['created_on']}', '{values['duration']}', '{values['total_tokens']}', '{values['total_cost']}')
    """)

    with POSTGRES_ENGINE.connect() as conn:
        conn.execute(insert_query, values)
        conn.commit()


if __name__ == "__main__":
    table = {
        "name": "logs",
        "schema": "testing",
        "columns": {
            "query_id": "text",
            "question": "text",
            "api_url": "text",
            "response": "text",
            "created_on": "text",
            "drilldowns": "text",
            "measures": "text",
            "cuts": "text",
            "cube": "text",
            "duration": "text",
            "total_tokens": "text",
            "total_cost": "text",
        },
    }

    insert_logs(table=table)
