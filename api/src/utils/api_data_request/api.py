import requests
import pandas as pd

from src.config import MONDRIAN_API, TESSERACT_API
from src.utils.table_selection.table_details import *
from src.utils.preprocessors.text import *
from src.utils.api_data_request.similarity_search import *

class ApiBuilder:

    def __init__(self, base_url):
        self.base_url = base_url
        self.cube = None
        self.cuts = {}
        self.drilldowns = set()
        self.measures = set()
        self.limit = None
        self.sort = None
        self.locale = None

    def add_cube(self, cube):
        self.cube = cube

    def add_cut(self, key, value):
        if key not in self.cuts:
            self.cuts[key] = set()
        self.cuts[key].add(str(value))

    def add_drilldown(self, drilldown):
        if isinstance(drilldown, list):
            for var in drilldown:
                self.drilldowns.add(var)
        else:
            self.drilldowns.add(drilldown)
    
    def add_measure(self, measure):
        if isinstance(measure, list):
            self.measures.update(measure)
        else:
            self.measures.add(measure)

    def set_limit(self, limit):
        self.limit = limit

    def set_sort(self, drilldown, order):
        self.sort = f"{drilldown}.{order}"

    def set_locale(self, locale):
        self.locale = locale

    def build_url(self):
        query_params = []

        if self.cube:
            query_params.append(f"cube={self.cube}")
        for key, values in self.cuts.items():
            query_params.append(f"{key}={','.join(values)}")
        if self.drilldowns:
            query_params.append("drilldowns=" + ",".join(self.drilldowns))
        if self.measures:
            query_params.append("measures=" + ",".join(self.measures))
        if self.limit is not None:
            query_params.append(f"limit={self.limit}")
        if self.sort:
            query_params.append(f"sort={self.sort}")
        if self.locale:
            query_params.append(f"locale={self.locale}")

        query_string = "&".join(query_params)
        return f"{self.base_url}{query_string}" if query_params else self.base_url

    def fetch_data(self):
            """
            Makes an API request to the constructed URL and returns the JSON data and a DataFrame.
            """
            try:
                r = requests.get(self.build_url())
                r.raise_for_status()

                if 'data' in r.json():
                    json_data = r.json()['data']
                    df = pd.DataFrame.from_dict(json_data)
                    return json_data, df, ""
                else:
                    return {}, pd.DataFrame(), "No data key in response."

            except Exception as e:
                return {}, pd.DataFrame(), f"An error occurred: {str(e)}"

    def __str__(self):
        return self.build_url()


def cuts_processing(cuts, table, table_manager, api):
    
    for i in range(len(cuts)):
        var = cuts[i].split('=')[0].strip()
        cut = cuts[i].split('=')[1].strip()

        var_levels = get_drilldown_levels(table_manager, table.name, var)
        
        if var == "Year" or var == "Month" or var == "Quarter" or var == "Month and Year" or var == "Time":
                api.add_cut(var, cut)
        else:
            drilldown_id, drilldown_name, s = get_similar_content(cut, table.name, var_levels)

            if drilldown_name != var:
                api.drilldowns.discard(var)
                api.add_drilldown(drilldown_name)

            api.add_cut(drilldown_name, drilldown_id)


def api_build(table, table_manager, drilldowns, measures, cuts, limit = ""):
    """
    Receives the drilldowns, measures and filters obtained from the LLM and adds them as attributes to the api instance.
    """
    base = table.api

    if base == "Mondrian": base = MONDRIAN_API
    else: base = TESSERACT_API + "data.jsonrecords?"
    
    api = ApiBuilder(base)

    api.add_cube(table.name)
    api.add_drilldown(drilldowns)
    api.add_measure(measures)

    cuts_processing(cuts, table, table_manager, api)

    return api