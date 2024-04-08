from langchain_community.llms import Ollama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough, RunnableLambda, RunnableParallel, chain
from langchain_core.output_parsers import JsonOutputParser
from wrapper.logsHandlerCallback import logsHandler
from langchain.globals import set_debug, set_verbose
from os import getenv
import json
from operator import itemgetter


TABLES_PATH = getenv('TABLES_PATH')
OLLAMA_URL = 'https://caleuche-ollama.datawheel.us'
CONFIG_FILE_NAME = 'wrapper_datausa.json'

model = Ollama(
    base_url= OLLAMA_URL,
    model= "llama2:7b-chat-q8_0",
    temperature= 0,
  ).with_config(
    seed= 123,
    run_name= 'basic_llama', 
  )

model_adv = Ollama(
    base_url= OLLAMA_URL,
    model= 'mixtral:8x7b-instruct-v0.1-q4_K_M',#'gemma:7b-instruct-q4_K_M',//
    system= '',
    temperature= 0,
).with_config(
    seed= 123,
    run_name= 'advance_mixtral',
)

# LLM Summary chat history 
    # Summary question     
    # route to question/no question/new question/complement question

summary_sys_prompt = """
You are an expert analyzing chat from questions.
"""

summary_prompt = """
Summarize the following chat history

Output format:

{{

}}

"""
@chain
def route_question(info):
    pass


# Use table_table selection
from ..table_selection.table_selector import get_relevant_tables_from_database

# LLM Classification 
    # rerank RAG answer pick a cube



# Call Schema Json to build Form JSON


# LLM validation
    # Extract variables
    # Route ask missing variables
    # Offer members for missing variables



# Build Chain


# Export function