import json
import pandas as pd
import sqlalchemy as db
import sys

from sentence_transformers import SentenceTransformer

from config import POSTGRES_ENGINE, SCHEMA_TABLES, CUBES_TABLE_NAME, TABLES_PATH
from utils.similarity_search import embedding

table_name = CUBES_TABLE_NAME
schema_name = SCHEMA_TABLES
embedding_size = 384

def create_table(table_name, schema_name, embedding_size = 384):
    POSTGRES_ENGINE.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    POSTGRES_ENGINE.execute(f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (table_name text, table_description text, embedding vector({embedding_size}))") 
    return

def load_data_to_db(df, table_name, schema_name):
    df_embeddings = embedding(df, 'table_description')
    df_embeddings.to_sql(table_name, con=POSTGRES_ENGINE, if_exists='append', index=False, schema=schema_name)
    return

def main(include_cubes=False):
    with open(TABLES_PATH, 'r') as file:
        cubes_json = json.load(file)

    create_table(table_name, schema_name)

    cubes = []

    for cube in cubes_json["cubes"]:
        cube_name = cube['name']
        if include_cubes and cube_name not in include_cubes:
            continue
        cube_info = {
            "table_name": cube["name"],
            "table_description": cube["description"]
        }
        cubes.append(cube_info)

    if not include_cubes:
        user_input = input("Are you sure you want to upload all cubes? (y/n): ")
        if user_input.lower() == 'y':
            df = pd.DataFrame(cubes)
            load_data_to_db(df, table_name, schema_name)
        else:
            pass

if __name__ == "__main__":
    include_cubes = False # if set to False it will ingest all the cubes in the schema.json
    main(include_cubes)

