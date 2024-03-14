import json
import openai
import requests
import time

from config import OLLAMA_API
from utils.table_selection.table_details import *
from utils.preprocessors.text import *
from utils.api_data_request.similarity_search import *
from utils.api_data_request.api import *

def get_api_components_messages(table, model_author, natural_language_query = ""):

    response_part = """
        {
            "variables": "",
            "measures": "",
            "filters": ""
        }
        """

    if(model_author == "openai"):

        message = f"""
You are an expert data scientist working with data organized in a multidimensional format, such as in OLAP cubes.
You are given the following JSON containing the dimensions and measures of a cube that contains data to answer a user's question. 
---------------------\n
{table.columns_description()}
---------------------\n
Your goal is to identify the variables, measures and filters needed in order to retrieve the data from the cube through an API.
The variables available correspond to the values in the 'levels' key.
You should respond in JSON format with your answer separated into the following fields:\n

    \"variables\" which is a list of strings that contain the variables.\n
    \"measures\" which is a list of strings that contain the relevant measures.\n
    \"filters\" which is a list of strings that contain the filters in the form of 'variable = filtered_value'.\n

in your answer, provide the markdown formatted like this:\n
```
{response_part}
```
Provide only the list of variables, measures and filters, and nothing else before or after.\n
A few rules to take into consideration:\n
- You cannot apply filters to different variables with the same parent dimension. Choose only one (the most relevant or most granular)\n
- For cases where the query requires to filter by a certain range of years or months, please specify all of them separately.
"""
        
    else: 
        
        message = f"""

Below you can find the metadata of the cube:
---------------------\n
{table.columns_description()}
---------------------\n

A few rules to take into consideration:\n
- You cannot apply filters to different variables with the same parent dimension. Choose only one (the most relevant or most granular)\n
- For cases where the query requires to filter by a certain range of years or months, please specify all of them separately.

This is my question: 
{natural_language_query}
"""

    return message


def get_model_author(model):
    """
    Identify Model Author for Model requests
    """
    # List of possible models
    models = {
      "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-0125-preview", "gpt-4-1106-preview"],
      "llama": ["llama2", "mistral", "codellama", "mixtral", "api_params"]
    }

    if model in models.get("openai"):
        author = "openai"
    elif model in models.get("llama"):
        author = "llama"
    else:
        author = None
    
    return author


def get_api_params_from_lm(natural_language_query, table = None, model="gpt-4", top_matches=False):
    """
    Identify API parameters to retrieve the data using OpenAI models or Llama.
    """
    start_time = time.time()
    model_author = get_model_author(model)

    content = get_api_components_messages(table, model_author, natural_language_query)

    # logic for openai models
    if model_author == "openai":
        max_attempts = 5
        attempts = 0

        messages = [{
            "role": "system",
            "content": content
        }]

        messages.append({
            "role": "user",
            "content": natural_language_query
        })
        
        while attempts < max_attempts:
            try:
                response = openai.ChatCompletion.create(
                    model = model,
                    messages = messages,
                    temperature = 0
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
        end_time = time.time()
        print("Duration:", end_time - start_time, "seconds")
        print("\nChatGPT response:", output_text)
        params = extract_text_from_markdown_triple_backticks(output_text)
        print("\nParameters:", params)

        variables = json.loads(params).get("variables")
        measures = json.loads(params).get("measures")
        cuts = json.loads(params).get("filters")

    elif model_author == "llama":
        url = "{}generate".format(OLLAMA_API)
        print(content)
        payload = {
            "model": model,
            "prompt": content
        }

        response = requests.post(url, json=payload)
        end_time = time.time()
        print("Duration:", end_time - start_time, "seconds")
        print(response.text)
        response = parse_response(response.text)
        print(response)
        params = extract_text_from_markdown_triple_backticks(response)

        variables = json.loads(params).get("variables")
        measures = json.loads(params).get("measures")
        cuts = json.loads(params).get("filters")

    else:
        # logic: ask for model on the list, or use a default one
        status = "bad status"

    return variables, measures, cuts