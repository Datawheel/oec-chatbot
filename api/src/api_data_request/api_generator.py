import json
import time
import requests

from typing import Dict, List, Tuple
from openai import OpenAI, APIConnectionError

from config import OLLAMA_API, OPENAI_KEY
from table_selection.table import *
from utils.preprocessors.text import *
from utils.similarity_search import *
from api_data_request.api import *
from data_analysis.token_counter import get_openai_token_cost_for_model

def _get_api_components_messages(table: Table, model_author: str, natural_language_query: str = "") -> str:

    response_part = """
        {
            "drilldowns": "",
            "measures": "",
            "filters": "",
            "explanation": ""
        }
        """

    if(model_author == "openai"):

        message = f"""
            You're a data scientist working with OLAP cubes. Given dimensions and measures in JSON format, identify the drilldowns, measures, and filters for querying the cube via API.

            **Dimensions:**
            {table.prompt_get_dimensions()}

            **Measures:**
            {table.get_measures_description()}

            Your response should be in JSON format with:

            - "drilldowns": List of specific levels within each dimension for drilldowns (ONLY the level names).
            - "measures": List of relevant measures.
            - "filters": List of filters in 'level = filtered_value' format.
            - "explanation": one to two sentence comment explaining why the chosen drilldowns and cuts are relevant goes here, double checking that the levels exist in the JSON given above.

            Response format:

            ```
            {response_part}
            ```

            Provide only the required lists, and adhere to these rules:

            - Apply filters only to the most relevant or granular level within the same parent dimension.
            - For year or month ranges, specify each separately.
            - Double check that the drilldowns and cuts contain ONLY the level names, and not the dimension.
            - For filters, just write the general name, as it will be matched to its ID later on.
        """
        
    else: 
        
        message = f"""
                Below you can find the metadata of the cube:
                ---------------------\n
                {table.prompt_columns_description()}
                ---------------------\n

                A few rules to take into consideration:\n
                - You cannot apply filters to different variables with the same parent dimension. Choose only one (the most relevant or most granular)\n
                - For cases where the query requires to filter by a certain range of years or months, please specify all of them separately.

                This is my question: 
                {natural_language_query}
                """
    return message


def _get_model_author(model: str) -> str:
    """
    Identifies the model's author.

    Args:
        model (str): The name of the model.

    Returns:
        str: Model's author name.
    """
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


def get_api_params_from_lm(natural_language_query: str, token_tracker: Dict[str, Dict[str, int]], table: Table = None, model: str = "gpt-4") -> Tuple[List[str], List[str], List[str], Dict[str, Dict[str, int]]]:
    """
    Identify API parameters to retrieve the data using OpenAI models or Llama.

    Args:
        natural_language_query (str): The user's question.
        token_tracker (Dict[str, Dict[str, int]]): Dictionary that tracks token usage (completion, prompt and total tokens, and total cost).
        table (Table, optional): An instance of the Table class. Defaults to None.
        model (str, optional): The name of the model. Defaults to "gpt-4".

    Returns:
        Tuple[List[str], List[str], List[str], Dict[str, Dict[str, int]]]: A tuple containing:
            - A list with the name of the drilldowns.
            - A list with the name of the measures.
            - A list with the cuts.
            - An updated token_tracker dictionary with new token usage information.
    """
    model_author = _get_model_author(model)
    content = _get_api_components_messages(table, model_author, natural_language_query)

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

        client = OpenAI(api_key=OPENAI_KEY)
        
        while attempts < max_attempts:
            try:
                response = client.chat.completions.create(
                    model = model,
                    messages = messages,
                    temperature = 0,
                  #  response_format={"type": "json_object"},
                    )
            except APIConnectionError as e:
                print(f"OpenAI API request failed to connect: {e}")
            else:
                break
            attempts += 1
            time.sleep(1)

        output_text = response.choices[0].message.content
            
        if 'get_api_params_from_lm' in token_tracker:
            token_tracker['get_api_params_from_lm']['completion_tokens'] += response.usage.completion_tokens
            token_tracker['get_api_params_from_lm']['prompt_tokens'] += response.usage.prompt_tokens
            token_tracker['get_api_params_from_lm']['total_tokens'] += response.usage.total_tokens
            token_tracker['get_api_params_from_lm']['total_cost'] = (get_openai_token_cost_for_model(model, response.usage.completion_tokens, is_completion = True) 
                                                                        + get_openai_token_cost_for_model(model, response.usage.prompt_tokens, is_completion = False))

        else:
            token_tracker['get_api_params_from_lm'] = {
                'completion_tokens': response.usage.completion_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'total_tokens': response.usage.total_tokens,
                'total_cost': (
                    get_openai_token_cost_for_model(model, response.usage.completion_tokens, is_completion = True) 
                    + get_openai_token_cost_for_model(model, response.usage.prompt_tokens, is_completion = False)
                )
            }

        print("\nChatGPT response:", output_text)
        params = extract_text_from_markdown_triple_backticks(output_text)

        drilldowns = json.loads(params).get("drilldowns")
        measures = json.loads(params).get("measures")
        cuts = json.loads(params).get("filters")

    # alternative prompt

    elif model_author == "llama":
        url = "{}generate".format(OLLAMA_API)
        print(content)
        payload = {
            "model": model,
            "prompt": content
        }

        response = requests.post(url, json=payload)
        print(response.text)
        response = parse_response(response.text)
        print(response)
        params = extract_text_from_markdown_triple_backticks(response)
        tokens = ""

        drilldowns = json.loads(params).get("drilldowns")
        measures = json.loads(params).get("measures")
        cuts = json.loads(params).get("filters")

    else:
        # logic: ask for model on the list, or use a default one
        status = "bad status"

    return drilldowns, measures, cuts, token_tracker # json