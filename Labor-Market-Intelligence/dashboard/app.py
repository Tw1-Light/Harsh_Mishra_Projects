"""
app.py — Labor Market Intelligence Dashboard
Design: matches dashboard_design/ — editorial, monospace, light theme
4 tabs: Overview | Technology Explorer | Signal Map | Methodology
"""

import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Config ──────────────────────────────────────────────────────────────────
_REPO_ROOT    = Path(__file__).parent.parent
_DB_PATH      = _REPO_ROOT / "labor_market.duckdb"
_PROJECT_ROOT = str(_REPO_ROOT)

st.set_page_config(
    page_title="Labor Market Intelligence",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS: editorial light theme ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #fbfbfa;
    color: #171717;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #d4d4ce; border-radius: 3px; }

/* Metric cards */
.kpi-card {
    background: white;
    border: 1px solid #e5e5df;
    border-radius: 4px;
    padding: 16px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    color: #171717;
    letter-spacing: -0.5px;
}
.kpi-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #52524d;
    margin-top: 4px;
}
.kpi-sub {
    font-size: 11px;
    color: #787870;
    margin-top: 2px;
}

/* Signal badges */
.badge-thriving  { background:#dcfce7; color:#166534; border:1px solid #bbf7d0; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:600; padding:2px 7px; border-radius:3px; letter-spacing:.05em; }
.badge-demand    { background:#dbeafe; color:#1e40af; border:1px solid #bfdbfe; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:600; padding:2px 7px; border-radius:3px; letter-spacing:.05em; }
.badge-hype      { background:#fef3c7; color:#92400e; border:1px solid #fde68a; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:600; padding:2px 7px; border-radius:3px; letter-spacing:.05em; }
.badge-weak      { background:#f3f4f6; color:#6b7280; border:1px solid #e5e7eb; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:600; padding:2px 7px; border-radius:3px; letter-spacing:.05em; }

/* Section headers */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #73736c;
    margin-bottom: 3px;
}
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #171717;
    letter-spacing: -0.3px;
    margin-bottom: 6px;
}
.section-desc {
    font-size: 13px;
    color: #575752;
    line-height: 1.6;
}

/* Data table */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}
.data-table th {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #73736c;
    font-weight: 500;
    border-bottom: 1px solid #e5e5df;
    padding: 6px 0;
}
.data-table td {
    padding: 7px 0;
    border-bottom: 1px solid #f5f5f0;
    color: #171717;
}
.data-table tr:hover td { background: #fbfbfa; }

/* Inspector panel */
.inspector-box {
    background: white;
    border: 1px solid #e5e5df;
    border-radius: 4px;
    padding: 16px;
}
.inspector-metric-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 4px 0;
}
.inspector-metric-label { color: #73736c; }
.inspector-metric-value { font-weight: 700; color: #171717; }

/* Freshness pill */
.freshness-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f4f4f0; border: 1px solid #e2e2dc; border-radius: 3px;
    padding: 2px 8px; font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: #52524d;
}
.dot-green  { display:inline-block; width:7px; height:7px; border-radius:50%; background:#16a34a; }
.dot-blue   { display:inline-block; width:7px; height:7px; border-radius:50%; background:#2563eb; }
.dot-stone  { display:inline-block; width:7px; height:7px; border-radius:50%; background:#78716c; }

/* Methodology blocks */
.method-card {
    background: white; border: 1px solid #e5e5df; border-radius: 4px;
    padding: 16px; height: 100%;
}
.method-card-title { font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:#171717; }
.method-card-cadence { font-family:'JetBrains Mono',monospace; font-size:10px; color:#73736c; background:#f4f4f0; padding:2px 6px; border-radius:2px; }

/* Divergence cards */
.div-demand { background:#f0f7ff; border:1px solid #bfdbfe; border-radius:4px; padding:10px 12px; }
.div-hype   { background:#fffbeb; border:1px solid #fde68a; border-radius:4px; padding:10px 12px; }
</style>
""", unsafe_allow_html=True)

# ── DB Connection ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Loading data...")
def load_signals() -> pd.DataFrame:
    try:
        md_token = st.secrets["MotherDuck_token"]
    except Exception:
        md_token = os.getenv("MotherDuck_token", "")

    if _DB_PATH.exists():
        con = duckdb.connect(str(_DB_PATH), read_only=True)
    elif md_token:
        con = duckdb.connect(f"md:labor_market?motherduck_token={md_token}")
    else:
        st.error("No data source found. Set MotherDuck_token in secrets.")
        st.stop()

    df = con.execute("""
        SELECT
            f.canonical_name,
            f.signal_week,
            f.weekly_job_count,
            f.so_adoption_pct,
            f.gh_usable_repos,
            f.gh_median_stars,
            f.gh_median_forks,
            f.gh_active_ratio,
            f.gh_top5_concentration,
            f.composite_signal,
            d.github_slug,
            d.adzuna_keyword,
            d.is_emerging
        FROM main_marts.fct_skill_signals f
        JOIN main_marts.dim_technology d ON f.tech_id = d.tech_id
        ORDER BY f.canonical_name, f.signal_week
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
        SELECT * FROM main_marts.fct_github_snapshots
        ORDER BY technology_name, snapshot_date
    """).df()
    con.close()
    return df


# ── Helpers ──────────────────────────────────────────────────────────────────
def badge_html(signal: str) -> str:
    m = {
        "thriving":   ("badge-thriving",  "THRIVING"),
        "demand_led": ("badge-demand",    "DEMAND-LED"),
        "hype_led":   ("badge-hype",      "HYPE-LED"),
        "weak":       ("badge-weak",      "WEAK"),
    }
    cls, lbl = m.get(signal.lower(), ("badge-weak", signal.upper()))
    return f'<span class="{cls}">{lbl}</span>'


def signal_color(signal: str) -> str:
    return {
        "thriving":   "#16a34a",
        "demand_led": "#2563eb",
        "hype_led":   "#d97706",
        "weak":       "#9ca3af",
    }.get(signal.lower(), "#9ca3af")


def quadrant_scatter(df_latest: pd.DataFrame, highlight: str = "all",
                     selected: str = None, height: int = 500) -> go.Figure:
    """Build the quadrant scatter plot."""
    fig = go.Figure()

    # Quadrant shading
    fig.add_shape(type="rect", x0=0, x1=5,  y0=30, y1=df_latest["gh_usable_repos"].max() + 5,
                  fillcolor="#fffbeb", opacity=0.4, line_width=0)
    fig.add_shape(type="rect", x0=5, x1=df_latest["weekly_job_count"].max() + 2, y0=0, y1=30,
                  fillcolor="#eff6ff", opacity=0.4, line_width=0)

    # Threshold lines
    fig.add_shape(type="line", x0=5, x1=5, y0=0, y1=df_latest["gh_usable_repos"].max() + 5,
                  line=dict(color="#d1d5db", width=1, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=df_latest["weekly_job_count"].max() + 2, y0=30, y1=30,
                  line=dict(color="#d1d5db", width=1, dash="dot"))

    # Quadrant labels
    max_x = df_latest["weekly_job_count"].max()
    max_y = df_latest["gh_usable_repos"].max()
    for label, x, y, color in [
        ("THRIVING", max_x * 0.85, max_y * 0.92, "#16a34a"),
        ("HYPE-LED",  1.5,          max_y * 0.92, "#d97706"),
        ("DEMAND-LED", max_x * 0.85, 5,           "#2563eb"),
        ("WEAK",       1.5,          5,            "#9ca3af"),
    ]:
        fig.add_annotation(x=x, y=y, text=label, showarrow=False,
                           font=dict(family="JetBrains Mono", size=9, color=color),
                           opacity=0.6)

    for signal, group in df_latest.groupby("composite_signal"):
        color = signal_color(signal)
        dim = highlight not in ("all", signal) and highlight != "divergence"
        if highlight == "divergence":
            dim = signal in ("thriving", "weak")

        for _, row in group.iterrows():
            is_sel = selected and row["canonical_name"] == selected
            size = 14 if is_sel else 9
            opacity = 0.15 if dim else (1.0 if is_sel else 0.75)
            fig.add_trace(go.Scatter(
                x=[row["weekly_job_count"]],
                y=[row["gh_usable_repos"]],
                mode="markers+text" if is_sel else "markers",
                marker=dict(
                    size=size, color=color, opacity=opacity,
                    line=dict(width=2 if is_sel else 0.5,
                              color="#171717" if is_sel else "white")
                ),
                text=[row["canonical_name"]] if is_sel else None,
                textposition="top center",
                textfont=dict(size=10, family="JetBrains Mono", color="#171717"),
                name=row["canonical_name"],
                hovertemplate=(
                    f"<b>{row['canonical_name']}</b><br>"
                    f"Jobs/week: {row['weekly_job_count']}<br>"
                    f"Usable repos: {row['gh_usable_repos']}<br>"
                    f"SO adoption: {row['so_adoption_pct']:.1f}%<br>"
                    f"Signal: <b>{badge_html(signal).replace('<','').replace('>','')}</b>"
                    "<extra></extra>"
                ),
                showlegend=False,
            ))

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="#fbfbfa",
        margin=dict(l=40, r=20, t=20, b=40),
        height=height,
        xaxis=dict(
            title="Weekly Job Postings (Adzuna India)",
            title_font=dict(family="JetBrains Mono", size=10, color="#73736c"),
            tickfont=dict(family="JetBrains Mono", size=10),
            gridcolor="#f0f0eb", zeroline=False,
            range=[-0.5, df_latest["weekly_job_count"].max() * 1.1 + 1],
        ),
        yaxis=dict(
            title="Usable GitHub Repositories (of Top 100)",
            title_font=dict(family="JetBrains Mono", size=10, color="#73736c"),
            tickfont=dict(family="JetBrains Mono", size=10),
            gridcolor="#f0f0eb", zeroline=False,
        ),
        hoverlabel=dict(font_family="JetBrains Mono", font_size=11,
                        bgcolor="white", bordercolor="#e5e5df"),
        dragmode="pan",
        font=dict(family="Inter"),
    )
    return fig


# ── Load Data ─────────────────────────────────────────────────────────────────
df_all    = load_signals()
df_snaps  = load_snapshots()

# Latest week per tech
df_latest = (
    df_all.sort_values("signal_week")
    .groupby("canonical_name")
    .last()
    .reset_index()
)

total_techs   = len(df_latest)
total_jobs    = int(df_all["weekly_job_count"].sum())
total_snaps   = len(df_snaps)
thriving_n    = int((df_latest["composite_signal"] == "thriving").sum())
latest_adzuna = str(df_all["signal_week"].max()) if not df_all.empty else "—"
latest_github = str(df_snaps["snapshot_date"].max()) if not df_snaps.empty else "—"


# ── App Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#fbfbfa; border-bottom:1px solid #e5e5df; padding:0 32px;">
  <div style="max-width:1400px; margin:0 auto;">
    <!-- Brand row -->
    <div style="display:flex; align-items:center; justify-content:space-between;
                padding:10px 0; border-bottom:1px solid #ecece8;">
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="display:inline-block; width:8px; height:8px; background:#171717; border-radius:2px;"></span>
        <span style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600;
                     text-transform:uppercase; letter-spacing:.1em; color:#171717;">
          Labor Market Intelligence
        </span>
        <span style="color:#a3a39e;">|</span>
        <span style="font-size:11px; color:#575752;">
          Technology demand vs developer ecosystem signals
        </span>
      </div>
      <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        <span class="freshness-pill"><span class="dot-green"></span>Adzuna: <strong>{latest_adzuna}</strong></span>
        <span class="freshness-pill"><span class="dot-blue"></span>GitHub: <strong>{latest_github}</strong></span>
        <span class="freshness-pill"><span class="dot-stone"></span>Stack Overflow: <strong>2024</strong></span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Navigation Tabs ───────────────────────────────────────────────────────────
tab_overview, tab_explorer, tab_signalmap, tab_methodology = st.tabs([
    "Overview",
    "Technology Explorer",
    "Signal Map",
    "Methodology",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
with tab_overview:
    st.markdown('<div style="max-width:1400px; margin:0 auto; padding:24px 32px 48px;">', unsafe_allow_html=True)

    # Header
    st.markdown(f"""
    <div style="border-bottom:1px solid #e5e5df; padding-bottom:20px; margin-bottom:24px;
                display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px;">
      <div>
        <div class="section-label">Research Briefing • Labor Market Intelligence</div>
        <div class="section-title">Technology demand vs developer ecosystem signals</div>
        <div class="section-desc" style="max-width:680px;">
          Synthesizing <strong>{total_jobs:,}</strong> observed IT employer job postings against
          Top-100 quality-classified GitHub repositories and 48K+ developer survey responses
          to distinguish genuine commercial hiring from ecosystem hype.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total_techs}</div><div class="kpi-label">Technologies tracked</div><div class="kpi-sub">Cross-referenced taxonomy</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">1,788</div><div class="kpi-label">Job postings</div><div class="kpi-sub">Adzuna India IT deduplicated</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">48K+</div><div class="kpi-label">Developer responses</div><div class="kpi-sub">Stack Overflow baseline</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">100</div><div class="kpi-label">GitHub repos sampled</div><div class="kpi-sub">Per technology, quality-scored</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # Signal Map preview
    st.markdown("""
    <div style="margin-bottom:6px;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
                  text-transform:uppercase; letter-spacing:.08em; color:#171717;">Technology Signal Map</div>
      <div style="font-size:12px; color:#666660; margin-top:2px;">
        Quadrants defined by Weekly Jobs (X = 5 threshold) vs Usable GitHub Repositories (Y = 30 threshold).
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(quadrant_scatter(df_latest, height=480), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Market Movement section — 3 columns
    st.markdown("""
    <div style="border-bottom:1px solid #e5e5df; padding-bottom:8px; margin-bottom:16px;">
      <div style="font-size:15px; font-weight:700; color:#171717; letter-spacing:-.2px;">Market Movement &amp; Analytical Divergence</div>
      <div style="font-size:12px; color:#666660; margin-top:2px;">Dissecting weekly employer requisitions against open-source repository traction</div>
    </div>
    """, unsafe_allow_html=True)

    col_demand, col_eco, col_div = st.columns(3)

    with col_demand:
        top_demand = df_latest.nlargest(6, "weekly_job_count")
        rows = ""
        for _, r in top_demand.iterrows():
            rows += f"""<tr>
              <td style="padding:7px 0; font-weight:600;">{r['canonical_name']}</td>
              <td style="padding:7px 0; text-align:right; font-weight:700;">{int(r['weekly_job_count'])}</td>
              <td style="padding:7px 0; text-align:right;">{badge_html(r['composite_signal'])}</td>
            </tr>"""
        st.markdown(f"""
        <div style="background:white; border:1px solid #e5e5df; border-radius:4px; padding:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ecece8; padding-bottom:10px; margin-bottom:12px;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Rising Employer Demand</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#73736c;">Adzuna Weekly</div>
          </div>
          <table class="data-table">
            <thead><tr>
              <th>Technology</th><th style="text-align:right">Jobs/wk</th><th style="text-align:right">Signal</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

    with col_eco:
        top_eco = df_latest.nlargest(6, "gh_usable_repos")
        rows2 = ""
        for _, r in top_eco.iterrows():
            stars_k = f"{r['gh_median_stars']/1000:.1f}K" if r['gh_median_stars'] >= 1000 else str(int(r['gh_median_stars']))
            rows2 += f"""<tr>
              <td style="padding:7px 0; font-weight:600;">{r['canonical_name']}</td>
              <td style="padding:7px 0; text-align:right; font-weight:700;">{int(r['gh_usable_repos'])}</td>
              <td style="padding:7px 0; text-align:right; color:#575752;">{stars_k}</td>
              <td style="padding:7px 0; text-align:right;">{int(r['gh_active_ratio']*100)}%</td>
            </tr>"""
        st.markdown(f"""
        <div style="background:white; border:1px solid #e5e5df; border-radius:4px; padding:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ecece8; padding-bottom:10px; margin-bottom:12px;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Ecosystem Attention</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#73736c;">GitHub Sample</div>
          </div>
          <table class="data-table">
            <thead><tr>
              <th>Technology</th><th style="text-align:right">Usable</th><th style="text-align:right">Stars</th><th style="text-align:right">Active</th>
            </tr></thead>
            <tbody>{rows2}</tbody>
          </table>
          <div style="margin-top:12px; padding-top:8px; border-top:1px solid #f0f0eb; font-family:'JetBrains Mono',monospace; font-size:10px; color:#787870;">
            Top 100 repositories sampled per technology
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_div:
        demand_led = df_latest[df_latest["composite_signal"] == "demand_led"].nlargest(2, "weekly_job_count")
        hype_led   = df_latest[df_latest["composite_signal"] == "hype_led"].nlargest(2, "gh_usable_repos")
        cards = ""
        for _, r in demand_led.iterrows():
            cards += f"""<div class="div-demand" style="margin-bottom:8px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700;">{r['canonical_name']}</span>
                {badge_html('demand_led')}
              </div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:11px; color:#4b5563; margin-top:3px;">
                {int(r['weekly_job_count'])} jobs/week &bull; {int(r['gh_usable_repos'])} usable repos
              </div>
              <div style="font-size:11px; color:#1e3a8a; margin-top:4px; line-height:1.5;">
                Strong hiring demand with comparatively limited ecosystem activity.
              </div>
            </div>"""
        for _, r in hype_led.iterrows():
            cards += f"""<div class="div-hype" style="margin-bottom:8px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700;">{r['canonical_name']}</span>
                {badge_html('hype_led')}
              </div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:11px; color:#4b5563; margin-top:3px;">
                {int(r['weekly_job_count'])} jobs/week &bull; {int(r['gh_usable_repos'])} usable repos
              </div>
              <div style="font-size:11px; color:#92400e; margin-top:4px; line-height:1.5;">
                Strong ecosystem attention without comparable observed hiring demand.
              </div>
            </div>"""
        st.markdown(f"""
        <div style="background:white; border:1px solid #e5e5df; border-radius:4px; padding:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ecece8; padding-bottom:10px; margin-bottom:12px;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Divergence Watch</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#73736c;">Signal Disagreement</div>
          </div>
          {cards}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — TECHNOLOGY EXPLORER
# ════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    st.markdown('<div style="max-width:1400px; margin:0 auto; padding:24px 32px 48px;">', unsafe_allow_html=True)

    st.markdown("""
    <div class="section-label">Full Dataset</div>
    <div class="section-title">Technology Explorer</div>
    <div class="section-desc" style="margin-bottom:20px;">
      Browse all tracked technologies. Each row combines Adzuna job demand, GitHub ecosystem signal, and Stack Overflow adoption baseline.
    </div>
    """, unsafe_allow_html=True)

    # Filters
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        sig_filter = st.multiselect(
            "Signal", ["thriving", "demand_led", "hype_led", "weak"],
            default=["thriving", "demand_led", "hype_led", "weak"],
            format_func=lambda x: x.replace("_", "-").upper(),
        )
    with fc2:
        search = st.text_input("Search technology", placeholder="e.g. Python, Docker…")
    with fc3:
        emerging_only = st.checkbox("Emerging only")

    df_filtered = df_latest.copy()
    if sig_filter:
        df_filtered = df_filtered[df_filtered["composite_signal"].isin(sig_filter)]
    if search:
        df_filtered = df_filtered[df_filtered["canonical_name"].str.contains(search, case=False)]
    if emerging_only:
        df_filtered = df_filtered[df_filtered["is_emerging"] == True]

    df_filtered = df_filtered.sort_values("weekly_job_count", ascending=False)

    # Table
    rows = ""
    for _, r in df_filtered.iterrows():
        stars_k = f"{r['gh_median_stars']/1000:.1f}K" if r['gh_median_stars'] >= 1000 else str(int(r['gh_median_stars']))
        so_pct  = f"{r['so_adoption_pct']:.1f}%" if pd.notna(r['so_adoption_pct']) else "—"
        act     = f"{int(r['gh_active_ratio']*100)}%" if pd.notna(r['gh_active_ratio']) else "—"
        emg     = '<span style="font-size:9px;background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:2px;padding:1px 5px;font-family:monospace;">NEW</span>' if r['is_emerging'] else ""
        rows += f"""<tr>
          <td style="padding:8px 0; font-weight:600;">{r['canonical_name']} {emg}</td>
          <td style="padding:8px 0; text-align:right; font-weight:700;">{int(r['weekly_job_count'])}</td>
          <td style="padding:8px 0; text-align:right;">{int(r['gh_usable_repos'])}</td>
          <td style="padding:8px 0; text-align:right; color:#575752;">{stars_k}</td>
          <td style="padding:8px 0; text-align:right;">{act}</td>
          <td style="padding:8px 0; text-align:right;">{so_pct}</td>
          <td style="padding:8px 0; text-align:right;">{badge_html(r['composite_signal'])}</td>
        </tr>"""

    st.markdown(f"""
    <div style="background:white; border:1px solid #e5e5df; border-radius:4px; padding:16px; overflow-x:auto;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#73736c; margin-bottom:8px;">
        {len(df_filtered)} technologies shown
      </div>
      <table class="data-table">
        <thead><tr>
          <th>Technology</th>
          <th style="text-align:right">Jobs/wk</th>
          <th style="text-align:right">GH Repos</th>
          <th style="text-align:right">Med. Stars</th>
          <th style="text-align:right">Active %</th>
          <th style="text-align:right">SO Adoption</th>
          <th style="text-align:right">Signal</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — SIGNAL MAP
# ════════════════════════════════════════════════════════════════════════════
with tab_signalmap:
    st.markdown('<div style="max-width:1400px; margin:0 auto; padding:24px 32px 48px;">', unsafe_allow_html=True)

    st.markdown("""
    <div class="section-label">Analytical Heart • Quadrant Decomposition</div>
    <div class="section-title">Signal Map</div>
    <div class="section-desc" style="margin-bottom:20px;">
      Where employer demand and developer ecosystem attention diverge.
      X = 5 jobs/week threshold, Y = 30 usable GitHub repositories threshold.
    </div>
    """, unsafe_allow_html=True)

    # View mode selector + filters
    sm_col1, sm_col2, sm_col3 = st.columns([3, 2, 1])
    with sm_col1:
        view_mode = st.radio(
            "View",
            ["divergence", "all", "thriving", "demand_led", "hype_led", "weak"],
            format_func=lambda x: {
                "divergence": "Divergence View",
                "all": "All Technologies",
                "thriving": "Thriving",
                "demand_led": "Demand-Led",
                "hype_led": "Hype-Led",
                "weak": "Weak",
            }[x],
            horizontal=True,
        )
    with sm_col2:
        sm_search = st.text_input("Highlight technology", placeholder="Type to highlight...", key="sm_search")
    with sm_col3:
        sm_emerging = st.checkbox("Emerging only", key="sm_emerging")

    if view_mode == "divergence":
        st.markdown("""
        <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:4px; padding:10px 14px;
                    font-size:12px; color:#1e40af; margin-bottom:12px;">
          <strong>Divergence Mode:</strong> Highlighting DEMAND-LED and HYPE-LED quadrants.
          Thriving and Weak are dimmed.
        </div>
        """, unsafe_allow_html=True)

    df_sm = df_latest.copy()
    if sm_emerging:
        df_sm = df_sm[df_sm["is_emerging"] == True]

    left_col, right_col = st.columns([8, 4])

    with left_col:
        selected_tech_name = sm_search if sm_search else None
        fig_sm = quadrant_scatter(df_sm, highlight=view_mode, selected=selected_tech_name, height=540)
        st.plotly_chart(fig_sm, use_container_width=True, config={"displayModeBar": False})

    with right_col:
        # Inspector panel — auto-populate from search or show most interesting divergence
        inspect_row = None
        if sm_search:
            match = df_sm[df_sm["canonical_name"].str.lower() == sm_search.lower()]
            if not match.empty:
                inspect_row = match.iloc[0]
        if inspect_row is None and not df_sm.empty:
            # Default: first hype-led or demand-led
            div = df_sm[df_sm["composite_signal"].isin(["hype_led", "demand_led"])]
            if not div.empty:
                inspect_row = div.iloc[0]
            else:
                inspect_row = df_sm.iloc[0]

        if inspect_row is not None:
            r = inspect_row
            jdir = "≥ 5 ↑" if r['weekly_job_count'] >= 5 else "< 5 ↓"
            gdir = "≥ 30 ↑" if r['gh_usable_repos'] >= 30 else "< 30 ↓"
            stars_k = f"{r['gh_median_stars']/1000:.1f}K" if r['gh_median_stars'] >= 1000 else str(int(r['gh_median_stars']))
            so_val = f"{r['so_adoption_pct']:.1f}%" if pd.notna(r['so_adoption_pct']) else "—"
            act_val = f"{int(r['gh_active_ratio']*100)}%" if pd.notna(r['gh_active_ratio']) else "—"

            st.markdown(f"""
            <div class="inspector-box">
              <div style="display:flex; justify-content:space-between; align-items:center;
                          border-bottom:1px solid #ecece8; padding-bottom:10px; margin-bottom:12px;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700;
                            text-transform:uppercase; letter-spacing:.08em; color:#73736c;">Technology Inspector</div>
              </div>
              <div style="margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div style="font-size:20px; font-weight:700; color:#171717; letter-spacing:-.3px;">{r['canonical_name']}</div>
                  {badge_html(r['composite_signal'])}
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:11px; color:#73736c; margin-top:4px;">
                  Adzuna keyword: <code style="color:#171717;">{r['adzuna_keyword']}</code>
                </div>
              </div>
              <div style="background:#fafaf8; border:1px solid #e8e8e2; border-radius:4px; padding:12px; margin-bottom:12px;">
                <div class="inspector-metric-row"><span class="inspector-metric-label">Employer Demand:</span><span class="inspector-metric-value">{int(r['weekly_job_count'])} jobs/week</span></div>
                <div class="inspector-metric-row"><span class="inspector-metric-label">GitHub Ecosystem:</span><span class="inspector-metric-value">{int(r['gh_usable_repos'])} usable repos</span></div>
                <div class="inspector-metric-row"><span class="inspector-metric-label">Stack Overflow:</span><span class="inspector-metric-value">{so_val}</span></div>
                <div class="inspector-metric-row"><span class="inspector-metric-label">Active Repositories:</span><span class="inspector-metric-value">{act_val}</span></div>
                <div class="inspector-metric-row"><span class="inspector-metric-label">Median Stars:</span><span class="inspector-metric-value">{stars_k}</span></div>
                <div class="inspector-metric-row"><span class="inspector-metric-label">Top-5 Star Conc.:</span><span class="inspector-metric-value">{r['gh_top5_concentration']:.1%}</span></div>
              </div>
              <div style="border-top:1px solid #d4d4ce; padding-top:10px;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:10px; text-transform:uppercase; color:#73736c; margin-bottom:4px;">Quadrant Signal Evaluation</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:13px; font-weight:700; color:#171717;">
                  Jobs {jdir} + Ecosystem {gdir} &rarr; {r['composite_signal'].replace('_','-').upper()}
                </div>
              </div>
              <div style="margin-top:12px; border-top:1px solid #ecece8; padding-top:12px; font-size:11px; color:#73736c; font-family:'JetBrains Mono',monospace;">
                GitHub topic: <a href="https://github.com/topics/{r['github_slug']}" target="_blank"
                  style="color:#2563eb; text-decoration:none;">github.com/topics/{r['github_slug']}</a>
              </div>
            </div>

            <!-- Divergence reference -->
            <div style="margin-top:12px; border-top:1px solid #ecece8; padding-top:12px; font-size:11px;">
              <div style="font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#171717; margin-bottom:8px;">Divergence Archetypes</div>
              <div class="div-demand" style="margin-bottom:6px; font-size:11px;">
                <strong>DEMAND-LED:</strong> High employer demand (Jobs &ge; 5) despite limited GitHub ecosystem (Repos &lt; 30). Common in enterprise backend and databases.
              </div>
              <div class="div-hype" style="font-size:11px;">
                <strong>HYPE-LED:</strong> High open-source attention (Repos &ge; 30) without comparable hiring (Jobs &lt; 5). Common in emerging AI tooling.
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — METHODOLOGY
# ════════════════════════════════════════════════════════════════════════════
with tab_methodology:
    st.markdown('<div style="max-width:900px; margin:0 auto; padding:24px 32px 48px;">', unsafe_allow_html=True)

    st.markdown("""
    <div class="section-label">Technical Specification &amp; Pipeline Architecture</div>
    <div class="section-title">How the signals are constructed</div>
    <div class="section-desc" style="margin-bottom:28px;">
      Rigorous methodology uniting annual survey baselines, daily observed hiring demand,
      and monthly quality-filtered open source ecosystem snapshots.
    </div>
    """, unsafe_allow_html=True)

    # 3-source pipeline
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
                text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid #ecece8;
                padding-bottom:8px; margin-bottom:16px; display:flex; justify-content:space-between;">
      <span>1. Three-Source Data Pipeline</span>
      <span style="font-weight:400; color:#73736c;">Orchestrated via dbt Core</span>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    for col, title, cadence, cadence_color, desc, metric_label in [
        (m1, "STACK OVERFLOW", "Annual", "#73736c", "48K+ global developer respondents establish the empirical developer adoption baseline and self-reported technology usage.", "Baseline: Developer Adoption %"),
        (m2, "ADZUNA IT INDIA", "Daily Extraction", "#047857", "Daily extraction of active IT employer postings deduplicated into ~1,788 current requisitions across tracked skill keywords.", "Metric: Weekly Job Postings"),
        (m3, "GITHUB SEARCH API", "Monthly Snapshot", "#1d4ed8", "Top-100 repository search per technology, quality-classified (project/educational/collection) and relevance-scored.", "Metric: Usable Repos (of 100)"),
    ]:
        with col:
            cadence_bg = "#f4f4f0" if cadence_color == "#73736c" else ("#ecfdf5" if cadence_color == "#047857" else "#eff6ff")
            st.markdown(f"""
            <div class="method-card">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span class="method-card-title">{title}</span>
                <span style="font-family:'JetBrains Mono',monospace; font-size:10px; color:{cadence_color};
                             background:{cadence_bg}; padding:2px 6px; border-radius:2px;">{cadence}</span>
              </div>
              <div style="font-size:13px; font-weight:600; color:#171717; margin-bottom:6px;">{title.title()}</div>
              <div style="font-size:12px; color:#575752; line-height:1.6;">{desc}</div>
              <div style="margin-top:12px; padding-top:8px; border-top:1px solid #f0f0eb;
                          font-family:'JetBrains Mono',monospace; font-size:10px; color:#73736c;">{metric_label}</div>
            </div>
            """, unsafe_allow_html=True)

    # GitHub quality classification
    st.markdown("""
    <div style="margin-top:28px; font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
                text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid #ecece8;
                padding-bottom:8px; margin-bottom:16px;">2. GitHub Quality Classification</div>
    <div style="background:white; border:1px solid #e5e5df; border-radius:4px; padding:16px; font-size:12px; color:#575752; line-height:1.7;">
      <p>Top-100 repositories per technology are classified into quality tiers using rule-based weighted scoring:</p>
      <ul style="margin:8px 0 8px 18px; space-y:4px;">
        <li><strong style="color:#171717;">Hard Exclusions:</strong> Fork, Archived, or Disabled repositories are excluded immediately.</li>
        <li><strong style="color:#171717;">Contamination Scoring:</strong> Negative weight keywords detect awesome-lists (+3.5), tutorial repos (+3.0), interview prep (+3.0), roadmaps (+2.0).</li>
        <li><strong style="color:#171717;">Positive Quality Bonus:</strong> Non-empty description (+1.5), topic tags present (+1.5), pushed within 180 days (+1.0), stars &gt; 500 (+0.5).</li>
        <li><strong style="color:#171717;">Relevance Scoring:</strong> Independent from quality. Language exact match (+4.0), topic exact match (+3.0), canonical name in repo name (+3.0). Threshold: ≥ 2.0 = usable.</li>
      </ul>
      <p>Result: A repository is <strong>usable</strong> if it is not hard-excluded, classified as <code>project</code> or <code>uncertain</code>, and has relevance_score ≥ 2.0.</p>
    </div>
    """, unsafe_allow_html=True)

    # Composite signal
    st.markdown("""
    <div style="margin-top:24px; font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
                text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid #ecece8;
                padding-bottom:8px; margin-bottom:16px;">3. Composite Signal Quadrant Matrix</div>
    """, unsafe_allow_html=True)

    q1, q2 = st.columns(2)
    for col, signal, bg, border, text_color, title, cond, meaning in [
        (q1, "THRIVING",   "#f0fdf4", "#bbf7d0", "#166534", "Thriving",   "Jobs ≥ 5 AND Repos ≥ 30", "Both employer demand and ecosystem are strong. High confidence skill investment."),
        (q2, "HYPE-LED",   "#fffbeb", "#fde68a", "#92400e", "Hype-Led",   "Jobs < 5 AND Repos ≥ 30", "Developer community attention without commercial hiring signal. Monitor, don't bet."),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {border}; border-radius:4px; padding:14px; margin-bottom:10px;">
              <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <strong style="color:{text_color}; font-family:'JetBrains Mono',monospace; font-size:11px;">{signal}</strong>
                <code style="font-family:'JetBrains Mono',monospace; font-size:10px; color:{text_color};">{cond}</code>
              </div>
              <div style="font-size:12px; color:#171717; font-weight:600; margin-bottom:4px;">{title}</div>
              <div style="font-size:11px; color:{text_color}; line-height:1.5;">{meaning}</div>
            </div>
            """, unsafe_allow_html=True)

    q3, q4 = st.columns(2)
    for col, signal, bg, border, text_color, title, cond, meaning in [
        (q3, "DEMAND-LED", "#eff6ff", "#bfdbfe", "#1e40af", "Demand-Led", "Jobs ≥ 5 AND Repos < 30", "Employers hiring despite limited open-source ecosystem. Often enterprise or legacy tech."),
        (q4, "WEAK",       "#f9fafb", "#e5e7eb", "#6b7280", "Weak",       "Jobs < 5 AND Repos < 30", "Low signal on both dimensions. Niche, deprecated, or outside dataset scope."),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {border}; border-radius:4px; padding:14px; margin-bottom:10px;">
              <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <strong style="color:{text_color}; font-family:'JetBrains Mono',monospace; font-size:11px;">{signal}</strong>
                <code style="font-family:'JetBrains Mono',monospace; font-size:10px; color:{text_color};">{cond}</code>
              </div>
              <div style="font-size:12px; color:#171717; font-weight:600; margin-bottom:4px;">{title}</div>
              <div style="font-size:11px; color:{text_color}; line-height:1.5;">{meaning}</div>
            </div>
            """, unsafe_allow_html=True)

    # Limitations
    st.markdown("""
    <div style="margin-top:24px; font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
                text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid #ecece8;
                padding-bottom:8px; margin-bottom:16px;">4. Known Limitations</div>
    <div style="background:white; border:1px solid #e5e5df; border-radius:4px; padding:16px;">
    <ul style="font-size:12px; color:#575752; line-height:1.8; margin:0; padding-left:18px;">
      <li><strong style="color:#171717;">Geography:</strong> Adzuna data is India-only. Global hiring demand is not represented.</li>
      <li><strong style="color:#171717;">Data volume:</strong> 1,788 Adzuna job postings across July 2026. Sufficient for signal demonstration, not production hiring analytics.</li>
      <li><strong style="color:#171717;">GitHub stars ≠ adoption.</strong> Stars measure developer attention around representative projects, not enterprise adoption.</li>
      <li><strong style="color:#171717;">Single GitHub snapshot:</strong> Month-over-month turnover ratio will populate after the second monthly run.</li>
      <li><strong style="color:#171717;">Entity resolution:</strong> Exact match on pre-validated crosswalk. Technologies with non-standard naming may be unresolved.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # dbt stack
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
                text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid #ecece8;
                padding-bottom:8px; margin-bottom:16px;">5. Data Mart Schema</div>
    <div style="background:#fafaf8; border:1px solid #e5e5df; border-radius:4px; padding:14px;
                font-family:'JetBrains Mono',monospace; font-size:11px; color:#171717; line-height:1.9;">
      <div><strong>main_marts.fct_skill_signals</strong> — Grain: canonical technology × week</div>
      <div style="color:#73736c; padding-left:16px;">weekly_job_count, so_adoption_pct, gh_usable_repos, gh_median_stars, gh_active_ratio, gh_top5_concentration, composite_signal</div>
      <div style="margin-top:8px;"><strong>main_marts.dim_technology</strong> — Canonical technology dimension</div>
      <div style="color:#73736c; padding-left:16px;">tech_id (MD5), canonical_name, github_slug, adzuna_keyword, is_emerging</div>
      <div style="margin-top:8px;"><strong>main_marts.fct_github_snapshots</strong> — Monthly ecosystem metrics</div>
      <div style="color:#73736c; padding-left:16px;">technology_name, snapshot_date, observed_repositories, usable_repositories, median_stars, active_repository_ratio, top5_star_concentration</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="border-top:1px solid #e5e5df; background:#f5f5f0; padding:20px 32px;
            font-family:'JetBrains Mono',monospace; font-size:11px; color:#73736c;">
  <div style="max-width:1400px; margin:0 auto; display:flex; flex-wrap:wrap;
              justify-content:space-between; align-items:center; gap:12px;">
    <div>
      <div style="font-weight:600; color:#171717; margin-bottom:3px;">
        Labor Market Intelligence &bull; Analytical Research Dashboard
      </div>
      <div style="font-size:10px; color:#85857e;">
        Data Marts: <code style="color:#171717;">fct_skill_signals</code> &nbsp;
        <code style="color:#171717;">dim_technology</code> &nbsp;
        <code style="color:#171717;">fct_github_snapshots</code>
      </div>
    </div>
    <div style="display:flex; flex-wrap:wrap; gap:16px; font-size:10px; align-items:center;">
      <span>Adzuna India IT: <strong style="color:#171717;">{latest_adzuna}</strong></span>
      <span>&bull;</span>
      <span>GitHub Snapshot: <strong style="color:#171717;">{latest_github}</strong></span>
      <span>&bull;</span>
      <span>Stack Overflow: <strong style="color:#171717;">2024</strong></span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
