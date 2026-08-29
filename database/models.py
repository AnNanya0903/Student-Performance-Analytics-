"""SQLAlchemy ORM models for the Student Performance Analytics Dashboard."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Student(Base):
    """One row per student — demographic / static information."""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    gender = Column(String)
    age = Column(Integer)
    department = Column(String, index=True)
    semester = Column(Integer, index=True)
    location = Column(String)
    internet_access = Column(String)
    extracurricular = Column(String)


class PerformanceRecord(Base):
    """One row per student — scores and derived performance metrics."""

    __tablename__ = "performance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, nullable=False, index=True)
    attendance_percentage = Column(Float)
    math_score = Column(Float)
    science_score = Column(Float)
    programming_score = Column(Float)
    english_score = Column(Float)
    assignment_score = Column(Float)
    internal_score = Column(Float)
    final_exam_score = Column(Float)
    study_hours_per_week = Column(Float)
    overall_score = Column(Float)
    pass_status = Column(String)
    risk_status = Column(String)
    performance_category = Column(String)


class AnalysisResult(Base):
    """Stores summary analysis results (KPIs / aggregates) per dataset load."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, index=True)
    metric_name = Column(String, nullable=False)
    metric_group = Column(String)  # e.g. 'department', 'overall', 'semester'
    metric_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
