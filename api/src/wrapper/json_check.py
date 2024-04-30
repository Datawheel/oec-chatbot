import json
from os import getenv
from table_selection.table_selector import request_tables_to_lm_from_db
from table_selection.table import TableManager

TABLES_PATH = getenv('TABLES_PATH')



def get_children(node, parent_id):
    """
    Generate children nodes for a JSON node. Apply different process wether node is dict or list.
    *node: node to extract children from
    *parent_id: parent_id to be pased to children
    Return a list of tuples in the shape of parent_id, positional and value 
    if no children then return None.
    """
    if type(node) == dict:
        return [(parent_id, key, val) for key, val in node.items()]
    elif type(node) == list:
        return [(parent_id, inx, val) for inx, val in enumerate(node)]
    return []


def repath_json(goal, visited):
    """
    Rebuild the route to any goal leaf in a JSON
    * goal: node_id of goal node
    * visited: map of node_id to parent_id and positional
    Returns paths to a goal
    """
    # navegate paths in reverse from goal value to json top
    parent, position, child_cnt, completion, type = visited[goal]
    path = [] # list of indices and keys
    while parent:
        if (child_cnt == completion and completion > 0):
            return None
        path.append(position)
        parent, position, child_cnt, completion, type = visited[parent]
    
    return path


def commpletion_updater(node_id, visited):
    parent, position, child_cnt, completion, type = visited[node_id]
    while True:
        # update value
        completion += 1
        visited[node_id] = (parent, position, child_cnt, completion, type)
        
        # if 1 child is completed and is list, then mark as completed
        if (type == list and child_cnt > 1) and parent:
            completion = child_cnt
            visited[node_id] = (parent, position, child_cnt, completion, type)

        # if completed, update parent
        if (child_cnt == completion) and parent:
            node_id = parent
            parent, position, child_cnt, completion, type = visited[node_id]
        else:
            break

    return visited
    


def json_iterator(json):
    """
    Iterate through JSON of any shape. Evaluate value changes againts other JSON of similar structure
    """
    visited = {} # shape { node_id : (parent_id, position, child_cnt, completion, types)}
    ids = 0
    stack = [(None, None, json)] # Every node is a tuple of parent_id, position and node
    blank, missing = [], []

    while stack:
        parent_id, position, node = stack.pop()
        ids += 1
        children = get_children(node, ids)
        visited[ids] = (parent_id, position, len(children), 0, type(node))
                     
        if children:
            stack += children

        else:
            # is leaf  
            if node == '' or node == []:
                blank.append(ids)
            else:
                visited = commpletion_updater(parent_id, visited)

    for id in blank:
        parent_id, position, child_cnt, completion, types = visited[id]
        path_to_node = repath_json(parent_id, visited)
        if path_to_node is not None:
            missing.append((path_to_node, position))

    
    return missing


# Call Schema Json to build Form JSON
def set_form_json(query):
    """
    Call request_tables_to_lm_from_db to obtain a new form_json

    Return: form_json
    """
    table_manager = TableManager(TABLES_PATH)
    selected_table, form_json, token_tracker = request_tables_to_lm_from_db(query, table_manager, {})
    if selected_table:
        form_json = {'base_url':"https://oec.world/api/olap-proxy/data.jsonrecords?",
                    'cube': selected_table.name,
                    'dimensions':{
                            "Year": [2023],
                            "HS Product": [],
                            "Hierarchy:Geography": [
                                {
                                    "Exporter": []
                                },
                                {
                                    "Importer": []
                                }
                            ],
                            "Unit": ["place_holder"]
                        },
                    'measures': [
                    "Trade Value",
                    "Quantity"
                    ],
                    "limit": "",
                    "sort": "",
                    "locale": "en"}
        return form_json
    else:
        return None



if __name__ == "__main__":
    form_json = {
    "base_url": "https://oec.world/api/olap-proxy/data.jsonrecords?",
    "cube": "trade_i_baci_a_96",
    "dimensions": {
        "Year": [2023],
        "HS Product": [],
        "Hierarchy:Geography": [
            {
                "Exporter": [
                    {'continent':""},
                    {'country':""}
                ]
            },
            {
                "Importer": [
                    {'continent':""},
                    {'country':""}
                ]
            }
        ],
        "Unit": []
    },
    "measures": [
        "Trade Value",
        "Measure"
    ],
    "limit": "1",
    "sort": "desc",
    "locale": ""
    }

    missing, visited, blank = json_iterator(form_json)
    #for k, v in visited.items(): print(k,v)
    print('\n missing')
    for m in missing: print(m)
    print('\n blanks')
    for m in blank:
        parent_id, position, child_cnt, completion, types = visited[m]
        path_to_node = repath_json(parent_id, visited)
        print(visited[m], path_to_node)

