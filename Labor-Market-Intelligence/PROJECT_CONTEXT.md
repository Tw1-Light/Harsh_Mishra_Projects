# SYSTEM CONTEXT & KNOWLEDGE BASE: Labor-Market Intelligence Pipeline
<!--
================================================================================
LLM INGESTION NOTICE:
This document is specifically structured for ingestion by Large Language Models (LLMs).
It serves as an exhaustive, self-contained system prompt and knowledge repository.
An LLM provided with this document has complete context to answer questions, debug,
mentor, write compatible code, formulate SQL, and enforce project constraints without
requiring file system access or external tool calls.
================================================================================
-->

<SYSTEM_METADATA>
Project_Name: "Labor-Market Intelligence Pipeline"
Repository_Path: "Harsh_Mishra_Projects/Labor-Market-Intelligence"
Git_Remote: "https://github.com/Tw1-Light/Harsh_Mishra_Projects.git"
Developer: "Harsh Mishra (Final-year CS student, AI/ML specialization)"
Target_Career_Track: "Data Engineering / Analytics Engineering"
Target_Database: "DuckDB (local dev) / MotherDuck (cloud prod)"
Orchestration_Engine: "Dagster (Software-Defined Assets)"
Transformation_Engine: "dbt (dbt-core + dbt-duckdb v1.11+)"
Presentation_Layer: "Streamlit + Plotly"
CI_Engine: "GitHub Actions"
Last_Updated: "2026-09-05"
</SYSTEM_METADATA>

---

## 1. LLM OPERATIONAL DIRECTIVES & MENTOR PERSONA

When acting as an AI assistant or mentor for this project, you must enforce the following rules derived from `mentor.md` and `instructions.md`:

### 1.1 Instruction Hierarchy & Persona Rules
1. **Socratic on Engineering Judgment Calls:**
   - When the user asks about design decisions, extraction architecture, entity-resolution matching logic, dbt join modeling, scheduling intervals, or handling anomalies: **DO NOT provide plug-and-play complete code**.
   - Instead, respond with probing questions, trade-off comparisons, and edge-case scenarios. Guide the user to find the answer.
2. **Direct on Tooling & Pure Syntax:**
   - When the user asks about CLI commands, environment setup, package installations, error message parsing, or library API syntax: **Provide direct, accurate, copy-pasteable answers immediately**.
3. **Debugging Methodology:**
   - When presented with broken code, isolate the region/file and ask what behavior was expected vs. observed. Escalate progressively: *Question $\rightarrow$ Pointer to line $\rightarrow$ Concrete code snippet*.
4. **Anti-Cosplay & Scale Guardrail:**
   - **Strictly reject "infra-cosplay"**: If the user suggests Kubernetes, Kafka, Spark, Airflow, or complex distributed systems, actively push back. The dataset size is thousands of job records and hundreds of GitHub repos—an embedded columnar OLAP engine (DuckDB) and Dagster asset graphs are the optimal engineering choice.
   - **Reject false scale claims**: Enforce that the user never claims "big data" or "enterprise scale." True scale: 1,788 Adzuna India job postings, 48k Stack Overflow survey responses, Top 100 GitHub repos per tech.
5. **Core Metric Disambiguation:**
   - **GitHub stars $\neq$ technology adoption**. Stars measure *developer attention around representative projects*. High stars can indicate tutorial hype or awesome-list contamination.

---

## 2. CORE ANALYTICAL MISSION & SIGNAL MATRIX

### 2.1 The Core Research Question
> **"Which software engineering skills and technologies are rising in real employer demand versus rising in developer ecosystem hype?"**

### 2.2 Tri-Source Analytical Roles

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Stack Overflow Developer Survey (Annual · Flat-file CSV)            │
│    -> Metric: Adoption Baseline (% of 48,000+ developers using it)     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Adzuna India IT Job Postings (Daily · Paginated REST API)           │
│    -> Metric: Real Employer Demand (Job counts, active requisitions)   │
├────────────────────────────────────────────────────────────────────────┤
│ 3. GitHub Search API (Monthly · Top 100 Periodic Repositories)         │
│    -> Metric: Ecosystem Signal (Developer attention, momentum, breadth)│
└────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Composite Signal Quadrant Matrix (`fct_skill_signals.composite_signal`)

$$\text{Composite Signal} = f(\text{weekly\_job\_count}, \text{gh\_usable\_repos})$$

| Signal Quadrant | Condition (Rule) | Analytical Meaning | Real-World Example Archetype |
|---|---|---|---|
| **`thriving`** | `job_count >= 5` AND `usable_repos >= 30` | **Jobs ↑ + GitHub ↑** : High employer demand backed by strong, active open-source ecosystem | Python, React, Docker |
| **`demand_led`** | `job_count >= 5` AND `usable_repos < 30` | **Jobs ↑ + GitHub ↓** : High hiring demand despite low community hype or niche open-source activity | SQL Server, Spring Boot, Legacy Enterprise |
| **`hype_led`** | `job_count < 5` AND `usable_repos >= 30` | **Jobs ↓ + GitHub ↑** : Vibrant community hype, tutorials, and repos, but minimal employer hiring | Experimental AI agents, nascent frameworks |
| **`weak`** | `job_count < 5` AND `usable_repos < 30` | **Jobs ↓ + GitHub ↓** : Low hiring demand and negligible developer community activity | Deprecated or highly specialized tools |

