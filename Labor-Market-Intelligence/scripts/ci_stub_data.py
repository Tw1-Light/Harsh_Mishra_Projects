"""
ci_stub_data.py
---------------
Creates minimal stub parquet/csv files in CI where real raw data doesn't exist.
Only used by the GitHub Actions workflow — not for local development.

Produces schema-compatible stubs so dbt run + dbt test work in CI
with zero real data (structural validation only).
"""

import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
RAW  = ROOT / "raw"

# ---------------------------------------------------------------------------
# SO Survey stub
# ---------------------------------------------------------------------------
so_path = RAW / "stackoverflow" / "filtered_survey.parquet"
so_path.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame({
    "ResponseId":               ["R1", "R2"],
    "LanguageHaveWorkedWith":   ["Python;JavaScript", "Python;SQL"],
    "LanguageWantToWorkWith":   ["Python", "TypeScript"],
    "DatabaseHaveWorkedWith":   ["PostgreSQL", "MySQL"],
    "DatabaseWantToWorkWith":   [None, "PostgreSQL"],
    "WebframeHaveWorkedWith":   ["React", "FastAPI"],
    "WebframeWantToWorkWith":   ["FastAPI", "React"],
    "PlatformHaveWorkedWith":   ["Docker", None],
    "PlatformWantToWorkWith":   ["Docker", "Docker"],
}).to_parquet(so_path, index=False)

# ---------------------------------------------------------------------------
# Adzuna stub
# ---------------------------------------------------------------------------
az_path = RAW / "adzuna" / "adzuna_extracted.csv"
az_path.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame({
    "id":           ["1001", "1002"],
    "created_date": ["2026-07-19", "2026-07-20"],
    "title":        ["Python Engineer", "React Developer"],
    "location":     ["Bangalore, Karnataka", "Mumbai, Maharashtra"],
    "technologies": ["PYTHON,SQL", "REACT,JAVASCRIPT"],
}).to_csv(az_path, index=False)

# ---------------------------------------------------------------------------
# GitHub stubs
# ---------------------------------------------------------------------------
snap_date = "2026-09-05"
for slug, name in [("python", "Python"), ("javascript", "JavaScript"), ("react", "React")]:
    repo_dir = RAW / "github" / snap_date / "repos"
    snap_dir = RAW / "github" / snap_date / "snapshots"
    repo_dir.mkdir(parents=True, exist_ok=True)
    snap_dir.mkdir(parents=True, exist_ok=True)

    repos = [
        {
            "id": i, "full_name": f"org/repo{i}", "name": f"repo{i}",
            "description": f"A {name} project",
            "language": name, "stargazers_count": 1000 * i,
            "forks_count": 100 * i, "topics": [slug],
            "fork": False, "archived": False, "disabled": False,
            "created_at": "2022-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "pushed_at":  "2026-08-01T00:00:00Z",
            "hard_excluded": False, "exclude_reason": None,
            "quality_class": "project", "quality_score": -2.5,
            "relevance_score": 4.0, "is_usable": True,
        }
        for i in range(1, 11)
    ]
    with open(repo_dir / f"{slug}.json", "w") as f:
        json.dump(repos, f)

    snap = {
        "technology": name, "snapshot_date": snap_date,
        "observed_repositories": 100, "usable_repositories": 10,
        "median_stars": 5000.0, "median_forks": 500.0,
        "active_repository_ratio": 0.8,
        "top1_star_concentration": 0.15,
        "top5_star_concentration": 0.45,
        "new_to_top100_ratio": None,
    }
    with open(snap_dir / f"{slug}.json", "w") as f:
        json.dump(snap, f)

# Re-run prepare_raw to build parquets from stubs
import subprocess, sys
subprocess.run([sys.executable, str(RAW / "prepare_raw.py")], check=True)
print("CI stub data prepared.")
