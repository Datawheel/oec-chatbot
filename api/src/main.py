import time
import json
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableLambda, chain
from app import get_api
from config import TABLES_PATH
from wrapper.lanbot import Langbot
from wrapper.reflexionWrappper import wrapperCall

# fastapi instance declaration
app = FastAPI()

# api functions
@app.get("/")
async def root():
    return {
        "name": "datausa-chat-api",
        "status": "ok"
      }

class Item(BaseModel):
    query: list
    form_json: dict | None = None
   
    

@app.post("/wrap/")
async def wrap(item: Item):
    query, form_json = item['query'], item['form_json']
    #query = [historyMock("HumanMessage", query)]
    print(form_json)
    return StreamingResponse(wrapperCall(query, form_json, handleAPIBuilder = lambda x: x), media_type="application/json")


@app.get("/query/{query}")
async def read_item(query: str):
    api_url, data, text_response = get_api(query, TABLES_PATH)

    return {
            "query":
                {
                    "question": query, 
                    "answer": text_response, 
                    "url": api_url
                }
            }

#test 
@chain
def just(input):
    for w in input['input'].split(' '):
        yield w 
    #return {'data': 'abcd', 'data2':'wxyz'}

#@chain
def fn(input):
    print(input)
    yield json.dumps({'msg':input})
    time.sleep(4)
    yield json.dumps({'msg':input})

def fn2():
    chain = just | fn
    time.sleep(2)
    for val in fn({'input':'the jumping flying fox'}):
        yield val

@app.get("/num/")
def num():
    return StreamingResponse(fn2(), media_type="application/json")


