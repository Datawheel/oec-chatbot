import openai

from dotenv import load_dotenv
from os import getenv
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
SCHEMA_LOGS = getenv("SCHEMA_LOGS")
CUBES_TABLE_NAME = getenv("CUBES_TABLE_NAME")
DRILLDOWNS_TABLE_NAME = getenv("DRILLDOWNS_TABLE_NAME")
LOGS_TABLE_NAME = getenv("LOGS_TABLE_NAME")

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
TESSERACT_API_SECRET = getenv("TESSERACT_API_SECRET")

# Mondrian Connection
MONDRIAN_API = getenv("MONDRIAN_API")

# Files Directories
DATA_PATH = getenv("DATA_PATH")
if not DATA_PATH:
    print("DATA_PATH not found, please check your environment")
    exit(1)

FEW_SHOT_PATH = getenv("FEW_SHOT_PATH")
if not FEW_SHOT_PATH:
    FEW_SHOT_PATH = DATA_PATH + "few_shot_examples.json"

TABLES_PATH = getenv("TABLES_PATH")
if not TABLES_PATH:
    TABLES_PATH = DATA_PATH + "schema.json"

DESCRIPTIONS_PATH = getenv("DESCRIPTIONS_PATH")
if not DESCRIPTIONS_PATH:
    DESCRIPTIONS_PATH = DATA_PATH + "descriptions.json"

# OEC token and API
OEC_TOKEN = getenv("OEC_TOKEN")
OEC_API = getenv("OEC_API")