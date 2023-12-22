import os
import pandas as pd

from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer

POSTGRES_USERNAME = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_URL = os.getenv('POSTGRES_URL')
POSTGRES_DATABASE = os.getenv('POSTGRES_DB')


def get_similar_content(text, cube_name, drilldown_names, threshold=0, content_limit=1, embedding_model='multi-qa-MiniLM-L6-cos-v1', verbose=False):
    """
    Receives a string, computes its embedding, and then looks for similar content in a database based on the given cube and drilldown levels.
    Returns top match, similarity score, and others depending on the drilldown.
    """

    POSTGRES_USERNAME = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_URL = os.getenv('POSTGRES_URL')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DB')

    engine = create_engine(
        'postgresql+psycopg2://{}:{}@{}:5432/{}'.format(POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_URL,
                                                        POSTGRES_DATABASE))

    model = SentenceTransformer(embedding_model)  # 384
    embedding = model.encode([text])

    drilldown_names_array = "{" + ",".join(map(lambda x: f'"{x}"', drilldown_names)) + "}"
 
    query = """select product_id, drilldown_name, similarity from "match_drilldowns_aux"('{}','{}' ,'{}','{}','{}'); """.format(embedding[0].tolist().__str__(), str(threshold), str(content_limit), str(cube_name), drilldown_names_array)
    
    if verbose: print(query)

    df = pd.read_sql(query,con=engine)

    if verbose: print(df)

    drilldown_id = df.product_id[0]
    drilldown_name = df.drilldown_name[0]
    similarity = df.similarity[0]

    return drilldown_id, drilldown_name, similarity