---

## 3. REPOSITORY TREE & FILE INVENTORY

```
d:\my first DE project - job analytics/
├── task.md                                # Phase checklist and roadmap (source of truth for progress)
├── instructions.md                        # Mentor notes, research prompts, and guardrails per phase
├── mentor.md                              # Mentor persona, teaching philosophy, and style guidelines
├── PROJECT_CONTEXT.md                     # THIS FILE — Self-contained context for LLM ingestion
└── Harsh_Mishra_Projects/
    ├── labor_market.duckdb                # Local DuckDB database file containing schemas: main_staging, main_intermediate, main_marts
    └── Labor-Market-Intelligence/         # Active Git repository root
        ├── .env                           # Secrets: GitHub_access_token, Adzuna_app_id, Adzuna_api, MotherDuck_token
        ├── .gitignore                     # Ignores .venv, .env, *.duckdb, raw CSVs, dbt packages/targets
        ├── requirements.txt               # Pinned dependencies (dagster, dbt-core, dbt-duckdb, streamlit, etc.)
        ├── README.md                      # Public documentation and architecture
        ├── .github/workflows/
        │   └── dbt_ci.yml                 # CI workflow: executes scripts/ci_stub_data.py -> dbt run -> dbt test
        ├── dagster/
        │   ├── definitions.py             # Dagster entrypoint: combines assets, jobs, schedules, dbt resource
        │   └── assets/
        │       ├── raw_assets.py          # Software-defined assets for SO survey, Adzuna, GitHub, and parquet prep
        │       └── dbt_assets.py          # dagster-dbt wrapper mapping dbt models to Dagster assets
        ├── dashboard/
        │   └── app.py                     # Streamlit dashboard consuming main_marts.fct_skill_signals
        ├── dbt/
        │   ├── dbt_project.yml            # dbt configuration with staging, intermediate, marts schemas
        │   ├── packages.yml               # dbt-labs/dbt_utils dependency
        │   ├── profiles.yml               # dev (local DuckDB) and prod (MotherDuck) profiles
        │   └── models/
        │       ├── staging/
        │       │   ├── sources.yml        # Source metadata and raw file references
        │       │   ├── schema.yml         # Staging tests (not_null, unique, accepted_values)
        │       │   ├── stg_stackoverflow.sql
        │       │   ├── stg_adzuna.sql
        │       │   ├── stg_github_repos.sql
        │       │   └── stg_github_snapshots.sql
        │       ├── intermediate/
        │       │   └── int_tech_crosswalk.sql
        │       └── marts/
        │           ├── schema.yml         # Mart tests (unique, not_null, accepted_values, foreign keys)
        │           ├── dim_technology.sql
        │           └── fct_skill_signals.sql
        ├── raw/
        │   ├── curated_tech.py            # Generates tech_dimension_table.json from SO tech list + GitHub validation
        │   ├── emerging_tech.json         # 38 emerging AI/ML/Data technologies not in SO Survey
        │   ├── tech_dimension_table.json  # Curated crosswalk: SO Name -> GitHub Slug -> Adzuna Keyword
        │   ├── prepare_raw.py             # Consolidates raw JSONs/CSVs into staging Parquet files
        │   ├── adzuna/
        │   │   ├── daily_data.py          # Daily 1-day pull with exponential backoff & checkpointing
        │   │   ├── initial_data.py        # 60-day historical pull
        │   │   ├── build_adzuna_csv.py    # Merges daily JSONs into adzuna_extracted.csv via regex keyword matching
        │   │   ├── adzuna_extracted.csv   # 1,788 deduped job postings with matched tech keywords
        │   │   └── *.json                 # Raw dated JSON API pulls (e.g. 2026-07-19.json)
        │   ├── github/
        │   │   ├── config.py              # Tunable scoring weights, contamination keywords, thresholds
        │   │   ├── classifier.py          # Quality classifier and technology relevance scoring functions
        │   │   ├── snapshot.py            # Ecosystem metrics computation (medians, concentrations, ratios)
        │   │   ├── github_extractor.py    # Main CLI: queries GitHub Search API, classifies, writes snapshots
        │   │   ├── topics_with_aliases.txt# Seed list of known GitHub topic slugs
        │   │   ├── <YYYY-MM-DD>/          # Dated snapshot directory (e.g. 2026-09-05)
        │   │   │   ├── repos/*.json       # Top 100 classified repo records per tech
        │   │   │   └── snapshots/*.json   # Computed ecosystem metrics per tech
        │   │   ├── all_repos.parquet      # Consolidated parquet of all repos
        │   │   └── all_snapshots.parquet  # Consolidated parquet of all snapshots
        │   └── stackoverflow/
        │       ├── get_data.py            # Download script for SO survey CSV
        │       ├── filter_data.py         # Parses tech columns, outputs tech_list.json
        │       ├── github_override.json   # Manual mappings for symbols (C++, C#, .NET, Node.js)
        │       ├── tech_list.json         # 141 unique extracted technologies
        │       ├── survey_result.csv      # Raw CSV (~140MB) [gitignored]
        │       └── filtered_survey.parquet# Slim parquet with tech columns only
        └── scripts/
            └── ci_stub_data.py            # Generates synthetic stub data for GitHub Actions headless CI
```

