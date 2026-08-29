import pandas as pd
import pytest

from analysis.statistics import (
    add_overall_score,
    add_pass_fail,
    add_performance_category,
    add_risk_status,
    at_risk_table,
    enrich_dataframe,
    top_performers,
)

SUBJECT_COLS = ["math_score", "science_score", "programming_score", "english_score",
                "assignment_score", "internal_score", "final_exam_score"]


def make_df(rows):
    """rows: list of dicts with subject scores, attendance_percentage."""
    base = {
        "student_id": [], "name": [], "department": [], "attendance_percentage": [],
        **{c: [] for c in SUBJECT_COLS},
    }
    for i, r in enumerate(rows):
        base["student_id"].append(f"S{i}")
        base["name"].append(f"Student{i}")
        base["department"].append(r.get("department", "Computer Science"))
        base["attendance_percentage"].append(r.get("attendance_percentage", 90))
        for c in SUBJECT_COLS:
            base[c].append(r.get(c, 80))
    return pd.DataFrame(base)


def test_add_overall_score_within_bounds():
    df = make_df([{}])
    result = add_overall_score(df)
    assert 0 <= result["overall_score"].iloc[0] <= 100


def test_pass_logic_pass_case():
    df = make_df([{"final_exam_score": 50, "internal_score": 50}])
    result = add_pass_fail(df)
    assert result["pass_status"].iloc[0] == "Pass"


def test_pass_logic_fail_on_final_exam():
    df = make_df([{"final_exam_score": 30, "internal_score": 90}])
    result = add_pass_fail(df)
    assert result["pass_status"].iloc[0] == "Fail"


def test_pass_logic_fail_on_internal():
    df = make_df([{"final_exam_score": 90, "internal_score": 30}])
    result = add_pass_fail(df)
    assert result["pass_status"].iloc[0] == "Fail"


def test_risk_status_low_attendance():
    df = make_df([{"attendance_percentage": 50}])
    result = add_risk_status(df)
    assert result["risk_status"].iloc[0] == "At Risk"
    assert "attendance" in result["risk_reason"].iloc[0].lower()


def test_risk_status_safe_case():
    df = make_df([{"attendance_percentage": 90, "final_exam_score": 80,
                    "math_score": 80, "science_score": 80, "programming_score": 80, "english_score": 80}])
    result = add_risk_status(df)
    assert result["risk_status"].iloc[0] == "Safe"


def test_performance_category_excellent():
    df = pd.DataFrame({"overall_score": [90]})
    result = add_performance_category(df)
    assert result["performance_category"].iloc[0] == "Excellent"


def test_performance_category_at_risk():
    df = pd.DataFrame({"overall_score": [20]})
    result = add_performance_category(df)
    assert result["performance_category"].iloc[0] == "At Risk"


def test_top_performers_ranking_order():
    df = make_df([
        {"final_exam_score": 90, "internal_score": 90},
        {"final_exam_score": 50, "internal_score": 50},
        {"final_exam_score": 70, "internal_score": 70},
    ])
    df = enrich_dataframe(df)
    top = top_performers(df, 3)
    scores = top["overall_score"].tolist()
    assert scores == sorted(scores, reverse=True)
    assert top["rank"].tolist() == [1, 2, 3]


def test_at_risk_table_only_contains_at_risk():
    df = make_df([
        {"attendance_percentage": 50},
        {"attendance_percentage": 95, "final_exam_score": 90, "math_score": 90,
         "science_score": 90, "programming_score": 90, "english_score": 90},
    ])
    df = enrich_dataframe(df)
    at_risk = at_risk_table(df)
    assert len(at_risk) == 1
    assert (at_risk["risk_reason"] != "").all()
