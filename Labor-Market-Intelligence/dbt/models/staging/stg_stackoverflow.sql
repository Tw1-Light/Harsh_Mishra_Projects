{{
  config(materialized='view')
}}

-- stg_stackoverflow.sql
-- One row per respondent per technology they have worked with.
-- Explodes the semicolon-delimited multi-value columns into individual rows.
-- Source: raw/stackoverflow/filtered_survey.parquet

with raw as (
    select * from read_parquet(
        '{{ env_var("PROJECT_ROOT", "..") }}/raw/stackoverflow/filtered_survey.parquet'
    )
),

tech_columns as (
    -- Unnest each tech column category independently, tag with category
    select
        "ResponseId"                        as respondent_id,
        'language'                          as tech_category,
        trim(tech)                          as technology_raw
    from raw,
    unnest(string_split(coalesce("LanguageHaveWorkedWith", ''), ';')) as t(tech)
    where trim(tech) != ''

    union all

    select
        "ResponseId"                        as respondent_id,
        'database'                          as tech_category,
        trim(tech)                          as technology_raw
    from raw,
    unnest(string_split(coalesce("DatabaseHaveWorkedWith", ''), ';')) as t(tech)
    where trim(tech) != ''

    union all

    select
        "ResponseId"                        as respondent_id,
        'webframe'                          as tech_category,
        trim(tech)                          as technology_raw
    from raw,
    unnest(string_split(coalesce("WebframeHaveWorkedWith", ''), ';')) as t(tech)
    where trim(tech) != ''

    union all

    select
        "ResponseId"                        as respondent_id,
        'platform'                          as tech_category,
        trim(tech)                          as technology_raw
    from raw,
    unnest(string_split(coalesce("PlatformHaveWorkedWith", ''), ';')) as t(tech)
    where trim(tech) != ''
)

select
    respondent_id,
    tech_category,
    technology_raw,
    -- Natural key: respondent + category + technology
    respondent_id || '|' || tech_category || '|' || technology_raw as record_id
from tech_columns
