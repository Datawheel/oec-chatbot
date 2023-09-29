import openai

from os import getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

TESSERACT_URL = getenv("TESSERACT_URL")
OPENAI_KEY = getenv("OPENAI_KEY")

POSTGRES_DB = getenv("POSTGRES_DB")
POSTGRES_URL = getenv("POSTGRES_URL")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_USER = getenv("POSTGRES_USER")

EVENTS_DB = getenv("EVENTS_DB")
EVENTS_URL = getenv("EVENTS_URL")
EVENTS_PASSWORD = getenv("EVENTS_PASSWORD")
EVENTS_USER = getenv("EVENTS_USER")

openai.api_key = OPENAI_KEY

if POSTGRES_URL:
    ENGINE = create_engine('postgresql+psycopg2://{}:{}@{}:5432/{}'.format(POSTGRES_USER,POSTGRES_PASSWORD,POSTGRES_URL,POSTGRES_DB))
    dialect_mapping = {
        "postgresql": "PostgreSQL 14",
    }
    DIALECT = dialect_mapping.get(ENGINE.dialect.name)
else:
    print('POSTGRES_URL not found, please check your environment')
    exit(1)

if EVENTS_URL:
    EVENTS_ENGINE = create_engine(EVENTS_URL)
else:
    EVENTS_ENGINE = None
