"""
Export helpers: CSV bytes for download buttons, and a plain-text analysis
report generator (used both for the on-screen report and the downloadable
.txt/.md report).
"""
from datetime import datetime
from io import BytesIO

import pandas as pd


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()


def build_report_text(
    kpis: dict,
    cleaning_summary: dict,
    pass_fail: dict,
    dept_avg: pd.DataFrame,
    at_risk_df: pd.DataFrame,
    top_df: pd.DataFrame,
    insights: list[str],
    recommendations: list[str],
) -> str:
    lines = []
    lines.append("STUDENT PERFORMANCE ANALYTICS — SUMMARY REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    lines.append("\n1. DATASET SUMMARY")
    lines.append(f"   Original rows: {cleaning_summary.get('original_rows')}")
    lines.append(f"   Duplicate rows removed: {cleaning_summary.get('duplicate_rows_removed')}")
    lines.append(f"   Missing values handled: {cleaning_summary.get('missing_values_handled')}")
    lines.append(f"   Invalid records removed: {cleaning_summary.get('invalid_records_removed')}")
    lines.append(f"   Final rows analyzed: {cleaning_summary.get('final_rows')}")

    lines.append("\n2. STUDENT / PERFORMANCE STATISTICS")
    lines.append(f"   Total Students: {kpis.get('total_students')}")
    lines.append(f"   Average Overall Score: {kpis.get('avg_score')}")
    lines.append(f"   Average Attendance: {kpis.get('avg_attendance')}%")
    lines.append(f"   Average Study Hours/Week: {kpis.get('avg_study_hours')}")
    lines.append(f"   Top Performer: {kpis.get('top_performer')}")

    lines.append("\n3. DEPARTMENT ANALYSIS")
    lines.append(dept_avg.to_string(index=False))

    lines.append("\n4. PASS / FAIL ANALYSIS")
    lines.append(f"   Passed: {pass_fail.get('passed')}")
    lines.append(f"   Failed: {pass_fail.get('failed')}")
    lines.append(f"   Pass Percentage: {pass_fail.get('pass_percentage')}%")
    lines.append(f"   Failure Percentage: {pass_fail.get('failure_percentage')}%")

    lines.append(f"\n5. AT-RISK ANALYSIS ({len(at_risk_df)} students)")
    if not at_risk_df.empty:
        lines.append(at_risk_df.head(15).to_string(index=False))
        if len(at_risk_df) > 15:
            lines.append(f"   ... and {len(at_risk_df) - 15} more")
    else:
        lines.append("   No at-risk students identified.")

    lines.append("\n6. TOP PERFORMERS")
    lines.append(top_df.to_string(index=False))

    lines.append("\n7. KEY INSIGHTS")
    for i, insight in enumerate(insights, 1):
        lines.append(f"   {i}. {insight.replace('**', '')}")

    lines.append("\n8. RECOMMENDATIONS")
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"   {i}. {rec}")

    lines.append("\n" + "=" * 60)
    lines.append("End of report.")

    return "\n".join(lines)
