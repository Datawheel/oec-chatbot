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

#Aux func
@chain
def stream_acc(info):
    """
    Prevent LLMs to stream (stutter) within a langchain chain. Use after the LLM.
    """
    print('In stream agg: {}'.format(info))
    return info

# Question LLM chat history 
    # Summary question     
    # route to:
        # no question
        # new question
        # complement question

question_sys_prompt = """
You are an expert analyzing questions in chats.
"""

question_prompt = PromptTemplate.from_template(
"""
In the following Chat history. 
Is the latest [User] input a new questionor, a complement information from a previous question or not a question?


Output format:

{{
"question": "",
"reasoning":"",
"type": "" 
}}

here is a chat history: {history}
""")

question_chain = question_prompt\
    .pipe(model.bind(system=question_sys_prompt, format='json'))\
        .pipe(stream_acc)\
            .pipe(JsonOutputParser())

question_chain_alt = question_prompt.pipe(model)

@chain
def route_question(info):
    
    if info['type'] == 'no_question':
        return PromptTemplate("Answer politely: {}").pipe(model)
    if info['type'] =='new_question':
        reset_form_json()
        
        return {'action': 'RAG', }
    if info['type'] == 'complement':
        return { 'action': 'summary','history': info['history']}

# Use table_table selection
from ..table_selection.table_selector import request_tables_to_lm_from_db
from ..table_selection.table import TableManager

SCHEMA = getenv('SCHEMA')
# LLM Classification 
    # rerank RAG answer pick a cube

# Call Schema Json to build Form JSON
def set_form_json(query):
    table_manager = TableManager(TABLES_PATH)
    table = request_tables_to_lm_from_db(query, table_manager)
    
    return table.get_drilldown_member()
 

# LLM validation
    # Extract variables
    # Route ask missing variables
    # Offer members for missing variables

validation_sys_prompt = """
You are linguistic expert, used to analyze questions and complete forms.
"""
validation_prompt = PromptTemplate.from_template(
"""
Based on a question complete the field of the following form in JSON format.
complete the form with the explicit information contained in the question.
 Here are some examples:

                                                 """)

alt_validation_prompt = PromptTemplate.from_template(
"""

""")

valid_chain = validation_prompt\
    .pipe(model.bind(
        system = validation_sys_prompt, 
        format='json'))\
            .pipe(JsonOutputParser())\
    .with_fallbacks(
        alt_validation_prompt\
            .pipe(model_adv.bind(
                system = validation_sys_prompt, 
                format= 'json'))\
                    .pipe(JsonOutputParser()))


# Build Chain
main_chain = RunnableSequence(
    question_chain | 
    {
        'action': route_question 
    } | valid_chain


)
# Export function

def wrapper(history, logger=[]):
    """
    
    """
    for answer in main_chain.stream({
        history: ';'.join([f"{' [AI]' if m.source =='AIMessage' else ' [User]'}:{m.content}"
                            for m in history]) + '[.]',
    }, config = {'callbacks':[logsHandler(logger, print_logs = True, print_starts=False)]}
    ):
        yield answer
