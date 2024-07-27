import time

from typing import Dict, Tuple

from table_selection.table_selector import request_tables_to_lm_from_db
from table_selection.table import TableManager
from api_data_request.api_generator import get_api_params_from_lm
from api_data_request.api import ApiBuilder
from data_analysis.data_analysis import agent_answer
#from utils.logs import *
from utils.functions import clean_string, set_to_string
from config import TABLES_PATH


def get_api(
        natural_language_query: str,
        token_tracker: Dict[str, Dict[str, int]] = None,
        step: str = None,
        form_json: Dict = None,
        **kwargs
        ) -> Tuple[str, Dict, str]:

    print("get_api")

    if token_tracker is None:
        token_tracker = {}

    if step == 'request_tables_to_lm_from_db':
        print("request_tables_to_lm_from_db")
        start_time = time.time()
        manager = TableManager(TABLES_PATH)
        table, form_json, token_tracker = request_tables_to_lm_from_db(natural_language_query, manager, token_tracker)
        return get_api(
            natural_language_query,
            token_tracker,
            step="get_api_params_from_lm",
            **{"table": table, "manager": manager, "start_time": start_time},
        )

    elif step == "get_api_params_from_lm":
        print("get_api_params_from_lm")
        variables, measures, cuts, limit, token_tracker = get_api_params_from_lm(natural_language_query, kwargs["table"], token_tracker, model="gpt-4")
        api = ApiBuilder(table=kwargs["table"], drilldowns=variables, measures=measures, cuts=cuts, limit=limit)
        api_url = api.build_api()
        cuts_context = api.format_cuts_context()
        print("API:", api_url)
        return get_api(
            natural_language_query,
            token_tracker,
            step="fetch_data",
            **{**kwargs, **{"api": api, "api_url": api_url, "cuts_context": cuts_context}},
        )

    elif step == "get_api_params_from_wrapper":
        print("get_api_params_from_wrapper")
        start_time = time.time()
        table_name = form_json.get("cube")
        manager = TableManager(TABLES_PATH)
        table = manager.get_table(table_name)
        api = ApiBuilder(table=table, form_json=form_json)
        api_url = api.build_api()
        print("API:", api_url)

        return get_api(
            natural_language_query,
            token_tracker,
            step="fetch_data",
            **{
                **kwargs,
                **{
                    "api": api,
                    "api_url": api_url,
                    "table": table,
                    "start_time": start_time,
                },
            },
        )

    elif step == "fetch_data":
        print("fetch_data")
        data, df, response = kwargs["api"].fetch_data()
        print(df)
        return get_api(
            natural_language_query,
            token_tracker,
            step="agent_answer",
            **{**kwargs, **{"df": df, "response": response, "data": data}},
        )

    elif step == "agent_answer":
        print("agent_answer")
        api = kwargs["api"]
        cuts_context = kwargs["cuts_context"]
        variables = api.drilldowns
        measures = api.measures
        cuts = api.cuts
        table = {
            "name": "logs",
            "schema": "chatbot",
            "columns": {
                "query_id": "text",
                "question": "text",
                "api_url": "text",
                "response": "text",
                "cube": "text",
                "drilldowns": "text",
                "measures": "text",
                "cuts": "text",
                "created_on": "text",
                "duration": "text",
                "total_tokens": "text",
                "total_cost": "text",
            },
        }
        values = {
            "question": natural_language_query,
            "cube": kwargs["table"].name,
            "duration": time.time() - kwargs["start_time"],
        }
        if kwargs["response"] == "No data found." or kwargs["df"].empty:
            values.update(
                {
                    "api_url": "",
                    "response": clean_string(kwargs["response"]),
                    "drilldowns": "",
                    "measures": "",
                    "cuts": "",
                    "total_tokens": token_tracker,
                }
            )
            # insert_logs(table=table, values=values, log_type="apicall")
        else:
            kwargs["response"], token_tracker = agent_answer(df = kwargs["df"], natural_language_query = natural_language_query, api_url = kwargs["api_url"], context = cuts_context, token_tracker = token_tracker)
            values.update(
                {
                    "api_url": kwargs["api_url"],
                    "response": clean_string(kwargs["response"]),
                    "drilldowns": set_to_string(variables),
                    "measures": set_to_string(measures),
                    "cuts": set_to_string(cuts),
                    "total_tokens": token_tracker,
                }
            )
            # insert_logs(table=table, values=values, log_type="apicall")
        return kwargs["api_url"], kwargs["data"], kwargs["response"]

    else:
        return get_api(natural_language_query, step="request_tables_to_lm_from_db")


form_json = {
    "base_url": "https://oec.world/api/olap-proxy/data.jsonrecords?",
    "cube": "trade_i_baci_a_96",
    "dimensions": {
        "Year": [2022],
        "HS Product": ["All"],
        "Hierarchy:Geography": [{"Exporter": ["Chile", "Argentina"]}, {"Importer": []}],
        "Unit": ["Metric Tons"],
    },
    "measures": ["Trade Value", "Quantity"],
    "limit": "All",
    "sort": "asc",
    "locale": "en",
}


if __name__ == "__main__":
    get_api(
        "what were the imports of chile in 2020?",
        step="request_tables_to_lm_from_db",
    )
