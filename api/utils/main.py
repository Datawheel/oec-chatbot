from fastapi import FastAPI

# fastapi instance declaration
app = FastAPI()

# api functions
@app.get("/")
async def root():
    return {"status": "ok"}
