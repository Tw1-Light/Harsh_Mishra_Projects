"""
app.py — Labor Market Intelligence Dashboard
Streamlit app answering: which skills are rising in real demand vs. ecosystem hype?

Run:
    streamlit run dashboard/app.py
"""

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent
_DB_PATH   = _REPO_ROOT / "labor_market.duckdb"
_PROJECT_ROOT = str(_REPO_ROOT)

st.set_page_config(
    page_title="Labor Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Loading data...")
def load_data() -> pd.DataFrame:
    """Load fct_skill_signals — local DuckDB in dev, MotherDuck in prod."""
    # st.secrets.get() throws if secrets file is missing; use try/except
    try:
        md_token = st.secrets["MotherDuck_token"]
    except Exception:
        md_token = os.getenv("MotherDuck_token", "")

    if _DB_PATH.exists():
        con = duckdb.connect(str(_DB_PATH), read_only=True)
    elif md_token:
        con = duckdb.connect(f"md:labor_market?motherduck_token={md_token}")
    else:
        st.error("No local DuckDB found and no MotherDuck_token set.")
        st.stop()

    df = con.execute("""
        SELECT
            canonical_name,
            signal_week,
            weekly_job_count,
            so_adoption_pct,
            gh_usable_repos,
            gh_median_stars,
            gh_active_ratio,
            gh_top5_concentration,
            composite_signal
        FROM main_marts.fct_skill_signals
        ORDER BY canonical_name, signal_week
    """).df()
    con.close()
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_snapshots() -> pd.DataFrame:
    try:
        md_token = st.secrets["MotherDuck_token"]
    except Exception:
        md_token = os.getenv("MotherDuck_token", "")
    if _DB_PATH.exists():
        con = duckdb.connect(str(_DB_PATH), read_only=True)
    elif md_token:
        con = duckdb.connect(f"md:labor_market?motherduck_token={md_token}")
    else:
        return pd.DataFrame()
    df = con.execute("""
        SELECT *
        FROM main_staging.stg_github_snapshots
        ORDER BY technology_name, snapshot_date
    """).df()
    con.close()
    return df


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("⚙️ Filters")

df = load_data()
snaps = load_snapshots()

techs = sorted(df["canonical_name"].unique())
selected_techs = st.sidebar.multiselect(
    "Technologies",
    options=techs,
    default=techs[:6] if len(techs) >= 6 else techs,
)

signal_filter = st.sidebar.multiselect(
    "Composite Signal",
    options=["thriving", "demand_led", "hype_led", "weak"],
    default=["thriving", "demand_led", "hype_led", "weak"],
)

# Apply filters
filtered = df[
    df["canonical_name"].isin(selected_techs) &
    df["composite_signal"].isin(signal_filter)
]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📊 Labor Market Intelligence")
st.markdown(
    "**Which skills are rising in real employer demand vs. rising in developer ecosystem hype?**  \n"
    "Combining Adzuna job postings (employer demand), GitHub ecosystem signals (developer attention), "
    "and Stack Overflow Survey (adoption baseline)."
)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Technologies tracked", len(techs))
col2.metric("Job postings analyzed", f"{df['weekly_job_count'].sum():,}")
col3.metric("GitHub snapshots", len(snaps))
col4.metric(
    "Thriving techs",
    len(df[df["composite_signal"] == "thriving"]["canonical_name"].unique())
)

st.divider()

# ---------------------------------------------------------------------------
# Composite signal overview
# ---------------------------------------------------------------------------
st.subheader("📌 Signal Overview — Demand vs. Ecosystem")

signal_colors = {
    "thriving":   "#22c55e",
    "demand_led": "#3b82f6",
    "hype_led":   "#f59e0b",
    "weak":       "#6b7280",
}

signal_labels = {
    "thriving":   "Jobs ↑ + GitHub ↑",
    "demand_led": "Jobs ↑ + GitHub ↓",
    "hype_led":   "Jobs ↓ + GitHub ↑",
    "weak":       "Jobs ↓ + GitHub ↓",
}

