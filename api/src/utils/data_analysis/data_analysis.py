from config import OPENAI_KEY
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.chat_models import ChatOpenAI


def agent_answer(df, natural_language_query):

    prompt = (
        f"""
        You are an expert data analyst whose goal is to give an answer, as accurate as possible, to a user's question. You are given a question from a user and a pandas dataframe that contains the data to answer this question.\n
        The question is the following:
        ---------------\n
        {natural_language_query}
        \n---------------\n
        Take into consideration the data type and formatting of the columns.
        Its possible that any product/service or other variables the user is referring to appears with a different name in the dataframe. Explain this in your answer in a polite manner, but always trying to give an answer with the available data.
        If you can't answer the question with the provided data, please answer with "I can't answer your question with the available data".
        Lets think it through step by step.
        Do not write 'python' anywhere.
        Avoid any further comments not related to the question itself.
        """
    )

    llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=0, openai_api_key=OPENAI_KEY)

    agent =  create_pandas_dataframe_agent(llm, df, verbose=True)
    response = agent.run(prompt)
    
    if(response == "Agent stopped due to iteration limit or time limit."): response = "I can't answer your question with the available data."
    
    return response