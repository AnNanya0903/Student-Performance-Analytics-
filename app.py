"""
Student Performance Analytics Dashboard
=========================================
A full-stack Streamlit application demonstrating data cleaning, SQL-backed
analytics, statistical analysis, and interactive visualization over student
performance data.

Run with:  streamlit run app.py
"""
from pathlib import Path
import io

import pandas as pd
import requests
import streamlit as st

from analysis.cleaning import ValidationError, clean_dataset, data_quality_report
from analysis.insights import generate_insights, generate_recommendations
from analysis.statistics import (
    at_risk_table,
    correlation_matrix,
    department_averages,
    descriptive_stats,
    enrich_dataframe,
    gender_averages,
    pass_fail_counts,
    semester_averages,
    subject_averages,
    summary_kpis,
    top_performers,
)
from analysis import sql_queries
from database.database import load_dataframe_to_db
from utils.export import build_report_text, df_to_csv_bytes
from visualizations import charts

st.set_page_config(page_title="Student Performance Analytics", layout="wide", page_icon="📊", initial_sidebar_state="expanded")

# Inject minimal card-effect CSS only
def _inject_css():
    css_path = Path(__file__).parent / "styles" / "cards.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

_inject_css()

DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "students.csv"


# ---------------------------------------------------------------------------
# Data loading / caching
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_raw_csv(file_or_path) -> pd.DataFrame:
    return pd.read_csv(file_or_path)


@st.cache_data(show_spinner=False)
def process_dataset(raw_df: pd.DataFrame):
    """Clean, validate and enrich the dataframe. Cached on the raw content."""
    cleaned_df, cleaning_summary = clean_dataset(raw_df)
    enriched_df = enrich_dataframe(cleaned_df)
    return enriched_df, cleaning_summary


def safe_load(uploaded_file):
    """Load + process a dataset, surfacing friendly errors instead of tracebacks."""
    try:
        if isinstance(uploaded_file, pd.DataFrame):
            raw_df = uploaded_file
        else:
            raw_df = load_raw_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the data source: {e}")
        return None, None

    if raw_df.empty:
        st.error("The data source is empty.")
        return None, None

    try:
        enriched_df, cleaning_summary = process_dataset(raw_df)
    except ValidationError as e:
        st.error(f"Validation failed: {e}")
        return None, None
    except Exception as e:
        st.error(f"An error occurred while processing the dataset: {e}")
        return None, None

    if enriched_df.empty:
        st.error("No valid rows remained after cleaning. Please check your data.")
        return None, cleaning_summary

    return enriched_df, cleaning_summary


# ---------------------------------------------------------------------------
# Sidebar — data source + filters
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="text-align: center; padding: 0.5rem 0 1.5rem 0;">
        <h1 style="font-size: 1.5rem; margin: 0; background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline;">
            <span style="-webkit-text-fill-color: initial; font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;">📊</span> 
            <span style="font-family: 'Inter', sans-serif;">Analytics</span>
        </h1>
        <p style="color: #a5b4fc; font-size: 0.8rem; margin: 0.25rem 0 0 0;">Student Performance</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🗂 Dataset")
data_source = st.sidebar.radio("Choose data source", ["Sample Dataset", "Upload CSV", "Google Sheets"], label_visibility="collapsed")

uploaded_file = None
source_for_load = None

if data_source == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload student CSV", type=["csv"])
    source_for_load = uploaded_file
elif data_source == "Google Sheets":
    st.sidebar.markdown("#### Google Sheets")
    sheet_url = st.sidebar.text_input("Paste Google Sheet URL (must be public)", placeholder="https://docs.google.com/spreadsheets/d/...")
    gid = st.sidebar.text_input("Sheet GID (optional, default: first sheet)", value="0")
    
    if sheet_url and st.sidebar.button("Load from Google Sheets"):
        try:
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            import requests
            response = requests.get(csv_url, timeout=30)
            response.raise_for_status()
            source_for_load = pd.read_csv(io.StringIO(response.text))
            st.sidebar.success("Google Sheet loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Failed to load Google Sheet: {e}")
            source_for_load = None
else:
    source_for_load = DEFAULT_DATA_PATH