# Latest signal per tech
latest = (
    filtered.sort_values("signal_week")
    .groupby("canonical_name")
    .last()
    .reset_index()
)

if latest.empty:
    st.info("No data for selected filters.")
else:
    # Bubble chart: x=job_count, y=gh_usable_repos, color=signal, size=so_adoption
    import plotly.express as px

    latest["signal_label"] = latest["composite_signal"].map(signal_labels)
    latest["so_size"] = latest["so_adoption_pct"].fillna(1).clip(lower=1)

    fig = px.scatter(
        latest,
        x="weekly_job_count",
        y="gh_usable_repos",
        color="signal_label",
        size="so_size",
        hover_name="canonical_name",
        color_discrete_map={v: signal_colors[k] for k, v in signal_labels.items()},
        labels={
            "weekly_job_count":  "Weekly Job Postings (Adzuna)",
            "gh_usable_repos":   "Usable GitHub Repos (Top 100)",
            "signal_label":      "Signal",
            "so_size":           "SO Adoption %",
        },
        title="Demand vs. Ecosystem Signal per Technology",
        height=500,
    )
    fig.update_layout(
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font_color="#f1f5f9",
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Weekly job trend (Adzuna)
# ---------------------------------------------------------------------------
st.subheader("📈 Weekly Job Postings by Technology (Adzuna)")

if not filtered.empty:
    pivot = filtered.pivot_table(
        index="signal_week", columns="canonical_name",
        values="weekly_job_count", aggfunc="sum"
    ).fillna(0)

    fig2 = px.line(
        pivot, height=400,
        labels={"value": "Job Count", "signal_week": "Week", "canonical_name": "Technology"},
        title="Employer Demand Over Time",
    )
    fig2.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#f1f5f9"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# GitHub ecosystem signals
# ---------------------------------------------------------------------------
st.subheader("🔭 GitHub Ecosystem Signals")

snap_filtered = snaps[snaps["technology_name"].isin(selected_techs)]

if not snap_filtered.empty:
    col_a, col_b = st.columns(2)

    with col_a:
        fig3 = px.bar(
            snap_filtered,
            x="technology_name", y="usable_repositories",
            color="technology_name",
            title="Usable Repositories (after quality filter)",
            labels={"usable_repositories": "Usable Repos", "technology_name": "Technology"},
            height=350,
        )
        fig3.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#f1f5f9",
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        fig4 = px.bar(
            snap_filtered,
            x="technology_name", y="active_repository_ratio",
            color="technology_name",
            title="Active Repository Ratio (pushed within 180 days)",
            labels={"active_repository_ratio": "Active Ratio", "technology_name": "Technology"},
            height=350,
        )
        fig4.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#f1f5f9",
            showlegend=False, yaxis_tickformat=".0%",
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("**Star Concentration — are ecosystems concentrated in a few flagship projects?**")
    fig5 = px.bar(
        snap_filtered,
        x="technology_name",
        y=["top1_star_concentration", "top5_star_concentration"],
        barmode="group",
        title="Top-1 and Top-5 Star Concentration",
        labels={"value": "Concentration", "technology_name": "Technology"},
        height=350,
    )
    fig5.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#f1f5f9",
        yaxis_tickformat=".0%",
    )
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Data table
# ---------------------------------------------------------------------------
with st.expander("📋 Raw Signal Data"):
    st.dataframe(
        filtered[["canonical_name", "signal_week", "weekly_job_count",
                   "so_adoption_pct", "gh_usable_repos", "gh_median_stars",
                   "gh_active_ratio", "composite_signal"]]
        .sort_values(["canonical_name", "signal_week"]),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    "---\n"
    "*Data sources: Adzuna India API (employer demand) · "
    "GitHub Repository Search (ecosystem signal) · "
    "Stack Overflow Developer Survey 2024 (adoption baseline)*  \n"
    "*GitHub stars ≠ adoption. They measure developer attention around representative projects.*"
)
