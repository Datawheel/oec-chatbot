import json
import requests

import xml.etree.ElementTree as ET

from config import DATA_PATH, TESSERACT_API

def parse_xml_to_json(xml_file):
    """
    Parses an schema.xml file into a custom tables.json file format.
    """

    tree = ET.parse(xml_file)
    root = tree.getroot()

    tables = []

    shared_dimensions = {}
    for shared_dimension in root.findall('.//SharedDimension'):
        shared_dimension_name = shared_dimension.get('name')
        hierarchy = shared_dimension.find('.//Hierarchy')
        hierarchy_name = hierarchy.get('name')
        levels = [level.get('name') for level in hierarchy.findall('.//Level')]
        shared_dimensions[shared_dimension_name] = {"hierarchy": hierarchy_name, "levels": levels}

    for cube in root.findall('.//Cube'):
        table_name = cube.get('name')

        measures = []
        dimensions = []
        table_description = None

        for measure in cube.findall('.//Measure'):
            measure_name = measure.get('name')
            measure_description = measure.find('.//Annotation[@name="caption_en"]')
            measure_description = measure_description.text if measure_description is not None else ""
            measures.append({"name": measure_name, "description": measure_description})

        for dimension in cube.findall('.//Dimension'):
            dimension_name = dimension.get('name')
            hierarchy_name = dimension.find('.//Hierarchy').get('name')
            levels = [level.get('name') for level in dimension.findall('.//Level')]
            dimensions.append({"name": dimension_name, "hierarchy": hierarchy_name, "levels": levels})

        for dimension_usage in cube.findall('.//DimensionUsage'):
            dimension_name = dimension_usage.get('name')
            shared_dimension_name = dimension_usage.get('source')
            hierarchy_info = shared_dimensions.get(shared_dimension_name)
            hierarchy_name = hierarchy_info["hierarchy"]
            levels = hierarchy_info["levels"]
            dimensions.append({"name": dimension_name, "hierarchy": hierarchy_name, "levels": levels})

        table_annotation = cube.find('.//Annotation[@name="table_en"]')
        if table_annotation is not None:
            table_description = table_annotation.text

        tables.append({
            "name": table_name,
            "api": "Tesseract",
            "description": table_description,
            "measures": measures,
            "dimensions": [
                {
                    "name": dimension["name"],
                    "description": f"{dimension['name']} dimension of the data.",
                    "hierarchies": [
                        {
                            "name": dimension["hierarchy"],
                            "levels": dimension["levels"]
                        }
                    ]
                } for dimension in dimensions
            ],
            "examples": [],
            "default": {},
        })

    return {"tables": tables}


def add_extra_entries(schema_json):
    """
    Add extra entries to the downloaded json file required by the api.
    """
    def get_member_key(member):
        """
        Get's the members key for obtaining the members list.
        If the tesseract member have the entry LABEL, then use it, if not, use ID
        """
        return "Label" if "Label" in member else "ID"

    for cube in schema_json["cubes"]:
        cube["api"] = "Tesseract"
        cube["default"] = {}
        cube["description"] = ""
        cube["examples"] = []
        for dimension in cube["dimensions"]:
            dimension["description"] = ""
            for hierarchy in dimension["hierarchies"]:
                for level in hierarchy["levels"]:
                    members = requests.get(TESSERACT_API + 'members.jsonrecords?cube={}&level={}'.format(cube["name"], level["name"])).json()["data"]
                    members_list = [member[get_member_key(member)] for member in members]
                    level["members"] = members_list
        for measure in cube["measures"]:
            measure["description"] = ""

    return schema_json


def parse_html_cubes_to_json(endpoint, json_file):
    """
    Download the latest cubes endpoint from tesseract and saves the request as a json.
    """
    r = requests.get(endpoint)
    schema = add_extra_entries(r.json())

    with open(DATA_PATH + json_file, 'w') as f:
        json.dump(schema, f, indent=4)


def main(json_file):
    endpoint = TESSERACT_API + "cubes"
    parse_html_cubes_to_json(endpoint, json_file)


if __name__ == "__main__":
    
    json_file = "schema.json"
    
    main(json_file)