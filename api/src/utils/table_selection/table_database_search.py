import pandas as pd

from config import POSTGRES_ENGINE
from typing import List

def get_similar_tables(vector, threshold=0, content_limit=1) -> List[str]:
    """
    Receives a string, computes its embedding and then looks for similar content in a database. 
    Returns top match, similarity score, and others depending on the drilldown.
    """
    query = """select table_name, similarity from "match_table"('{}','{}' ,'{}'); """.format(vector[0].tolist().__str__(), str(threshold), str(content_limit))
    
    df = pd.read_sql(query, con=POSTGRES_ENGINE)
    tables = df['table_name'].tolist()

    return tables