import openai

from os import getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load .env file if exists
load_dotenv()

# PostgreSQL Connection
POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = getenv("POSTGRES_HOST")
POSTGRES_DB = getenv("POSTGRES_DB")
POSTGRES_PORT = 5432

if POSTGRES_HOST:
    POSTGRES_ENGINE = create_engine("postgresql+psycopg2://{}:{}@{}:{}/{}".format(POSTGRES_USER,POSTGRES_PASSWORD,POSTGRES_HOST,POSTGRES_PORT,POSTGRES_DB))
else:
    print("POSTGRES_HOST not found, please check your environment")
    exit(1)

SCHEMA_TABLES = getenv("SCHEMA_TABLES")
SCHEMA_DRILLDOWNS = getenv("SCHEMA_DRILLDOWNS")
CUBES_TABLE_NAME = getenv("CUBES_TABLE_NAME")
DRILLDOWNS_TABLE_NAME = getenv("DRILLDOWNS_TABLE_NAME")

# OpenAI Connection
OPENAI_KEY = getenv("OPENAI_KEY")

if OPENAI_KEY:
    openai.api_key = OPENAI_KEY
else:
    print("OPENAI_KEY not found, please check your environment")
    exit(1)

# OLLAMA Connection
OLLAMA_API = getenv("OLLAMA_API")

# Tesseract Connection
TESSERACT_API = getenv("TESSERACT_API")

# Mondrian Connection

MONDRIAN_API = getenv('MONDRIAN_API')

# Files Directories
TABLES_PATH = getenv('TABLES_PATH')
FEW_SHOT_PATH = getenv('FEW_SHOT_PATH')

