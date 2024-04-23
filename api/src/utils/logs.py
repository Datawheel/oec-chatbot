import json
import random
import string
import time

from datetime import datetime
from sqlalchemy import text

from config import POSTGRES_ENGINE, LOGS_TABLE_NAME, SCHEMA_LOGS

def generate_custom_id() -> str:
    """
    Generates a custom ID.

    Returns:
        str: The generated custom ID.
    """
    timestamp = str(int(time.time()))
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ID-{timestamp}-{random_chars}"

def create_table(table_name: str, schema_name: str) -> None:
    """
    Creates a table in the specified schema if it doesn't exist.

    Args:
        table_name (str): The name of the table to create.
        schema_name (str): The name of the schema where the table should be created.
    """
    POSTGRES_ENGINE.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    POSTGRES_ENGINE.execute(f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (query_id text, question text, api_url text, response text, created_on text, drilldowns text, measures text, cuts text, cube text, duration float, total_tokens int, total_cost float)")
    return

def log_apicall(
    natural_language_query: str,
    api_url: str,
    response: str,
    drilldowns: set,
    measures: set,
    cuts: dict,
    cube,
    start_time: float,
    tokens: dict,
) -> dict:
    """
    Logs an API call in the database.

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
    ct = datetime.now()
    custom_id = generate_custom_id()

    # Convert sets and dict to JSON strings
    drilldowns_list = list(drilldowns)
    measures_list = list(measures)
    cuts_dict = {key: list(value) for key, value in cuts.items()}

    drilldowns_json = json.dumps(drilldowns_list)
    measures_json = json.dumps(measures_list)
    cuts_json = json.dumps(cuts_dict)

    duration = time.time() - start_time

    # Calculate total tokens and total cost
    total_tokens = 0
    total_cost = 0
    
    if 'request_tables_to_lm_from_db' in tokens:
        total_tokens += tokens['request_tables_to_lm_from_db'].get('total_tokens', 0)
        total_cost += tokens['request_tables_to_lm_from_db'].get('total_cost', 0)
        
    if 'get_api_params_from_lm' in tokens:
        total_tokens += tokens['get_api_params_from_lm'].get('total_tokens', 0)
        total_cost += tokens['get_api_params_from_lm'].get('total_cost', 0)
        
    if 'agent_answer' in tokens:
        total_tokens += tokens['agent_answer'].get('total_tokens', 0)
        total_cost += tokens['agent_answer'].get('total_cost', 0)

    params = {
        "query_id": custom_id,
        "question": natural_language_query,
        "api_url": api_url,
        "response": response,
        "created_on": ct,
        "drilldowns": drilldowns_json,
        "measures": measures_json,
        "cuts": cuts_json,
        "cube": cube.name,
        "duration": duration,
        "total_tokens": total_tokens,
        "total_cost": total_cost
    }
    
    create_table(LOGS_TABLE_NAME, SCHEMA_LOGS)

    insert_query = text("""
        INSERT INTO chat.logs (query_id, question, api_url, response, created_on, drilldowns, measures, cuts, cube, duration, total_tokens, total_cost)
        VALUES (:query_id, :question, :api_url, :response, :created_on, :drilldowns, :measures, :cuts, :cube, :duration, :total_tokens, :total_cost)
    """)

    with POSTGRES_ENGINE.connect() as conn:
        conn.execute(insert_query, params)
       # conn.commit()

    return {"status": "success"}