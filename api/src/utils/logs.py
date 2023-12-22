import datetime
import random
import string
import os
import time

from sqlalchemy import text
from sqlalchemy import create_engine

POSTGRES_USERNAME = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_URL = os.getenv('POSTGRES_URL')
POSTGRES_DATABASE = os.getenv('POSTGRES_DB')

def generate_custom_id():
    timestamp = str(int(time.time()))
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ID-{timestamp}-{random_chars}"


def log_apicall(query, api_url, response):
    ct = datetime.datetime.now()
    custom_id = generate_custom_id()

    params = {
        "query_id": custom_id,
        "question": query,
        "api_url": api_url,
        "response": response,
        "created_on": ct,
    }

    insert_query = text("""
        INSERT INTO datausa_logs.logs (query_id, question, api_url, response, created_on)
        VALUES (:query_id, :question, :api_url, :response, :created_on)
    """)

    engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/{}'.format(POSTGRES_USERNAME,POSTGRES_PASSWORD,POSTGRES_URL,POSTGRES_DATABASE))

    with engine.connect() as conn:
        conn.execute(insert_query, params)
       # conn.commit()
    
    return {"status": "success"}
