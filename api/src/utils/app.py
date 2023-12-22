from src.utils.table_selection.table_selector import *
from src.utils.table_selection.table_details import *
from src.utils.api_data_request.api_generator import *
from src.utils.data_analysis.data_analysis import *

from os import getenv
from dotenv import load_dotenv

load_dotenv()

def get_api(query):

    table_db_llm = request_tables_to_lm_from_db(query)
    v, m, c = get_api_params_from_lm(query, table_db_llm[0], model = 'gpt-4-1106-preview')
    api_url = api_build(table = table_db_llm[0], drilldowns = v, measures = m, cuts = c)
    data, df = api_request(api_url)

    response = agent_answer(df, query)

    return api_url, data, response