if source_for_load is None:
    st.title("🎓 Student Performance Analytics Dashboard")
    st.info("Upload a CSV file from the sidebar to get started, or switch to the sample dataset.")
    st.stop()

df, cleaning_summary = safe_load(source_for_load)
if df is None:
    st.stop()

# Persist to SQLite so SQL tab demonstrates real queries against real data
if "db_loaded_for" not in st.session_state or st.session_state.get("db_loaded_for") != id(df):
    try:
        load_dataframe_to_db(df)
        st.session_state["db_loaded_for"] = id(df)
    except Exception as e:
        st.sidebar.warning(f"Database sync skipped: {e}")

st.sidebar.markdown("### Filters")

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

key_prefix = f"filter_{st.session_state.reset_counter}"

departments = sorted(df["department"].unique())
sel_departments = st.sidebar.multiselect("Department", departments, default=departments, key=f"{key_prefix}_departments")

semesters = sorted(df["semester"].unique())
sel_semesters = st.sidebar.multiselect("Semester", semesters, default=semesters, key=f"{key_prefix}_semesters")

genders = sorted(df["gender"].unique())
sel_genders = st.sidebar.multiselect("Gender", genders, default=genders, key=f"{key_prefix}_genders")

att_min, att_max = int(df["attendance_percentage"].min()), int(df["attendance_percentage"].max())
sel_attendance = st.sidebar.slider("Attendance range (%)", att_min, att_max, (att_min, att_max), key=f"{key_prefix}_attendance")

score_min, score_max = int(df["overall_score"].min()), int(df["overall_score"].max())
sel_score = st.sidebar.slider("Overall score range", score_min, score_max, (score_min, score_max), key=f"{key_prefix}_score")

extracurricular_opts = sorted(df["extracurricular"].unique())
sel_extracurricular = st.sidebar.multiselect("Extracurricular", extracurricular_opts, default=extracurricular_opts, key=f"{key_prefix}_extracurricular")

internet_opts = sorted(df["internet_access"].unique())
sel_internet = st.sidebar.multiselect("Internet Access", internet_opts, default=internet_opts, key=f"{key_prefix}_internet")

filtered_df = df[
    df["department"].isin(sel_departments)
    & df["semester"].isin(sel_semesters)
    & df["gender"].isin(sel_genders)
    & df["attendance_percentage"].between(*sel_attendance)
    & df["overall_score"].between(*sel_score)
    & df["extracurricular"].isin(sel_extracurricular)
    & df["internet_access"].isin(sel_internet)
].copy()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Filters", use_container_width=True):
    st.session_state.reset_counter += 1
    st.rerun()
st.sidebar.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** students after filtering.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            <span style="-webkit-text-fill-color: initial; font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;">🎓</span> 
            <span style="font-family: 'Inter', sans-serif;">Student Performance Analytics</span>
        </h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-top: 0.5rem; font-weight: 400;">
            Interactive dashboard for academic insights, risk analysis, and performance tracking
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if filtered_df.empty:
    st.warning("No students match the current filters. Adjust the filters in the sidebar.")
    st.stop()

tabs = st.tabs([
    "Overview", "Performance Analysis", "Department Analysis", "At-Risk Students",
    "Student Profile", "SQL Analysis", "Data Quality", "Reports",
])

# ----- Overview -----
with tabs[0]:
    kpis = summary_kpis(filtered_df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", kpis["total_students"])
    c2.metric("Average Score", kpis["avg_score"])
    c3.metric("Average Attendance", f"{kpis['avg_attendance']}%")
    c4.metric("Pass Percentage", f"{kpis['pass_percentage']}%")

    c5, c6, c7 = st.columns(3)
    c5.metric("Top Performer", kpis["top_performer"])
    c6.metric("At-Risk Students", kpis["at_risk_count"])
    c7.metric("Avg Study Hours/Week", kpis["avg_study_hours"])

    st.markdown("### Key Insights")
    insights = generate_insights(filtered_df)
    for i, insight in enumerate(insights):
        clean_insight = insight.replace("**", "")
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08));
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 12px;
                padding: 1rem 1.25rem;
                margin-bottom: 0.75rem;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                animation: fadeInUp 0.5s ease-out {i * 0.1}s both;
            " onmouseover="this.style.transform='translateX(8px)'; this.style.borderColor='rgba(99,102,241,0.5)'" onmouseout="this.style.transform='translateX(0)'; this.style.borderColor='rgba(99,102,241,0.2)'">
                <span style="color: var(--primary); font-weight: 600; margin-right: 0.5rem;">💡</span>
                <span style="color: var(--text); font-weight: 500;">{clean_insight}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(charts.pass_fail_distribution_chart(filtered_df), use_container_width=True)
    with col_b:
        st.plotly_chart(charts.performance_category_chart(filtered_df), use_container_width=True)

