from os import getenv

from table_selection.table_selector import *
from table_selection.table import *
from api_data_request.api_generator import *
from data_analysis.data_analysis import *
from utils.logs import *

def get_api(query, TABLES_PATH, step=None, **kwargs):

    if step == 'request_tables_to_lm_from_db':
        manager = TableManager(TABLES_PATH)
        table = request_tables_to_lm_from_db(query, manager)
        return get_api(query, TABLES_PATH, step='get_api_params_from_lm', **{'table': table, 'manager': manager})
        
    elif step == 'get_api_params_from_lm':
        table = kwargs['table']
        manager = kwargs['manager']
        variables, measures, cuts = get_api_params_from_lm(query, table, model = 'gpt-4')
        api = api_build(table, manager, variables, measures, cuts)
        api_url = api.build_api()
        print("API:", api_url)
        return get_api(query, TABLES_PATH, step='fetch_data', **{**kwargs, **{'api': api, "api_url": api_url}})

    elif step == 'fetch_data': 
        api = kwargs['api']
        api_url = kwargs['api_url']
        data, df, response = api.fetch_data()
        return get_api(query, TABLES_PATH, step='agent_answer', **{**kwargs, **{'df': df, 'response': response}})

    elif step == 'agent_answer':
        api = kwargs['api']
        table = kwargs['table']
        response = kwargs['response']
        df = kwargs['df']
        variables = api.drilldowns
        measures = api.measures
        cuts = api.cuts
        api_url = kwargs['api_url']

        if (response == "No data found." or df.empty):
            log_apicall(query, "", response, "", "", "", table, duration="")
            return api_url, data, response
        
        else:
            response = agent_answer(df, query)
            log_apicall(query, api_url, response, variables, measures, cuts, table, duration="")
            return api_url, data, response
        
    else: return get_api(query, TABLES_PATH, step='request_tables_to_lm_from_db')
    

if __name__ == "__main__":
    TABLES_PATH = getenv('TABLES_PATH')
    get_api('How much coffee did Colombia export to Chile between 2010 and 2020?', TABLES_PATH)