---

## 4. INGESTION & EXTRACTION ENGINES SPECIFICATION

### 4.1 Stack Overflow Survey Ingestion
- **Frequency:** Annual bulk flat file.
- **Parsing Strategy:**
  - Semicolon-delimited multi-values in survey columns:
    `LanguageHaveWorkedWith`, `LanguageWantToWorkWith`, `LanguageAdmired`,
    `DatabaseHaveWorkedWith`, `DatabaseWantToWorkWith`, `DatabaseAdmired`,
    `WebframeHaveWorkedWith`, `WebframeWantToWorkWith`, `WebframeAdmired`,
    `PlatformHaveWorkedWith`, `PlatformWantToWorkWith`, `PlatformAdmired`.
  - Filtered to respondents with $\ge 1$ technology non-null. Output stored as `raw/stackoverflow/filtered_survey.parquet`.

### 4.2 Adzuna API Extractor (`raw/adzuna/`)
- **API Endpoint:** `https://api.adzuna.com/v1/api/jobs/in/search/{page_no}`
- **Parameters:** `category=it-jobs`, `results_per_page=50`, `max_days_old=1`, `full_time=1`, `permanent=1`.
- **Free-Tier Limits:** 250 requests/day, 1,000/week, 2,500/month.
- **Resilience & Checkpoint Architecture:**
  - `fetch_with_retry(url, max_retries=5, timeout=10)`: Exponential backoff on HTTP 429 and 5xx ($2^{\text{attempt}+1}$s).
  - Writes progress to `progess-<today>.json` after every successful page. If interrupted, next run resumes at `next_page`.
- **Keyword Matching Strategy (`build_adzuna_csv.py`):**
  - Concatenates `title` and `description`, upper-cased.
  - Matches using negative lookaround on alphanumeric boundaries:
    ```python
    pattern = r'(?<![A-Z0-9])' + re.escape(keyword) + r'(?![A-Z0-9])'
    ```
    *Why not `\b`?* Regular word boundaries (`\b`) fail on symbols like `C#`, `C++`, and `.NET`. Negative lookaround handles them without false positive substring matches.
  - Deduplication: File-level via `processed_files.txt`, record-level via `seen_ids` set.

### 4.3 GitHub Ecosystem Extractor (`raw/github/`)

#### 4.3.1 Sampling Methodology
- Target: Top 100 repositories per technology query `topic:<slug>` sorted by `stars` descending.
- **Why exactly 100?** Top-star queries are contaminated with educational repos, tutorials, and curated lists. 100 provides enough sample volume to filter down to ~50–80 usable repositories.
- Cadence: Monthly snapshot (not daily; daily churn produces meaningless noise and wastes API quotas).

#### 4.3.2 Quality Classification Algorithm (`classifier.py`)
1. **Hard Exclusions:** If `fork=True` OR `archived=True` OR `disabled=True` $\rightarrow$ `hard_excluded=True`, `quality_class='excluded'`, skipped from metrics.
2. **Contamination Scoring:** Weighted keyword match on `lower(name + " " + description + " " + " ".join(topics))`:
   - Strong Collection (Weight 3.5–4.0): `awesome-list`, `curated`, `resource-collection`.
   - Strong Educational (Weight 3.0–3.5): `tutorial`, `course`, `education`, `100-days`, `interview-questions`.
   - Medium/Weak (Weight 0.5–2.5): `cheatsheet`, `notes`, `beginner`, `roadmap`, `sample`, `template`.
3. **Positive Quality Bonus (offsets weak contamination):**
   - Non-empty description (+1.5)
   - At least 1 topic tag (+1.5)
   - Recent push within 180 days (+1.0)
   - Stargazers count > 500 (+0.5)
4. **Classification Decision Logic:**
   - $\text{Net Score} = \text{Contamination Score} - \text{Bonus}$.
   - If dominant collection keywords matched $\rightarrow$ `collection`.
   - If dominant educational keywords matched $\rightarrow$ `educational`.
   - If $\text{Net Score} \ge 5.0 \rightarrow$ `educational`.
   - If $\text{Net Score} \ge 2.0 \rightarrow$ `uncertain`.
   - If missing description and topics $\rightarrow$ `other`.
   - Else $\rightarrow$ `project`.

