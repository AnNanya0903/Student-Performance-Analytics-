"""
Data validation and cleaning pipeline.

Takes a raw (possibly messy, possibly user-uploaded) dataframe and returns a
cleaned dataframe plus a summary dict describing every action taken, so the
dashboard can show a transparent "Data Quality" report.
"""
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "student_id", "name", "gender", "age", "department", "semester",
    "attendance_percentage", "math_score", "science_score", "programming_score",
    "english_score", "assignment_score", "internal_score", "final_exam_score",
    "study_hours_per_week", "extracurricular", "internet_access", "location",
]

SCORE_COLUMNS = [
    "math_score", "science_score", "programming_score", "english_score",
    "assignment_score", "internal_score", "final_exam_score",
]

NUMERIC_COLUMNS = SCORE_COLUMNS + ["attendance_percentage", "age", "study_hours_per_week"]

CANONICAL_DEPARTMENTS = {
    "computer science": "Computer Science",
    "information science": "Information Science",
    "electronics": "Electronics",
    "mechanical": "Mechanical",
    "civil": "Civil",
}


class ValidationError(Exception):
    """Raised when an uploaded CSV is missing required columns."""


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    return df


def validate_columns(df: pd.DataFrame) -> list[str]:
    """Return a list of missing required columns (empty list = valid)."""
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def clean_dataset(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Run the full cleaning pipeline on a raw dataframe.

    Returns (cleaned_df, summary) where summary contains counts of every
    action performed, suitable for display in the Data Quality tab.
    """
    summary = {
        "original_rows": len(raw_df),
        "duplicate_rows_removed": 0,
        "missing_values_handled": 0,
        "invalid_records_removed": 0,
        "outliers_capped": 0,
        "whitespace_fixed": 0,
        "type_conversions": 0,
        "final_rows": 0,
        "warnings": [],
    }

    df = normalize_column_names(raw_df)

    missing_cols = validate_columns(df)
    if missing_cols:
        raise ValidationError(
            f"Missing required column(s): {', '.join(missing_cols)}"
        )

    # --- Whitespace & categorical normalization -------------------------
    text_cols = ["name", "gender", "department", "extracurricular", "internet_access", "location", "student_id"]
    for col in text_cols:
        if col in df.columns:
            before = df[col].astype(str)
            after = before.str.strip()
            changed = (before != after).sum()
            df[col] = after
            summary["whitespace_fixed"] += int(changed)

    if "department" in df.columns:
        df["department"] = df["department"].apply(
            lambda x: CANONICAL_DEPARTMENTS.get(str(x).strip().lower(), str(x).strip().title())
        )

    if "gender" in df.columns:
        df["gender"] = df["gender"].str.title()

    if "extracurricular" in df.columns:
        df["extracurricular"] = df["extracurricular"].str.title()

    if "internet_access" in df.columns:
        df["internet_access"] = df["internet_access"].str.title()

    # --- Type conversion --------------------------------------------------
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            before_na = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            after_na = df[col].isna().sum()
            summary["type_conversions"] += int(after_na - before_na) if after_na > before_na else 0

    # --- Duplicates ---------------------------------------------------------
    dup_mask = df.duplicated(subset=["student_id"], keep="first")
    summary["duplicate_rows_removed"] = int(dup_mask.sum())
    df = df[~dup_mask].copy()

    # --- Invalid numeric ranges: out-of-bounds scores/attendance ------------
    invalid_mask = pd.Series(False, index=df.index)
    for col in SCORE_COLUMNS + ["attendance_percentage"]:
        if col in df.columns:
            invalid_mask |= (df[col] < 0) | (df[col] > 100)
    if "age" in df.columns:
        invalid_mask |= (df["age"] < 15) | (df["age"] > 60)

    summary["invalid_records_removed"] = int(invalid_mask.sum())
    df = df[~invalid_mask].copy()

    # --- Missing values -------------------------------------------------
    missing_before = int(df[NUMERIC_COLUMNS].isna().sum().sum()) if all(c in df.columns for c in NUMERIC_COLUMNS) else int(df.isna().sum().sum())

    for col in SCORE_COLUMNS + ["internal_score"]:
        if col in df.columns and df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    if "attendance_percentage" in df.columns and df["attendance_percentage"].isna().any():
        df["attendance_percentage"] = df["attendance_percentage"].fillna(df["attendance_percentage"].median())

    if "study_hours_per_week" in df.columns and df["study_hours_per_week"].isna().any():
        df["study_hours_per_week"] = df["study_hours_per_week"].fillna(df["study_hours_per_week"].median())

    if "age" in df.columns and df["age"].isna().any():
        df["age"] = df["age"].fillna(df["age"].median())

    for col in ["gender", "department", "extracurricular", "internet_access", "location"]:
        if col in df.columns and df[col].isna().any():
            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
            df[col] = df[col].fillna(mode_val)

    # Any remaining rows with missing critical identifiers are dropped
    critical = ["student_id", "name"]
    before_drop = len(df)
    df = df.dropna(subset=[c for c in critical if c in df.columns])
    summary["invalid_records_removed"] += before_drop - len(df)

    summary["missing_values_handled"] = missing_before

    # --- Outlier capping (winsorize extreme study hours) --------------------
    if "study_hours_per_week" in df.columns:
        cap = 70
        outliers = (df["study_hours_per_week"] > cap).sum()
        df["study_hours_per_week"] = df["study_hours_per_week"].clip(upper=cap)
        summary["outliers_capped"] += int(outliers)

    df = df.reset_index(drop=True)
    summary["final_rows"] = len(df)

    if summary["final_rows"] == 0:
        summary["warnings"].append("All rows were removed during cleaning — check the source data.")

    return df, summary


def data_quality_report(df: pd.DataFrame) -> dict:
    """Build the metrics shown on the Data Quality tab for an already-cleaned df."""
    total_rows = len(df)
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    missing = df.isna().sum()
    missing_pct = (missing / total_rows * 100).round(2) if total_rows else missing
    completeness = round(100 - missing_pct.mean(), 2) if total_rows else 0.0

    return {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "duplicate_rows": int(df.duplicated(subset=["student_id"]).sum()) if "student_id" in df.columns else 0,
        "missing_values": missing.to_dict(),
        "missing_pct": missing_pct.to_dict(),
        "dtypes": dtypes,
        "completeness_pct": completeness,
    }
