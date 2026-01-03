from sqlalchemy import Column, Integer, Date, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date

from app.database.db import Base


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    leave_type = Column(String, nullable=False)  # Paid, Sick, Unpaid
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    reason = Column(String, nullable=True)
    status = Column(String, default="Pending")  # Pending, Approved, Rejected
    applied_on = Column(Date, default=date.today)

    employee = relationship("Employee", backref="leave_requests")
