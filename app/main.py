from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.database.db import engine, Base

app = FastAPI(title="Dayflow HRMS")

# Create database tables
Base.metadata.create_all(bind=engine)

# Include auth routes
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Dayflow HRMS API is running"}
