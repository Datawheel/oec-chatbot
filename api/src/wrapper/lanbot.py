from langchain_community.llms import Ollama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough, RunnableLambda, RunnableParallel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain.globals import set_debug, set_verbose

set_debug(True)
set_verbose(True)



### handler

class logsHandler(BaseCallbackHandler):

    def __init__(self, outFile = [], **kwargs):
        super()
        self.outFile = outFile
  
    def on_chain_start(self, chain):
        print( f'Entering new chain: {chain.keys()} {chain.type}')
        self.outFile.append(chain)
    
    def on_chain_end(self, chain):
        print(f'Finish chain:  {chain.keys()}')
        self.outFile.append(chain)
    
    def on_chain_error(self, chain):
        print(f'Error chain:  {chain.keys()}')
        self.outFile.append(chain)

    def on_LLM_start(self, chain):
        print(f'Starting llm:  {chain.keys()} ')
        self.outFile.append(chain)
    
    def on_LLM_end(self, chain):
        print(f'Finish llm:  {chain.keys()} ')
        self.outFile.append(chain)
      
    def on_LLM_error(self, chain):
        print(f'Error llm:  {chain.keys()} ')
        self.outFile.append(chain)   


## Models
model = Ollama(
    base_url= 'https://caleuche-ollama.datawheel.us',
    model= "llama2:7b-chat-q8_0",
    temperature= 0,
  ).with_config(
    seed= 123,
    run_name= 'basic_llama'
  )

model_adv = Ollama(
    base_url= 'https://caleuche-ollama.datawheel.us',
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

Here is some examples: 

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

electionVars = ['political party', 'US state', ' candidate name']
productVars = ['product name', 'US state', 'transportation medium']
priceVars = ['prodcut name','date']


category_prompts = [
    {
        'name':'Senate election',
        'metrics': ['number of votes'],
        'optional_vars': ['year'],
        'prompt_template':f'{baseCategoryPrompt} {electionVars} {baseOutputPrompt}',
        'prompt_alternative':f'{baseCategoryPrompt} {electionVars} {alternativeOutputPrompt}',
        'examples':[
            'What candidate to senate from the republican party received the most amount of votes in California during the 2020 elections?']
    },
    {
        'name':'House election',
        'metrics': ['number of votes'],
        'optional_vars': ['year'],
        'prompt_template':f'{baseCategoryPrompt} {electionVars} {baseOutputPrompt}',
        'prompt_alternative':f'{baseCategoryPrompt} {electionVars} {alternativeOutputPrompt}',
        'examples':[
            'What democrat candidate to the US house of representatives received the least amount of  votes in Washington during the 2010 elections?',
            'What party received the least amount of votes during the 2010 US house of representatives elections in the state of Washington?']
    },
    {
        'name':'President election',
        'metrics': ['number of votes'],
        'optional_vars': ['year'],
        'prompt_template':f'{baseCategoryPrompt} {electionVars} {baseOutputPrompt}',
        'prompt_alternative':f'{baseCategoryPrompt} {electionVars} {alternativeOutputPrompt}',
        'examples': [
            'What candidates from the republican and democratic parties received the most amount of votes across the country during the 2016 presidential elections?']
    },
    {
        'name':'Consumer Price Index',
        'metrics':['cuantity', 'price metric'],
        'optional_vars': ['year'],
        'prompt_template': f'{baseCategoryPrompt} {priceVars} {baseOutputPrompt}',
        'prompt_alternative': f'{baseCategoryPrompt} {priceVars} {alternativeOutputPrompt}',
        'examples':[
            'How much was the CPI of eggs in January of 2013?',
            'How much was the YoY variation of the CPI of eggs in January of 2014?']
    },
    {
        'name':'Freight movement',
        'metrics': ['amount', 'money'],
        'optional_vars': ['year'],
        'prompt_template': f'{baseCategoryPrompt} {productVars} {baseOutputPrompt}', 
        'prompt_alternative': f'{baseCategoryPrompt} {productVars} {alternativeOutputPrompt}',
        'examples': [
            'How many dollars in electronics were transported from Texas to California during 2020 by truck?',
            'How many tons of plastic were moved from Texas to California by truck during 2021?']
    },
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

classifyOne = classify_prompt.pipe(model.bind(
            system= 'You are an linguistic expert in summarization and classification tasks.',
            format='json')
        ).pipe(JsonOutputParser()
        ).pipe(RunnableLambda(class_parser))

classifyTwo = classify_prompt.pipe(model_adv.bind(
            system= 'You are an linguistic expert in summarization and classification tasks. You can only output valid JSON.',
            format='json')
        ).pipe(JsonOutputParser()
        ).pipe(RunnableLambda(class_parser)) 


def route(info):
    """
    Route prompts for categories from classify_num chain
    * @param {*} info 
    * @returns string or JSON with answer property for action function
    """
    print(f'In route: {info.keys()}')
    for c in category_prompts[:-2]:
        if c['name'].lower() in info['category'].lower():
            print('Class: {}'.format(c['name']))

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

    #updater = init.input.updater
    #handleTable = init.input.handleTable

    if isinstance(info['action'], dict) and 'answer' in info['action'].keys():
        if info['action']['answer'].lower() == 'complete':
            resp = '...'
            searchText = info['question'].split(':')[-1]
            print(searchText)


            #### Call get_query #TODO
            
            return {
                    'content': "Good question! let's check the data...", 
                    'question': resp
                    }

        else:
            # ask for additional info
            return {'content': 'please, specify in your question: {info.action.answer}'}
    else:
        # pass 
        return {'content': info['action']}

from operator import itemgetter
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

### Memory
newChatMessageHistory = ChatMessageHistory()
newChatMessageHistory.add_ai_message('Hi, ready to help you')

print(newChatMessageHistory.messages[0].lc_id())

def Langbot(newMessage, setMessages, handleTable, logger=[]):

    newChatMessageHistory.add_user_message(newMessage)

    ans = altern_chain.invoke({
        'history': ';'.join([f"{' [AI]' if m.lc_id()[2]=='AIMessage' else ' [User]'}:{m.content}"
                            for m in newChatMessageHistory.messages]) + '[.]',
        'updater': setMessages,
        'handleTable': handleTable
    },
    config={'callbacks':[logsHandler(logger)]})
    print(logger)
    return ans


