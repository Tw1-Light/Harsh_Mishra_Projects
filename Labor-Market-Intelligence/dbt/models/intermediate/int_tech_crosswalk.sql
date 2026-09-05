{{
  config(materialized='table')
}}

-- int_tech_crosswalk.sql
-- Maps raw technology strings from each source to a canonical name.
--
-- Design decision (logged here per instructions.md):
--   Approach: exact match via the pre-built tech_dimension_table.json crosswalk.
--   Rationale: the dimension table was constructed with manual overrides (github_override.json)
--   and slug resolution — it already encodes the hard judgment calls (C++ -> cpp, Node.js -> nodejs).
--   Fuzzy matching was rejected because for this dataset (known tech names from SO Survey),
--   exact match on a pre-validated list produces zero confidently-wrong matches.
--   Fuzzy matching would be appropriate for free-text Adzuna titles; we instead
--   keyword-match on the uppercase tech list (already done in build_adzuna_csv.py).
--   Unmatched SO techs are retained with canonical_name = technology_raw so they
--   surface in the dashboard rather than silently disappearing.
--
-- Sources joined:
--   so_survey    -> StackOverflow column (exact name)
--   adzuna       -> Adzuna column (uppercase keyword)
--   github       -> Github_Topic slug
--   emerging     -> canonical_name + aliases

with dim as (
    select * from read_json_auto(
        '{{ env_var("PROJECT_ROOT", "..") }}/raw/tech_dimension_table.json',
        format = 'array'
    )
),

emerging_raw as (
    select
        j.canonical_name,
        j.github_topic,
        j.category,
        j.status
    from read_json_auto(
        '{{ env_var("PROJECT_ROOT", "..") }}/raw/emerging_tech.json'
    ) e,
    unnest(e.technologies) as t(j)
    where j.status = 'active'
),

-- SO Survey → canonical mapping
so_map as (
    select
        "StackOverflow"         as raw_name,
        'so_survey'             as source,
        "StackOverflow"         as canonical_name,
        "Github_Topic"          as github_slug,
        upper("StackOverflow")  as adzuna_keyword,
        null                    as category
    from dim
),

-- Emerging tech → canonical mapping
emerging_map as (
    select
        canonical_name          as raw_name,
        'emerging_tech'         as source,
        canonical_name,
        github_topic            as github_slug,
        upper(canonical_name)   as adzuna_keyword,
        category
    from emerging_raw
),

-- Adzuna keyword reverse lookup (so Adzuna rows can join to canonical)
-- Adzuna keywords are already uppercased tech names from dim table
adzuna_map as (
    select
        upper("StackOverflow")  as raw_name,
        'adzuna'                as source,
        "StackOverflow"         as canonical_name,
        "Github_Topic"          as github_slug,
        upper("StackOverflow")  as adzuna_keyword,
        null                    as category
    from dim
    where "Github_Topic" is not null
),

all_mappings as (
    select * from so_map
    union all
    select * from emerging_map
    union all
    select * from adzuna_map
),

-- Deduplicate: prefer emerging_tech entry when slug appears in both
deduped as (
    select
        raw_name,
        source,
        canonical_name,
        github_slug,
        adzuna_keyword,
        category,
        row_number() over (
            partition by lower(canonical_name)
            order by
                case source
                    when 'emerging_tech' then 1
                    when 'so_survey'     then 2
                    when 'adzuna'        then 3
                    else 4
                end
        ) as rn
    from all_mappings
)

select
    raw_name,
    source,
    canonical_name,
    github_slug,
    adzuna_keyword,
    category,
    -- Flag unresolved: kept for observability, not silently dropped
    (github_slug is null)   as is_unresolved
from deduped
where rn = 1
