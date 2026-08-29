"""
Core statistical / performance-analysis calculations.

Everything here operates on real Pandas/NumPy computations over the cleaned
dataframe — no hardcoded numbers. Also implements pass/fail logic, at-risk
classification, performance categories, and the weighted overall score.
"""
import numpy as np
import pandas as pd

SUBJECT_COLUMNS = [
    "math_score", "science_score", "programming_score", "english_score",
]

WEIGHTS = {
    "math_score": 0.12,
    "science_score": 0.12,
    "programming_score": 0.15,
    "english_score": 0.10,
    "assignment_score": 0.13,
    "internal_score": 0.13,
    "final_exam_score": 0.25,
}


def add_overall_score(df: pd.DataFrame) -> pd.DataFrame:
    """Attach a weighted 'overall_score' column (0-100)."""
    df = df.copy()
    weighted_sum = sum(df[col] * w for col, w in WEIGHTS.items() if col in df.columns)
    total_weight = sum(w for col, w in WEIGHTS.items() if col in df.columns)
    df["overall_score"] = (weighted_sum / total_weight).round(2)
    return df


def add_pass_fail(df: pd.DataFrame) -> pd.DataFrame:
    """A student passes if final_exam_score >= 40 AND internal_score >= 40."""
    df = df.copy()
    df["pass_status"] = np.where(
        (df["final_exam_score"] >= 40) & (df["internal_score"] >= 40), "Pass", "Fail"
    )
    return df


def add_risk_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    At risk if attendance < 75 OR final_exam_score < 40 OR
    average subject score < 45. Also records the reason(s).
    """
    df = df.copy()
    avg_subject = df[SUBJECT_COLUMNS].mean(axis=1)
    df["avg_subject_score"] = avg_subject.round(2)

    low_att = df["attendance_percentage"] < 75
    low_final = df["final_exam_score"] < 40
    low_avg = avg_subject < 45

    is_at_risk = low_att | low_final | low_avg
    df["risk_status"] = np.where(is_at_risk, "At Risk", "Safe")

    def reason(row_low_att, row_low_final, row_low_avg):
        reasons = []
        if row_low_att:
            reasons.append("Low attendance")
        if row_low_final:
            reasons.append("Low final exam score")
        if row_low_avg:
            reasons.append("Low average subject score")
        return "; ".join(reasons) if reasons else ""

    df["risk_reason"] = [
        reason(a, f, s) for a, f, s in zip(low_att, low_final, low_avg)
    ]
    return df


def add_performance_category(df: pd.DataFrame) -> pd.DataFrame:
    """Classify by overall_score into Excellent/Good/Average/Needs Improvement/At Risk."""
    df = df.copy()

    def categorize(score):
        if score >= 85:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 50:
            return "Average"
        if score >= 40:
            return "Needs Improvement"
        return "At Risk"

    df["performance_category"] = df["overall_score"].apply(categorize)
    return df


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all derived-column calculations in the correct order."""
    df = add_overall_score(df)
    df = add_pass_fail(df)
    df = add_risk_status(df)
    df = add_performance_category(df)
    return df


def summary_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_students": 0, "avg_score": 0, "avg_attendance": 0,
            "pass_percentage": 0, "top_performer": "N/A", "at_risk_count": 0,
            "avg_study_hours": 0,
        }
    top_row = df.loc[df["overall_score"].idxmax()]
    return {
        "total_students": len(df),
        "avg_score": round(df["overall_score"].mean(), 2),
        "avg_attendance": round(df["attendance_percentage"].mean(), 2),
        "pass_percentage": round((df["pass_status"] == "Pass").mean() * 100, 2),
        "top_performer": top_row["name"],
        "at_risk_count": int((df["risk_status"] == "At Risk").sum()),
        "avg_study_hours": round(df["study_hours_per_week"].mean(), 2),
    }


def descriptive_stats(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Mean/median/min/max/std for the given numeric columns."""
    stats = df[columns].agg(["mean", "median", "min", "max", "std"]).T
    stats.columns = ["Mean", "Median", "Min", "Max", "Std Dev"]
    return stats.round(2)


def department_averages(df: pd.DataFrame) -> pd.DataFrame:
    metrics = ["overall_score", "attendance_percentage", "final_exam_score", "study_hours_per_week"]
    return df.groupby("department")[metrics].mean().round(2).reset_index()


def semester_averages(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("semester")["overall_score"].mean().round(2).reset_index()


def gender_averages(df: pd.DataFrame) -> pd.DataFrame:
    metrics = ["overall_score", "attendance_percentage", "final_exam_score"]
    return df.groupby("gender")[metrics].mean().round(2).reset_index()


def subject_averages(df: pd.DataFrame) -> pd.Series:
    return df[SUBJECT_COLUMNS + ["assignment_score", "internal_score", "final_exam_score"]].mean().round(2)


def pass_fail_counts(df: pd.DataFrame) -> dict:
    counts = df["pass_status"].value_counts()
    total = len(df)
    passed = int(counts.get("Pass", 0))
    failed = int(counts.get("Fail", 0))
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_percentage": round(passed / total * 100, 2) if total else 0,
        "failure_percentage": round(failed / total * 100, 2) if total else 0,
    }


def department_pass_percentage(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("department")["pass_status"].apply(lambda s: (s == "Pass").mean() * 100).round(2)
    return grp.reset_index(name="pass_percentage")


def at_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    at_risk = df[df["risk_status"] == "At Risk"][
        ["student_id", "name", "department", "attendance_percentage",
         "avg_subject_score", "final_exam_score", "risk_reason"]
    ].copy()
    return at_risk.sort_values("avg_subject_score").reset_index(drop=True)


def top_performers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    top = df.sort_values("overall_score", ascending=False).head(n).copy()
    top = top[["name", "department", "overall_score", "attendance_percentage"]].reset_index(drop=True)
    top.insert(0, "rank", range(1, len(top) + 1))
    return top


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "attendance_percentage", "study_hours_per_week", "assignment_score",
        "internal_score", "final_exam_score", "overall_score",
    ]
    return df[cols].corr().round(2)
