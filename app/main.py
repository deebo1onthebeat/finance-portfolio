from fastapi import FastAPI
from app.routers.auth import router as auth_routers
from app.routers.user import router as user_routers 

app = FastAPI()

app.include_router(auth_routers)
app.include_router(user_routers)

@app.get("/")
async def read_root():
    return {"message": "Hello, Finance Killer!"}