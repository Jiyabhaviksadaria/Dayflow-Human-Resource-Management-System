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
@router.post("/check-out")
def check_out(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    today = date.today()

    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date == today
    ).first()

    if not attendance or not attendance.check_in:
        raise HTTPException(status_code=400, detail="Check-in not found for today")

    if attendance.check_out:
        raise HTTPException(status_code=400, detail="Already checked out today")

    check_out_time = datetime.now().time()
    attendance.check_out = check_out_time

    # Calculate work hours in minutes
    check_in_dt = datetime.combine(today, attendance.check_in)
    check_out_dt = datetime.combine(today, check_out_time)

    work_minutes = int((check_out_dt - check_in_dt).total_seconds() / 60)
    attendance.work_hours = work_minutes

    db.commit()
    db.refresh(attendance)

    return {
        "message": "Check-out successful",
        "check_out_time": attendance.check_out,
        "work_minutes": attendance.work_hours
    }
from typing import List
from datetime import date
from fastapi import Query


# -------------------------
# EMPLOYEE: VIEW OWN ATTENDANCE
# -------------------------
@router.get("/my-records")
def get_my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    query = db.query(Attendance).filter(
        Attendance.employee_id == employee.id
    )

    if start_date:
        query = query.filter(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.filter(Attendance.attendance_date <= end_date)

    return query.order_by(Attendance.attendance_date.desc()).all()


# -------------------------
# ADMIN: VIEW ALL ATTENDANCE
# -------------------------
@router.get("/all")
def get_all_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(Attendance)

    if start_date:
        query = query.filter(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.filter(Attendance.attendance_date <= end_date)

    return query.order_by(Attendance.attendance_date.desc()).all()
