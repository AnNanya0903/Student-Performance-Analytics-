"""
Real SQL queries executed against the SQLite database (via database.run_sql).

Every function here issues an actual SQL statement — none of this data is
computed in Pandas and relabeled as "SQL".
"""
import pandas as pd

from database.database import run_sql


def avg_score_by_department() -> pd.DataFrame:
    query = """
        SELECT s.department,
               ROUND(AVG(p.overall_score), 2) AS avg_overall_score,
               COUNT(*) AS student_count
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        GROUP BY s.department
        ORDER BY avg_overall_score DESC;
    """
    return run_sql(query)


def avg_attendance_by_department() -> pd.DataFrame:
    query = """
        SELECT s.department,
               ROUND(AVG(p.attendance_percentage), 2) AS avg_attendance
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        GROUP BY s.department
        ORDER BY avg_attendance DESC;
    """
    return run_sql(query)


def top_students(limit: int = 10) -> pd.DataFrame:
    query = """
        SELECT s.name, s.department, p.overall_score, p.attendance_percentage
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        ORDER BY p.overall_score DESC
        LIMIT :limit;
    """
    return run_sql(query, {"limit": limit})


def failed_students() -> pd.DataFrame:
    query = """
        SELECT s.student_id, s.name, s.department, p.final_exam_score, p.internal_score
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        WHERE p.pass_status = 'Fail'
        ORDER BY p.final_exam_score ASC;
    """
    return run_sql(query)


def at_risk_students() -> pd.DataFrame:
    query = """
        SELECT s.student_id, s.name, s.department, p.attendance_percentage,
               p.final_exam_score, p.risk_reason
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        WHERE p.risk_status = 'At Risk'
        ORDER BY p.attendance_percentage ASC;
    """
    return run_sql(query)


def pass_percentage_by_semester() -> pd.DataFrame:
    query = """
        SELECT s.semester,
               ROUND(100.0 * SUM(CASE WHEN p.pass_status = 'Pass' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pass_percentage,
               COUNT(*) AS total_students
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        GROUP BY s.semester
        ORDER BY s.semester;
    """
    return run_sql(query)


def attendance_below_75() -> pd.DataFrame:
    query = """
        SELECT s.student_id, s.name, s.department, p.attendance_percentage
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        WHERE p.attendance_percentage < 75
        ORDER BY p.attendance_percentage ASC;
    """
    return run_sql(query)


def final_score_above_80() -> pd.DataFrame:
    query = """
        SELECT s.student_id, s.name, s.department, p.final_exam_score
        FROM students s
        JOIN performance_records p ON s.student_id = p.student_id
        WHERE p.final_exam_score > 80
        ORDER BY p.final_exam_score DESC;
    """
    return run_sql(query)
