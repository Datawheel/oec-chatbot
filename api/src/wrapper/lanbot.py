from langchain_community.llms import Ollama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough, RunnableLambda, RunnableParallel, chain
from langchain_core.output_parsers import JsonOutputParser
from wrapper.logsHandlerCallback import logsHandler
from src.wrapper.logsHandlerCallback import logsHandler
from langchain.globals import set_debug, set_verbose
from os import getenv
import json
from operator import itemgetter
from operator import itemgetter
#set_debug(True)
#set_verbose(True)
TABLES_PATH = getenv('TABLES_PATH')
OLLAMA_URL = 'https://caleuche-ollama.datawheel.us'
CONFIG_FILE_NAME = 'wrapper_datausa.json'

with open(f'./{CONFIG_FILE_NAME}') as f:
    category_prompts = json.load(f)

## Models
model = Ollama(
    base_url= OLLAMA_URL,
    base_url= OLLAMA_URL,
    model= "llama2:7b-chat-q8_0",
    temperature= 0,
  ).with_config(
    seed= 123,
    run_name= 'basic_llama', 
    run_name= 'basic_llama', 
  )

model_adv = Ollama(
    base_url= OLLAMA_URL,
    base_url= OLLAMA_URL,
    model= 'mixtral:8x7b-instruct-v0.1-q4_K_M',#'gemma:7b-instruct-q4_K_M',//
    system= '',
    temperature= 0,
).with_config(
    seed= 123,
    run_name= 'advance_mixtral',
)
                            
## Prompts                             
baseCategoryPrompt = """You are an expert analyzing questions content.
    Check if a question explicitly mentions all of the following elements:"""

baseOutputPrompt = """
. If it does reply '''COMPLETE'''. If it doesn't, the list of the missing elements. 
Answer in the following JSON format:  

{{"analysis": "[your analysis]",
"answer": "[your answer]"}}

Here are some examples: 
Here are some examples: 

question: How many dollars in electronics were transported from Texas to California during 2020 by truck?

{{"analysis": "The question explicitly mentions a product, a transport medium, and at least one state.",
"answer": "COMPLETE"}}

question: Who is the president?

{{"analysis": "The question does not mention a political party and state or a candidate name.", 
"answer": "political party, state and candidate name"}} 

Here is a question: {question}
"""

alternativeOutputPrompt = """
. If it does reply '''COMPLETE'''. If it doesn't, the list of the missing elements. 
All output must be in valid JSON format. Don't add explanation beyond the JSON. Follow this examples:

question: How many dollars in electronics were transported from Texas to California?

{{"analysis": "The question explicitly mentions a product, and at least one state but no transport.",
"answer": "transport medium"}} 

question: How many dollars in electronics were transported from Texas to California during 2020 by truck? 
{{"analysis": "The question explicitly mentions a product, a transport medium, and at least one state.", 
"answer": "COMPLETE"}}

question: Who is the president?
{{"analysis": "The question does not mention a political party and state or a candidate name.",
"answer": "political party, state and candidate name"}}

question: {question} 
"""


# Add templtas
for c in category_prompts:
    c['prompt_template'] = '{} {} {}'.format(baseCategoryPrompt, ', '.join(c['vars']), baseOutputPrompt)
    c['prompt_alternative'] = '{} {} {}'.format(baseCategoryPrompt, ', '.join(c['vars']), alternativeOutputPrompt)
    c['prompt_template'] = '{} {} {}'.format(baseCategoryPrompt, ', '.join(c['vars']), baseOutputPrompt)
    c['prompt_alternative'] = '{} {} {}'.format(baseCategoryPrompt, ', '.join(c['vars']), alternativeOutputPrompt)


base_cases =  [
    {
        'name': 'Greetings',
        'prompt_template': 'Greet back',
        'prompt_alternative':'Greet back',
        'examples': [],
    },
    {
        'name': 'Other topic',
        'prompt_template':'Say: >>>DataUSA does not have information about that topic, please ask another question<<<',
        'prompt_alternative':'Say: >>>DataUSA does not have information about that topic, please ask another question<<<',
        'examples': ['What is the GDP per capita?'],
    },
    {
        'name': 'Not a question',
        'prompt_template':'Say: >>>please, write your query as a question<<<',
        'prompt_alternative':'Say: >>>please, write your query as a question<<<',
        'examples': ['hi, how are you?'],
    },
]

category_prompts = category_prompts + base_cases


category_prompts = category_prompts + base_cases

#print(json.dumps(category_prompts, indent = 4))

