import json


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
    return None


def repath_json(goal, visited):
    """
    Rebuild the route to any goal leaf in a JSON
    * goal: node_id of goal node
    * visited: map of node_id to parent_id and positional
    Returns paths to a goal
    """
    # navegate paths in reverse from goal value to json top
    parent, position = visited[goal]
    path = [] # list of indices and keys
    while parent:
        path.append(position)
        parent, position = visited[parent]
    
    return path



def json_iterator(json):
    """
    Iterate through JSON of any shape. Evaluate value changes againts other JSON of similar structure
    """
    visited = {} # shape { node_id : (parent_id, position)}
    ids = 0
    queue = [(None, None, json)] # Every node is a tuple of parent_id, position and node
    missing = []

    while queue:
        parent_id, position, node = queue.pop(0)
        ids += 1
        visited[ids] = (parent_id, position)
        children = get_children(node, ids)
        
        if children:
            queue += children

        else:
            # is leaf
           
            if node == '' or node == []:
                path_to_node = repath_json(parent_id, visited)
                missing.append((path_to_node, position))
    
    return missing


if __name__ == "__main__":
    form_json = {
    "base_url": "https://api-dev.datausa.io/tesseract/data.jsonrecords?",
    "cube": "Consumer Price Index - CPI",
    "cuts": {
        "Time": [
            "2021",
            "2019",
            "2020"
        ],
        "Level 5.5": [
            "501010407009"
        ]
    },
    "drilldowns": {
        "Flow": [ "Imports", "Exports" ],
        "Level 5.5": []
    },
    "measures": [
        "Consumer Price Index",
        "Percent Change"
    ],
    "limit": "",
    "sort": "",
    "locale": ""
    } 
    missing = json_iterator(form_json)
    print(missing)
