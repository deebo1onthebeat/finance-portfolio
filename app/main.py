from fastapi import FastAPI
from app.database import engine

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello, Finance Killer!"}