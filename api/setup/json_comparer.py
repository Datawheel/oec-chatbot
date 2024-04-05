import json


def get_children(node, parent_id):
    """
    Generate children nodes for a JSON node. Apply different proces whether node is dict or list.
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


def repath_json(goal, alternaive, visited):
    """
    Rebuild the route to any goal leaf in a JSON
    * goal: node_id of goal node
    * alternative: JSON file to iterate
    * visited: map of node_id to parent_id and positional
    Returns a value in the given leaf
    """
    # navegate paths in reverse from goal value to json top
    parent, position = visited[goal]
    path = [] # list of indices and keys
    while parent:
        path.append(position)
        parent, position = visited[parent]

    #rebuild the path in the alternetive json
    query = alternaive
    while path:
        current = path.pop()
        query = query[current]    
    return query



def json_iterator(json, json_compare):
    """
    Iterate through JSON of any shape. Evaluate value changes againts other JSON of similar structure
    """
    visited = {} # shape { node_id : (parent_id, position)}
    ids = 0
    queue = [(None, None, json)] # Every node is a tuple of parent_id, position and node

    while queue:
        parent_id, position, node = queue.pop(0)
        ids += 1
        visited[ids] = (parent_id, position)
        children = get_children(node, ids)
        if children:
            queue += children
        else:
            # is leaf

            # follow path to value of alternative json
            value = repath_json(ids, json_compare, visited)
        
            if node != value:
                print('Old value: {}, New value: {}'.format(node, value))
        

if __name__ == '__main__':

    with open(f'../src/wrapper_datausa.json') as f:
        to_parse = json.load(f)

    with open(f'../src/wrapper_datausa2.json') as f:
        to_compare = json.load(f)

    json_iterator(to_parse, to_compare)