import pandas as pd

from config import POSTGRES_ENGINE, CUBES_TABLE_NAME, SCHEMA_TABLES
from utils.similarity_search import embedding

def create_table():
    POSTGRES_ENGINE.execute(f"CREATE TABLE IF NOT EXISTS {SCHEMA_TABLES}.{CUBES_TABLE_NAME} (table_name text, table_description text, embedding vector(384))") 
    return


def load_data_to_db(df):

    print(df.head())

    df_embeddings = embedding(df, 'table_description')
    df_embeddings.to_sql('cubes', con=POSTGRES_ENGINE, if_exists='append', index=False, schema=SCHEMA_TABLES)

    return


df = pd.DataFrame()

table_name = 'gini_inequality_income'
table_desc = 'Estimated household income inequality indicators from 1960 to 2020. It includes data on the year, country, and Gini coefficient'

df["table_name"] = [table_name]
df['table_description'] = [table_desc]


create_table()

load_data_to_db(df)