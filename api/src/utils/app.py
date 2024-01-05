from src.utils.table_selection.table_selector import *
from src.utils.table_selection.table_details import *
from src.utils.api_data_request.api_generator import *
from src.utils.data_analysis.data_analysis import *
from src.utils.logs import *

from os import getenv
from dotenv import load_dotenv

load_dotenv()

def get_api(query):

    table_db = request_tables_to_lm_from_db(query)
    #table_db = get_relevant_tables_from_database(query)
    print(table_db)
    v, m, c = get_api_params_from_lm(query, table_db[0], model = 'gpt-4-1106-preview')
    api_url = api_build(table = table_db[0], drilldowns = v, measures = m, cuts = c)
    print("API:", api_url)
    data, df, response = api_request(api_url)

    if (response == "No data found." or df.empty):
        return api_url, data, response
    
    else:
        response = agent_answer(df, query)
        log_apicall(query, api_url, response, v, m, c, table_db[0])

        return api_url, data, response
    

get_api('what was the growth in the inflation rate of housing between 2018 and 2020?')