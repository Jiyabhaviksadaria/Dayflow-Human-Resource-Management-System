from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.employee import Employee
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/employees", tags=["Employees"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# GET MY PROFILE (AUTO-CREATE)
# -------------------------
@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    # Auto-create employee profile if not exists
    if not employee:
        employee = Employee(
            user_id=current_user.id,
            full_name=current_user.email.split("@")[0]
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)

    return employee


# -------------------------
# UPDATE MY PROFILE (EMPLOYEE)
# -------------------------
@router.put("/me")
def update_my_profile(
    full_name: str | None = None,
    department: str | None = None,
    designation: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    if full_name is not None:
        employee.full_name = full_name
    if department is not None:
        employee.department = department
    if designation is not None:
        employee.designation = designation
    if phone is not None:
        employee.phone = phone
    if address is not None:
        employee.address = address

    db.commit()
    db.refresh(employee)

    return employee


# -------------------------
# ADMIN: UPDATE ANY EMPLOYEE
# -------------------------
@router.put("/{employee_id}")
def admin_update_employee(
    employee_id: int,
    full_name: str | None = None,
    department: str | None = None,
    designation: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if full_name is not None:
        employee.full_name = full_name
    if department is not None:
        employee.department = department
    if designation is not None:
        employee.designation = designation
    if phone is not None:
        employee.phone = phone
    if address is not None:
        employee.address = address

    db.commit()
    db.refresh(employee)

    return employee
