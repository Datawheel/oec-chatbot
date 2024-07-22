import pandas as pd
import requests
import json

from sentence_transformers import SentenceTransformer
from typing import List
from sqlalchemy import text as sql_text

from config import POSTGRES_ENGINE, OLLAMA_API

def get_similar_content(text, cube_name, drilldown_names, threshold=0, content_limit=1, embedding_model='multi-qa-mpnet-base-cos-v1', verbose=False):
    """
    Receives a string, computes its embedding, and then looks for similar content in a database based on the given cube and drilldown levels.
    Returns top match, similarity score, and others depending on the drilldown.
    """
    embedding_column_name = {
        'multi-qa-mpnet-base-cos-v1': 'embedding' #768 dimensions
    }

    drilldown_names_array = "{" + ",".join(map(lambda x: f'"{x}"', drilldown_names)) + "}"

    model = SentenceTransformer(embedding_model)
    embedding = model.encode([text])
    query = """select drilldown_id, drilldown_name, drilldown, similarity from "match_drilldowns"('{}','{}' ,'{}','{}','{}', '{}'); """.format(embedding[0].tolist().__str__(), str(threshold), str(content_limit), str(cube_name), drilldown_names_array, embedding_column_name[embedding_model])

    with POSTGRES_ENGINE.connect() as connection:
            df = pd.read_sql_query(sql_text(query), connection)
            if verbose: 
                print(df)

    drilldown_id = df.drilldown_id[0]
    drilldown_name = df.drilldown_name[0]
    similarity = df.similarity[0]

    return drilldown_id, drilldown_name, similarity


def get_similar_tables(vector, threshold=0, content_limit=1) -> List[str]:
    """
    Receives an embedding and then looks for similar content in a database. 
    Returns top match, similarity score, and others depending on the drilldown.
    """
    query = """select table_name, similarity from "match_table"('{}','{}' ,'{}'); """.format(vector[0].tolist().__str__(), str(threshold), str(content_limit))
    
    with POSTGRES_ENGINE.connect() as connection:
        df = pd.read_sql_query(sql_text(query), connection)
    
    tables = df['table_name'].tolist()

    return tables


def embedding(dataframe, column, model):
    """
    Creates embeddings for text in the column passed as argument
    """
    if model == 'multi-qa-MiniLM-L6-cos-v1' or model == 'all-mpnet-base-v2' or model == 'all-MiniLM-L12-v2' or model == 'multi-qa-mpnet-base-cos-v1':

        model = SentenceTransformer(model)

        model_embeddings = model.encode(dataframe[column].to_list())
        dataframe['embedding'] = model_embeddings.tolist()

    else: 
        url = "{}embeddings".format(OLLAMA_API)

        for index, row in dataframe.iterrows():
            text = row[column]

            payload = {
                "model": model,
                "prompt": text
            }

            response = requests.post(url, json = payload)
            embeddings_json = json.loads(response.text)
            embedding = embeddings_json['embedding']
            if embedding is not None:
                dataframe.at[index, 'embedding'] = embedding

    return dataframe