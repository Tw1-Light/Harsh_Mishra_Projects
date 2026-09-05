"""
build_jobs_csv.py
-----------------
Reads daily Adzuna JSON files and builds a rolling CSV of job records.

Each CSV row contains:
  ID           - Adzuna's unique job identifier (natural key, dedup guard)
  Created      - posting date (YYYY-MM-DD)
  Technologies - comma-separated tech names matched against tech_dimension_table

Dedup strategy (two levels):
  1. File-level  : processed_files.txt  — skips JSON files already merged
  2. Record-level: seen_ids set          — skips job IDs already in the CSV
                   (built once before the loop, updated in memory after each file
                    so cross-file duplicates in the same run are also caught)

Run this after daily_data.py in the Dagster pipeline.
"""

import csv
import glob
import json
import logging
import re
import sys
from os import path

# ---------------------------------------------------------------------------
# Logging — timestamps + level label for easy reading
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# File paths  (UPPER_SNAKE_CASE = module-level constants, per PEP 8)
# ---------------------------------------------------------------------------
_BASE_DIR = path.dirname(__file__)

DAILY_JSON_GLOB      = path.join(_BASE_DIR, '*.json')
PROCESSED_FILES_PATH = path.join(_BASE_DIR, 'processed_files.txt')
JOBS_CSV_PATH        = path.join(_BASE_DIR, 'adzuna_jobs.csv')
TECH_TABLE_PATH      = path.abspath(path.join(_BASE_DIR, '..', 'tech_dimension_table.json'))

CSV_HEADER = ['ID', 'Created', 'Technologies']


# ---------------------------------------------------------------------------
# Loaders — each returns a safe default instead of crashing on missing files
# ---------------------------------------------------------------------------

def load_tech_table(table_path: str) -> list[dict]:
    """Load tech_dimension_table.json. Exits immediately if missing or corrupt."""
    if not path.exists(table_path):
        log.error('Tech dimension table not found: %s', table_path)
        sys.exit(1)
    try:
        with open(table_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        log.error('Could not parse tech dimension table: %s', exc)
        sys.exit(1)


def load_processed_files(manifest_path: str) -> set:
    """
    Return the set of file paths already merged into the CSV.
    Creates the manifest file if it does not exist yet (first run).
    """
    if not path.exists(manifest_path):
        log.info('Manifest not found — creating empty one: %s', manifest_path)
        open(manifest_path, 'w', encoding='utf-8').close()
        return set()
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip()}
    except OSError as exc:
        log.warning('Could not read manifest (%s) — treating as empty.', exc)
        return set()


def load_seen_ids(csv_path: str) -> set:
    """
    Build a set of job IDs already in the CSV for record-level dedup.
    Returns an empty set if the CSV does not exist or is empty.
    """
    if not path.exists(csv_path) or path.getsize(csv_path) == 0:
        return set()
    seen = set()
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                seen.add(row['ID'])
    except (OSError, KeyError) as exc:
        log.warning('Could not read existing CSV for dedup (%s) — starting fresh.', exc)
    log.info('Loaded %d existing job IDs from CSV.', len(seen))
    return seen


# ---------------------------------------------------------------------------
# Tech matching
# ---------------------------------------------------------------------------

def _match_technologies(searchable_text: str, tech_table: list[dict]) -> str:
    """
    Find which technologies from the dimension table appear in the job text.
    Returns a comma-separated string of matched Adzuna terms.

    Why (?<![A-Z0-9]) instead of \\b:
      \\b only fires at transitions between \\w and \\W chars.
      '#' and '+' are \\W, so \\bC\\#\\b fails to match 'C#' at end of token.
      Negative lookahead/lookbehind on [A-Z0-9] correctly anchors symbol-
      containing names like C#, C++, F# without false positives inside words.
    """
    matched = []
    for entry in tech_table:
        term = entry['Adzuna']  # already uppercase in the dimension table
        pattern = r'(?<![A-Z0-9])' + re.escape(term) + r'(?![A-Z0-9])'
        if re.search(pattern, searchable_text):
            matched.append(term)
    return ','.join(matched)


