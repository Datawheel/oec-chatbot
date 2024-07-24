import json

from operator import itemgetter
import time
from langchain.globals import set_debug, set_verbose
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.llms import Ollama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableSequence,
    RunnablePassthrough,
    RunnableLambda,
    RunnableParallel,
    chain,
)
from langchain_openai import ChatOpenAI, OpenAI
from table_selection.table import TableManager
from wrapper.json_check import json_iterator, set_form_json
from wrapper.logsHandlerCallback import logsHandler

from config import TABLES_PATH, OPENAI_KEY, OLLAMA_API

from langchain.globals import set_debug, set_verbose

set_verbose(False)
set_debug(False)
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field, validator


class QuestionParser(BaseModel):
    history: str = Field(description="same as chat history")
    reasoning: str = Field(description="with your analysis")
    summary: str = Field(description="with a synthesis of the users question")
    type: str = Field(description="with the classification category")


OLLAMA_URL = "https://caleuche-ollama.datawheel.us"
LLAMA_2_URL = "https://oec-chatbot-nginx.datawheel.us/model/llama2-7b/"
LLAMA_3_URL = "https://oec-chatbot-nginx.datawheel.us/model/llama3-8b/"
MIXTRAL_URL = "https://oec-chatbot-nginx.datawheel.us/model/mixtral-8x7b/"


######### Models

model = ChatOpenAI(model_name="gpt-4-turbo", temperature=0, openai_api_key=OPENAI_KEY)

model_basic = Ollama(
    base_url=OLLAMA_URL,
    model="llama2:7b-chat-q8_0",  # use
    temperature=0,
    keep_alive="1h",
    num_ctx=4096,
    num_predict=64,
).with_config(
    seed=123,
    run_name="basic_llama",
)


model_adv = Ollama(
    base_url=LLAMA_3_URL,
    model="llama3:8b-instruct-q8_0",  # "llama3:8b-instruct-q4_K_M", #"llama2:7b-chat-q8_0",
    temperature=0,
    keep_alive="1h",
).with_config(
    seed=123,
    run_name="adv_llama",
)


model_mix = Ollama(
    base_url=MIXTRAL_URL,
    model="mixtral:8x7b-instruct-v0.1-q4_K_M",  #'gemma:7b-instruct-q4_K_M',//
    temperature=0,
    keep_alive="1h",
).with_config(
    seed=123,
    run_name="advance_mixtral",
)


############# Aux func
@chain
def stream_acc(info):
    """
    Prevent LLMs to stream (stutter) within a langchain chain. Use after the LLM.
    """
    print("In stream acc: {}".format(info))
    return info


############# Prompts

#####  LLM Question

question_sys_prompt = """
You are a grammar expert analyzing questions in chats. All output must be in valid JSON format. 
Don't add explanation beyond the JSON. Do not respond to questions, just analyze them.
Take a depth breath and think step by step.
"""

question_prompt = PromptTemplate.from_template(
    """
In the following Chat history, classify if the latest [User] input is:
- a new question about economic data made by the user, or 
- a complementary information for a previous question, or 
- not a question

If the input is classified as 'complementary information', summarize the question.

Answer using following output format. All answer must contain all the four fields (chat_history, reasoning, question and type).
Make sure "chat_history" field is an exact copy of the chat history.
Here are some examples:

{{
"chat_history": "[User]: Which country exported most copper;[AI]: Which year?;[User]:2022[.]",
"reasoning":"User initially asked which country exported the most copper, then AI asked in which year, then user complemented with year 2022",
"summary": "Which country exported most copper in 2022",
"type": "complementary information" 
}}

{{
"chat_history": "[User]: Which country exported most copper in 2022?;[AI]:Chile;[User]:What are the top five exporting countries for cars in terms of value?;[.]",
"reasoning":"The lastest question is What are the top five exporting countries for cars in terms of value? which is not related to previous questions",
"summary": "What are the top five exporting countries for cars in terms of value?",
"type": "new question" 
}}

{{
"chat_history": "[User]: Hi. how are you?[.]",
"reasoning":"The user greet",
"summary": "User said hi",
"type": "not a question" 
}}

here is a chat history: {chathistory}
"""
)

