import pandas as pd
import requests
import urllib.parse

from config import POSTGRES_ENGINE
from utils.similarity_search import embedding

def create_table():
    POSTGRES_ENGINE.execute("CREATE TABLE IF NOT EXISTS datausa_drilldowns.drilldowns (product_id text, product_name text, cube_name text, drilldown text, embedding vector(384))") 
    return


def get_data_from_api(api_url):
    try:
        r = requests.get(api_url)
        df = pd.DataFrame.from_dict(r.json()['data'])
    except: raise ValueError('Invalid API url:', api_url)

    return df


def get_api_params(api_url):
    parsed_url = urllib.parse.urlparse(api_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    cube = query_params.get('cube', [''])[0]
    drilldown = query_params.get('drilldowns', [''])[0]

    cube_name = cube.replace('+', ' ')
    drilldown = drilldown.replace('+', ' ')

    return cube_name, drilldown


def load_data_to_db(api_url, measure_name):
    cube_name, drilldown = get_api_params(api_url)
    df = get_data_from_api(api_url=api_url)
    
    df.rename(columns={f"{drilldown}": "drilldown_name", f"{drilldown} ID": "drilldown_id"}, inplace=True)

    df['cube_name'] = f"{cube_name}"
    df['drilldown'] = f"{drilldown}"
    df.drop(f"{measure_name}", axis=1, inplace=True)

    if 'drilldown_id' not in df.columns:
        df['drilldown_id'] = df['drilldown']

    df.replace('', pd.NA, inplace=True)
    df.dropna(subset=['drilldown_name', 'drilldown_id'], how='all', inplace=True)

    print(df.head())

    df_embeddings = embedding(df, 'product_name')
    df_embeddings.to_sql('drilldowns', con=POSTGRES_ENGINE, if_exists='append', index=False, schema='datausa_drilldowns')

    return


print("Enter API url: ")
api_url = input()
print("Enter measure name: ")
measure_name = input()
#df = pd.read_csv('/Users/alexandrabjanes/Datawheel/CODE/datausa-chat/tables.csv')
#print(df.head())

#create_table()
load_data_to_db(api_url, measure_name = measure_name)
