import openai
import os
import pandas as pd
import requests
import time
import json

from os import getenv
from dotenv import load_dotenv
from langchain.llms import OpenAI
from utils.table_selection.table_selector import get_table_schemas
from utils.table_selection.table_details import get_table_api_base
from utils.preprocessors.text import *

load_dotenv()

# environment initialization
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# variable initialization
OPENAI_KEY = getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY

TESSERACT_API = getenv("TESSERACT_API")
MONDRIAN_API = getenv('MONDRIAN_API')


def get_api_components_messages(table):
    message = (
        """
        You are an expert data scientist. You are given a natural language query from a user and need to identify the variables, measures and filters that are relevant and are needed to retrieve this data through an API.\n
        Return a JSON object with these variables, measures and filters to be applied to answer the following natural language query:\n
        ---------------\n
        {natural_language_query}
        \n---------------\n
        Respond in JSON format with your answer separated into the following fields: 
        \"variables\" which is a list of strings that contain the variables. This are usually time variables, locations, or others.\n
        \"measures\" which is a list of strings that contain the relevant measures. Any numeric variable like wages, population.\n
        \"filters\" which is a list of strings that contain the filters in the form of 'variable = filtered_value'.\n

        Write your answer in markdown format.\n
        """
    )

    #response_part = "<json with variables, measures and filters>"
    response_part = """
        {{
            "variables": "",
            "measures": "",
            "filters": ""
        }}
        """

    return (
        message +
        f"""
        The following is the table you can query, along with its description, columns and the definition of their enums:\n
        ---------------------\n
        {get_table_schemas([table])}
        ---------------------\n

        in your answer, provide the following information:\n
        
        - <one to two sentence comment explaining why the chosen variables, measures and filters can answer the query>\n
        - <for each variable, measure and filter identified, comment double checking that they exist in the table>\n
        - the markdown formatted like this:\n
        ```
        {response_part}
        ```

        Provide only the list of variables, measures and filters, and nothing else after.
        """
    )


def get_api_params_from_lm(natural_language_query, table = None, model="gpt-4", top_matches=False):
    """
    Identify relevant tables for answering a natural language query via LM
    """
    max_attempts = 5
    attempts = 0

    content = get_api_components_messages(table).format(
        natural_language_query = natural_language_query,
    )

    messages = []
    messages.append({
        "role": "user",
        "content": content
    })
    
    while attempts < max_attempts:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0
                )
        except openai.error.Timeout as e:
            print(f"OpenAI API request timed out (attempt {attempts + 1}): {e}")
        except openai.error.APIError as e:
            print(f"OpenAI API returned an API Error (attempt {attempts + 1}): {e}")
        except openai.error.APIConnectionError as e:
            print(f"OpenAI API request failed to connect: {e}")
        except openai.error.ServiceUnavailableError as e:
            print(f"OpenAI API service unavailable: {e}")
        else:
            break
        attempts += 1
        time.sleep(1)

    output_text = response['choices'][0]['message']['content']
    print("\nChatGPT response:", output_text)
    params = extract_text_from_markdow_triple_backticks(output_text)
    print("\nParameters:", params)

    variables = json.loads(params).get("variables")
    measures = json.loads(params).get("measures")
    cuts = json.loads(params).get("filters")

    return variables, measures, cuts


def api_build(table, drilldowns, measures, cuts = "", limit = ""):
    base = get_table_api_base(table)
    drilldowns = clean_string(drilldowns)
    measures = clean_string(measures)
    
    if base == "Mondrian": 
        base = MONDRIAN_API
    else:
        base = TESSERACT_API + "cube=" + table + "&"


    #if (cut): url = base + cut + "&cube=" + cube + "&drilldowns=" + drilldown + "&measures=" + measure + limit
    #else: url = base + "cube=" + cube + "&drilldowns=" + drilldown + "&measures=" + measure + limit
    
    url = base + "drilldowns=" + drilldowns + "&measures=" + measures

    return url


def api_request(url):
    try:
        r = requests.get(url)
        # df = pd.DataFrame.from_dict(r.json()['data'])
        json_data = r.json()['data']
        df = pd.DataFrame.from_dict(r.json()['data'])
    except: raise ValueError('Invalid API url:', url)
    return json_data, df