from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from pandas import DataFrame
from typing import Dict, Tuple

from config import OPENAI_KEY
from data_analysis.token_counter import TokenTrackingHandler, get_openai_token_cost_for_model

cb = TokenTrackingHandler()
ALLOW_DANGEROUS_REQUEST = True

def agent_answer(
        df: DataFrame, 
        natural_language_query: str, 
        api_url: str, 
        context: str,
        token_tracker: Dict[str, Dict[str, int]] = None, 
        model="gpt-4-turbo"
    ) -> Tuple[str, Dict[str, Dict[str, int]]]:
    
    """
    Answer the user's question based on the provided dataframe and additional information.

    Args:
        df (DataFrame): The DataFrame containing the data to be analyzed.
        natural_language_query (str): The user's question.
        api_url (str): The URL of the API used to extract the DataFrame.
        token_tracker (Dict[str, int]): Dictionary that tracks token usage (completion, prompt and total tokens, and total cost).
        model (str, optional): The name of the language model to use. Defaults to 'gpt-4-turbo'.

    Returns:
        Tuple[str, Dict[str, Dict[str, int]]]: A tuple containing:
            - A response to the user's query.
            - An updated token_tracker dictionary with new token usage information.
    """
    prompt = f"""
            You are an expert data analyst working for the Observatory of Economic Complexity. Your goal is to provide an accurate and complete answer to the following user's question using the data available.

            **User's Question**:
            {natural_language_query}

            **Data Provided**:
            - The provided data has been extracted from a database specifically to answer the user's question.
            - The following filters have been applied in the query to retrieve it: {context}

            **Guidelines**:
            - Take into consideration the data type and formatting of the columns. 
            - If a product, service, or other variable referred to by the user appears under a different name in the data, explain this politely and provide an answer using the available information.
            - In the exceptional case that you cannot answer the question with the provided data, respond with "I can't answer your question with the available data."
            - Avoid any comments unrelated to the question.
            - Always provide the corresponding trade value, and quantity if required.
            - All quantities are in metric tons, and trade value is in USD.
            - You can complement your answer with any content found in the Observatory of Economic Complexity. 
            - Think through the answer step by step.
        """
    
    print('Context for agent:', context)

    simple_prompt = f"""
        You are an expert data analyst working for the Observatory of Economic Complexity, whose goal is to
        give an answer, as accurate and complete as possible, to the following user's question using the 
        given dataframe.

        Here is the question:
        {natural_language_query}

        Take into consideration the data type and formatting of the columns.
        It's possible that any product/service or other variables the user is referring to appears with a different name in the dataframe. Explain this in your answer in a polite manner, but always trying to give an answer with the available data.
        If you can't answer the question with the provided data, please answer with "I can't answer your question with the available data".
        Avoid any further comments not related to the question itself.
    """

    llm = ChatOpenAI(model_name=model, temperature=0, openai_api_key=OPENAI_KEY, callbacks=[cb])
    agent = create_pandas_dataframe_agent(
        llm, df, verbose=True, agent_type="openai-tools", max_iterations=3, allow_dangerous_code=ALLOW_DANGEROUS_REQUEST, number_of_head_rows=df.shape[0]
    )
    response = agent.invoke(prompt)

    if token_tracker:
        if "agent_answer" in token_tracker:
            token_tracker["agent_answer"]["completion_tokens"] += cb.completion_tokens
            token_tracker["agent_answer"]["prompt_tokens"] += cb.prompt_tokens
            token_tracker["agent_answer"]["total_tokens"] += cb.total_tokens
            token_tracker["agent_answer"]["total_cost"] = get_openai_token_cost_for_model(
                model, cb.completion_tokens, is_completion=True
            ) + get_openai_token_cost_for_model(model, cb.prompt_tokens, is_completion=False)

        else:
            token_tracker["agent_answer"] = {
                "completion_tokens": cb.completion_tokens,
                "prompt_tokens": cb.prompt_tokens,
                "total_tokens": cb.total_tokens,
                "total_cost": (
                    get_openai_token_cost_for_model(model, cb.completion_tokens, is_completion=True)
                    + get_openai_token_cost_for_model(model, cb.prompt_tokens, is_completion=False)
                ),
            }
    else:
        token_tracker = {}
        token_tracker["agent_answer"] = {
            "completion_tokens": cb.completion_tokens,
            "prompt_tokens": cb.prompt_tokens,
            "total_tokens": cb.total_tokens,
            "total_cost": (
                get_openai_token_cost_for_model(model, cb.completion_tokens, is_completion=True)
                + get_openai_token_cost_for_model(model, cb.prompt_tokens, is_completion=False)
            ),
        }

    if response == "Agent stopped due to iteration limit or time limit.":
        response = "I can't answer your question with the available data."

    return response["output"], token_tracker
