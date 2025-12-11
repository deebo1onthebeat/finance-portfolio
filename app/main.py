from fastapi import FastAPI
from app.routers.auth import router as auth_routers

app = FastAPI()

app.include_router(auth_routers)

@app.get("/")
async def read_root():
    return {"message": "Hello, Finance Killer!"}