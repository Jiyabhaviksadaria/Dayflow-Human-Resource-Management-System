from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.database.db import SessionLocal
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/check-in")
def check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get employee
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    today = date.today()

    # Check if already checked in today
    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date == today
    ).first()

    if existing and existing.check_in is not None:
        raise HTTPException(status_code=400, detail="Already checked in today")

    # Create attendance record
    attendance = Attendance(
        employee_id=employee.id,
        attendance_date=today,
        check_in=datetime.now().time()
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return {
        "message": "Check-in successful",
        "check_in_time": attendance.check_in
    }
