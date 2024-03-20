import json
import pandas as pd
from config import POSTGRES_ENGINE
from sentence_transformers import SentenceTransformer

# ENV Variables

table_name = 'cubes'
schema_name = 'datausa_tables'
embedding_size = 384

def embedding(dataframe, column):
    """
    Creates embeddings for text in the column passed as argument
    """
    model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')

    model_embeddings = model.encode(dataframe[column].to_list())
    dataframe['embedding'] = model_embeddings.tolist()

    return dataframe

def create_table(table_name, schema_name, embedding_size = 384):
    POSTGRES_ENGINE.execute(f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (table_name text, table_description text, embedding vector({embedding_size}))") 
    return

def load_data_to_db(df, table_name, schema_name):
    df_embeddings = embedding(df, 'table_description')
    df_embeddings.to_sql(table_name, con=POSTGRES_ENGINE, if_exists='append', index=False, schema=schema_name)
    return

with open('output.json', 'r') as file:
    cubes_data = json.load(file)

cubes = []

for cube in cubes_data["tables"]:
    cube_info = {
        "table_name": cube["name"],
        "table_description": cube["description"]
    }
    cubes.append(cube_info)

df = pd.DataFrame(cubes)

create_table()

load_data_to_db(df)