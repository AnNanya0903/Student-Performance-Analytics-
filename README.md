# 🎓 Student Performance Analytics Dashboard

A full-stack data analytics application that cleans, stores, analyzes, and
visualizes student academic performance data — built to demonstrate
real-world data analyst / data engineering skills end-to-end: from messy CSV
to a SQL-backed, interactive dashboard with automated insights.

---

## 📌 Project Overview

Educational institutions collect a lot of student data (attendance, scores,
study habits) but rarely turn it into actionable insight. This project takes
raw, imperfect student records and turns them into:

- A validated, cleaned dataset
- A relational SQLite database queried with real SQL
- Statistical analysis (descriptive stats, correlations, pass/fail, risk
  classification)
- An interactive, filterable Streamlit dashboard
- Automated, data-driven insights and recommendations
- Exportable CSV data and a generated summary report

## 🧩 Business Problem

Academic teams need to answer questions like:
- Which departments/subjects are underperforming?
- Which students are at risk of failing, and why?
- Does attendance or study time actually correlate with performance?
- Who are the top performers, and what does a "typical" struggling student
  look like?

This dashboard answers all of these from raw data, with every number backed
by an actual calculation — nothing is hardcoded.

## ✨ Features

- **CSV upload** with column validation, type coercion, and friendly error
  messages (no raw tracebacks)
- **Data cleaning pipeline**: duplicate removal, missing-value imputation,
  invalid-range filtering, whitespace/casing normalization, outlier capping
- **SQLite + SQLAlchemy** persistence layer (`students`, `performance_records`,
  `analysis_results` tables)
- **Real SQL queries** (department averages, top students, at-risk students,
  pass rates by semester, etc.) — see `analysis/sql_queries.py`
- **Statistical analysis**: mean/median/std/min/max, department/semester/
  gender breakdowns, correlation matrix
- **Pass/Fail logic**, **at-risk classification**, and **performance
  categories**, all rule-based and transparent
- **10 interactive Plotly charts**
- **Automated insights engine** — plain-language findings generated from
  the actual computed statistics
- **Data-driven recommendations**
- **Student search / profile view** with a radar chart of subject scores
- **CSV exports** (filtered data, at-risk students, top performers,
  performance summary) and a downloadable text report
- **Dedicated Data Quality tab** showing cleaning actions and completeness
- **10+ pytest unit tests** covering cleaning and business logic

## 🛠 Tech Stack

| Layer            | Technology                     |
|-------------------|---------------------------------|
| UI / App          | Streamlit                      |
| Data processing   | Pandas, NumPy                  |
| Database          | SQLite + SQLAlchemy            |
| Visualization     | Plotly (+ statsmodels trendline) |
| Stats / ML        | scikit-learn (available for extension), NumPy |
| Export            | OpenPyXL, built-in CSV          |
| Testing           | Pytest                         |

## 🏗 Architecture

```
CSV (sample or uploaded)
        │
        ▼
analysis/cleaning.py   ── validate columns, clean, dedupe, impute
        │
        ▼
analysis/statistics.py ── overall score, pass/fail, risk, category
        │
        ├──────────────► database/database.py ─► SQLite (students,
        │                                          performance_records,
        │                                          analysis_results)
        │                                              │
        │                                 analysis/sql_queries.py
        │                                   (real SQL SELECT/JOIN/GROUP BY)
        ▼
   Streamlit app.py
        │
        ├─► visualizations/charts.py  (Plotly figures)
        ├─► analysis/insights.py      (auto-generated findings)
        └─► utils/export.py           (CSV / report generation)
```

### Data Flow

1. User selects the sample dataset or uploads a CSV.
2. `analysis/cleaning.py` normalizes column names, validates required
   columns, coerces types, removes duplicates/invalid rows, imputes missing
   values, and returns a cleaning summary.
3. `analysis/statistics.py` derives `overall_score`, `pass_status`,
   `risk_status`, `risk_reason`, and `performance_category` for every row.
4. The enriched dataframe is written into SQLite via SQLAlchemy
   (`database/database.py`), replacing prior data on each load.
5. The Streamlit sidebar filters operate on the in-memory dataframe; the
   **SQL Analysis** tab separately queries the SQLite database directly with
   raw SQL to demonstrate genuine database usage.
6. `analysis/insights.py` and `utils/export.py` turn the computed statistics
   into plain-language insights, recommendations, and downloadable reports.

## 📁 Project Structure

```
student-performance-analytics/
├── app.py                     # Streamlit dashboard (entry point)
├── generate_data.py           # Generates the sample dataset
├── data/
│   └── students.csv           # 550+ realistic sample student records
├── database/
│   ├── database.py            # Engine, session, load/query helpers
│   └── models.py              # SQLAlchemy ORM models
├── analysis/
│   ├── cleaning.py            # Validation + cleaning pipeline
│   ├── statistics.py          # Stats, pass/fail, risk, rankings
│   ├── insights.py            # Automated insights + recommendations
│   └── sql_queries.py         # Real SQL queries against SQLite
├── visualizations/
│   └── charts.py              # Plotly chart builders
├── utils/
│   └── export.py              # CSV / report export helpers
├── tests/
│   ├── test_cleaning.py
│   └── test_statistics.py
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

## 📊 Dataset Description

`data/students.csv` contains **550+ synthetic but realistic** student
records across 5 departments (Computer Science, Information Science,
Electronics, Mechanical, Civil) and 8 semesters, with correlated
attendance/study-hours/scores so the analytics are meaningful rather than
random noise. The generator (`generate_data.py`) deliberately injects a
small amount of realistic messiness — duplicate rows, missing values,
whitespace/casing issues, and a few out-of-range values — so the cleaning
pipeline has genuine work to do.

Columns: `student_id, name, gender, age, department, semester,
attendance_percentage, math_score, science_score, programming_score,
english_score, assignment_score, internal_score, final_exam_score,
study_hours_per_week, extracurricular, internet_access, location`

## 🧹 Data Cleaning Methodology

- Normalize column names (lowercase, trim, underscore-separated)
- Validate all required columns are present (clear error if not)
- Strip whitespace and standardize casing on text/categorical fields
- Coerce numeric columns to numeric types (invalid text → NaN → imputed)
- Remove duplicate `student_id` rows
- Remove rows with out-of-range scores/attendance/age
- Impute missing numeric values with the column median, categorical values
  with the column mode
- Cap unrealistic outliers (e.g. absurd study-hour values)
- Produce a full before/after summary shown in the **Data Quality** tab

## 📈 Analytics Methodology

- **Overall score**: a weighted average across all seven graded components
  (final exam weighted highest at 25%)
- **Pass/Fail**: Pass requires `final_exam_score >= 40` **and**
  `internal_score >= 40`
- **At-risk**: flagged if attendance < 75%, final exam < 40, or average
  subject score < 45 — with the specific reason(s) recorded per student
- **Performance category**: Excellent (≥85) / Good (70–84) / Average
  (50–69) / Needs Improvement (40–49) / At Risk (<40)
- **Correlation analysis** between attendance, study hours, assignment/
  internal/final scores and overall score (correlation, not causation)
- **Insights & recommendations** are template sentences filled entirely
  from computed values — no fabricated findings

## 🖼 Screenshots

*(Add screenshots here after running the app locally — suggested shots
below.)*

Suggested screenshots for your GitHub repo:
1. Overview tab with KPI cards and key insights
2. Performance Analysis tab with correlation heatmap
3. Department Analysis charts
4. At-Risk Students table
5. Student Profile radar chart
6. SQL Analysis tab showing a query + result
7. Data Quality tab
8. Generated report preview

## 💻 Installation & Setup (Windows)

```bat
:: 1. Clone the repository
git clone https://github.com/<your-username>/student-performance-analytics.git
cd student-performance-analytics

:: 2. Create a virtual environment
python -m venv venv

:: 3. Activate the virtual environment
venv\Scripts\activate

:: 4. Install dependencies
pip install -r requirements.txt

:: 5. (Optional) Regenerate the sample dataset
python generate_data.py

:: 6. Run the dashboard
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python generate_data.py   # optional — a dataset is already included
streamlit run app.py
```

## ✅ Running Tests

```bat
pytest
```

or for verbose output:

```bat
pytest -v
```

18 tests cover column validation, cleaning behavior (duplicates, missing
values, invalid ranges, whitespace normalization), pass/fail logic, risk
classification, performance categories, and top-performer ranking.

## 🔍 Demo Usage

1. Launch the app — it loads the bundled sample dataset by default.
2. Use the sidebar to filter by department, semester, gender, attendance,
   score range, extracurricular activity, and internet access.
3. Explore the **Overview**, **Performance Analysis**, **Department
   Analysis**, **At-Risk Students**, and **Student Profile** tabs.
4. Open **SQL Analysis** to run real SQL queries against the SQLite
   database.
5. Check **Data Quality** to see exactly what the cleaning pipeline did.
6. Go to **Reports**, click **Generate Report**, and download it — or
   download any of the CSV exports.
7. Try uploading your own CSV (same required columns) from the sidebar.

## 💡 Sample Insights (from the bundled dataset)

- Computer Science has the highest average overall score; Mechanical the
  lowest.
- Assignment scores are the strongest subject on average; final exam
  scores need the most improvement.
- Roughly a third of students have attendance below 75%.
- Study hours show a measurable positive correlation with overall score.
- Around 40% of students are flagged at-risk under the current thresholds
  (tune the rules in `analysis/statistics.py` to match your institution's
  standards).

## 🚀 Future Improvements

- Add authentication for multi-user / teacher-specific views
- Support PostgreSQL/MySQL for production deployments
- Add a proper PDF report generator (ReportLab/WeasyPrint)
- Add trend analysis across multiple semesters/years per student
- Add a scikit-learn model to predict at-risk students proactively
- Deploy to Streamlit Community Cloud with scheduled data refresh

## 🌐 GitHub Usage

```bat
git init
git add .
git commit -m "Initial commit: Student Performance Analytics Dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/student-performance-analytics.git
git push -u origin main
```

`.gitignore` already excludes the generated SQLite database, `__pycache__`,
virtual environments, and any `.env` secrets.

## 📄 License

This project is provided as-is for educational and portfolio purposes.
