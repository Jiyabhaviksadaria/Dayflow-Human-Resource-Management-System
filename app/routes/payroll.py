from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.db import SessionLocal
from app.models.payroll import Payroll
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/payroll", tags=["Payroll"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate")
def generate_payroll(
    employee_id: int,
    month: int,
    year: int,
    base_salary: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🔐 Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    records = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        func.strftime("%m", Attendance.attendance_date) == f"{month:02d}",
        func.strftime("%Y", Attendance.attendance_date) == str(year)
    ).all()

    if not records:
        raise HTTPException(status_code=400, detail="No attendance records found")

    total_days = len(records)
    present_days = len([r for r in records if r.check_in is not None])

    salary_amount = round(
        (present_days / total_days) * base_salary, 2
    )

    payroll = Payroll(
        employee_id=employee_id,
        month=month,
        year=year,
        present_days=present_days,
        salary_amount=salary_amount
    )

    db.add(payroll)
    db.commit()
    db.refresh(payroll)

    return {
        "employee_id": employee_id,
        "month": month,
        "year": year,
        "present_days": present_days,
        "salary_amount": salary_amount,
        "status": payroll.status
    }
from typing import Optional
from fastapi import Query


@router.get("/me")
def get_my_payroll(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    query = db.query(Payroll).filter(
        Payroll.employee_id == employee.id
    )

    if month:
        query = query.filter(Payroll.month == month)
    if year:
        query = query.filter(Payroll.year == year)

    return query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
@router.get("/all")
def get_all_payrolls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    employee_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(Payroll)

    if employee_id:
        query = query.filter(Payroll.employee_id == employee_id)
    if month:
        query = query.filter(Payroll.month == month)
    if year:
        query = query.filter(Payroll.year == year)

    return query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
