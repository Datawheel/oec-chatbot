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
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
# fastapi instance declaration
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# api functions
@app.get("/")
async def root():
    return {
        "name": "datausa-chat-api",
        "status": "ok"
      }

class Item(BaseModel):
    query: List[Dict]
    form_json: Dict | None = None
  

@app.post("/wrap/")
async def wrap(item: Item):
    print(item)
    query, form_json = item.query, item.form_json
    #query = [historyMock("HumanMessage", query)]
    print(form_json)
    return StreamingResponse(wrapperCall(query, form_json, handleAPIBuilder = lambda x: str(x)), media_type="application/json")


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


