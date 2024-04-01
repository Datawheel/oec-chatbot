import json
import pandas as pd
import requests
import urllib.parse

from sentence_transformers import SentenceTransformer
from config import POSTGRES_ENGINE, SCHEMA_DRILLDOWNS, DRILLDOWNS_TABLE_NAME

# ENV Variables

TESSERACT_API = 'https://api.datasaudi.datawheel.us/tesseract/'
table_name = DRILLDOWNS_TABLE_NAME
schema_name = SCHEMA_DRILLDOWNS
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
    POSTGRES_ENGINE.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    POSTGRES_ENGINE.execute(f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (drilldown_id text, drilldown_name text, cube_name text, drilldown text, embedding vector({embedding_size}))")
    return


def get_data_from_api(api_url):
    try:
        r = requests.get(api_url)
        df = pd.DataFrame.from_dict(r.json()['data'])
    except:
        raise ValueError('Invalid API url:', api_url)

    return df


def get_api_params(api_url):
    parsed_url = urllib.parse.urlparse(api_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    cube = query_params.get('cube', [''])[0]
    drilldown = query_params.get('drilldowns', [''])[0]

    cube_name = cube.replace('+', ' ')
    drilldown = drilldown.replace('+', ' ')

    return cube_name, drilldown


def load_data_to_db(api_url, measure_name, table_name, schema_name):
    cube_name, drilldown = get_api_params(api_url)
    df = get_data_from_api(api_url=api_url)

    df.rename(columns={f"{drilldown}": "drilldown_name", f"{drilldown} ID": "drilldown_id"}, inplace=True)

    df['cube_name'] = f"{cube_name}"
    df['drilldown'] = f"{drilldown}"
    df.drop(f"{measure_name}", axis=1, inplace=True)

    if 'drilldown_id' not in df.columns:
        df['drilldown_id'] = df['drilldown_name']

    df.replace('', pd.NA, inplace=True)
    df.dropna(subset=['drilldown_name', 'drilldown_id'], how='all', inplace=True)

    df = df[['drilldown_id', 'drilldown_name', 'cube_name', 'drilldown']]
    df['drilldown_name'] = df['drilldown_name'].astype(str)
    print(df.head())

    df_embeddings = embedding(df, 'drilldown_name')
    df_embeddings.to_sql(table_name, con=POSTGRES_ENGINE, if_exists='append', index=False, schema=schema_name)

    return


with open('tables.json', 'r') as file:
    cubes_json = json.load(file)

create_table(table_name, schema_name)

for table in cubes_json['tables']:
    cube_name = table['name']
    measure = table['measures'][0]['name']
    for dimension in table['dimensions']:
        for hierarchy in dimension['hierarchies']:
            for level in hierarchy['levels']:
                api_url = f"{TESSERACT_API}data.jsonrecords?cube={cube_name}&drilldowns={level}&measures={measure}"
                load_data_to_db(api_url, measure, table_name, schema_name)