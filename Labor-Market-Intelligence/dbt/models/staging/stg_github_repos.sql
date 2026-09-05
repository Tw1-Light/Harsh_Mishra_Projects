{{
  config(materialized='view')
}}

-- stg_github_repos.sql
-- One row per repository per technology per snapshot date.
-- Includes quality classification and relevance score.
-- Source: raw/github/all_repos.parquet (built by raw/prepare_raw.py)

with raw as (
    select * from read_parquet(
        '{{ env_var("PROJECT_ROOT", "..") }}/raw/github/all_repos.parquet'
    )
)

select
    -- Identity
    cast(id as varchar)                     as repo_id,
    full_name,
    name                                    as repo_name,
    _technology_slug                        as technology_slug,
    cast(_snapshot_date as date)            as snapshot_date,

    -- Repo metadata
    description,
    language,
    cast(stargazers_count as integer)       as stars,
    cast(forks_count as integer)            as forks,
    cast(created_at as timestamptz)         as repo_created_at,
    cast(updated_at as timestamptz)         as repo_updated_at,
    cast(pushed_at as timestamptz)          as last_pushed_at,

    -- Flags
    cast(coalesce(fork, false) as boolean)      as is_fork,
    cast(coalesce(archived, false) as boolean)  as is_archived,
    cast(coalesce(disabled, false) as boolean)  as is_disabled,

    -- Classification
    cast(coalesce(hard_excluded, false) as boolean) as hard_excluded,
    exclude_reason,
    quality_class,
    cast(quality_score as double)           as quality_score,
    cast(relevance_score as double)         as relevance_score,
    cast(coalesce(is_usable, false) as boolean) as is_usable,

    -- Natural key
    cast(id as varchar) || '|' || _technology_slug || '|' || _snapshot_date as record_id

from raw
where id is not null
