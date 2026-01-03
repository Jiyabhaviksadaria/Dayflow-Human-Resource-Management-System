from sqlalchemy import Column, Integer, Float, String, ForeignKey
from app.database.db import Base


class Payroll(Base):
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    present_days = Column(Integer, nullable=False)
    salary_amount = Column(Float, nullable=False)

    status = Column(String, default="Generated")  # Generated / Paid
