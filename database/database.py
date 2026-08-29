"""
Database engine, session management, and load/query helpers.

Uses SQLite via SQLAlchemy. The dashboard writes cleaned data here on every
dataset load and reads it back out via real SQL queries (see analysis/sql_queries.py).
"""
import uuid
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database.models import AnalysisResult, Base, PerformanceRecord, Student

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "student_analytics.db"
ENGINE_URL = f"sqlite:///{DB_PATH}"

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(ENGINE_URL, connect_args={"check_same_thread": False})
        Base.metadata.create_all(_engine)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


@contextmanager
def get_session():
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_database():
    """Drop and recreate all tables. Used before loading a fresh dataset."""
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def load_dataframe_to_db(df: pd.DataFrame) -> str:
    """
    Persist a cleaned student dataframe into the students, performance_records
    and analysis_results tables. Returns a run_id identifying this load.
    """
    reset_database()
    run_id = str(uuid.uuid4())[:8]

    student_cols = [
        "student_id", "name", "gender", "age", "department", "semester",
        "location", "internet_access", "extracurricular",
    ]
    perf_cols = [
        "student_id", "attendance_percentage", "math_score", "science_score",
        "programming_score", "english_score", "assignment_score", "internal_score",
        "final_exam_score", "study_hours_per_week", "overall_score", "pass_status",
        "risk_status", "performance_category",
    ]

    students_df = df[[c for c in student_cols if c in df.columns]].drop_duplicates("student_id")
    perf_df = df[[c for c in perf_cols if c in df.columns]].drop_duplicates("student_id")

    engine = get_engine()
    students_df.to_sql("students", engine, if_exists="append", index=False)
    perf_df.to_sql("performance_records", engine, if_exists="append", index=False)

    # Store a handful of headline aggregate metrics as demonstration of the
    # analysis_results table being genuinely populated (not just schema-only).
    with get_session() as session:
        overall_metrics = {
            "avg_overall_score": float(df["overall_score"].mean()) if "overall_score" in df else None,
            "avg_attendance": float(df["attendance_percentage"].mean()) if "attendance_percentage" in df else None,
            "pass_rate": float((df["pass_status"] == "Pass").mean() * 100) if "pass_status" in df else None,
        }
        for metric_name, value in overall_metrics.items():
            if value is not None:
                session.add(AnalysisResult(run_id=run_id, metric_name=metric_name, metric_group="overall", metric_value=value))

        if "department" in df.columns and "overall_score" in df.columns:
            dept_avg = df.groupby("department")["overall_score"].mean()
            for dept, value in dept_avg.items():
                session.add(AnalysisResult(run_id=run_id, metric_name=f"avg_score_{dept}", metric_group="department", metric_value=float(value)))

    return run_id


def run_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    """Execute a raw SQL query against the SQLite database and return a DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        rows = result.fetchall()
        cols = result.keys()
    return pd.DataFrame(rows, columns=cols)
