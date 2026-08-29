import numpy as np
import pandas as pd
import pytest

from analysis.cleaning import ValidationError, clean_dataset, normalize_column_names, validate_columns

REQUIRED_SAMPLE = {
    "student_id": ["S1", "S2", "S3"],
    "name": ["Alice", "Bob", "Carol"],
    "gender": ["Female", "Male", "Female"],
    "age": [20, 21, 22],
    "department": ["Computer Science", "Civil", "Mechanical"],
    "semester": [1, 2, 3],
    "attendance_percentage": [80, 90, 70],
    "math_score": [70, 80, 60],
    "science_score": [70, 80, 60],
    "programming_score": [70, 80, 60],
    "english_score": [70, 80, 60],
    "assignment_score": [70, 80, 60],
    "internal_score": [70, 80, 60],
    "final_exam_score": [70, 80, 60],
    "study_hours_per_week": [5, 6, 7],
    "extracurricular": ["Yes", "No", "Yes"],
    "internet_access": ["Yes", "Yes", "No"],
    "location": ["Urban", "Rural", "Urban"],
}


def make_df(overrides=None, **kwargs):
    data = {k: list(v) for k, v in REQUIRED_SAMPLE.items()}
    merged_overrides = {**(overrides or {}), **kwargs}
    for k, v in merged_overrides.items():
        data[k] = v
    return pd.DataFrame(data)


def test_normalize_column_names_lowercases_and_strips():
    df = pd.DataFrame({" Student ID ": [1], "Full-Name": ["x"]})
    normalized = normalize_column_names(df)
    assert list(normalized.columns) == ["student_id", "full_name"]


def test_validate_columns_detects_missing():
    df = pd.DataFrame({"student_id": [1]})
    missing = validate_columns(df)
    assert "name" in missing
    assert "math_score" in missing


def test_clean_dataset_raises_on_missing_required_column():
    df = make_df()
    df = df.drop(columns=["math_score"])
    with pytest.raises(ValidationError):
        clean_dataset(df)


def test_clean_dataset_removes_duplicates():
    df = make_df()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    cleaned, summary = clean_dataset(df)
    assert summary["duplicate_rows_removed"] == 1
    assert cleaned["student_id"].duplicated().sum() == 0


def test_clean_dataset_handles_missing_values():
    df = make_df()
    df.loc[0, "math_score"] = np.nan
    cleaned, summary = clean_dataset(df)
    assert cleaned["math_score"].isna().sum() == 0
    assert summary["missing_values_handled"] >= 1


def test_clean_dataset_removes_invalid_scores():
    df = make_df(final_exam_score=[70, 150, -10])
    cleaned, summary = clean_dataset(df)
    assert (cleaned["final_exam_score"] > 100).sum() == 0
    assert (cleaned["final_exam_score"] < 0).sum() == 0
    assert summary["invalid_records_removed"] >= 2


def test_clean_dataset_final_rows_matches_len():
    df = make_df()
    cleaned, summary = clean_dataset(df)
    assert summary["final_rows"] == len(cleaned)


def test_clean_dataset_strips_whitespace_in_department():
    df = make_df(department=["  computer science  ", "Civil", "Mechanical"])
    cleaned, _ = clean_dataset(df)
    assert cleaned.loc[cleaned["student_id"] == "S1", "department"].iloc[0] == "Computer Science"
