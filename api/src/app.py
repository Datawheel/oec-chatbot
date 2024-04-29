import time

from os import getenv

from table_selection.table_selector import *
from table_selection.table import *
from api_data_request.api_generator import *
from data_analysis.data_analysis import *
from utils.logs import *
from config import TABLES_PATH

def get_api(
        natural_language_query: str, 
        token_tracker: Dict[str, Dict[str, int]] = None, 
        step: str = None, 
        tables_path: str = TABLES_PATH, 
        **kwargs
        ) -> Tuple[str, Dict, str]:
    
    if token_tracker is None:
        token_tracker = {}

    if step == 'request_tables_to_lm_from_db':
        start_time = time.time()
        manager = TableManager(tables_path)
        table, form_json, token_tracker = request_tables_to_lm_from_db(natural_language_query, manager, token_tracker)
        return get_api(natural_language_query, token_tracker, step ='get_api_params_from_lm', **{'table': table, 'manager': manager, 'start_time': start_time})
        
    elif step == 'get_api_params_from_lm':
        variables, measures, cuts, token_tracker = get_api_params_from_lm(natural_language_query, kwargs['table'], token_tracker, model = 'gpt-4')
        api = ApiBuilder(table = kwargs['table'], drilldowns = variables, measures = measures, cuts = cuts)
        api_url = api.build_api()
        print("API:", api_url)
        return get_api(natural_language_query, token_tracker, step = 'fetch_data', **{**kwargs, **{'api': api, "api_url": api_url}})

    elif step == 'get_api_params_from_wrapper':
        variables, measures, cuts, token_tracker = get_api_params_from_lm(natural_language_query, kwargs['table'], token_tracker, model = 'gpt-4')
        api = ApiBuilder(table = kwargs['table'], form_json = form_json)
        api_url = api.build_api()
        print("API:", api_url)
        return get_api(natural_language_query, token_tracker, step = 'fetch_data', **{**kwargs, **{'api': api, "api_url": api_url}})

    elif step == 'fetch_data': 
        data, df, response = kwargs['api'].fetch_data()
        return get_api(natural_language_query, token_tracker, step = 'agent_answer', **{**kwargs, **{'df': df, 'response': response, 'data': data}})

    elif step == 'agent_answer':
        api = kwargs['api']
        variables = api.drilldowns
        measures = api.measures
        cuts = api.cuts
        if kwargs['response'] == "No data found." or kwargs['df'].empty:
            log_apicall(natural_language_query, "", kwargs['response'], "", "", "", kwargs['table'], kwargs['start_time'], tokens = token_tracker)
        else:
            kwargs['response'], token_tracker = agent_answer(kwargs['df'], natural_language_query, kwargs['api_url'], token_tracker)
            log_apicall(natural_language_query, kwargs['api_url'], kwargs['response'], variables, measures, cuts, kwargs['table'], kwargs['start_time'], tokens = token_tracker)

        return kwargs['api_url'], kwargs['data'], kwargs['response']

    else: return get_api(natural_language_query, step = 'request_tables_to_lm_from_db')

if __name__ == "__main__":
    get_api('How much coffee was exported from Colombia to chile between 2010 and 2015?')