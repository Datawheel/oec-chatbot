from dotenv import load_dotenv
from fastapi import FastAPI
from os import getenv
from src.utils.app import get_api
from src.wrapper.lanbot import Langbot

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

    return Langbot(query, lambda x: print(x), get_api)


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