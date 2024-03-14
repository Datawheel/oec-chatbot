from fastapi import FastAPI

from config import TABLES_PATH
from utils.app import get_api

# fastapi instance declaration
app = FastAPI()

# api functions
@app.get("/")
async def root():
    return {
        "name": "datausa-chat-api",
        "status": "ok"
      }

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