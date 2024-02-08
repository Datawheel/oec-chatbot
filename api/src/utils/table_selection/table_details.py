import json

from os import getenv
from typing import List

class Table:
    
    def __init__(self, table_data):
        self.name = table_data['name']
        self.api = table_data.get('api')
        self.description = table_data.get('description')
        self.measures = table_data.get('measures', [])
        self.variables = table_data.get('variables', [])

    def get_measures_description(self, measure_name=None):
        if measure_name:
            for measure in self.measures:
                if measure['name'] == measure_name:
                    return f"{measure['name']}: {measure.get('description', 'No description available')}"
            return f"No description available for measure: {measure_name}"
        
        else: return [f"{measure['name']}: {measure.get('description', 'No description available')}" for measure in self.measures]

    def get_variables_description(self, variable_name=None):
        if variable_name:
            for variable in self.variables:
                if variable['name'] == variable_name:
                    return f"{variable['name']}: {variable.get('description', 'No description available')}"
            return f"No description available for variable: {variable_name}"
        
        else: return [f"{variable['name']}: {variable.get('description', 'No description available')}" for variable in self.variables]

    def get_variable_hierarchies(self, variable_name):
        for variable in self.variables:
            if variable['name'] == variable_name and "hierarchies" in variable:
                return variable["hierarchies"]
        return None
    
    def schema_description(self):
        dimensions_str = ", ".join([f"{var['name']} ({var.get('description', 'No description')})" for var in self.variables])
        measures_str = ", ".join([f"{measure['name']} ({measure.get('description', 'No description')})" for measure in self.measures])
        return f"Table Name: {self.name}\nDescription: {self.description}\nDimensions: {dimensions_str}\nMeasures: {measures_str}\n"

    def columns_description(self):
        dimensions_str_list = [
            f"{dimension['name']} ({dimension.get('description', 'No description')}) [Parent dimension: {dimension.get('parent dimension', 'N/A')}];\n" 
            for dimension in self.variables
        ]
        
        measures_str_list = [
            f"{measure['name']} ({measure.get('description', 'No description')});\n"
            for measure in self.measures
        ]
        
        dimensions_str = ''.join(dimensions_str_list)
        measures_str = ''.join(measures_str_list)

        columns_str = f"Table Name: {self.name}\n" + "Variables:\n" + dimensions_str + "Measures:\n" + measures_str
        return columns_str

    def __str__(self):
        measures_str = ", ".join(self.get_measures_description())
        variables_str = ", ".join(self.get_variables_description())
        return f"Table Name: {self.name}\nDescription: {self.description}\nMeasures: {measures_str}\nVariables: {variables_str}\n"
    

class TableManager:

    def __init__(self, tables_path):
        self.tables_path = tables_path
        self.tables = self.load_tables()

    def load_tables(self):
        with open(self.tables_path, 'r') as file:
            data = json.load(file)
            return [Table(table_data) for table_data in data.get('tables', [])]

    def get_table(self, name):
        for table in self.tables:
            if table.name == name:
                return table
        return None

    def list_tables(self):
        return [table.name for table in self.tables]

    def print_table_details(self, name):
        table = self.get_table(name)
        if table:
            print(table)
        else:
            print("Table not found.")

    def get_table_schemas(self, table_names: List[str] = None) -> str:
        tables_str_list = []
        
        for table in self.tables:
            if table_names is None or table.name in table_names:
                tables_str_list.append(table.schema_description())
        
        return "\n\n".join(tables_str_list)


def get_drilldown_levels(manager, table_name, variable_name):
    table = manager.get_table(table_name)
    if table:
        return table.get_variable_hierarchies(variable_name)
    else:
        return None