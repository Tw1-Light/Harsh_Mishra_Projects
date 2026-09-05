{{
  config(materialized='table')
}}

-- dim_technology.sql
-- One row per canonical technology — the technology dimension table.
-- Joins SO Survey, emerging_tech, and GitHub slug info.

with crosswalk as (
    select * from {{ ref('int_tech_crosswalk') }}
),

github_snaps as (
    select distinct technology_name
    from {{ ref('stg_github_snapshots') }}
),

-- Distinct canonical technologies observed across any source
all_techs as (
    select distinct canonical_name, github_slug, adzuna_keyword, source
    from crosswalk
    where canonical_name is not null
),

-- Aggregate: a tech may appear in multiple source entries; collapse to one row
deduped as (
    select
        canonical_name,
        -- Take first non-null github_slug
        max(github_slug)        as github_slug,
        max(adzuna_keyword)     as adzuna_keyword,
        -- Tag as emerging if it came from emerging_tech (non-exclusive)
        max(case when source = 'emerging_tech' then true else false end) as is_emerging
    from all_techs
    group by canonical_name
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['canonical_name']) }} as tech_id,
        canonical_name,
        github_slug,
        adzuna_keyword,
        is_emerging,
        -- Is there actual GitHub snapshot data for this tech?
        case when gs.technology_name is not null then true else false end as has_github_data
    from deduped d
    left join github_snaps gs
        on lower(d.canonical_name) = lower(gs.technology_name)
)

select * from final
