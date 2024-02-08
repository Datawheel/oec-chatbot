import time

from src.utils.table_selection.table_selector import *
from src.utils.table_selection.table_details import *
from src.utils.api_data_request.api_generator import *
from src.utils.data_analysis.data_analysis import *
from src.utils.logs import *

from dotenv import load_dotenv

load_dotenv()
TABLES_PATH = getenv('TABLES_PATH')

def get_api(query, TABLES_PATH=TABLES_PATH):
    start_time = time.time()

    manager = TableManager(TABLES_PATH)

    table = request_tables_to_lm_from_db(query, manager)

    variables, measures, cuts = get_api_params_from_lm(query, table, model = 'gpt-4-1106-preview')

    api_url = api_build(table, manager, variables, measures, cuts)
    
    print("API:", api_url)
    
    data, df, response = api_request(api_url)
    end_time = time.time()
    duration = end_time - start_time

    if (response == "No data found." or df.empty):
        
        log_apicall(query, "", response, "", "", "", table, duration)
        
        return api_url, data, response
    
    else:
        response = agent_answer(df, query)
        log_apicall(query, api_url, response, variables, measures, cuts, table, duration)

        return api_url, data, response