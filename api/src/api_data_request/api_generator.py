import json
from openai import OpenAI, APIConnectionError
import requests
import time

from config import OLLAMA_API, OPENAI_KEY
from table_selection.table import *
from utils.preprocessors.text import *
from utils.similarity_search import *
from api_data_request.api import *

def get_api_components_messages(table, model_author, natural_language_query = ""):

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

        drilldowns = json.loads(params).get("drilldowns")
        measures = json.loads(params).get("measures")
        cuts = json.loads(params).get("filters")

    else:
        # logic: ask for model on the list, or use a default one
        status = "bad status"

    return drilldowns, measures, cuts # json