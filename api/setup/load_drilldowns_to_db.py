import json
import pandas as pd
import requests
import urllib.parse

from config import POSTGRES_ENGINE, SCHEMA_DRILLDOWNS, TESSERACT_API, TABLES_PATH
from utils.similarity_search import embedding
from sqlalchemy import text as sql_text

embedding_model = "sfr-embedding-mistral:q8_0"
embedding_size = 4096
DRILLDOWNS_TABLE_NAME = "drilldowns_sfr"

def create_table(table_name=DRILLDOWNS_TABLE_NAME, schema_name=SCHEMA_DRILLDOWNS, embedding_size=embedding_size):
    query_schema = f"CREATE SCHEMA IF NOT EXISTS {schema_name}"
    query_table = f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (drilldown_id text, drilldown_name text, cube_name text, drilldown text, embedding vector({embedding_size}))"
    
    with POSTGRES_ENGINE.connect() as conn:
            conn.execute(sql_text(query_schema))
            conn.execute(sql_text(query_table))
            conn.commit()

def get_data_from_api(api_url):
    try:
        r = requests.get(api_url)
        df = pd.DataFrame.from_dict(r.json()['data'])
    except Exception as e:
        raise ValueError(f"Error fetching data from API: {e}")
    return df

def prepare_dataframe(df, measure_name, cube_name, drilldown_name, drilldown_unique_name=None):
    if f"{drilldown_name} ID" not in df.columns:
        df[f"{drilldown_name} ID"] = df[drilldown_name]

    df.rename(columns={f"{drilldown_name}": "drilldown_name", f"{drilldown_name} ID": "drilldown_id"}, inplace=True)
    df['cube_name'] = cube_name
    df['drilldown'] = drilldown_unique_name if drilldown_unique_name else drilldown_name
    df.drop(measure_name, axis=1, inplace=True)
    
    df['drilldown_id'] = df['drilldown_id'].fillna(df['drilldown_name'])
    df.dropna(subset=['drilldown_name', 'drilldown_id'], how='all', inplace=True)
    df = df[['drilldown_id', 'drilldown_name', 'cube_name', 'drilldown']]
    df['drilldown_name'] = df['drilldown_name'].astype(str)
    df["embedding"] = ""
    df['embedding'] = df['embedding'].astype(object)
    print(df.head())
    return df

def load_data_to_db(api_url, measure_name, cube_name, drilldown_name, drilldown_unique_name=None, schema_name=SCHEMA_DRILLDOWNS, db_table_name=DRILLDOWNS_TABLE_NAME):
    df = get_data_from_api(api_url)
    df = prepare_dataframe(df, measure_name, cube_name, drilldown_name, drilldown_unique_name)
    df_embeddings = embedding(df, 'drilldown_name', model = embedding_model)
    df_embeddings.to_sql(db_table_name, con=POSTGRES_ENGINE, if_exists='append', index=False, schema=schema_name)

def main(include_cubes=False):
    with open(TABLES_PATH, 'r') as file:
        cubes_json = json.load(file)

    if not include_cubes:
        user_input = input("Are you sure you want to upload all cubes? (y/n): ")
        if user_input.lower() == 'y':
            create_table()

            for table in cubes_json['cubes']:
                cube_name = table['name']
                measure = table['measures'][0]['name']
                for dimension in table['dimensions']:
                    for hierarchy in dimension['hierarchies']:
                        for level in hierarchy['levels']:
                            drilldown_name = level['name']
                            drilldown_unique_name = level.get('unique_name')
                            api_url = f"{TESSERACT_API}data.jsonrecords?cube={cube_name}&drilldowns={level['unique_name'] if drilldown_unique_name is not None else drilldown_name}&measures={measure}"
                            load_data_to_db(api_url, measure, cube_name, drilldown_name, drilldown_unique_name)
        else: pass

    else: 
        create_table()

        for table in cubes_json['cubes']:
            cube_name = table['name']
            if include_cubes and cube_name not in include_cubes:
                continue
            measure = table['measures'][0]['name']
            for dimension in table['dimensions']:
                for hierarchy in dimension['hierarchies']:
                    for level in hierarchy['levels']:
                        drilldown_name = level['name']
                        drilldown_unique_name = level.get('unique_name')
                        api_url = f"{TESSERACT_API}data.jsonrecords?cube={cube_name}&drilldowns={level['unique_name'] if drilldown_unique_name is not None else drilldown_name}&measures={measure}"
                        load_data_to_db(api_url, measure, cube_name, drilldown_name, drilldown_unique_name)

if __name__ == "__main__":
    include_cubes = ['trade_i_baci_a_96'] # if set to False it will upload the drilldowns of all cubes in the schema.json
    main(include_cubes)