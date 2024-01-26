import random
import string
import time

from datetime import datetime
from os import getenv
from sqlalchemy import text
from sqlalchemy import create_engine

POSTGRES_USERNAME = getenv('POSTGRES_USER')
POSTGRES_PASSWORD = getenv('POSTGRES_PASSWORD')
POSTGRES_URL = getenv('POSTGRES_URL')
POSTGRES_DATABASE = getenv('POSTGRES_DB')

def generate_custom_id():
    timestamp = str(int(time.time()))
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ID-{timestamp}-{random_chars}"


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
        "cube": cube,
        "duration": duration
    }

    insert_query = text("""
        INSERT INTO datausa_logs.logs (query_id, question, api_url, response, created_on, drilldowns, measures, cuts, cube, duration)
        VALUES (:query_id, :question, :api_url, :response, :created_on, :drilldowns, :measures, :cuts, :cube, :duration)
    """)

    engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/{}'.format(POSTGRES_USERNAME,POSTGRES_PASSWORD,POSTGRES_URL,POSTGRES_DATABASE))

    with engine.connect() as conn:
        conn.execute(insert_query, params)
        conn.commit()

    return {"status": "success"}