#### 4.3.3 Technology Relevance Scoring (`classifier.py`)
Independent from quality scoring:
- `language_exact_match` (+4.0): Repo primary language matches target language.
- `topic_exact_match` (+3.0 per matching topic).
- `name_canonical_match` (+3.0) / `name_alias_match` (+2.0).
- `desc_canonical_match` (+1.5) / `desc_alias_match` (+1.0).
- **Usability Criterion:** `relevance_score >= 2.0` marks `is_usable = True`.

#### 4.3.4 Usable Repository Formula
$$\text{usable} = (\text{hard\_excluded} == \text{False}) \land (\text{quality\_class} \in [\text{'project'}, \text{'uncertain'}]) \land (\text{is\_usable} == \text{True})$$

#### 4.3.5 Ecosystem Snapshot Formulas (`snapshot.py`)
- `observed_repositories`: Total count returned by GitHub Search API.
- `usable_repositories`: Count of repositories satisfying usable formula.
- `median_stars`: $\text{median}(\{r.\text{stars} \mid r \in \text{usable}\})$ (Median prevents outlier distortion).
- `median_forks`: $\text{median}(\{r.\text{forks} \mid r \in \text{usable}\})$.
- `active_repository_ratio`: $\frac{|\{r \in \text{usable} \mid \text{days\_since}(r.\text{pushed\_at}) \le 180\}|}{|\text{usable}|}$.
- `top1_star_concentration`: $\frac{\max_{r \in \text{usable}}(r.\text{stars})}{\sum_{r \in \text{usable}} r.\text{stars}}$.
- `top5_star_concentration`: $\frac{\sum \text{stars of top 5 usable repos}}{\sum_{r \in \text{usable}} r.\text{stars}}$.
- `new_to_top100_ratio`: $\frac{|\text{usable\_ids}_{\text{current}} \setminus \text{usable\_ids}_{\text{previous}}|}{|\text{usable}|}$ (Null on first snapshot).

---

## 5. ENTITY RESOLUTION SPECIFICATION

### 5.1 The Resolution Problem
Different sources use conflicting representations for identical technologies:
- SO Survey: `Amazon Web Services (AWS)`, `C++`, `Node.js`, `Bash/Shell (all shells)`
- GitHub Topic Slug: `aws`, `cpp`, `nodejs`, `bash`
- Adzuna Keyword: `AWS`, `C++`, `NODE.JS`, `AMAZON WEB SERVICES`
- Emerging Tech: `LangChain`, `CrewAI`, `DuckDB`, `Apache Iceberg`

### 5.2 Resolution Architecture: Exact Curated Crosswalk
- **Decision:** Exact matching against a pre-validated crosswalk (`tech_dimension_table.json` + `emerging_tech.json`).
- **Defense:** Fuzzy matching (e.g. Levenshtein distance) produces catastrophic **confidently-wrong false positives** on short skill strings (e.g. matching `Java` to `JavaScript`, `Rust` to `Ruby`). Because the Stack Overflow technology list is a closed set (141 names), an exact-match crosswalk with manual overrides (`github_override.json`) guarantees 100% precision.
- **Handling Unmatched Entries:** Preserved with `is_unresolved = true` and `canonical_name = raw_name`. Never silently dropped.

### 5.3 Resolution Priority Hierarchy
1. Manual Overrides Table (`github_override.json`)
2. Local Topic Set (`topics_with_aliases.txt`)
3. Dot-variant transformation (e.g. `node.js` $\rightarrow$ `nodejs` or `nodedotjs`)
4. GitHub Search API verification (`total_count > 0`)
5. None $\rightarrow$ Logged as unresolved for manual review

---

## 6. DATA DICTIONARY & COMPLETE SQL MODEL DDL

### 6.1 Database Schema Organization (DuckDB / MotherDuck)
- `main_staging`: Standardized views built directly from raw Parquet and CSV files.
- `main_intermediate`: Entity resolution crosswalk table.
- `main_marts`: Analytical dimension and fact tables.

---

### 6.2 Staging Models

#### Model: `main_staging.stg_stackoverflow`
- **File:** `dbt/models/staging/stg_stackoverflow.sql`
- **Materialization:** View
- **Source:** `raw/stackoverflow/filtered_survey.parquet`
- **Grain:** One row per survey respondent per technology worked with.

```sql
with raw as (
    select * from read_parquet('{{ env_var("PROJECT_ROOT", "..") }}/raw/stackoverflow/filtered_survey.parquet')
),
tech_columns as (
    select "ResponseId" as respondent_id, 'language' as tech_category, trim(tech) as technology_raw
    from raw, unnest(string_split(coalesce("LanguageHaveWorkedWith", ''), ';')) as t(tech) where trim(tech) != ''
    union all
    select "ResponseId" as respondent_id, 'database' as tech_category, trim(tech) as technology_raw
    from raw, unnest(string_split(coalesce("DatabaseHaveWorkedWith", ''), ';')) as t(tech) where trim(tech) != ''
    union all
    select "ResponseId" as respondent_id, 'webframe' as tech_category, trim(tech) as technology_raw
    from raw, unnest(string_split(coalesce("WebframeHaveWorkedWith", ''), ';')) as t(tech) where trim(tech) != ''
    union all
    select "ResponseId" as respondent_id, 'platform' as tech_category, trim(tech) as technology_raw
    from raw, unnest(string_split(coalesce("PlatformHaveWorkedWith", ''), ';')) as t(tech) where trim(tech) != ''
)
select
    respondent_id,
    tech_category,
    technology_raw,
    respondent_id || '|' || tech_category || '|' || technology_raw as record_id
from tech_columns
```

