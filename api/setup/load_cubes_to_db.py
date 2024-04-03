import json
import pandas as pd
import sqlalchemy as db
import sys

from sentence_transformers import SentenceTransformer

from src.config import POSTGRES_ENGINE, SCHEMA_TABLES, CUBES_TABLE_NAME
from src.utils.similarity_search import embedding

table_name = CUBES_TABLE_NAME
schema_name = SCHEMA_TABLES
embedding_size = 384


def create_table(table_name, schema_name, embedding_size = 384):
    POSTGRES_ENGINE.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    POSTGRES_ENGINE.execute(f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (table_name text, table_description text, embedding vector({embedding_size}))") 
    return

def load_data_to_db(df, table_name, schema_name):
    df_embeddings = embedding(df, 'table_description')
    df_embeddings.to_sql(table_name, con=POSTGRES_ENGINE, if_exists='replace', index=False, schema=schema_name)
    return

with open('tables.json', 'r') as file:
    cubes_data = json.load(file)

cubes = []

for cube in cubes_data["tables"]:
    cube_info = {
        "table_name": cube["name"],
        "table_description": cube["description"]
    }
    cubes.append(cube_info)

df = pd.DataFrame(cubes)

create_table(table_name, schema_name)
load_data_to_db(df, table_name, schema_name)

