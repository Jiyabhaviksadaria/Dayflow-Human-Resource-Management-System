from sqlalchemy import Column, Integer, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date

from app.database.db import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    attendance_date = Column(Date, default=date.today)
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)
    work_hours = Column(Integer, nullable=True)  # minutes

    employee = relationship("Employee", backref="attendance_records")