**Columns & Tests:**
- `record_id` (VARCHAR, PK): `unique`, `not_null`
- `respondent_id` (VARCHAR): `not_null`
- `tech_category` (VARCHAR): `not_null`, `accepted_values: ['language', 'database', 'webframe', 'platform']`
- `technology_raw` (VARCHAR): `not_null`

---

#### Model: `main_staging.stg_adzuna`
- **File:** `dbt/models/staging/stg_adzuna.sql`
- **Materialization:** View
- **Source:** `raw/adzuna/adzuna_extracted.csv`
- **Grain:** One row per job posting per matched technology keyword.

```sql
with raw as (
    select * from read_csv_auto(
        '{{ env_var("PROJECT_ROOT", "..") }}/raw/adzuna/adzuna_extracted.csv',
        header = true,
        types = {'id': 'VARCHAR', 'created_date': 'DATE'}
    )
),
exploded as (
    select
        id as job_id,
        created_date,
        title,
        location,
        trim(tech) as technology_keyword
    from raw,
    unnest(string_split(coalesce(technologies, ''), ',')) as t(tech)
    where trim(tech) != ''
)
select
    job_id,
    created_date,
    title,
    location,
    technology_keyword,
    job_id || '|' || technology_keyword as record_id
from exploded
```

**Columns & Tests:**
- `record_id` (VARCHAR, PK): `unique`, `not_null`
- `job_id` (VARCHAR): `not_null`
- `created_date` (DATE): `not_null`
- `title` (VARCHAR)
- `location` (VARCHAR)
- `technology_keyword` (VARCHAR): `not_null`

---

#### Model: `main_staging.stg_github_repos`
- **File:** `dbt/models/staging/stg_github_repos.sql`
- **Materialization:** View
- **Source:** `raw/github/all_repos.parquet`
- **Grain:** One row per repository per technology per snapshot date.

```sql
with raw as (
    select * from read_parquet('{{ env_var("PROJECT_ROOT", "..") }}/raw/github/all_repos.parquet')
)
select
    cast(id as varchar) as repo_id,
    full_name,
    name as repo_name,
    _technology_slug as technology_slug,
    cast(_snapshot_date as date) as snapshot_date,
    description,
    language,
    cast(stargazers_count as integer) as stars,
    cast(forks_count as integer) as forks,
    cast(created_at as timestamptz) as repo_created_at,
    cast(updated_at as timestamptz) as repo_updated_at,
    cast(pushed_at as timestamptz) as last_pushed_at,
    cast(coalesce(fork, false) as boolean) as is_fork,
    cast(coalesce(archived, false) as boolean) as is_archived,
    cast(coalesce(disabled, false) as boolean) as is_disabled,
    cast(coalesce(hard_excluded, false) as boolean) as hard_excluded,
    exclude_reason,
    quality_class,
    cast(quality_score as double) as quality_score,
    cast(relevance_score as double) as relevance_score,
    cast(coalesce(is_usable, false) as boolean) as is_usable,
    cast(id as varchar) || '|' || _technology_slug || '|' || _snapshot_date as record_id
from raw
where id is not null
```

**Columns & Tests:**
- `record_id` (VARCHAR, PK): `unique`, `not_null`
- `repo_id` (VARCHAR): `not_null`
- `technology_slug` (VARCHAR): `not_null`
- `snapshot_date` (DATE): `not_null`
- `quality_class` (VARCHAR): `not_null`, `accepted_values: ['project', 'educational', 'collection', 'other', 'uncertain', 'excluded']`
- `stars` (INTEGER): `not_null`
- `is_usable` (BOOLEAN)

---

#### Model: `main_staging.stg_github_snapshots`
- **File:** `dbt/models/staging/stg_github_snapshots.sql`
- **Materialization:** View
- **Source:** `raw/github/all_snapshots.parquet`
- **Grain:** One row per technology per snapshot date.

```sql
with raw as (
    select * from read_parquet('{{ env_var("PROJECT_ROOT", "..") }}/raw/github/all_snapshots.parquet')
)
select
    technology as technology_name,
    cast(snapshot_date as date) as snapshot_date,
    cast(observed_repositories as integer) as observed_repositories,
    cast(usable_repositories as integer) as usable_repositories,
    cast(median_stars as double) as median_stars,
    cast(median_forks as double) as median_forks,
    cast(active_repository_ratio as double) as active_repository_ratio,
    cast(top1_star_concentration as double) as top1_star_concentration,
    cast(top5_star_concentration as double) as top5_star_concentration,
    cast(new_to_top100_ratio as double) as new_to_top100_ratio,
    case
        when observed_repositories > 0
        then cast(usable_repositories as double) / observed_repositories
        else null
    end as usable_ratio,
    technology || '|' || cast(snapshot_date as varchar) as record_id
from raw
where technology is not null and snapshot_date is not null
```

