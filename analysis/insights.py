"""
Automated insights engine.

Generates plain-language findings and data-driven recommendations purely
from the calculated statistics — nothing here is hardcoded or invented.
"""
import pandas as pd

from analysis.statistics import (
    department_averages,
    department_pass_percentage,
    subject_averages,
)

SUBJECT_LABELS = {
    "math_score": "Math",
    "science_score": "Science",
    "programming_score": "Programming",
    "english_score": "English",
    "assignment_score": "Assignment",
    "internal_score": "Internal Assessment",
    "final_exam_score": "Final Exam",
}


def generate_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No data available to generate insights."]

    insights = []

    dept_avg = department_averages(df)
    best_dept = dept_avg.loc[dept_avg["overall_score"].idxmax()]
    worst_dept = dept_avg.loc[dept_avg["overall_score"].idxmin()]
    insights.append(
        f"**{best_dept['department']}** has the highest average performance "
        f"(overall score {best_dept['overall_score']}), while **{worst_dept['department']}** "
        f"has the lowest (overall score {worst_dept['overall_score']})."
    )

    subj_avg = subject_averages(df)
    best_subject = subj_avg.idxmax()
    worst_subject = subj_avg.idxmin()
    insights.append(
        f"**{SUBJECT_LABELS.get(best_subject, best_subject)}** has the highest average score "
        f"({subj_avg[best_subject]}), while **{SUBJECT_LABELS.get(worst_subject, worst_subject)}** "
        f"needs the most improvement ({subj_avg[worst_subject]})."
    )

    avg_attendance = df["attendance_percentage"].mean()
    low_attendance_pct = (df["attendance_percentage"] < 75).mean() * 100
    insights.append(
        f"Average attendance across all students is {avg_attendance:.1f}%; "
        f"{low_attendance_pct:.1f}% of students have attendance below 75%."
    )

    corr = df[["study_hours_per_week", "overall_score"]].corr().iloc[0, 1]
    if corr > 0.3:
        strength = "a positive relationship"
    elif corr < -0.3:
        strength = "a negative relationship"
    else:
        strength = "little to no clear relationship"
    insights.append(
        f"Study hours per week and overall score show {strength} "
        f"(correlation coefficient: {corr:.2f}). This is a correlation, not proof of causation."
    )

    at_risk_count = int((df["risk_status"] == "At Risk").sum())
    at_risk_pct = at_risk_count / len(df) * 100
    insights.append(
        f"There are **{at_risk_count} at-risk students** ({at_risk_pct:.1f}% of the dataset), "
        "based on low attendance, low final exam scores, or low average subject scores."
    )

    dept_pass = department_pass_percentage(df)
    best_pass_dept = dept_pass.loc[dept_pass["pass_percentage"].idxmax()]
    insights.append(
        f"**{best_pass_dept['department']}** has the highest pass rate "
        f"at {best_pass_dept['pass_percentage']:.1f}%."
    )

    return insights


def generate_recommendations(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No data available to generate recommendations."]

    recs = []

    low_attendance_pct = (df["attendance_percentage"] < 75).mean() * 100
    if low_attendance_pct > 10:
        recs.append(
            f"{low_attendance_pct:.1f}% of students have attendance below 75% — "
            "consider monitoring and intervening for students with attendance below this threshold."
        )

    subj_avg = subject_averages(df)
    weakest = subj_avg.idxmin()
    if subj_avg[weakest] < 60:
        recs.append(
            f"Average {SUBJECT_LABELS.get(weakest, weakest)} score is {subj_avg[weakest]:.1f}, "
            "the lowest among all subjects — additional practice sessions or tutoring in this "
            "area may help improve outcomes."
        )

    at_risk_pct = (df["risk_status"] == "At Risk").mean() * 100
    if at_risk_pct > 15:
        recs.append(
            f"{at_risk_pct:.1f}% of students are classified as at-risk — "
            "a structured early-intervention or mentoring program is recommended."
        )

    fail_pct = (df["pass_status"] == "Fail").mean() * 100
    if fail_pct > 10:
        recs.append(
            f"{fail_pct:.1f}% of students are currently failing — "
            "consider remedial classes or additional assessment opportunities."
        )

    corr = df[["study_hours_per_week", "overall_score"]].corr().iloc[0, 1]
    if corr > 0.3:
        recs.append(
            "Since study hours correlate positively with performance, "
            "encouraging structured study time may benefit lower-performing students."
        )

    if not recs:
        recs.append("Overall performance metrics look healthy — no urgent interventions identified.")

    return recs
