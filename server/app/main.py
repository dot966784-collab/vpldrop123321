from fastapi import FastAPI
from app.api.auth import router as auth_router

app = FastAPI(title="VPL DROP API")

app.include_router(auth_router)

@app.get("/")
def index():
    return {"status": "API запущен успешно"}