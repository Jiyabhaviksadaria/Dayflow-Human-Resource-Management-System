from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import Optional

from app.database.db import SessionLocal
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])


# -------------------------
# DATABASE DEPENDENCY
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# CHECK-IN
# -------------------------
@router.post("/check-in")
def check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    today = date.today()

    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date == today
    ).first()

    if existing and existing.check_in:
        raise HTTPException(status_code=400, detail="Already checked in today")

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


# -------------------------
# CHECK-OUT
# -------------------------
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

    attendance.check_out = datetime.now().time()

    check_in_dt = datetime.combine(today, attendance.check_in)
    check_out_dt = datetime.combine(today, attendance.check_out)

    attendance.work_hours = int(
        (check_out_dt - check_in_dt).total_seconds() / 60
    )

    db.commit()
    db.refresh(attendance)

    return {
        "message": "Check-out successful",
        "check_out_time": attendance.check_out,
        "work_minutes": attendance.work_hours
    }


# -------------------------
# EMPLOYEE: MY ATTENDANCE
# -------------------------
@router.get("/me")
def get_my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    return db.query(Attendance).filter(
        Attendance.employee_id == employee.id
    ).order_by(Attendance.attendance_date.desc()).all()


# -------------------------
# ADMIN: ALL ATTENDANCE
# -------------------------
@router.get("/all")
def get_all_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(Attendance)

    if start_date:
        query = query.filter(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.filter(Attendance.attendance_date <= end_date)

    return query.order_by(Attendance.attendance_date.desc()).all()


# -------------------------
# ATTENDANCE SUMMARY
# -------------------------
@router.get("/me/summary")
def get_my_attendance_summary(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    records = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        func.strftime("%m", Attendance.attendance_date) == f"{month:02d}",
        func.strftime("%Y", Attendance.attendance_date) == str(year)
    ).all()

    total_days = len(records)

    # ✅ PRESENT = check_in exists
    present_days = len([r for r in records if r.check_in is not None])

    return {
        "month": month,
        "year": year,
        "total_working_days": total_days,
        "present_days": present_days,
        "attendance_percentage": (
            round((present_days / total_days) * 100, 2)
            if total_days > 0 else 0
        )
    }
