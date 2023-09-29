import os
import pandas as pd

from typing import List
from sqlalchemy import create_engine


def get_similar_tables(vector, threshold=0, content_limit=1) -> List[str]:
    """
    Receives a string, computes its embedding and then looks for similar content in a database. 
    Returns top match, similarity score, and others depending on the drilldown.
    """
    
    # Postgres
    POSTGRES_USERNAME = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_URL = os.getenv('POSTGRES_URL')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DB')

    engine = create_engine('postgresql+psycopg2://{}:{}@{}:5432/{}'.format(POSTGRES_USERNAME,POSTGRES_PASSWORD,POSTGRES_URL,POSTGRES_DATABASE))
    

    query = """select cube_name, variables, measures, similarity from "match_query_cube"('{}','{}' ,'{}'); """.format(vector[0].tolist().__str__(), str(threshold), str(content_limit))
    df = pd.read_sql(query,con=engine)
    
    cubes = df['cube_name'].tolist()

    return cubes
