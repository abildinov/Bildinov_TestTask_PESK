from fastapi import FastAPI
from app.api.v1.auth import router as register


app = FastAPI()
app.include_router(register, prefix="/api/v1", tags=["auth_router"])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