alt_question_prompt = PromptTemplate.from_template(
    """
You are a grammar expert analyzing questions in chats. All output must be in valid JSON format. 
Don't add explanation beyond the JSON.

In the following Chat history, classify if the latest [User] input is:

- a new question made by the user, or 
- a complementary information for a previous question, or 
- not a question

If the input is classified as 'complementary information', summarize the question.
Answer using following output format. 
All answer must contain all the four fields: 
"history" withthe chat history, 
"reasoning" with your analysis, 
"summary": with a synthesis of the user's input
"type": with the classification categoty

Here are some examples:

{{
"history": "[User]: Which country exported most copper;[AI]: Which year?;[User]:2022[.]",
"reasoning":"User initially asked which country exported the most copper, then AI asked in which year, then user complemented with year 2022",
"summary": "Which country exported most copper in 2022",
"type": "complementary information" 
}}

{{
"history": "[User]: Which country exported most copper in 2022?;[AI]:Chile;[User]:What are the top five exporting countries for cars in terms of value?;[.]",
"reasoning":"The lastest question is What are the top five exporting countries for cars in terms of value? which is not related to previous questions",
"summary": "What are the top five exporting countries for cars in terms of value?",
"type": "new question" 
}}

{{
"history": "[User]: Hi. how are you?[.]",
"reasoning":"The user greet",
"summary": "User said hi",
"type": "not a question" 
}}

here is a chat history: {chathistory}
"""
)

##### LLM validation

validation_sys_prompt = """
You are linguistic expert analyst used to analyze questions and complete forms in JSON format precisely.
These forms are use later to create an API query, they need to be precise. 
Also, all output must be also in valid JSON format. 
Don't add explanations beyond the JSON.
Take a depth breath and think step by step.
"""

trade_validation_few_shot = [
    {
        "question": "Which country export the most copper?",
        "explanation": "question mentions a geography exporter and a product, but does not mention a year. \
    Then year is left as it is, the product is filled with 'copper' and Exporter is not specified then is filled with 'All'.\
    User wants 'the most', then sort is set to 'desc' for descending order, and limit is set to '1'.\
    The rest is left untouched.",
        "form_json": {
            "base_url": "https://oec.world/api/olap-proxy/data.jsonrecords?",
            "cube": "trade_i_baci_a_96",
            "dimensions": {
                "Year": [2022],
                "HS Product": ["copper"],
                "Hierarchy:Geography": [{"Exporter": ["All"]}, {"Importer": []}],
                "Unit": ["Metric Tons"],
            },
            "measures": ["Trade Value", "Quantity"],
            "limit": "1",
            "sort": "desc",
            "locale": "en",
        },
    },
    {
        "question": "How much coffee did Colombia exported to US?",
        "explanation": "question mentions a exporter geography, importer geography, a product, but does not mention a year. \
    Then year is left as it is, HS Product is filled with 'coffee', and exporter and importer filled with 'Colombia' and 'US'.\
    User wants to know 'how much', then sort is set to 'desc' for descending order, and limit is set to 'All'",
        "form_json": {
            "base_url": "https://oec.world/api/olap-proxy/data.jsonrecords?",
            "cube": "trade_i_baci_a_96",
            "dimensions": {
                "Year": [2022],
                "HS Product": ["coffee"],
                "Hierarchy:Geography": [
                    {"Exporter": ["Colombia"]},
                    {"Importer": ["US"]},
                ],
                "Unit": ["Metric Tons"],
            },
            "measures": ["Trade Value", "Quantity"],
            "limit": "All",
            "sort": "desc",
            "locale": "en",
        },
    },
    {
        "question": "How much product in 2019?",
        "explanation": "question mentions product, but does not mention a year or geography.\
    Then year is left as it is and HS Product is set to 'All', but exporter and imported are left blank.\
    User wants to know 'how much', then sort is set to 'desc' for descending order and limit is set to 'All'.",
        "form_json": {
            "base_url": "https://oec.world/api/olap-proxy/data.jsonrecords?",
            "cube": "trade_i_baci_a_96",
            "dimensions": {
                "Year": [2019],
                "HS Product": ["All"],
                "Hierarchy:Geography": [{"Exporter": []}, {"Importer": []}],
                "Unit": ["Metric Tons"],
            },
            "measures": ["Trade Value", "Quantity"],
            "limit": "All",
            "sort": "desc",
            "locale": "en",
        },
    },
    {
        "question": "What products among HS4 had the largest share of exports from USA in 2020?",
        "explanation": "question mentions a year, a exporter geography and product, it also mention a product level,\
    so we add that to the product description as a python dictionary. \
    Then year is left as it is and product is set to 'All', and exporter is set to 'USA'.\
    User wants to know 'what', then sort is set to 'desc' for descending order and limit is set to 'All'\
    ",
        "form_json": {
            "base_url": "https://oec.world/api/olap-proxy/data.jsonrecords?",
            "cube": "trade_i_baci_a_96",
            "dimensions": {
                "Year": [2020],
                "HS Product": [{"HS4": "All"}],
                "Hierarchy:Geography": [{"Exporter": []}, {"Importer": []}],
                "Unit": ["Metric Tons"],
            },
            "measures": ["Trade Value", "Quantity"],
            "limit": "All",
            "sort": "desc",
            "locale": "en",
        },
    },
]