**Columns & Tests:**
- `record_id` (VARCHAR, PK): `unique`, `not_null`
- `technology_name` (VARCHAR): `not_null`
- `snapshot_date` (DATE): `not_null`
- `observed_repositories` (INTEGER): `not_null`
- `usable_repositories` (INTEGER): `not_null`

---

### 6.3 Intermediate Model

#### Model: `main_intermediate.int_tech_crosswalk`
- **File:** `dbt/models/intermediate/int_tech_crosswalk.sql`
- **Materialization:** Table / View
- **Grain:** Unique canonical technology record across all sources.

```sql
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
    from read_json_auto('{{ env_var("PROJECT_ROOT", "..") }}/raw/emerging_tech.json') e,
    unnest(e.technologies) as t(j)
    where j.status = 'active'
),
so_map as (
    select
        "StackOverflow" as raw_name,
        'so_survey' as source_type,
        "StackOverflow" as canonical_name,
        "Github_Topic" as github_slug,
        upper("StackOverflow") as adzuna_keyword,
        null as category
    from dim
),
emerging_map as (
    select
        canonical_name as raw_name,
        'emerging_tech' as source_type,
        canonical_name,
        github_topic as github_slug,
        upper(canonical_name) as adzuna_keyword,
        category
    from emerging_raw
),
adzuna_map as (
    select
        upper("StackOverflow") as raw_name,
        'adzuna' as source_type,
        "StackOverflow" as canonical_name,
        "Github_Topic" as github_slug,
        upper("StackOverflow") as adzuna_keyword,
        null as category
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
deduped as (
    select
        raw_name,
        source_type,
        canonical_name,
        github_slug,
        adzuna_keyword,
        category,
        row_number() over (
            partition by lower(canonical_name)
            order by case source_type
                when 'emerging_tech' then 1
                when 'so_survey' then 2
                when 'adzuna' then 3
                else 4
            end
        ) as rn
    from all_mappings
)
select
    raw_name,
    source_type,
    canonical_name,
    github_slug,
    adzuna_keyword,
    category,
    (github_slug is null) as is_unresolved
from deduped
where rn = 1
```

---

### 6.4 Mart Models

#### Model: `main_marts.dim_technology`
- **File:** `dbt/models/marts/dim_technology.sql`
- **Materialization:** Table
- **Grain:** One row per canonical technology.

```sql
with crosswalk as (
    select * from {{ ref('int_tech_crosswalk') }}
),
github_snaps as (
    select distinct technology_name
    from {{ ref('stg_github_snapshots') }}
),
all_techs as (
    select distinct canonical_name, github_slug, adzuna_keyword, source_type
    from crosswalk
    where canonical_name is not null
),
deduped as (
    select
        canonical_name,
        max(github_slug) as github_slug,
        max(adzuna_keyword) as adzuna_keyword,
        max(case when source_type = 'emerging_tech' then true else false end) as is_emerging
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
        case when gs.technology_name is not null then true else false end as has_github_data
    from deduped d
    left join github_snaps gs
        on lower(d.canonical_name) = lower(gs.technology_name)
)
select * from final
```

**Columns & Tests:**
- `tech_id` (VARCHAR, PK): `not_null`, `unique`
- `canonical_name` (VARCHAR): `not_null`, `unique`
- `github_slug` (VARCHAR): `not_null`
- `adzuna_keyword` (VARCHAR)
- `is_emerging` (BOOLEAN)
- `has_github_data` (BOOLEAN)

---

#### Model: `main_marts.fct_skill_signals`
- **File:** `dbt/models/marts/fct_skill_signals.sql`
- **Materialization:** Table
- **Grain:** One row per canonical technology per week (Adzuna) + closest prior GitHub snapshot.

