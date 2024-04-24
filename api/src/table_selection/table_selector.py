import json
import time

from typing import Dict, List, Tuple
from openai import OpenAI, APIConnectionError
from sentence_transformers import SentenceTransformer

from config import OPENAI_KEY
from table_selection.table import Table, TableManager
from utils.few_shot_examples import get_few_shot_example_messages
from utils.preprocessors.text import extract_text_from_markdown_triple_backticks
from utils.similarity_search import get_similar_tables
from data_analysis.token_counter import get_openai_token_cost_for_model

def _get_table_selection_message_with_descriptions(table_manager: TableManager, table_names: List[str] = None):

    response_part = """
        {
            "explanation": "",
            "table": ""
        }
        """

    message = (
        f"""
        You are an expert data analyst. 
        You are given a question from a user, and a list of tables you are able to query. 
        Select the most relevant table that could contain the data to answer the user's question:

        ---------------------\n
        {table_manager.get_table_schemas(table_names)}
        ---------------------\n

        Your response should be in JSON format with:

            - "explanation": one to two sentence comment explaining why the chosen table is relevant goes here, double checking it exists in the list provided before.
            - "table": The name of the selected table, the most relevant one to answer the question.

        Response format:

        ```
        {response_part}
        ```

        """
    )

    return message


def _get_table_selection_messages() -> List[str]:
    default_messages = []
    default_messages.extend(get_few_shot_example_messages(mode = "table_selection"))
    return default_messages


def get_relevant_tables_from_database(
        natural_language_query: str, 
        content_limit: int = 1, 
        embedding_model: str = 'multi-qa-MiniLM-L6-cos-v1'
        ) -> List[str]:
    """
    Matches the user's question to a table using their embeddings.

    Args:
        natural_language_query (str): The user's question.
        content_limit (int, optional): Number of table names to retrieve. Defaults to 1.
        embedding_model (str, optional): The embedding model to use. Defaults to 'multi-qa-MiniLM-L6-cos-v1'.

    Returns:
        List[str]: List of table names.
    """
    model = SentenceTransformer(embedding_model)
    vector = model.encode([natural_language_query])

    results = get_similar_tables(vector, content_limit = content_limit)

    return list(results)


def get_relevant_tables_from_lm(
        natural_language_query: str, 
        table_manager: TableManager, 
        table_list: List[str] = None, 
        token_tracker: Dict[str, Dict[str, int]] = None, 
        model: str = "gpt-4"
        ) -> Tuple[str, Dict[str, int]]:
    """
    Identifies relevant tables to answer a natural language query via LM.

    Args:
        natural_language_query (str): The user's question.
        table_manager (TableManager): An instance of the TableManager class.
        table_list (List[str], optional): List of table_names for the LM to choose from. Defaults to None.
        token_tracker (Dict[str, Dict[str, int]]): Dictionary that tracks token usage (completion, prompt and total tokens, and total cost).
        model (str, optional): Name of the model to use. Defaults to "gpt-4".

    Returns:
        Tuple[str, Dict[str, Dict[str, int]]]: A tuple containing:
            - Name of the chosen table.
            - Updated token_tracker dictionary with new token usage information.
    """
    max_attempts = 5
    attempts = 0

    content = _get_table_selection_message_with_descriptions(table_manager, table_list)

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
               # response_format={"type": "json_object"},
                )
        except APIConnectionError as e:
            print(f"OpenAI API request failed to connect: {e}")
        else:
            break
        attempts += 1
        time.sleep(1)

    output_text = response.choices[0].message.content

    if token_tracker:

        if 'request_tables_to_lm_from_db' in token_tracker:
            token_tracker['request_tables_to_lm_from_db']['completion_tokens'] += response.usage.completion_tokens
            token_tracker['request_tables_to_lm_from_db']['prompt_tokens'] += response.usage.prompt_tokens
            token_tracker['request_tables_to_lm_from_db']['total_tokens'] += response.usage.total_tokens
            token_tracker['request_tables_to_lm_from_db']['total_cost'] = (get_openai_token_cost_for_model(model, response.usage.completion_tokens, is_completion=True) 
                                                                        + get_openai_token_cost_for_model(model, response.usage.prompt_tokens, is_completion=False))

        else:
            token_tracker['request_tables_to_lm_from_db'] = {
                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens,
                    'total_cost': (
                        get_openai_token_cost_for_model(model, response.usage.completion_tokens, is_completion=True) 
                        + get_openai_token_cost_for_model(model, response.usage.prompt_tokens, is_completion=False)
                    )
                }
            
    else: 
        token_tracker = {}
        token_tracker['request_tables_to_lm_from_db'] = {
                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens,
                    'total_cost': (
                        get_openai_token_cost_for_model(model, response.usage.completion_tokens, is_completion=True) 
                        + get_openai_token_cost_for_model(model, response.usage.prompt_tokens, is_completion=False)
                    )
                }

    print("\nChatGPT response:", output_text)
    tables_json_str = extract_text_from_markdown_triple_backticks(output_text)
    table_name = json.loads(tables_json_str).get("table")

    return table_name, token_tracker
    


def request_tables_to_lm_from_db(
        natural_language_query: str, 
        table_manager: TableManager, 
        token_tracker: Dict[str, Dict[str, int]] = None, 
        content_limit: int = 3
        ) -> Tuple[Table, Dict, Dict[str, Dict[str, int]]]:
    """
    Extracts most similar tables from database using embeddings and similarity functions, and then lets the llm choose the most relevant one.

    Args:
        natural_language_query (str): The user's question.
        table_manager (TableManager): An instance of the TableManager class.
        token_tracker (Dict[str, Dict[str, int]]): Dictionary that tracks token usage (completion, prompt and total tokens, and total cost).
        content_limit (int, optional): Number of tables to retrieve from the database, that the LM will choose from. Defaults to 3.

    Returns:
        Tuple[Table, Dict, Dict[str, Dict[str, int]]]: A tuple containing:
            - The instance of the Table class with the selected table.
            - A JSON object with all the parameters needed to build the API.
            - An updated token_tracker dictionary with new token usage information.
    """
    db_tables = get_relevant_tables_from_database(natural_language_query, content_limit)

    if token_tracker: 
        lm_table, token_tracker = get_relevant_tables_from_lm(natural_language_query, table_manager, db_tables, token_tracker)
        
    else: lm_table, token_tracker = get_relevant_tables_from_lm(natural_language_query, table_manager, db_tables)

    selected_table = table_manager.get_table(lm_table)
    form_json = {}
    return selected_table, form_json, token_tracker