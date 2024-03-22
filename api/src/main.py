from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from os import getenv
from src.utils.app import get_api
from src.wrapper.lanbot import Langbot
import time
import json
# fastapi instance declaration
app = FastAPI()

# get tables path
load_dotenv()
TABLES_PATH = getenv('TABLES_PATH')
# api functions
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/wrap/{query}")
async def wrap(query):

    return StreamingResponse(Langbot(query, get_api), media_type="application/json")


async def numnum():
    for i in range(10):
        time.sleep(2)
        yield json.dumps({f'{i}':'abs'})

@app.get("/num/")
async def num():
    return StreamingResponse(numnum(), media_type="application/json")


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