```sql
with dim_tech as (
    select * from {{ ref('dim_technology') }}
),
-- Adzuna weekly aggregation
adzuna_weekly as (
    select
        upper(technology_keyword) as adzuna_keyword,
        date_trunc('week', created_date) as week_start,
        count(distinct job_id) as job_count
    from {{ ref('stg_adzuna') }}
    where technology_keyword is not null and created_date is not null
    group by 1, 2
),
adzuna_with_tech as (
    select
        dt.tech_id,
        dt.canonical_name,
        aw.week_start,
        aw.job_count
    from adzuna_weekly aw
    inner join dim_tech dt
        on upper(aw.adzuna_keyword) = upper(dt.adzuna_keyword)
),
-- SO survey baseline adoption
so_adoption as (
    select technology_raw, count(distinct respondent_id) as respondent_count
    from {{ ref('stg_stackoverflow') }}
    group by technology_raw
),
so_total as (
    select count(distinct respondent_id) as total_respondents
    from {{ ref('stg_stackoverflow') }}
),
so_with_tech as (
    select
        dt.tech_id,
        dt.canonical_name,
        round(cast(sa.respondent_count as double) / st.total_respondents * 100, 2) as so_adoption_pct
    from so_adoption sa
    inner join dim_tech dt
        on lower(sa.technology_raw) = lower(dt.canonical_name)
    cross join so_total st
),
-- GitHub snapshot signals
github_with_tech as (
    select
        dt.tech_id,
        dt.canonical_name,
        gs.snapshot_date,
        gs.usable_repositories,
        gs.median_stars,
        gs.median_forks,
        gs.active_repository_ratio,
        gs.top5_star_concentration,
        gs.new_to_top100_ratio
    from {{ ref('stg_github_snapshots') }} gs
    inner join dim_tech dt
        on lower(gs.technology_name) = lower(dt.canonical_name)
),
-- Join Adzuna weekly to SO baseline and nearest GitHub snapshot
combined as (
    select
        a.tech_id,
        a.canonical_name,
        a.week_start as signal_week,
        a.job_count as weekly_job_count,
        so.so_adoption_pct,
        gh.snapshot_date as github_snapshot_date,
        gh.usable_repositories as gh_usable_repos,
        gh.median_stars as gh_median_stars,
        gh.median_forks as gh_median_forks,
        gh.active_repository_ratio as gh_active_ratio,
        gh.top5_star_concentration as gh_top5_concentration,
        gh.new_to_top100_ratio as gh_turnover_ratio,
        case
            when a.job_count >= 5 and coalesce(gh.usable_repositories, 0) >= 30 then 'thriving'
            when a.job_count >= 5 and coalesce(gh.usable_repositories, 0) < 30 then 'demand_led'
            when a.job_count < 5 and coalesce(gh.usable_repositories, 0) >= 30 then 'hype_led'
            else 'weak'
        end as composite_signal
    from adzuna_with_tech a
    left join so_with_tech so on a.tech_id = so.tech_id
    left join (
        select
            gh1.tech_id,
            gh1.snapshot_date,
            gh1.usable_repositories,
            gh1.median_stars,
            gh1.median_forks,
            gh1.active_repository_ratio,
            gh1.top5_star_concentration,
            gh1.new_to_top100_ratio,
            row_number() over (partition by gh1.tech_id order by gh1.snapshot_date desc) as rn
        from github_with_tech gh1
    ) gh on a.tech_id = gh.tech_id and gh.rn = 1
)
select
    {{ dbt_utils.generate_surrogate_key(['tech_id', 'signal_week']) }} as signal_id,
    tech_id,
    canonical_name,
    signal_week,
    weekly_job_count,
    so_adoption_pct,
    github_snapshot_date,
    gh_usable_repos,
    gh_median_stars,
    gh_median_forks,
    gh_active_ratio,
    gh_top5_concentration,
    gh_turnover_ratio,
    composite_signal
from combined
```

**Columns & Tests:**
- `signal_id` (VARCHAR, PK): `unique`, `not_null`
- `tech_id` (VARCHAR, FK): `not_null`, `relationships: { to: ref('dim_technology'), field: tech_id }`
- `canonical_name` (VARCHAR)
- `signal_week` (TIMESTAMP): `not_null`
- `weekly_job_count` (BIGINT): `not_null`
- `so_adoption_pct` (DOUBLE)
- `github_snapshot_date` (DATE)
- `gh_usable_repos` (INTEGER)
- `gh_median_stars` (DOUBLE)
- `gh_median_forks` (DOUBLE)
- `gh_active_ratio` (DOUBLE)
- `gh_top5_concentration` (DOUBLE)
- `gh_turnover_ratio` (DOUBLE)
- `composite_signal` (VARCHAR): `not_null`, `accepted_values: ['thriving', 'demand_led', 'hype_led', 'weak']`

---

## 7. DAGSTER ORCHESTRATION ARCHITECTURE

### 7.1 Asset Definitions
- **`raw_assets.py`**:
  - `stackoverflow_parquet`: Materializes `filtered_survey.parquet` from raw CSV.
  - `adzuna_jobs_csv`: Subprocesses `build_adzuna_csv.py`, returns row count metadata.
  - `github_ecosystem_snapshots`: Subprocesses `github_extractor.py`, returns snapshot count.
  - `consolidated_parquet`: Runs `prepare_raw.py` to create `all_repos.parquet` and `all_snapshots.parquet`. Depends on the previous three extraction assets.
- **`dbt_assets.py`**:
  - `labor_market_dbt_assets`: Generates one Dagster asset per dbt model from `target/manifest.json`. Runs `dbt run --full-refresh`.

