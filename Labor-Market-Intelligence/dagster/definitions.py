"""
definitions.py
--------------
Dagster Definitions — the single entry point for all assets, jobs, schedules, and resources.

Run the Dagster UI:
    dagster dev -f dagster/definitions.py
"""

import os
from pathlib import Path

from dagster import (
    Definitions,
    EnvVar,
    ScheduleDefinition,
    load_assets_from_modules,
)
from dagster_dbt import DbtCliResource

from dagster.assets import raw_assets, dbt_assets as dbt_assets_module
from dagster.assets.raw_assets import (
    daily_extraction_job,
    monthly_github_job,
    annual_so_job,
)
from dagster.assets.dbt_assets import labor_market_dbt_assets, dbt_project

_REPO_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
raw = load_assets_from_modules([raw_assets])

all_assets = [*raw, labor_market_dbt_assets]

# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------
# Adzuna: daily at 02:00 IST (20:30 UTC previous day)
daily_schedule = ScheduleDefinition(
    job=daily_extraction_job,
    cron_schedule="30 20 * * *",
    name="daily_adzuna_extraction",
)

# GitHub: first day of each month at 03:00 IST (21:30 UTC previous day)
monthly_schedule = ScheduleDefinition(
    job=monthly_github_job,
    cron_schedule="30 21 1 * *",
    name="monthly_github_snapshot",
)

# SO Survey: annual (manual trigger only — add cron if you want auto-refresh)

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------
dbt_resource = DbtCliResource(
    project_dir=str(dbt_project.project_dir),
    profiles_dir=str(dbt_project.project_dir),
    target="dev",
)

# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------
defs = Definitions(
    assets=all_assets,
    jobs=[daily_extraction_job, monthly_github_job, annual_so_job],
    schedules=[daily_schedule, monthly_schedule],
    resources={
        "dbt": dbt_resource,
    },
)
