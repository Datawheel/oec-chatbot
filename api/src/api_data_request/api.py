import pandas as pd
import requests

from datetime import datetime
from typing import Dict, List, Tuple, Union, Any

from config import TESSERACT_API
from table_selection.table import Table
from utils.similarity_search import get_similar_content

class ApiBuilder:

    def __init__(
            self, 
            table: Table, 
            base_url: str = TESSERACT_API + "data.jsonrecords?",
            drilldowns: List[str] = None, 
            measures: List[str] = None, 
            cuts: List[str] = None,
            limit: str = None,
            form_json: Dict = None, 
            ):
        """
        Initializes the ApiBuilder.

        Args:
            base_url (str): The base URL for the API.
            table (Table): The table.
            drilldowns (List[str]): List of drilldowns.
            measures (List[str]): List of measures.
            cuts (List[str]): List of cuts.
            limit (str): The limit of the response.
            form_json (Dict): JSON data for initialization.
        """
        self.base_url = base_url
        self.cube = table.name
        self.cuts = {}
        self.cuts_context = {}
        self.drilldowns = set()
        self.measures = set()
        self.limit = None
        self.sort = None
        self.locale = None
        
        if form_json:
            self.from_json(form_json = form_json, table = table)
        
        else:
            if table:
                self.cube = table.name
                valid_drilldowns = table.get_dimension_levels()

                if drilldowns:
                    drilldowns = [drilldown for drilldown in drilldowns if drilldown in valid_drilldowns]
                    self.add_drilldown(drilldowns)

                if measures:
                    self.add_measure(measures)
                else: 
                    self.measures = table.measures

                if cuts:
                    cuts_processing(cuts, table, self)

                if limit:
                    self.limit = limit

    def add_cut(self, key: str, value: str, name: str):
        if key not in self.cuts:
            self.cuts[key] = set()
            self.cuts_context[key] = set()
        self.cuts[key].add(str(value))
        self.cuts_context[key].add(str(name))

    def format_cuts_context(self):
        return ', '.join([f"{key} = {', '.join(values)}" for key, values in self.cuts_context.items()])

    def add_drilldown(self, drilldown: Union[str, List[str]]):
        """
        Adds a drilldown or a list of drilldowns to the API request.

        Args:
            drilldown (Union[str, List[str]]): The drilldown(s).
        """
        if isinstance(drilldown, list):
            for var in drilldown:
                self.drilldowns.add(var)
        else:
            self.drilldowns.add(drilldown)
    
    def add_measure(self, measure: Union[str, List[str]]):
        """
        Adds a measure or a list of measures to the API request.

        Args:
            measure (Union[str, List[str]]): The measure(s).
        """
        if isinstance(measure, list):
            self.measures.update(measure)
        else:
            self.measures.add(measure)

    def set_sort(self, measure: str, order: str):
        self.sort = f"{measure}.{order}"

    def from_json(self, form_json: Dict[str, Any], table: Table):
        """
        Initializes the ApiBuilder from JSON data.

        Args:
            form_json (Dict[str, Any]): JSON data containing API parameters.
        """
        self.cube = form_json.get("cube", self.cube)
        #self.limit = form_json.get("limit", self.limit)
        #self.sort = form_json.get("sort", self.sort)
        #self.locale = form_json.get("locale", self.locale)
        self.measures = set(form_json.get("measures", self.measures))

        for dimension, values in form_json["dimensions"].items():
            if isinstance(values, list):
                if all(isinstance(val, dict) for val in values):
                    for subdict in values:
                        for key, val in subdict.items():
                            cuts = []
                            for value in val:
                                cut = str(key) + " = " + str(value)
                                cuts.append(cut)
                            cuts_processing(cuts, table, self)
                else:
                    if values:
                        cuts = []
                        for value in values:
                            cut = str(dimension) + " = " + str(value)
                            cuts.append(cut)
                        cuts_processing(cuts, table, self)
            else:
                print(f"Unexpected format for dimension '{dimension}': {values}")

    def update_json(self, json_data: Dict[str, Any]):
        """
        Updates the ApiBuilder from JSON data.

        Args:
            json_data (Dict[str, Any]): JSON data containing API parameters.
        """
        self.from_json(json_data)

    def build_api(self) -> str:
        """
        Builds the API request URL.

        Returns:
            str: The API request URL.
        """
        query_params = []

        if 'Trade Value' in self.measures:
            self.set_sort('Trade Value', 'desc')
        elif 'Quantity' in self.measures:
            self.set_sort('Quantity', 'desc')

        if self.cube:
            query_params.append(f"cube={self.cube}")
        for key, values in self.cuts.items():
            query_params.append(f"{key}={','.join(values)}")
        
        if self.drilldowns:
            query_params.append("drilldowns=" + ",".join(self.drilldowns))
        else: 
            query_params.append("drilldowns=Year")

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

    def fetch_data(self) -> Tuple[Dict[str, Any], pd.DataFrame, str]:
        """
        Makes an API request and returns the JSON data and a DataFrame.

        Returns:
            Tuple[Dict[str, Any], pd.DataFrame, str]: JSON data, DataFrame, and error message (if any).
        """
        try:
            r = requests.get(self.build_api())
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
        return self.build_api()


def cuts_processing(cuts: List[str], table: Table, api: ApiBuilder):
    """
    Process cuts for the API request.

    Args:
        cuts (List[str]): List of cuts.
        table (Table): The table.
        api (ApiBuilder): The ApiBuilder instance.
    """
    year_cuts = []
    other_cuts = []

    # Separate year cuts from other cuts
    for cut in cuts:
        if "Year" in cut and ("<=" in cut or ">=" in cut):
            year_cuts.append(cut)
        else:
            other_cuts.append(cut)

    # Process year cuts separately
    year_range = None
    for cut in year_cuts:
        if 'All' in cut or 'all' in cut:
            api.add_drilldown('Year')
        elif ">=" in cut:
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
        for year in range(min(year_range), max(year_range) + 1):
            api.add_cut("Year", str(year), str(year))

    # Process other cuts
    for cut in other_cuts:
        var = cut.split('=')[0].strip()
        cut = cut.split('=')[1].strip()

        if 'All' in cut:
            var_levels = table.get_dimension_levels(var)
            api.add_drilldown(var_levels[-1])

        else:
            var_levels = table.get_dimension_levels(var)

            if var == "Year" or var == "Month" or var == "Quarter" or var == "Month and Year" or var == "Time":
                api.add_cut(var, cut, cut)
            else:
                drilldown_id, drilldown, s, drilldown_name = get_similar_content(cut, table.name, var_levels)

                if drilldown != var:
                    api.drilldowns.discard(var)
                    api.add_drilldown(drilldown)

                api.add_cut(drilldown, drilldown_id, drilldown_name)

    for cut, values in api.cuts.items():
        if len(values) > 1:
            api.add_drilldown(cut)
        # elif "HS" in cut:
        #     api.add_drilldown(cut)
        else: 
            api.drilldowns.discard(cut)