### 7.2 Job & Schedule Definitions (`definitions.py`)
```python
# Daily job: Adzuna pull + Parquet prep
daily_extraction_job = define_asset_job(
    name="daily_extraction",
    selection=["adzuna_jobs_csv", "consolidated_parquet"]
)
daily_schedule = ScheduleDefinition(
    job=daily_extraction_job,
    cron_schedule="30 20 * * *",  # 02:00 IST
    name="daily_adzuna_extraction"
)

# Monthly job: GitHub Top 100 snapshot + Parquet prep
monthly_github_job = define_asset_job(
    name="monthly_github_snapshot",
    selection=["github_ecosystem_snapshots", "consolidated_parquet"]
)
monthly_schedule = ScheduleDefinition(
    job=monthly_github_job,
    cron_schedule="30 21 1 * *",  # 03:00 IST on 1st of month
    name="monthly_github_snapshot"
)
```

---

## 8. CI/CD & TESTING SUITE (GitHub Actions)

### 8.1 Workflow: `.github/workflows/dbt_ci.yml`
- Runs on: `push` to `main`, `dev` and `pull_request` to `main`.
- Environment: `ubuntu-latest`, Python 3.11.
- Problem Solved: In CI, large survey CSVs (~140MB) and Adzuna API keys are omitted from Git.
- Solution: Pre-flight script `scripts/ci_stub_data.py` generates deterministic, schema-compatible synthetic stubs:
  - `raw/stackoverflow/filtered_survey.parquet` (2 synthetic rows)
  - `raw/adzuna/adzuna_extracted.csv` (2 synthetic jobs)
  - `raw/github/2026-09-05/` (3 technologies: Python, JavaScript, React with 10 repos each)
- Workflow sequence:
  1. `python scripts/ci_stub_data.py`
  2. `dbt deps`
  3. `dbt run`
  4. `dbt test` (asserts zero test failures)

---

## 9. KNOWN GOTCHAS, BUGS & LLM HALLUCINATION GUARDS

When answering or coding for this project, the LLM must be aware of the following known edge cases:

1. **`int_tech_crosswalk` Column Aliases:**
   - In `dbt/models/intermediate/int_tech_crosswalk.sql`, ensure that `source_type` is aliased properly. `dim_technology.sql` explicitly expects `source_type`. Do NOT rename it to `source` without updating `dim_technology.sql`.
2. **First Snapshot Turnover Ratio is Null:**
   - In `stg_github_snapshots` and `fct_skill_signals`, `new_to_top100_ratio` is expected to be `NULL` for the first snapshot date (`2026-09-05`). It only populates when a second date exists for comparison. Do not flag this as a bug.
3. **Regex Word Boundary on Skill Names:**
   - Never use `\b` when keyword matching skills in job descriptions. `C#`, `C++`, and `.NET` will fail. Always use negative lookaround on alphanumeric boundaries: `r'(?<![A-Z0-9])' + re.escape(term) + r'(?![A-Z0-9])'`.
4. **Adzuna Rate Limit Management:**
   - Daily cap: 250 calls. Monthly cap: 2,500 calls.
   - Do NOT write unbounded while loops or large multi-page batch scrapers that exhaust the quota in a single execution.
5. **GitHub API Rate Limits:**
   - Unauthenticated: 60 requests/hr (hits wall immediately).
   - Authenticated (`GITHUB_ACCESS_TOKEN`): 5,000 requests/hr.
   - Extractor sleeps 60s when `X-RateLimit-Remaining < 50`.
6. **dbt Generic Test Syntax in v1.11+:**
   - In dbt v1.11+, generic tests (like `relationships`) require nested properties under `arguments` or standard shorthand syntax to avoid deprecation warnings.

---

## 10. TASK CHECKLIST & MILESTONES (`task.md` Summary)

- [x] **Phase 0 (Environment):** Python venv, MotherDuck, Adzuna API, GitHub PAT, repo scaffold.
- [x] **Phase 1 (Extraction):** SO Survey parsed; Adzuna extractor with exponential backoff & checkpointing; GitHub Top 100 extractor with quality & relevance scoring.
- [x] **Phase 2 (Staging):** Staging views (`stg_stackoverflow`, `stg_adzuna`, `stg_github_repos`, `stg_github_snapshots`) with schema tests.
- [x] **Phase 3 (Entity Resolution):** Curated crosswalk `int_tech_crosswalk.sql` with exact matching; unresolved records preserved.
- [x] **Phase 4 (Marts):** `dim_technology` and `fct_skill_signals` table models with composite signal quadrant logic.
- [x] **Phase 5 (Orchestration):** Dagster asset graph and schedules in `definitions.py`.
- [x] **Phase 6 (CI):** GitHub Actions workflow executing synthetic stub tests.
- [x] **Phase 7 (Dashboard):** Streamlit analytical dashboard (`dashboard/app.py`) with Plotly demand vs. ecosystem visual.
- [ ] **Phase 8 (Documentation & Case Study):**
  - [x] Architecture diagram and comprehensive README.
  - [ ] Written 500–800 word case study on entity resolution trade-offs.
  - [ ] Interview-ready resume bullet point formulation.
