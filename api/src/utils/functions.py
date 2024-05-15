import datetime
import json
import jwt
import requests
import re


def request_to_tesseract(endpoint, auth=None):
    """
    Make a request to the tesseract api endpoint.
    If you want to make a request with authentication required, please add as a second parameter to the function call the TESSERACT_API_SECRET variable.
    """

    if auth != None:
        JWT_ALGORITHM = "HS256"
        JWT_EXP_DELTA_MINUTES = 30

        payload = {
            "auth_level": 2,
            "sub": "server",
            "status": "valid",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_DELTA_MINUTES),
        }

        jwt_token = jwt.encode(payload, auth, JWT_ALGORITHM)

        headers = {"x-tesseract-jwt-token": jwt_token}

        response = requests.get(endpoint, headers=headers)
    else:
        response = requests.get(endpoint)

    return response


def dict_to_tuple(input_dict):
    # Format dictionary items as strings
    items_as_strings = [f"{key} {value}" for key, value in input_dict.items()]

    # Join the formatted items with commas to create a single string
    tuple_string = ", ".join(items_as_strings)

    # Convert the string to a tuple
    result_tuple = tuple_string

    return result_tuple


def keys_to_tuple(input_dict):
    # Convert dictionary keys to a tuple
    result_tuple = tuple(input_dict.keys())

    # Clean tuple to eliminate singleqoutes
    result_str = "(" + ", ".join(str(elem) for elem in result_tuple) + ")"

    return result_str


def set_to_json(input_set):
    # Convert set to list
    result_list = list(input_set)

    # Serialize the list to JSON
    json_data = json.dumps(result_list, default=list)

    return json.dumps(json_data).replace("'", "")


def set_to_string(input_set):
    # Convert set to list
    result_list = list(input_set)

    # Join the list elements into a comma-separated string
    joined_string = ", ".join(result_list)

    return str(joined_string)


def clean_string(text):
    # Define a regular expression pattern to match single quotes
    single_quote_pattern = r"'"

    # Replace single quotes with an empty string
    cleaned_text = re.sub(single_quote_pattern, "", text)

    return cleaned_text


def calculate_total_cost(tokens: dict):
    # Calculate total tokens and total cost
    total_tokens = 0
    total_cost = 0

    if "request_tables_to_lm_from_db" in tokens:
        total_tokens += tokens["request_tables_to_lm_from_db"].get("total_tokens", 0)
        total_cost += tokens["request_tables_to_lm_from_db"].get("total_cost", 0)

    if "get_api_params_from_lm" in tokens:
        total_tokens += tokens["get_api_params_from_lm"].get("total_tokens", 0)
        total_cost += tokens["get_api_params_from_lm"].get("total_cost", 0)

    if "agent_answer" in tokens:
        total_tokens += tokens["agent_answer"].get("total_tokens", 0)
        total_cost += tokens["agent_answer"].get("total_cost", 0)

    return {"tokens": total_tokens, "cost": total_cost}
