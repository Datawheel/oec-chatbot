import json

from typing import List, Dict, Any, Union

class Table:
    """
    Represents a table with its schema and methods for data retrieval.
    """
    def __init__(self, table_data: Dict[str, Any]):
        """
        Initializes the Table object.

        Args:
            table_data (Dict[str, Any]): Data containing information about the table.
        """
        self.name = table_data['name']
        self.api = table_data.get('api')
        self.description = table_data.get('description')
        self.measures = [measure['name'] for measure in table_data.get('measures', [])]
        self.dimensions = [dimension['name'] for dimension in table_data.get('dimensions', [])]
        self.schema = table_data

    # Methods used in prompts
                
    def prompt_schema_description(self, descriptions: bool = False) -> str:
        """
        Generates a description of the table schema.

        Args:
            descriptions (bool): Flag to include descriptions of dimensions and measures.

        Returns:
            str: The schema description.
        """
        if descriptions:
            dimensions_str = ", ".join([f"{var['name']}" for var in self.schema['dimensions']])
            measures_str = ", ".join([f"{measure['name']}" for measure in self.schema['measures']])
        else: 
            dimensions_str = ", ".join([f"{var['name']} ({var.get('description', 'No description')})" for var in self.schema['dimensions']])
            measures_str = ", ".join([f"{measure['name']} ({measure.get('description', 'No description')})" for measure in self.schema['measures']])
        return f"Table Name: {self.name}\nDescription: {self.description}\nDimensions: {dimensions_str}\nMeasures: {measures_str}\n"

    def prompt_get_dimensions(self, dimension_name: str = None) -> List[Dict[str, Any]]:
        """
        Generates a description of dimension levels.

        Args:
            dimension_name (str): The name of the dimension.

        Returns:
            List[Dict[str, Any]]: Description of dimension levels.
        """
        dimensions = self.schema['dimensions']
        
        def get_level_name(level):
            return level.get('unique_name') or level['name']
        
        if dimension_name:
            dimension = next((dim for dim in dimensions if dim['name'] == dimension_name), None)
            if dimension:
                levels = [get_level_name(level) for hierarchy in dimension['hierarchies'] for level in hierarchy['levels']]
                return [{
                    "name": dimension['name'],
                    "levels": levels
                }]
            else:
                return []
        else:
            return [{
                "name": dimension['name'],
                "levels": [get_level_name(level) for hierarchy in dimension['hierarchies'] for level in hierarchy['levels']]
            } for dimension in dimensions]
        
    def prompt_columns_description(self, include_levels: bool = False) -> str:
        """
        Generates a description of columns.

        Args:
            include_levels (bool): Flag to include levels.

        Returns:
            str: The description of columns.
        """
        dimensions_str_list = []
        for dimension in self.schema['dimensions']:
            default_hierarchy_name = dimension['default_hierarchy']
            if default_hierarchy_name:
                for hierarchy in dimension['hierarchies']:
                    if hierarchy['name'] == default_hierarchy_name:
                        if include_levels:
                            levels = [level['unique_name'] if level.get('unique_name') else level['name'] for level in hierarchy['levels']]
                            dimensions_str_list.append(f"{dimension['name']} ({dimension.get('description', 'No description')}) [Levels: {', '.join(levels)}];\n")
                        else: 
                            dimensions_str_list.append(f"{dimension['name']} ({dimension.get('description', 'No description')});\n")
                        break
            else:
                if include_levels: 
                    levels = [level['unique_name'] if level.get('unique_name') else level['name'] for level in dimension['hierarchies'][0]['levels']]
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
    
    # Other methods

    def get_measures_description(self, measure_name: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves descriptions of measures.

        Args:
            measure_name (str): The name of the measure.

        Returns:
            List[Dict[str, Any]]: Descriptions of measures.
        """
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

    def get_dimensions_description(self, dimension_name: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves descriptions of dimensions.

        Args:
            dimension_name (str): The name of the dimension.

        Returns:
            List[Dict[str, Any]]: Descriptions of dimensions.
        """
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

    def get_dimension_hierarchies(self, dimension_name: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves dimension hierarchies.

        Args:
            dimension_name (str): The name of the dimension.

        Returns:
            List[Dict[str, Any]]: Dimension hierarchies.
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
        
    def get_drilldown_members(self, drilldown_name: str) -> List[str]:
        """
        Retrieves drilldown members.

        Args:
            drilldown_name (str): The name of the drilldown/level.

        Returns:
            List[str]: Drilldown members.
        """
        for dimension in self.schema['dimensions']:
            for hierarchy in dimension['hierarchies']:
                for level in hierarchy['levels']:
                    if level['unique_name'] is not None: level_name = level['unique_name']
                    else: level_name = level['name']
   
                    if level_name == drilldown_name:
                        return level['members']
        return []
    
    def get_dimension_levels(self, name: str = None) -> List[str]:
        """
        Retrieves dimension levels.

        Args:
            name (str): The name of the dimension or level.

        Returns:
            List[str]: Dimension levels.
        """
        if name:
            # Check if the provided name is a level name
            for dimension in self.schema['dimensions']:
                for hierarchy in dimension['hierarchies']:
                    for level in hierarchy['levels']:
                        if level['name'] == name or level['unique_name'] == name:
                            levels = []
                            for level in hierarchy['levels']:
                                if level['unique_name'] is not None:
                                    levels.append(level['unique_name'])
                                else:
                                    levels.append(level['name'])
                            return levels
            
            # If the provided name is not a level name, it might be a dimension name
            for dimension in self.schema['dimensions']:
                if dimension['name'] == name:
                    levels = []
                    for hierarchy in dimension['hierarchies']:
                        for level in hierarchy['levels']:
                            if level['unique_name'] is not None:
                                levels.append(level['unique_name'])
                            else:
                                levels.append(level['name'])
                    return levels
            
            # If neither a dimension nor a level with the provided name is found
            return []
        
        else:
            all_levels = []
            for dimension in self.schema['dimensions']:
                for hierarchy in dimension['hierarchies']:
                    for level in hierarchy['levels']:
                        if level['unique_name'] is not None:
                            all_levels.append(level['unique_name'])
                        else:
                            all_levels.append(level['name'])
            return all_levels

    def get_form_json(self):
        #levels = self.get_dimension_levels()
        dimensions_info = self.schema["dimensions"]

        drilldowns = {}

        dimension_hierarchies = {}
        for dimension_info in dimensions_info:
            dimension_name = dimension_info["name"]
            for hierarchy_info in dimension_info["hierarchies"]:
                hierarchy_name = hierarchy_info["name"]
                if hierarchy_name not in dimension_hierarchies:
                    dimension_hierarchies[hierarchy_name] = []
                dimension_hierarchies[hierarchy_name].append(dimension_name)

        for hierarchy_name, dimensions in dimension_hierarchies.items():
            if len(dimensions) == 1:
                dimension_name = dimensions[0]
                if dimension_name == 'Time' or dimension_name == 'Year': 
                    years = self.get_drilldown_members(drilldown_name = 'Year')
                    latest_year = max(years)
                    drilldowns[dimension_name] = [latest_year]
                else:
                    drilldowns[dimension_name] = []
            else:
                hierarchy_drilldowns = []
                for dimension_name in dimensions:
                    item = {dimension_name: []}
                    hierarchy_drilldowns.append(item)
                drilldowns["Hierarchy:" + (hierarchy_name)] = hierarchy_drilldowns

        # Construct JSON data
        json_data = {
            "base_url": "",
            "cube": self.name,
            "dimensions": drilldowns,
            "measures": self.measures,
            "limit": "",
            "sort": "",
            "locale": "en"
        }

        return json.dumps(json_data, indent=4)

    def __str__(self) -> str:
        """
        Returns a string representation of the table.

        Returns:
            str: String representation.
        """
        return self.prompt_schema_description(descriptions=True)
    

class TableManager:
    """
    Manages tables and provides methods for interacting with them.
    """
    def __init__(self, tables_path: str):
        """
        Initializes the TableManager.

        Args:
            tables_path (str): The path to the tables JSON file.
        """
        self.tables_path = tables_path
        self.tables = self.load_tables()

    def load_tables(self) -> List[Table]:
        """
        Loads tables from the JSON file.

        Returns:
            List[Table]: List of loaded tables.
        """
        with open(self.tables_path, 'r') as file:
            data = json.load(file)
            return [Table(table_data) for table_data in data.get('cubes', [])]

    def get_table(self, name: str) -> Union[Table, None]:
        """
        Retrieves a table by name.

        Args:
            name (str): The name of the table.

        Returns:
            Union[Table, None]: The table if found, None otherwise.
        """
        for table in self.tables:
            if table.name == name:
                return table
        return None

    def list_tables(self) -> List[str]:
        """
        Lists the names of all tables.

        Returns:
            List[str]: List of table names.
        """
        return [table.name for table in self.tables]

    def print_table_details(self, table_name: str):
        """
        Prints details of a table.

        Args:
            table_name (str): The name of the table.
        """
        table = self.get_table(table_name)
        if table:
            print(table)
        else:
            print("Table not found.")

    def get_table_schemas(self, table_names: List[str] = None) -> str:
        """
        Retrieves schemas of tables.

        Args:
            table_names (List[str]): List of table names. If None, retrieves schemas for all tables.

        Returns:
            str: Schemas of the tables.
        """
        tables_str_list = []
        
        for table in self.tables:
            if table_names is None or table.name in table_names:
                tables_str_list.append(table.prompt_schema_description())
        
        return "\n\n".join(tables_str_list)