validation_template = (
    """
Complete the form based only on the explicit information contained in the question.
If no information is available in the question for a field, keep the current value in the JSON.
If the question contains information that is already filled in the form, replace it with the question information.
If a dimension is mentioned but no specified, fill it with "All". Do not remove any field.
Answer in JSON format as shown in the following examples:

"""
    + "\n".join([str(d).replace("{", "{{").replace("}", "}}") for d in trade_validation_few_shot[:-2]])
    + """

Here is the question: {question}
Here is the form: {form_json}
"""
)
validation_prompt = PromptTemplate.from_template(validation_template)

alt_validation_prompt = PromptTemplate.from_template(validation_template)

# CHAINs

# .pipe(model)\
question_chain = (
    question_prompt.pipe(model_adv.bind(system=question_sys_prompt, format="json"))
    .pipe(stream_acc)
    .pipe(JsonOutputParser())
    .with_fallbacks(
        [alt_question_prompt.pipe(model_mix.bind(system=question_sys_prompt, format="json")).pipe(stream_acc).pipe(JsonOutputParser())]
    )
)

# .pipe(model_adv.bind(system = validation_sys_prompt, format='json'))\
valid_chain = (
    validation_prompt.pipe(model_adv.bind(system=validation_sys_prompt, format="json"))
    .pipe(JsonOutputParser())
    .with_fallbacks([alt_validation_prompt.pipe(model_mix.bind(system=validation_sys_prompt, format="json")).pipe(JsonOutputParser())])
)


polite_chain = PromptTemplate.from_template("Answer politely: {question}").pipe(model_basic)

########## ROUTING LOGIC


@chain
def route_question(info):
    print("In route_question: ", info)
    form_json = info["form_json"]
    action = info["action"]

    if action["type"] == "not a question":
        return {"question": lambda x: action["summary"]} | polite_chain

    elif action["type"] == "new question":
        form_json = set_form_json(action["summary"])

        if form_json:
            return {
                "form_json": lambda x: form_json,
                "question": lambda x: action["summary"],
            } | valid_chain
        else:
            return "I'm sorry, but OEC does not have data regarding your question, please try something different"

    elif action["type"] == "complementary information":
        print("complement!!!!!!!!!!!!!")
        return {
            "form_json": lambda x: form_json,
            "question": lambda x: action["summary"],
        } | valid_chain
    # case type no api call needed


@chain
def route_answer(info):
    print("In route_answer: ", info)
    handleAPIBuilder = info["input"]["handleAPIBuilder"]
    process = info["process"]

    # if answer is not json is not a question
    if isinstance(process, str):
        yield json.dumps({"content": process})

    else:
        form_json = process["form_json"]
        missing = json_iterator(form_json)

        # Missing questions
        table_manager = TableManager(TABLES_PATH)
        table = table_manager.get_table(form_json["cube"])
        print("MISSING: ", missing)
        if missing:
            request_info = "Please, specify the following: "
            for m in missing:
                if ":" in m[1]:
                    dimension = m[1].split(":")[-1]
                else:
                    dimension = m[1]

                try:
                    options = table.get_drilldown_members(dimension)
                except:  # noqa: E722
                    options = None

                request_info += "{} ".format(dimension)
                if options:
                    request_info += ", such as :{} ".format(", ".join(options))

            yield json.dumps({"content": request_info, "form_json": form_json})

        else:
            yield json.dumps({"content": "Good question, let's check the data..."})
            query = process["question"]
            for response in handleAPIBuilder(query, form_json=form_json, step="get_api_params_from_wrapper"):
                if isinstance(response, dict):
                    yield json.dumps(response)
                else:
                    yield json.dumps({"content": response, "form_json": form_json})


