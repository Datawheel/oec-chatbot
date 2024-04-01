import time

from os import getenv

from utils.table_selection.table_selector import *
from utils.table_selection.table_details import *
from utils.api_data_request.api_generator import *
from utils.data_analysis.data_analysis import *
from utils.logs import *

def get_api(query, TABLES_PATH):
    start_time = time.time()

    manager = TableManager(TABLES_PATH)
    table = request_tables_to_lm_from_db(query, manager)
    variables, measures, cuts = get_api_params_from_lm(query, table, model = 'gpt-4')

    api = api_build(table, manager, variables, measures, cuts)
    api_url = api.build_url()
    print("API:", api_url)
    
    data, df, response = api.fetch_data()
    end_time = time.time()
    duration = end_time - start_time

    if (response == "No data found." or df.empty):
        log_apicall(query, "", response, "", "", "", table, duration)
        return api_url, data, response
    
    else:
        response = agent_answer(df, query)
        log_apicall(query, api_url, response, variables, measures, cuts, table, duration)
        return api_url, data, response
    
if __name__ == "__main__":
    TABLES_PATH = getenv('TABLES_PATH')
    get_api('How much did the CPI of fresh fruits change between 2019 and 2021', TABLES_PATH)