# ---------------------------------------------------------------------------
# Core extractor
# ---------------------------------------------------------------------------

def extract_job_rows(
    json_path: str,
    tech_table: list[dict],
    seen_ids: set,
) -> list[list]:
    """
    Parse one daily JSON file and return a list of CSV rows.

    Each row: [job_id, created_date, technologies_string]

    - Records whose ID is already in seen_ids are skipped (dedup).
    - Records with missing required fields are logged and skipped.
    - File-level errors (bad JSON, missing file) return an empty list
      so the rest of the run continues uninterrupted.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except FileNotFoundError:
        log.error('JSON file disappeared before it could be read: %s', json_path)
        return []
    except json.JSONDecodeError as exc:
        log.error('Corrupt JSON in %s: %s', path.basename(json_path), exc)
        return []

    if not isinstance(jobs, list):
        log.error(
            'Expected a list in %s, got %s — skipping.',
            path.basename(json_path), type(jobs).__name__,
        )
        return []

    rows = []
    for job in jobs:
        # --- ID ---
        job_id = job.get('id')
        if not job_id:
            log.warning('Record with missing "id" skipped in %s.', path.basename(json_path))
            continue
        job_id = str(job_id)   # IDs can be int in JSON; normalise to str

        if job_id in seen_ids:
            continue

        # --- Date ---
        created_raw = job.get('created', '')
        if not created_raw:
            log.warning('Job %s skipped: missing "created" field.', job_id)
            continue
        created_date = created_raw[:10]     # "2024-01-15T10:30:00Z" -> "2024-01-15"

        # --- Tech matching ---
        title       = job.get('title', '')
        description = job.get('description', '')
        combined    = (title + ' ' + description).upper()
        # Keep only uppercase letters, spaces, # and + (needed for C#, C++)
        searchable_text = re.sub(r'[^A-Z #+]', ' ', combined)

        technologies = _match_technologies(searchable_text, tech_table)

        rows.append([job_id, created_date, technologies])

    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    log.info('=== build_jobs_csv.py started ===')

    tech_table     = load_tech_table(TECH_TABLE_PATH)
    processed_set  = load_processed_files(PROCESSED_FILES_PATH)
    seen_ids       = load_seen_ids(JOBS_CSV_PATH)
    all_json_files = glob.glob(DAILY_JSON_GLOB)

    log.info('Found %d JSON file(s) in folder.', len(all_json_files))

    needs_header = (
        not path.exists(JOBS_CSV_PATH) or path.getsize(JOBS_CSV_PATH) == 0
    )

    total_new_rows  = 0
    newly_processed = []

    try:
        with open(JOBS_CSV_PATH, 'a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            if needs_header:
                writer.writerow(CSV_HEADER)
                log.info('New CSV — header written.')

            for json_file in sorted(all_json_files):   # sorted = deterministic order
                if json_file in processed_set:
                    log.info('Skip (already processed): %s', path.basename(json_file))
                    continue

                rows = extract_job_rows(json_file, tech_table, seen_ids)

                if rows:
                    writer.writerows(rows)
                    # Update in memory so the NEXT file in this run also deduplicates
                    # against records added by this file — no need to re-read the CSV.
                    seen_ids.update(row[0] for row in rows)

                total_new_rows  += len(rows)
                newly_processed.append(json_file)
                log.info(
                    'Processed %-30s  +%d rows',
                    path.basename(json_file), len(rows),
                )

    except OSError as exc:
        log.error('Failed to write to CSV: %s', exc)
        sys.exit(1)

    # Persist newly processed file paths to the manifest
    try:
        with open(PROCESSED_FILES_PATH, 'a', encoding='utf-8') as manifest:
            for filepath in newly_processed:
                manifest.write(filepath + '\n')
    except OSError as exc:
        log.warning(
            'Could not update manifest: %s — re-run is safe (dedup will handle it).', exc
        )

    log.info(
        '=== Done. %d new row(s) written from %d file(s). %d total known IDs. ===',
        total_new_rows, len(newly_processed), len(seen_ids),
    )
