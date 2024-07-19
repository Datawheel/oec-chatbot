import time

from typing import Dict, Generator

from table_selection.table_selector import request_tables_to_lm_from_db
from table_selection.table import TableManager
from api_data_request.api_generator import get_api_params_from_lm
from api_data_request.api import ApiBuilder
from data_analysis.data_analysis import agent_answer
#from utils.logs import *
from config import TABLES_PATH

def get_api(
        natural_language_query: str, 
        token_tracker: Dict[str, Dict[str, int]] = None, 
        step: str = None, 
        form_json: Dict = None,
        **kwargs
        ) -> Generator[str, Dict, str]:
    
    print("get_api")

    if token_tracker is None:
        token_tracker = {}

    if step == 'request_tables_to_lm_from_db':
        print("request_tables_to_lm_from_db")
        start_time = time.time()
        manager = TableManager(TABLES_PATH)
        table, form_json, token_tracker = request_tables_to_lm_from_db(natural_language_query, manager, token_tracker)
        yield from get_api(natural_language_query, token_tracker, step ='get_api_params_from_lm', **{'table': table, 'manager': manager, 'start_time': start_time})
        
    elif step == 'get_api_params_from_lm':
        print("get_api_params_from_lm")
        variables, measures, cuts, token_tracker = get_api_params_from_lm(natural_language_query, kwargs['table'], token_tracker, model = 'gpt-4')
        api = ApiBuilder(table = kwargs['table'], drilldowns = variables, measures = measures, cuts = cuts)
        api_url = api.build_api()
        print("API:", api_url)
        yield from get_api(natural_language_query, token_tracker, step = 'fetch_data', **{**kwargs, **{'api': api, "api_url": api_url}})

    elif step == 'get_api_params_from_wrapper':
        print("get_api_params_from_wrapper")
        start_time = time.time()
        table_name = form_json.get("cube")
        manager = TableManager(TABLES_PATH)
        table = manager.get_table(table_name)
        api = ApiBuilder(table = table, form_json = form_json)
        api_url = api.build_api()
        print("API:", api_url)
        #yield {'tesseract_api': api_url}
        yield from get_api(natural_language_query, token_tracker, step = 'fetch_data', **{**kwargs, **{'api': api, "api_url": api_url, 'table': table, 'start_time': start_time}})

    elif step == 'fetch_data': 
        print("fetch_data")
        data, df, response = kwargs['api'].fetch_data()
        yield from get_api(natural_language_query, token_tracker, step = 'agent_answer', **{**kwargs, **{'df': df, 'response': response, 'data': data}})

    elif step == 'agent_answer':
        print("agent_answer")
        api = kwargs['api']
        variables = api.drilldowns
        measures = api.measures
        cuts = api.cuts
        if kwargs['response'] == "No data found." or kwargs['df'].empty:
            print('pass')
            #log_apicall(natural_language_query, "", kwargs['response'], "", "", "", kwargs['table'], kwargs['start_time'], tokens = token_tracker)
        else:
            kwargs['response'], token_tracker = agent_answer(kwargs['df'], natural_language_query, kwargs['api_url'], token_tracker)
            #log_apicall(natural_language_query, kwargs['api_url'], kwargs['response'], variables, measures, cuts, kwargs['table'], kwargs['start_time'], tokens = token_tracker)

        yield kwargs['response']

    else: 
        yield from get_api(natural_language_query, step = 'request_tables_to_lm_from_db')


form_json = {
    'base_url': 'https://oec.world/api/olap-proxy/data.jsonrecords?', 
    'cube': 'trade_i_baci_a_96',
    'dimensions': {
        'Year': [2022], 
        'HS Product': ['All'], 
        'Hierarchy:Geography': [
            {'Exporter': ['Chile', 'Argentina']}, 
            {'Importer': []}], 
        'Unit': ['Metric Tons']}, 
        'measures': ['Trade Value', 'Quantity'], 
        'limit': 'All', 
        'sort': 'asc', 
        'locale': 'en'}

#if __name__ == "__main__":

#    get_api('What where the main exporters of cucumber in 2022?', step = 'get_api_params_from_wrapper', form_json = form_json)

for result in get_api('how much coffee was traded globally in 1998?'):
    print(result)

#get_api(natural_language_query='What where the main exporters of cucumber in 2022?')