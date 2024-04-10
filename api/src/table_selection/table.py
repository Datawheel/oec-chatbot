import json

from typing import List

class Table:
    
    def __init__(self, table_data):
        self.name = table_data['name']
        self.api = table_data.get('api')
        self.description = table_data.get('description')
        self.measures = [measure['name'] for measure in table_data.get('measures', [])]
        self.dimensions = [dimension['name'] for dimension in table_data.get('dimensions', [])]
        self.schema = table_data

    def get_measures_description(self, measure_name=None):
        measures_description = []
        if measure_name:
            for measure in self.schema['measures']:
                if measure['name'] == measure_name:
                    description = {
                        "name": measure['name'],
                        "units_of_measurement": measure.get('annotations', {}).get('units_of_measurement', ''),
                        "description": measure.get('annotations', {}).get('details', '')
                    }
                    measures_description.append(description)
                    return measures_description
                
        else:
            for measure in self.schema['measures']:
                description = {
                    "name": measure['name'],
                    "units_of_measurement": measure.get('annotations', {}).get('units_of_measurement', ''),
                    "description": measure.get('annotations', {}).get('details', '')
                }
                measures_description.append(description)
            return measures_description

    def get_dimensions_description(self, dimension_name=None):
        if dimension_name:
            for dimension in self.schema['dimensions']:
                if dimension['name'] == dimension_name:
                    return [{
                        "name": dimension['name'],
                        "description": dimension['description']
                    }]
            return []
        else:
            return [{
                "name": dimension['name'],
                "description": dimension['description']
            } for dimension in self.schema['dimensions']]

    def get_dimension_hierarchies(self, dimension_name=None):
        """
        Returns the hierarchies of each dimensions of the table and their levels.
        If passed a dimension name, it will return only the hierarchies of the specified dimension and its levels.
        """
        if dimension_name:
            for dimension in self.schema['dimensions']:
                if dimension['name'] == dimension_name:
                    return [{
                        "name": dimension['name'],
                        "hierarchies": [{
                            "name": hierarchy['name'],
                            "levels": [{"name": level['name']} for level in hierarchy['levels']]
                        } for hierarchy in dimension['hierarchies']],
                        "default_hierarchy": dimension['default_hierarchy'],
                        "description": dimension['description']
                    }]
            return []
        else:
            return [{
                "name": dimension['name'],
                "hierarchies": [{
                    "name": hierarchy['name'],
                    "levels": [{"name": level['name']} for level in hierarchy['levels']]
                } for hierarchy in dimension['hierarchies']],
                "default_hierarchy": dimension['default_hierarchy'],
                "description": dimension['description']
            } for dimension in self.schema['dimensions']]
    
    def schema_description(self):
        dimensions_str = ", ".join([f"{var['name']} ({var.get('description', 'No description')})" for var in self.schema['dimensions']])
        measures_str = ", ".join([f"{measure['name']} ({measure.get('description', 'No description')})" for measure in self.schema['measures']])
        return f"Table Name: {self.name}\nDescription: {self.description}\nDimensions: {dimensions_str}\nMeasures: {measures_str}\n"

    def columns_description(self, levels_str = False):
        dimensions_str_list = []
        for dimension in self.schema['dimensions']:
            default_hierarchy_name = dimension['default_hierarchy']
            if default_hierarchy_name:
                for hierarchy in dimension['hierarchies']:
                    if hierarchy['name'] == default_hierarchy_name:
                        if levels_str:
                            levels = [level['name'] for level in hierarchy['levels']]
                            dimensions_str_list.append(f"{dimension['name']} ({dimension.get('description', 'No description')}) [Levels: {', '.join(levels)}];\n")
                        else: 
                            dimensions_str_list.append(f"{dimension['name']} ({dimension.get('description', 'No description')});\n")
                        break
            else:
                if levels_str: 
                    levels = [level['name'] for level in dimension['hierarchies'][0]['levels']]
                    dimensions_str_list.append(f"{dimension['name']} ({dimension.get('description', 'No description')}) [Levels: {', '.join(levels)}];\n")
                else: 
                    dimensions_str_list.append(f"{dimension['name']} ({dimension.get('description', 'No description')});\n")
        
        measures_str_list = [
            f"{measure['name']} ({measure.get('description', 'No description')});\n"
            for measure in self.schema['measures']
        ]
        
        dimensions_str = ''.join(dimensions_str_list)
        measures_str = ''.join(measures_str_list)

        columns_str = f"Dimensions:\n" + dimensions_str + "\nMeasures:\n" + measures_str
        return columns_str
    
    def get_drilldown_members(self, drilldown):
        for dimension in self.schema['dimensions']:
            for hierarchy in dimension['hierarchies']:
                for level in hierarchy['levels']:
                    if level['name'] == drilldown:
                        return level['members']
        return []
   
    def __str__(self):
        return self.schema_description()
    

class TableManager:

    def __init__(self, tables_path):
        self.tables_path = tables_path
        self.tables = self.load_tables()

    def load_tables(self):
        with open(self.tables_path, 'r') as file:
            data = json.load(file)
            return [Table(table_data) for table_data in data.get('cubes', [])]

    def get_table(self, name):
        for table in self.tables:
            if table.name == name:
                return table
        return None

    def list_tables(self):
        return [table.name for table in self.tables]

    def print_table_details(self, table_name):
        table = self.get_table(table_name)
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


def get_drilldown_levels(manager, table_name, dimension_name):
    table = manager.get_table(table_name)
    if table:
        return table.get_dimension_hierarchies(dimension_name)
    else:
        return None