# ----- Performance Analysis -----
with tabs[1]:
    st.markdown("### Descriptive Statistics")
    score_cols = [
        "math_score", "science_score", "programming_score", "english_score",
        "assignment_score", "internal_score", "final_exam_score", "overall_score",
        "attendance_percentage",
    ]
    st.dataframe(descriptive_stats(filtered_df, score_cols), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.subject_wise_avg_chart(filtered_df), use_container_width=True)
        st.plotly_chart(charts.attendance_vs_final_score_chart(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(charts.score_distribution_chart(filtered_df), use_container_width=True)
        st.plotly_chart(charts.study_hours_vs_performance_chart(filtered_df), use_container_width=True)

    st.markdown("### Correlation Analysis")
    corr = correlation_matrix(filtered_df)
    st.plotly_chart(charts.correlation_heatmap(corr), use_container_width=True)
    strongest = corr["overall_score"].drop("overall_score").abs().idxmax()
    strongest_val = corr["overall_score"][strongest]
    st.info(
        f"**{strongest.replace('_', ' ').title()}** has the strongest observed relationship with "
        f"overall score (correlation: {strongest_val}). Correlation does not imply causation."
    )

    st.markdown("### Top 10 Performers")
    top_df = top_performers(filtered_df, 10)
    st.dataframe(top_df, use_container_width=True, hide_index=True)

# ----- Department Analysis -----
with tabs[2]:
    st.markdown("### Department Averages")
    dept_avg = department_averages(filtered_df)
    st.dataframe(dept_avg, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.department_avg_score_chart(filtered_df), use_container_width=True)
        st.plotly_chart(charts.department_pass_percentage_chart(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(charts.semester_performance_chart(filtered_df), use_container_width=True)
        st.plotly_chart(charts.gender_performance_chart(filtered_df), use_container_width=True)

    st.markdown("### Semester Averages")
    st.dataframe(semester_averages(filtered_df), use_container_width=True, hide_index=True)

    st.markdown("### Gender Averages")
    st.dataframe(gender_averages(filtered_df), use_container_width=True, hide_index=True)

# ----- At-Risk Students -----
with tabs[3]:
    at_risk_df = at_risk_table(filtered_df)
    st.markdown(f"### At-Risk Students ({len(at_risk_df)})")
    if at_risk_df.empty:
        st.success("No at-risk students under current filters.")
    else:
        st.dataframe(at_risk_df, use_container_width=True, hide_index=True)
        st.plotly_chart(charts.at_risk_by_department_chart(filtered_df), use_container_width=True)
        st.download_button(
            "⬇ Download At-Risk Students CSV", df_to_csv_bytes(at_risk_df),
            "at_risk_students.csv", "text/csv",
        )

# ----- Student Profile -----
with tabs[4]:
    st.markdown("### Student Search")
    search_mode = st.radio("Search by", ["Student ID", "Name"], horizontal=True)
    if search_mode == "Student ID":
        query = st.text_input("Enter Student ID (e.g. STU0001)")
        matches = filtered_df[filtered_df["student_id"].str.contains(query, case=False, na=False)] if query else pd.DataFrame()
    else:
        query = st.text_input("Enter student name")
        matches = filtered_df[filtered_df["name"].str.contains(query, case=False, na=False)] if query else pd.DataFrame()

    if query and matches.empty:
        st.warning("No matching students found.")
    elif not matches.empty:
        selected_id = st.selectbox("Select student", matches["student_id"] + " — " + matches["name"])
        student_id = selected_id.split(" — ")[0]
        row = filtered_df[filtered_df["student_id"] == student_id].iloc[0]

        pass_color = "#10b981" if row["pass_status"] == "Pass" else "#ef4444"
        risk_color = "#ef4444" if row["risk_status"] == "At Risk" else "#10b981"
        cat_color = {
            "Excellent": "#6366f1",
            "Good": "#8b5cf6",
            "Average": "#f59e0b",
            "Needs Improvement": "#f97316",
            "At Risk": "#ef4444",
        }.get(row["performance_category"], "#64748b")

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,250,252,0.9));
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                padding: 2rem;
                box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
                margin-bottom: 1.5rem;
            ">
                <div style="display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.5rem;">
                    <div style="
                        width: 64px; height: 64px; border-radius: 50%;
                        background: linear-gradient(135deg, #6366f1, #8b5cf6);
                        display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 1.75rem; font-weight: 700;
                        box-shadow: 0 4px 15px rgba(99,102,241,0.4);
                    ">{row['name'][0].upper()}</div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #1e293b;">{row['name']}</h3>
                        <p style="margin: 0.25rem 0 0 0; color: #64748b; font-size: 0.9rem;">{row['student_id']} · {row['department']} · Semester {row['semester']}</p>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                    <div style="background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08)); border-radius: 12px; padding: 1rem; text-align: center;">
                        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; font-weight: 600;">Overall Score</div>
                        <div style="font-size: 1.75rem; font-weight: 800; color: #1e293b; margin-top: 0.25rem;">{row['overall_score']}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, rgba(6,182,212,0.08), rgba(16,185,129,0.08)); border-radius: 12px; padding: 1rem; text-align: center;">
                        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; font-weight: 600;">Attendance</div>
                        <div style="font-size: 1.75rem; font-weight: 800; color: #1e293b; margin-top: 0.25rem;">{row['attendance_percentage']}%</div>
                    </div>
                    <div style="background: linear-gradient(135deg, rgba(245,158,11,0.08), rgba(239,68,68,0.08)); border-radius: 12px; padding: 1rem; text-align: center;">
                        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; font-weight: 600;">Category</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: {cat_color}; margin-top: 0.5rem;">{row['performance_category']}</div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;">
                    <div style="background: #f8fafc; border-radius: 12px; padding: 0.75rem 1rem; display: flex; align-items: center; justify-content: space-between; border: 1px solid #e2e8f0;">
                        <span style="color: #64748b; font-weight: 500;">Pass Status</span>
                        <span style="background: {pass_color}; color: white; padding: 0.35rem 1rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">{row['pass_status']}</span>
                    </div>
                    <div style="background: #f8fafc; border-radius: 12px; padding: 0.75rem 1rem; display: flex; align-items: center; justify-content: space-between; border: 1px solid #e2e8f0;">
                        <span style="color: #64748b; font-weight: 500;">Risk Status</span>
                        <span style="background: {risk_color}; color: white; padding: 0.35rem 1rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">{row['risk_status']}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Details")
        info_df = pd.DataFrame({
            "Field": ["Department", "Semester", "Gender", "Age", "Location", "Study Hours/Week"],
            "Value": [row["department"], row["semester"], row["gender"], row["age"], row["location"], row["study_hours_per_week"]],
        })
        st.dataframe(info_df, use_container_width=True, hide_index=True)

        st.plotly_chart(charts.student_score_radar(row), use_container_width=True)

# ----- SQL Analysis -----
with tabs[5]:
    st.markdown("### SQL-backed Queries")
    st.caption("These results are produced by real SQL queries executed against the SQLite database "
               "(unfiltered — reflects the full loaded dataset). See `analysis/sql_queries.py`.")

    query_options = {
        "Average score by department": sql_queries.avg_score_by_department,
        "Average attendance by department": sql_queries.avg_attendance_by_department,
        "Top 10 students": sql_queries.top_students,
        "Failed students": sql_queries.failed_students,
        "At-risk students": sql_queries.at_risk_students,
        "Pass percentage by semester": sql_queries.pass_percentage_by_semester,
        "Attendance below 75%": sql_queries.attendance_below_75,
        "Final score above 80": sql_queries.final_score_above_80,
    }
    choice = st.selectbox("Choose a query", list(query_options.keys()))
    try:
        result = query_options[choice]()
        st.dataframe(result, use_container_width=True, hide_index=True)
        with st.expander("View SQL"):
            import inspect
            st.code(inspect.getsource(query_options[choice]), language="python")
    except Exception as e:
        st.error(f"Query failed: {e}")

# ----- Data Quality -----
with tabs[6]:
    st.markdown("### Cleaning Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Original Rows", cleaning_summary["original_rows"])
    c2.metric("Duplicates Removed", cleaning_summary["duplicate_rows_removed"])
    c3.metric("Missing Values Handled", cleaning_summary["missing_values_handled"])
    c4.metric("Invalid Records Removed", cleaning_summary["invalid_records_removed"])
    c5.metric("Final Rows", cleaning_summary["final_rows"])

    for w in cleaning_summary.get("warnings", []):
        st.warning(w)

    st.markdown("### Data Quality Report (post-cleaning)")
    quality = data_quality_report(df)
    q1, q2, q3 = st.columns(3)
    q1.metric("Total Rows", quality["total_rows"])
    q2.metric("Total Columns", quality["total_columns"])
    q3.metric("Completeness", f"{quality['completeness_pct']}%")

    st.markdown("#### Column Data Types")
    dtype_df = pd.DataFrame(list(quality["dtypes"].items()), columns=["Column", "Type"])
    st.dataframe(dtype_df, use_container_width=True, hide_index=True)

    st.markdown("#### Missing Values by Column")
    missing_df = pd.DataFrame({
        "Column": quality["missing_values"].keys(),
        "Missing Count": quality["missing_values"].values(),
        "Missing %": quality["missing_pct"].values(),
    })
    st.dataframe(missing_df, use_container_width=True, hide_index=True)

# ----- Reports -----
with tabs[7]:
    st.markdown("### Generate Report")
    st.caption("Report is generated from the currently filtered data.")

    if st.button("📄 Generate Report", type="primary"):
        kpis = summary_kpis(filtered_df)
        pf = pass_fail_counts(filtered_df)
        dept_avg = department_averages(filtered_df)
        at_risk_df = at_risk_table(filtered_df)
        top_df = top_performers(filtered_df, 10)
        insights = generate_insights(filtered_df)
        recs = generate_recommendations(filtered_df)

        report_text = build_report_text(kpis, cleaning_summary, pf, dept_avg, at_risk_df, top_df, insights, recs)
        st.session_state["report_text"] = report_text

    if "report_text" in st.session_state:
        st.markdown(
            """
            <div style="
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
            """,
            unsafe_allow_html=True,
        )
        st.text_area("Report Preview", st.session_state["report_text"], height=400, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
        st.download_button(
            "⬇ Download Report (.txt)", st.session_state["report_text"].encode("utf-8"),
            "student_performance_report.txt", "text/plain",
        )

    st.markdown("---")
    st.markdown("### Export Data")
    st.caption("Download datasets in CSV format for further analysis")
    
    export_cards = [
        ("📊 Filtered Data", "filtered_students.csv", df_to_csv_bytes(filtered_df)),
        ("🏆 Top Performers", "top_performers.csv", df_to_csv_bytes(top_performers(filtered_df, 10))),
        ("⚠️ At-Risk Students", "at_risk_students.csv", df_to_csv_bytes(at_risk_table(filtered_df))),
        ("📈 Performance Summary", "performance_summary.csv", df_to_csv_bytes(department_averages(filtered_df))),
    ]
    
    cols = st.columns(4)
    for i, (title, filename, data) in enumerate(export_cards):
        with cols[i]:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, rgba(99,102,241,0.05), rgba(139,92,246,0.05));
                    border: 1px solid rgba(99,102,241,0.15);
                    border-radius: 16px;
                    padding: 1.25rem;
                    text-align: center;
                    transition: all 0.3s ease;
                    margin-bottom: 1rem;
                " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 10px 25px -5px rgba(99,102,241,0.15)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                    <div style="font-size: 1.75rem; margin-bottom: 0.5rem;">{title.split()[0]}</div>
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.75rem; font-size: 0.9rem;">{' '.join(title.split()[1:])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.download_button(
                f"⬇ Download {filename.replace('.csv', '').replace('_', ' ').title()}",
                data, filename, "text/csv", use_container_width=True
            )

st.sidebar.markdown("---")
