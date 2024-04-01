import json
import sys

def tesseract_schema_mapping(input_file, output_file):

    with open(input_file, 'r') as f:
        input_json = json.load(f)
    
    tables = []

    cube_map = input_json.get("cube_map", {})
    for cube_name, cube_data in cube_map.items():
        table_data = cube_data.get("table", {})
        dimensions_data = cube_data.get("dimension_map", {})
        measures_data = cube_data.get("measure_map", {})

        table = {
            "name": cube_name,
            "api": "Tesseract",
            "description": f"Table `{cube_name}` has data on {', '.join(measures_data.keys())}.",
            "measures": [],
            "dimensions": []
        }

        for measure_name, measure_data in measures_data.items():
            measure = {
                "name": measure_name,
                "description": f"Contains the {measure_name.lower()} for {cube_name.replace('_', ' ')}"
            }
            table["measures"].append(measure)

        for dimension_name, dimension_data in dimensions_data.items():
            dimension = {
                "name": dimension_name,
                "description": f"{dimension_name.lower()} dimension of the data.",
                "hierarchies": []
            }

            hierarchy_map = dimension_data.get("hierarchy_map", {})
            for hierarchy_name, hierarchy_data in hierarchy_map.items():
                levels = []
                level_map = hierarchy_data.get("level_map", {})
                for level_name, level_data in level_map.items():
                    levels.append(level_name)

                hierarchy = {
                    "name": hierarchy_name,
                    "levels": levels
                }
                dimension["hierarchies"].append(hierarchy)

            table["dimensions"].append(dimension)

        tables.append(table)

    output_json = {"tables": tables}

    with open(output_file, 'w') as f:
        json.dump(output_json, f, indent=4)

    return None


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python tesseract_schema_mapping.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    tesseract_schema_mapping(input_file, output_file)