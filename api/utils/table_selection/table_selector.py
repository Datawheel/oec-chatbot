import json
import re
from typing import List
from sentence_transformers import SentenceTransformer

from .table_details import get_table_schemas, get_table_names
from .table_database_search import get_similar_tables
from ..few_shot_examples import get_few_shot_example_messages
from ..messages import get_assistant_message_from_openai


def _extract_text_from_markdown(text):
    matches = re.findall(r"```([\s\S]+?)```", text)
    if matches:
        return matches[0]
    return text


def _get_table_selection_message_with_descriptions(scope="USA"):
    message = (
        """
        You are an expert data scientist.
        Return a JSON object with relevant SQL tables for answering the following natural language query:
        ---------------
        {natural_language_query}
        ---------------
        Respond in JSON format with your answer in a field named \"tables\" which is a list of strings.
        Respond with an empty list if you cannot identify any relevant tables.
        Write your answer in markdown format.
        """
    )
    return (
        message +
        f"""
        The following are the scripts that created the tables and the definition of their enums:
        ---------------------
        {get_table_schemas(scope=scope)}
        ---------------------

        in your answer, provide the following information:
        
        - <one to two sentence comment explaining what tables can be relevant goes here>
        - <for each table identified, comment double checking the table is in the schema above along with what the first column in the table is or (none) if it doesn't exist. be careful that any tables suggested were actually above>
        - <if any tables were incorrectly identified, make a note here about what tables from the schema should actually be used if any>
        - the markdown formatted like this:
        ```
        <json of the tables>
        ```

        Provide only the list of related tables and nothing else after.
        """
    )


def _get_table_selection_messages(scope = "USA"):

    default_messages = []
    default_messages.extend(get_few_shot_example_messages(mode = "table_selection", scope = scope))
    return default_messages


def get_relevant_tables_from_database(natural_language_query, scope = "USA", embedding_model = 'multi-qa-MiniLM-L6-cos-v1') -> List[str]:
    """
    Returns a list of the top k table names (matches the embedding vector of the NLQ with the stored vectors of each table)
    """
    #vector = get_embedding(natural_language_query, "text-embedding-ada-002")

    model = SentenceTransformer(embedding_model) # 384
    vector = model.encode([natural_language_query])

    results = get_similar_tables(vector, content_limit = 3)

    return list(results)


def get_relevant_tables_from_lm(natural_language_query, scope="USA", model="gpt-3.5-turbo", session_id=None):
    """
    Identify relevant tables for answering a natural language query via LM
    """
    content = _get_table_selection_message_with_descriptions(scope).format(
        natural_language_query = natural_language_query,
    )

    messages = _get_table_selection_messages(scope).copy()
    messages.append({
        "role": "user",
        "content": content
    })

    try:
        response = get_assistant_message_from_openai(
                messages=messages,
                model=model,
                scope=scope,
                purpose="table_selection",
                session_id=session_id,
            )["message"]["content"]
        tables_json_str = _extract_text_from_markdown(response)

        tables = json.loads(tables_json_str).get("tables")
    except:
        tables = []

    possible_tables = get_table_names(scope=scope)

    tables = [table for table in tables if table in possible_tables]

    # only get the first 7 tables
    tables = tables[:7]

    return tables


