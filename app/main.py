from fastapi import FastAPI
from app.routes.auth import router as auth_router

app = FastAPI(title="Dayflow HRMS")

app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Dayflow HRMS API is running"}
