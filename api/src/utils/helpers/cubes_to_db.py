import pandas as pd

from config import POSTGRES_ENGINE
from sentence_transformers import SentenceTransformer

def embedding(dataframe, column):
    """
    Creates embeddings for text in the passed column
    """
    model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')

    model_embeddings = model.encode(dataframe[column].to_list())
    dataframe['embedding'] = model_embeddings.tolist()

    return dataframe


def create_table():
    POSTGRES_ENGINE.execute("CREATE TABLE IF NOT EXISTS datausa_tables.cubes (table_name text, table_description text, embedding vector(384))") 
    return


def load_data_to_db(df):

    print(df.head())

    df_embeddings = embedding(df, 'table_description')
    df_embeddings.to_sql('cubes', con=POSTGRES_ENGINE, if_exists='append', index=False, schema='datausa_tables')

    return


df = pd.DataFrame()

df["table_name"] = ["Data_USA_House_election"]
df['table_description'] = ["Table 'Data_USA_House_election' contains House election data, including number of votes by candidate, party and state."]

create_table()

load_data_to_db(df)