################ Build Chain

main_chain = RunnableSequence(
    {
        "input": RunnablePassthrough(),
        "process": ({"form_json": itemgetter("form_json"), "action": question_chain} | route_question),
    }
    | route_answer,
)


#######################


@chain
def get_input(info):
    # return latest input
    return {"question": info["chathistory"].split(";")[-1].replace("[.]", "").replace("[User]", "").strip()}


@chain
def get_form(info):
    print("In get form: ", info)
    question = info["question"]

    try:
        # form_json = set_form_json(question)
        form_json = {
            "base_url": "https://oec.world/api/olap-proxy/data.jsonrecords?",
            "cube": "trade_i_baci_a_96",
            "dimensions": {
                "Year": [2022],
                "HS Product": [],
                "Hierarchy:Geography": [{"Exporter": []}, {"Importer": []}],
                "Unit": "Metric Tons",
            },
            "measures": ["Trade Value", "Quantity"],
            "limit": "placeholder",
            "sort": "placeholder",
            "locale": "en",
        }
    except Exception as error:
        print("no cube: ", error)
        form_json = None

    return form_json


@chain
def route_question2(info):
    print("In route_question: ", info)
    parallel = info["parallel"]
    form_json = info["form_json"]
    action = info["action"]

    if action["type"] == "not a question":
        return parallel["polite"]

    elif action["type"] == "new question":
        form_json = parallel["cube"]
        if form_json:
            return {
                "form_json": lambda x: form_json,
                "question": lambda x: action["summary"],
            } | valid_chain
        else:
            return "I'm sorry, but OEC does not have data regarding your question, please try something different"

    elif action["type"] == "complementary information":
        return {
            "form_json": lambda x: form_json,
            "question": lambda x: action["summary"],
        } | valid_chain


alt_chain = RunnableSequence(
    {
        "input": RunnablePassthrough(),
        "process": {
            "parallel": get_input
            | {
                "polite": polite_chain,
                "cube": get_form,
            },
            "action": question_chain,
            "form_json": itemgetter("form_json"),
        }
        | route_question2,
    }
    | route_answer
)


########  Short

check_template = PromptTemplate.from_template(
    """
Classify the following input as "question" if the in put is a question of trade products among countries
or "not a question" if is something else.
Respond following the the JSON format.

Here are some examples:

{{
"input":"How much wine did Chile exported in 2021?",
"reasoning":"The input explicitly asked information about Chile exports",
"type": "question"
}}

{{
"input":"Hi, how are you?",
"reasoning":"The input asked a question not realated to international commerce or trade",
"type":"not a question"
}}

Here is the input:
{chathistory}
"""
)

simple_check = check_template.pipe(model_basic.bind(system=question_sys_prompt, format="json")).pipe(JsonOutputParser())


@chain
def assistant(info):
    query = info["chathistory"]
    handleAPIBuilder = info["handleAPIBuilder"]
    manager = TableManager(TABLES_PATH)
    table = manager.get_table("trade_i_baci_a_92")
    response = handleAPIBuilder(query, form_json={}, step="get_api_params_from_lm", **{"table": table, "start_time": time.time()})
    return json.dumps({"content": [i for i in response], "form_json": {}})


@chain
def short_route(info):
    if info["check"]["type"] == "not a question":
        yield json.dumps({"content": "Please, try a different question..."})
    yield info["assistant"]


short_chain = {"assistant": assistant, "check": simple_check} | short_route


############# Export function


def wrapperCall(history, form_json, handleAPIBuilder, logger=[]):
    """
    Stream main_chain answers
    """
    for answer in short_chain.stream(
        {
            "chathistory": ";".join([f"{' [User]' if m['user'] else ' [AI]'}:{m['text']}" for m in history]) + "[.]",
            "form_json": form_json,
            "handleAPIBuilder": handleAPIBuilder,  # lambda x, form_json, step: range(2)
        },
        config={"callbacks": [logsHandler(logger, print_logs=True, print_starts=False)]},
    ):
        yield answer


if __name__ == "__main__":
    wrapperCall(
        [
            {"user": False, "text": "hi, how can I help you"},
            {"user": True, "text": "Which country export the most copper?"},
        ],
        form_json={},
        handleAPIBuilder=lambda x: x,
    )
