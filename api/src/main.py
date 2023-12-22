from fastapi import FastAPI

from src.utils.app import get_api

# fastapi instance declaration
app = FastAPI()

# api functions
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/query/{query}")
async def read_item(query: str):
    api_url, data, text_response = get_api(query)

    return {
            "query":
                {
                    "question": query, 
                    "answer": text_response, 
                    "url": api_url
                }
            }