import random
import string
import time

from datetime import datetime
from sqlalchemy import text

from config import POSTGRES_ENGINE, LOGS_TABLE_NAME, SCHEMA_LOGS

def generate_custom_id():
    timestamp = str(int(time.time()))
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ID-{timestamp}-{random_chars}"


def create_table(table_name, schema_name):
    POSTGRES_ENGINE.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    POSTGRES_ENGINE.execute(f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (query_id text, question text, api_url text, response text, created_on text, drilldowns text, measures text, cuts text, cube text, duration text)")
    return


def log_apicall(query, api_url, response, drilldowns, measures, cuts, cube, duration):
    ct = datetime.now()
    custom_id = generate_custom_id()

    params = {
        "query_id": custom_id,
        "question": query,
        "api_url": api_url,
        "response": response,
        "created_on": ct,
        "drilldowns": drilldowns,
        "measures": measures,
        "cuts": cuts,
        "cube": cube.name,
        "duration": duration
    }
    
    create_table(LOGS_TABLE_NAME, SCHEMA_LOGS)

    insert_query = text("""
        INSERT INTO chat.logs (query_id, question, api_url, response, created_on, drilldowns, measures, cuts, cube, duration)
        VALUES (:query_id, :question, :api_url, :response, :created_on, :drilldowns, :measures, :cuts, :cube, :duration)
    """)

    with POSTGRES_ENGINE.connect() as conn:
        conn.execute(insert_query, params)
        conn.commit()

    return {"status": "success"}