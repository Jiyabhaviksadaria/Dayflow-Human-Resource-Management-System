from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.leave import LeaveRequest
from app.models.employee import Employee
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.leave import LeaveApplyRequest

router = APIRouter(prefix="/leaves", tags=["Leaves"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# APPLY LEAVE (EMPLOYEE)
# ---------------------------
@router.post("/apply")
def apply_leave(
    payload: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🔑 AUTO-CREATE EMPLOYEE PROFILE
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        employee = Employee(
            user_id=current_user.id,
            name=current_user.email.split("@")[0]
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)

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


# ---------------------------
# ADMIN APPROVE LEAVE
# ---------------------------
@router.put("/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    leave = db.query(LeaveRequest).filter(
        LeaveRequest.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Leave already {leave.status}"
        )

    leave.status = "Approved"
    db.commit()
    db.refresh(leave)

    return {
        "message": "Leave approved",
        "leave_id": leave.id,
        "status": leave.status
    }


# ---------------------------
# ADMIN REJECT LEAVE
# ---------------------------
@router.put("/{leave_id}/reject")
def reject_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    leave = db.query(LeaveRequest).filter(
        LeaveRequest.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Leave already {leave.status}"
        )

    leave.status = "Rejected"
    db.commit()
    db.refresh(leave)

    return {
        "message": "Leave rejected",
        "leave_id": leave.id,
        "status": leave.status
    }


# ---------------------------
# EMPLOYEE VIEW OWN LEAVES
# ---------------------------
@router.get("/me")
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🔑 AUTO-CREATE EMPLOYEE PROFILE
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()

    if not employee:
        employee = Employee(
            user_id=current_user.id,
            name=current_user.email.split("@")[0]
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)

    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee.id
    ).all()

    return leaves


# ---------------------------
# ADMIN VIEW ALL LEAVES
# ---------------------------
@router.get("/all")
def get_all_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(LeaveRequest).all()
