import requests
import pandas as pd
from datetime import datetime

from config import MONDRIAN_API, TESSERACT_API
from table_selection.table import *
from utils.preprocessors.text import *
from utils.similarity_search import *

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

    def from_json(self, json_data):
        self.base_url = json_data.get("base_url", self.base_url)
        self.cube = json_data.get("cube", self.cube)
        self.cuts = json_data.get("cuts", self.cuts)
        self.drilldowns = set(json_data.get("drilldowns", self.drilldowns))
        self.measures = set(json_data.get("measures", self.measures))
        self.limit = json_data.get("limit", self.limit)
        self.sort = json_data.get("sort", self.sort)
        self.locale = json_data.get("locale", self.locale)

    def update_json(self, json_data):
        self.from_json(json_data)

    def build_api(self):
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


def _cuts_processing(cuts, table, table_manager, api):
    
    for i in range(len(cuts)):
        var = cuts[i].split('=')[0].strip()
        cut = cuts[i].split('=')[1].strip()

        var_levels = get_drilldown_levels(table_manager, table.name, var)

        print('var:', var, 'var_levels', var_levels)
        
        if var == "Year" or var == "Month" or var == "Quarter" or var == "Month and Year" or var == "Time":
                api.add_cut(var, cut)
        else:
            drilldown_id, drilldown_name, s = get_similar_content(cut, table.name, var_levels)

            if drilldown_name != var:
                api.drilldowns.discard(var)
                api.add_drilldown(drilldown_name)

            api.add_cut(drilldown_name, drilldown_id)


def cuts_processing(cuts, table, table_manager, api):
    year_cuts = []
    other_cuts = []

    # Separate year cuts from other cuts
    for cut in cuts:
        if "Year" in cut:
            year_cuts.append(cut)
        else:
            other_cuts.append(cut)

    # Process year cuts separately
    year_range = None
    for cut in year_cuts:
        if ">=" in cut:
            start_year = int(cut.split('>=')[1].strip())
            if year_range:
                year_range = (max(year_range[0], start_year), year_range[1])
            else:
                year_range = (start_year, datetime.now().year)
        elif "<=" in cut:
            end_year = int(cut.split('<=')[1].strip())
            if year_range:
                year_range = (year_range[0], min(year_range[1], end_year))
            else:
                year_range = (1970, end_year)
        elif "-" in cut:
            start_year, end_year = map(int, cut.split('=')[1].strip().split('-'))
            if year_range:
                year_range = (max(year_range[0], start_year), min(year_range[1], end_year))
            else:
                year_range = (start_year, end_year)
        else:
            year = int(cut.split('=')[1].strip())
            if year_range:
                year_range = (max(year_range[0], year), min(year_range[1], year))
            else:
                year_range = (year, year)

    if year_range:
        for year in range(year_range[0], year_range[1] + 1):
            api.add_cut("Year", str(year))

    # Process other cuts
    for cut in other_cuts:
        var = cut.split('=')[0].strip()
        cut = cut.split('=')[1].strip()

        var_levels = get_drilldown_levels(table_manager, table.name, var)

        print('var:', var, 'var_levels', var_levels)

        if var == "Year" or var == "Month" or var == "Quarter" or var == "Month and Year" or var == "Time":
            api.add_cut(var, cut)
        else:
            drilldown_id, drilldown_name, s = get_similar_content(cut, table.name, var_levels)

            if drilldown_name != var:
                api.drilldowns.discard(var)
                api.add_drilldown(drilldown_name)

            api.add_cut(drilldown_name, drilldown_id)


def init_api(table, table_manager, drilldowns, measures, cuts, limit = ""):
    """
    Receives the drilldowns, measures and filters obtained from the LLM and adds them as attributes to the api instance.
    """
    base = table.api
    valid_drilldowns = table.get_dimension_levels()

    for drilldown in drilldowns:
        if drilldown in valid_drilldowns:
            pass
        else: drilldowns.remove(drilldown)

    if base == "Mondrian": base = MONDRIAN_API
    else: base = TESSERACT_API + "data.jsonrecords?"
    
    api = ApiBuilder(base)

    api.add_cube(table.name)
    api.add_drilldown(drilldowns)
    api.add_measure(measures)

    cuts_processing(cuts, table, table_manager, api)

    return api