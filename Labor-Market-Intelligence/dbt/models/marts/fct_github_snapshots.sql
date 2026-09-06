{{
  config(materialized='table')
}}

-- fct_github_snapshots.sql
-- Materializes snapshot metrics as a proper table so the dashboard
-- can query it from MotherDuck without needing local parquet files.

select
    technology_name,
    snapshot_date,
    observed_repositories,
    usable_repositories,
    median_stars,
    median_forks,
    active_repository_ratio,
    top1_star_concentration,
    top5_star_concentration,
    new_to_top100_ratio,
    usable_ratio
from {{ ref('stg_github_snapshots') }}
