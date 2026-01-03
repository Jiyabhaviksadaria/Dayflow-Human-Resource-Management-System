from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database.db import SessionLocal
from app.models.leave import LeaveRequest
from app.models.employee import Employee
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.leave import LeaveApplyRequest

# ✅ ROUTER MUST BE DEFINED BEFORE USING IT
router = APIRouter(prefix="/leaves", tags=["Leaves"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/apply")
def apply_leave(
    payload: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date"
        )

    leave = LeaveRequest(
        employee_id=employee.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        status="Pending"
    )

    db.add(leave)
    db.commit()
    db.refresh(leave)

    return {
        "message": "Leave request submitted",
        "leave_id": leave.id,
        "status": leave.status
    }
