from langchain_community.llms import Ollama
from langchain_openai import OpenAI
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
OPENAI = getenv('OPENAI_KEY')

model = OpenAI(
    model_name="gpt-3.5-turbo-instruct",
    temperature=0,
    openai_api_key=OPENAI
    )

model_ = Ollama(
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
You are a grammar expert analyzing questions in chats. All output must be in valid JSON format. 
Don't add explanation beyond the JSON.
"""

question_prompt = PromptTemplate.from_template(
"""
You are a grammar expert analyzing questions in chats. All output must be in valid JSON format. 
Don't add explanation beyond the JSON.

In the following Chat history, classify if the the latest [User] input is:

- a new question made by the user, or 
- a complementary information for a previous question, or 
- not a question

If the input is classified as 'complementary information for a previous question', summarize the the question.
Answer using following output format, here are some examples:

{{
"history": "[User]: Which country exported most copper;[AI]: Which year?;[User]:2022[.]",
"reasoning":"User initially asked which country exported the most copper, then AI asked in which year, then user complemented with year 2022",
"type": "complementary information" 
"question": "Which country exported most copper in 2022",
}}

{{
"history": "[User]: Which country exported most copper in 2022?;[AI]:Chile;[User]:What are the top five exporting countries for cars in terms of value?;[.]",
"reasoning":"The lastest question is What are the top five exporting countries for cars in terms of value? which is not related to previous questions",
"type": "new question" 
"question": "What are the top five exporting countries for cars in terms of value?",
}}

{{
"history": "[User]: Hi. how are you?[.]",
"reasoning":"The user greet",
"type": "not a question" 
"question": "None",
}}

here is a chat history: {chathistory}
""")

          #.bind(system=question_sys_prompt, format='json'))\
question_chain = question_prompt\
    .pipe(model)\
        .pipe(stream_acc)\
            .pipe(JsonOutputParser())

question_chain_alt = question_prompt.pipe(model)

@chain
def route_question(info):
    json_form = info['json_form']
    action = info['action']

    if action['type'] == 'not a question':
        return PromptTemplate("Answer politely: {question}").pipe(model)
    
    if action['type'] =='new question':
        json_form = set_json_form(action['question'])
        return {'json_form': json_form, 'question': action['question']} | valid_chain
    
    if action['type'] == 'complement information':
        return {'json_form': json_form, 'question': action['question']} | valid_chain


# Use table_table selection
from table_selection.table_selector import request_tables_to_lm_from_db
from table_selection.table import TableManager

# Call Schema Json to build Form JSON
def set_json_form(query):
    table_manager = TableManager(TABLES_PATH)
    table = request_tables_to_lm_from_db(query, table_manager)
    json_form = {'cube': table.name}
    
    return json_form

# LLM validation
    # Extract variables
    # Route ask missing variables
    # Offer members for missing variables

validation_sys_prompt = """
You are linguistic expert, used to analyze questions and complete forms precisely. All output must be in valid JSON format. 
Don't add explanation beyond the JSON.
"""
validation_prompt = PromptTemplate.from_template(
"""
Complete the form based on the question input. User only the explicit information contained in the question.
If no information is available in the question, left the field blank.
Answer in JSON format as shown in the following examples:

{{
"question":""
"explanation":" ",
"json_form":"{{}}",
}}

Here is the form: {json_form}
Here is the question: {question}
"""
)

alt_validation_prompt = PromptTemplate.from_template(
"""

""")

valid_chain = validation_prompt\
    .pipe(model.bind(
        system = validation_sys_prompt, 
        format='json'))\
    .pipe(JsonOutputParser())\
    .with_fallbacks(
        [alt_validation_prompt\
            .pipe(model_adv.bind(
                system = validation_sys_prompt, 
                format= 'json'))\
            .pipe(JsonOutputParser())])

def get_empty_json_fields(json):
    return None


@chain
def route_answer(info):
    handleAPIBuilder = info['input']['handleAPIBuilder']
    info = info['process']

    # if answer is not json is not a question
    if type(info) == str:
        yield {'content': info}

    json_form = info['json_form']
    missing = get_empty_json_fields(json_form)

    if missing:
        for m in missing:
            yield {'content': f'Please specify {m}'}
    else:
        yield {'content': " Good question, let's check the data..."}
        response = handleAPIBuilder(json_form)
        yield {'content': response}


# Build Chain
main_chain = RunnableSequence(
    {
        'input': RunnablePassthrough(),
        'process': (
                {
                    'json_form': itemgetter("json_form"),
                    'action': question_chain  
                } | route_question 
            )
    } | route_answer 
)

# Export function

def wrapperCall(history, json_form, handleAPIBuilder, logger=[] ):
    """
    
    """
    for answer in main_chain.stream({
        'chathistory': ';'.join([f"{' [AI]' if m.source =='AIMessage' else ' [User]'}:{m.content}"
                            for m in history]) + '[.]',
        'json_form': json_form, 
        'handleAPIBuilder': handleAPIBuilder
    }, config = {'callbacks':[logsHandler(logger, print_logs = True, print_starts=False)]}
    ):
        yield answer

"""
if __name__ == "__main__":
    wrapperCall([{'source':'AIMessage', 'content':'hi, how can I help you'},
             {'source':'AIMessage', 'content':'Which country export the most copper?'}])
"""