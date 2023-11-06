import pandas as pd
import os
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer


POSTGRES_USERNAME = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_URL = os.getenv('POSTGRES_URL')
POSTGRES_DATABASE = os.getenv('POSTGRES_DB')

engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/{}'.format(POSTGRES_USERNAME,POSTGRES_PASSWORD,POSTGRES_URL,POSTGRES_DATABASE))
conn = engine.connect()

def embedding(dataframe, column):
    """
    Creates embeddings
    """
    model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')

    model_embeddings = model.encode(dataframe[column].to_list())
    dataframe['embedding'] = model_embeddings.tolist()

    return dataframe



def create_table():
    engine.execute("CREATE TABLE IF NOT EXISTS tables.tables (table_name text, table_description text, embedding vector(384))") 
    return

df = pd.read_csv('/Users/alexandrabjanes/Datawheel/CODE/datausa-chat/tables.csv')
print(df.head())


df_embeddings = embedding(df, 'table_description')

create_table()

df_embeddings.to_sql('tables', conn, if_exists='append', index=False, schema='datausa_tables')
