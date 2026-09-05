{{
  config(materialized='view')
}}

-- stg_github_snapshots.sql
-- One row per technology per snapshot date — ecosystem-level metrics.
-- Source: raw/github/all_snapshots.parquet (built by raw/prepare_raw.py)

with raw as (
    select * from read_parquet(
        '{{ env_var("PROJECT_ROOT", "..") }}/raw/github/all_snapshots.parquet'
    )
)

select
    technology                                      as technology_name,
    cast(snapshot_date as date)                     as snapshot_date,

    cast(observed_repositories as integer)          as observed_repositories,
    cast(usable_repositories as integer)            as usable_repositories,

    cast(median_stars as double)                    as median_stars,
    cast(median_forks as double)                    as median_forks,

    cast(active_repository_ratio as double)         as active_repository_ratio,
    cast(top1_star_concentration as double)         as top1_star_concentration,
    cast(top5_star_concentration as double)         as top5_star_concentration,
    cast(new_to_top100_ratio as double)             as new_to_top100_ratio,

    -- Derived: filter ratio measures how many repos survived quality/relevance check
    case
        when observed_repositories > 0
        then cast(usable_repositories as double) / observed_repositories
        else null
    end                                             as usable_ratio,

    -- Natural key
    technology || '|' || cast(snapshot_date as varchar) as record_id

from raw
where technology is not null
  and snapshot_date is not null