classify_prompt = PromptTemplate.from_template(
"""
    Summarize in conversation as a question, then classify the summary into one 
    of these categories:""" + ", ".join([c['name'] for c in category_prompts]) + """. All output must be in valid JSON. 
    Don't add explanation beyond the JSON as shown in the following examples: 
        {{"conversation": "[AI]:Hi, I'm ready to help;,[User]:Hi;[.]", 
        "summary": "User said Hi",
        "explanation":"The user simply said hi", 
        "category": "Greetings",}}

        {{"conversation": "[AI]:Hi, I'm ready to help;,[User]:Which party won the latest presidential election?;[.]",
        "summary": "Which party won the latest presidential election?",
        "explanation":"User asked for the party that won the latest presidential election", 
        "category": "President election",}}

        {{"conversation": "[AI]:Hi, I'm ready to help;,[User]:Who is the president?;,[User]:the current president;,[User]:of US;[.],
        "summary": "Who is the current president of US?",
        "explanation":"User asked who is the president, and added details later", 
        "category": "President election",}}

    Here is a conversation: {history}.
"""
)


### Chains
@chain
def class_parser(info):
    """
    Adhoc function to parse JSON object from chain and return object with question and category 
    * properties only
    * @param {object} info JSON object
    * @returns object with question and category properties
    """
    print('In class_parser: {}'.format(info.keys()))
    return {
        'question': info['summary'],
        'category': info['category']
    }

@chain
def stream_acc(info):
    """
    Prevent LLMs to stream (stutter) within a langchain chain. Use after the LLM.
    """
    print('In stream agg: {}'.format(info))
    return info

classifyOne = classify_prompt.pipe(model.bind(
            system= 'You are an linguistic expert in summarization and classification tasks.',
            format='json')
        ).pipe(stream_acc
        ).pipe(JsonOutputParser()
        ).pipe(class_parser)

classifyTwo = classify_prompt.pipe(model_adv.bind(
            system= 'You are an linguistic expert in summarization and classification tasks. You can only output valid JSON.',
            format='json')
        ).pipe(stream_acc
        ).pipe(JsonOutputParser()
        ).pipe(class_parser) 


def route(info):
    """
    Route prompts for categories from classify_num chain
    * @param {*} info 
    * @returns string or JSON with answer property for action function
    """
    print('In route: {}>> {}'.format(info.keys(), [info[k ]for k in info]))

    for c in category_prompts[:-2]:
        if c['name'].lower() in info['category'].lower():
            print('Class: {} {}'.format(c['name'], c['prompt_template']))

            newChain = PromptTemplate.from_template(c['prompt_template'])
            alterChain = PromptTemplate.from_template(c['prompt_alternative'])

            if c['name'] == 'Greetings':
                newChain = newChain.pipe(model)
                alterChain = alterChain.pipe(model_adv)
            else:
                newChain = newChain.pipe(model_adv.bind(format= 'json')).pipe(JsonOutputParser())
                alterChain = alterChain.pipe(model_adv.bind(format= 'json')).pipe(JsonOutputParser())
        
            return  newChain.with_fallbacks(
                fallbacks = [alterChain]
            )
                             

    if 'not a question' in info['category'].lower():
        return 'Please, formulate a question'
    else:
        return 'DataUSA does not have information regarding that topic, please ask another question'


def action(init):
    """
    Call API or pass previous step messages
    * @param {*} init object with line and input property
    * @returns return object with content property as chain output
    """
    info = init['line']
    print('In action fn: {}'.format([(k, info[k]) for k in info.keys()]))

    handleQuery = init['input']['handleQuery']
    args = init['input']['pass_args']

    if isinstance(info['action'], dict) and 'answer' in info['action'].keys():
        if info['action']['answer'].lower() == 'complete':

            yield json.dumps({'content': "Good question! let's check the data..."})
            #resp = '...'
            searchText = info['question'].split(':')[-1]
            print(searchText)

            #### Call get_query
            resp = handleQuery(searchText, *args)

            yield json.dumps({ 'content': resp})

        else:
            # ask for additional info
            yield json.dumps({'content': 'please, specify in your question: {}'.format(info['action']['answer'])})
    else:
        # pass 
        yield json.dumps({'content': info['action']})


### Main chain
altern_chain = RunnableSequence(
                RunnableParallel({
                    'line': (
                                classifyOne.with_fallbacks(fallbacks = [classifyTwo]) 
                                | {
                                    'question': itemgetter("question"),
                                    'action': RunnableLambda(route),
                                }
                            ),
                    'input': RunnablePassthrough()
                })
                | RunnableLambda(action),
            )



def Langbot(newMessage, handleQuery, logger=[], *args):
    """
    Activate chain to reflect upon user chat history to ask more information or to pass to get_query chain or other function.
    """
    newChatMessageHistory = ChatMessageHistory()
    newChatMessageHistory.add_ai_message('Hi, ready to help you')
    newChatMessageHistory.add_user_message(newMessage)

    for ans in altern_chain.stream({
        'history': ';'.join([f"{' [AI]' if m.lc_id()[2]=='AIMessage' else ' [User]'}:{m.content}"
                            for m in newChatMessageHistory.messages]) + '[.]',
        'handleQuery': handleQuery,
        'pass_args': args
        },
        config={'callbacks':[logsHandler(logger, print_logs = True, print_starts=False)]}):
        yield ans
    #print('\n\n>>>>>>>>>>>>>  ', logger)
    


