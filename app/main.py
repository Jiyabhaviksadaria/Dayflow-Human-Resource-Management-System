from fastapi import FastAPI, Depends

from app.routes.auth import router as auth_router
from app.database.db import engine, Base

# 👇 IMPORT MODELS (VERY IMPORTANT)
from app.models import user, employee
from app.routes.employee import router as employee_router
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models import user, employee, attendance
from app.routes.attendance import router as attendance_router
app = FastAPI(title="Dayflow HRMS")

app.include_router(employee_router)
app.include_router(attendance_router)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include auth routes
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Dayflow HRMS API is running"}

@app.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }
