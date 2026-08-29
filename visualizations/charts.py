"""
Interactive Plotly chart builders. Every chart is built from the real,
filtered dataframe passed in — nothing is precomputed or faked.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CUSTOM_THEME = {
    "layout": {
        "font": {"family": "Inter, sans-serif", "color": "#1e293b"},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(248,250,252,0.5)",
        "colorway": ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6"],
        "colorscale": {"sequential": "Viridis", "diverging": "RdBu"},
        "xaxis": {
            "gridcolor": "#e2e8f0",
            "linecolor": "#e2e8f0",
            "tickfont": {"size": 12},
            "title_font": {"size": 13, "color": "#475569"},
        },
        "yaxis": {
            "gridcolor": "#e2e8f0",
            "linecolor": "#e2e8f0",
            "tickfont": {"size": 12},
            "title_font": {"size": 13, "color": "#475569"},
        },
        "title": {
            "font": {"size": 16, "color": "#1e293b", "family": "Inter, sans-serif"},
            "x": 0.5,
            "xanchor": "center",
        },
        "legend": {
            "font": {"size": 12, "color": "#475569"},
            "bgcolor": "rgba(255,255,255,0.8)",
            "bordercolor": "#e2e8f0",
            "borderwidth": 1,
        },
        "margin": {"l": 60, "r": 40, "t": 80, "b": 60},
    }
}


def _apply_theme(fig):
    fig.update_layout(**CUSTOM_THEME["layout"])
    return fig


def department_avg_score_chart(df):
    grp = df.groupby("department", as_index=False)["overall_score"].mean().round(2)
    fig = px.bar(
        grp, x="department", y="overall_score", color="department",
        title="Department-wise Average Overall Score",
        labels={"overall_score": "Average Overall Score", "department": "Department"},
    )
    fig.update_layout(showlegend=False)
    return _apply_theme(fig)


def semester_performance_chart(df):
    grp = df.groupby("semester", as_index=False)["overall_score"].mean().round(2)
    fig = px.line(
        grp, x="semester", y="overall_score", markers=True,
        title="Semester-wise Average Performance",
        labels={"overall_score": "Average Overall Score", "semester": "Semester"},
    )
    return _apply_theme(fig)


def attendance_vs_final_score_chart(df):
    fig = px.scatter(
        df, x="attendance_percentage", y="final_exam_score", color="department",
        title="Attendance vs Final Exam Score", opacity=0.7,
        labels={"attendance_percentage": "Attendance (%)", "final_exam_score": "Final Exam Score"},
        trendline="ols" if len(df) > 5 else None,
    )
    return _apply_theme(fig)


def study_hours_vs_performance_chart(df):
    fig = px.scatter(
        df, x="study_hours_per_week", y="overall_score", color="pass_status",
        title="Study Hours vs Overall Performance", opacity=0.7,
        labels={"study_hours_per_week": "Study Hours / Week", "overall_score": "Overall Score"},
    )
    return _apply_theme(fig)


def pass_fail_distribution_chart(df):
    counts = df["pass_status"].value_counts().reset_index()
    counts.columns = ["pass_status", "count"]
    fig = px.pie(
        counts, names="pass_status", values="count", title="Pass vs Fail Distribution",
        color="pass_status",
        color_discrete_map={"Pass": "#2ca02c", "Fail": "#d62728"},
        hole=0.4,
    )
    return _apply_theme(fig)


def subject_wise_avg_chart(df):
    subjects = ["math_score", "science_score", "programming_score", "english_score",
                "assignment_score", "internal_score", "final_exam_score"]
    labels = ["Math", "Science", "Programming", "English", "Assignment", "Internal", "Final Exam"]
    values = [df[c].mean() for c in subjects]
    fig = px.bar(
        x=labels, y=values, title="Subject-wise Average Scores",
        labels={"x": "Subject", "y": "Average Score"},
    )
    return _apply_theme(fig)


def gender_performance_chart(df):
    grp = df.groupby("gender", as_index=False)["overall_score"].mean().round(2)
    fig = px.bar(
        grp, x="gender", y="overall_score", color="gender", title="Gender-wise Average Performance",
        labels={"overall_score": "Average Overall Score"},
    )
    fig.update_layout(showlegend=False)
    return _apply_theme(fig)


def department_pass_percentage_chart(df):
    grp = df.groupby("department").apply(lambda g: (g["pass_status"] == "Pass").mean() * 100).round(2)
    grp = grp.reset_index(name="pass_percentage")
    fig = px.bar(
        grp, x="department", y="pass_percentage", color="department",
        title="Department-wise Pass Percentage",
        labels={"pass_percentage": "Pass %"},
    )
    fig.update_layout(showlegend=False)
    return _apply_theme(fig)


def score_distribution_chart(df):
    fig = px.histogram(
        df, x="overall_score", nbins=30, title="Overall Score Distribution",
        labels={"overall_score": "Overall Score"},
    )
    return _apply_theme(fig)


def at_risk_by_department_chart(df):
    at_risk = df[df["risk_status"] == "At Risk"]
    grp = at_risk.groupby("department", as_index=False).size().rename(columns={"size": "at_risk_count"})
    fig = px.bar(
        grp, x="department", y="at_risk_count", color="department",
        title="At-Risk Students by Department",
        labels={"at_risk_count": "At-Risk Student Count"},
    )
    fig.update_layout(showlegend=False)
    return _apply_theme(fig)


def correlation_heatmap(corr_df):
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_df.values, x=corr_df.columns, y=corr_df.columns,
            colorscale="RdBu", zmid=0, text=corr_df.values, texttemplate="%{text}",
        )
    )
    fig.update_layout(title="Correlation Matrix")
    return _apply_theme(fig)


def performance_category_chart(df):
    counts = df["performance_category"].value_counts().reset_index()
    counts.columns = ["performance_category", "count"]
    order = ["Excellent", "Good", "Average", "Needs Improvement", "At Risk"]
    counts["performance_category"] = pd.Categorical(counts["performance_category"], categories=order, ordered=True)
    counts = counts.sort_values("performance_category")
    fig = px.bar(
        counts, x="performance_category", y="count", color="performance_category",
        title="Performance Category Distribution",
    )
    fig.update_layout(showlegend=False)
    return _apply_theme(fig)


def student_score_radar(row):
    categories = ["Math", "Science", "Programming", "English", "Assignment", "Internal", "Final Exam"]
    values = [
        row["math_score"], row["science_score"], row["programming_score"],
        row["english_score"], row["assignment_score"], row["internal_score"],
        row["final_exam_score"],
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill="toself", name=row["name"]))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=f"Score Profile — {row['name']}", showlegend=False,
    )
    return _apply_theme(fig)
