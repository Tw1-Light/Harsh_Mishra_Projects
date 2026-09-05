"""
curated_tech.py
---------------
Builds tech_dimension_table.json — a crosswalk that maps each technology name
from the Stack Overflow Developer Survey to:
  - its GitHub topic slug  (used to search repos via the GitHub Search API)
  - its Adzuna search term (used to keyword-match job descriptions / titles)

Resolution order for the GitHub topic slug:
  1. Manual override table  (github_override.json) — handles symbols like C++, C#
  2. Local topic list       (topics_with_aliases.txt) — no-dot slug, e.g. "nodejs"
  3. Local topic list       — dot-literal slug,   e.g. "nodedotjs"
  4. GitHub Search API      — confirms slug exists with at least 1 real repo
  5. None                   — logged as unresolved; add to github_override.json manually

Run once to seed the table. Re-run whenever tech_list.json is updated.
"""

import json
import re
import sys
from os import path,getenv

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Constants — module-level paths in UPPER_SNAKE_CASE (Python convention for
# module-level constants, as specified in PEP 8)
# ---------------------------------------------------------------------------
_BASE_DIR = path.dirname(__file__)

TECH_TABLE_PATH    = path.join(_BASE_DIR, "tech_dimension_table.json")
GITHUB_TOPICS_PATH = path.join(_BASE_DIR, "github", "topics_with_aliases.txt")
SO_TECH_LIST_PATH  = path.join(_BASE_DIR, "stackoverflow", "tech_list.json")
OVERRIDE_PATH      = path.join(_BASE_DIR, "stackoverflow", "github_override.json")

API_TIMEOUT = 10  # seconds — prevents requests.get() from hanging forever

# Load .env and build the Authorization header.
# Unauthenticated GitHub Search API: 10 requests/minute, 60/hour.
# Authenticated:                     30 requests/minute, 5,000/hour.
# Without the token this script will hit the rate limit after ~10 API calls.
load_dotenv()
_token = getenv("GitHub_access_token")
GITHUB_HEADERS = {"Authorization": f"token {_token}"} if _token else {}
if not _token:
    print("[WARN] GITHUB_ACCESS_TOKEN not found in .env — running unauthenticated (low rate limit).")


# ---------------------------------------------------------------------------
# Data loaders — called once in the main builder, not once per tech
# (opening and reading a file 141 times in a loop is wasteful I/O)
# ---------------------------------------------------------------------------

def load_topic_set(topics_path: str) -> set:
    """
    Read the comma-separated topics file into a Python set.
    A set gives O(1) membership checks — 'slug in topic_set' is instant
    regardless of how many topics are in the file.
    """
    with open(topics_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    return {item.strip() for item in raw.split(",")}


def load_overrides(override_path: str) -> dict:
    """
    Load manual SO-name → GitHub-topic mappings.
    Keys are normalised to lowercase so the lookup is case-insensitive.
    This is what allows 'C++' → 'cpp' and 'Node.js' → 'nodejs' to work
    regardless of capitalisation in the SO survey.
    """
    with open(override_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k.lower(): v for k, v in raw.items()}


# ---------------------------------------------------------------------------
# GitHub API helper
# ---------------------------------------------------------------------------

def topic_exists_on_github(slug: str) -> bool:
    """
    Return True only if at least one GitHub repository uses this topic slug.

    Why check total_count and not just status_code?
    GitHub's Search API returns HTTP 200 even when zero repositories match.
    A 200 with total_count == 0 means the slug is valid syntax but no real
    project uses it — which is not a useful topic for our pipeline.
    """
    try:
        url = f"https://api.github.com/search/repositories?q=topic:{slug}&per_page=1"
        response = requests.get(url, headers=GITHUB_HEADERS, timeout=API_TIMEOUT)

        if response.status_code == 200:
            return response.json().get("total_count", 0) > 0

        if response.status_code == 403:
            # 403 from GitHub Search API = rate limit exceeded
            print(f"  [WARN] GitHub rate limit hit checking '{slug}'. Skipping API fallback.")
            return False

        if response.status_code == 422:
            # 422 = slug contains invalid characters for GitHub topic syntax
            return False

        return False

    except requests.exceptions.Timeout:
        print(f"  [WARN] Request timed out checking GitHub topic '{slug}'.")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  [WARN] No network connection while checking '{slug}'.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  [WARN] Unexpected network error for '{slug}': {e}")
        return False


# ---------------------------------------------------------------------------
# Core resolution logic
# ---------------------------------------------------------------------------

def _extract_name_candidates(tech_name: str) -> list[str]:
    """
    For names that include a parenthetical, return both the base name
    and the content inside the brackets as separate candidates to try.

    This handles SO survey names like:
      'Amazon Web Services (AWS)'  → ['Amazon Web Services', 'AWS']
      'Bash/Shell (all shells)'    → ['Bash/Shell', 'all shells']
      'Maven (build tool)'         → ['Maven', 'build tool']
      'Python'                     → ['Python']  (no change)

    Why try both?
      The base name often slugifies to the real GitHub topic ('maven').
      The abbreviation is sometimes the canonical slug ('aws', 'aws-lambda').
      Trying both costs nothing locally and only 1-2 extra API calls if needed.
    """
    match = re.search(r'^(.*?)\s*\(([^)]+)\)\s*$', tech_name)
    if match:
        return [match.group(1).strip(), match.group(2).strip()]
    return [tech_name]


def _slugify(name: str) -> tuple[str, str]:
    """
    Convert a plain name string into the two GitHub topic slug variants.
      'Node.js' → ('nodejs', 'nodedotjs')
      'AWS'     → ('aws', 'aws')           (no dots, so both are identical)
    """
    cleaned = re.sub(r"[^a-z0-9. ]", "", name.lower()).strip()
    cleaned = cleaned.replace(" ", "-")
    return cleaned.replace(".", ""), cleaned.replace(".", "dot")

def resolve_github_topic(
    tech_name: str,
    topic_set: set,
    overrides: dict,
) -> str | None:
    """
    Resolve a SO tech name to a GitHub topic slug.

    Parameters
    ----------
    tech_name  : the exact string from SO survey e.g. "Node.js", "C++"
    topic_set  : pre-loaded set of valid GitHub topic slugs
    overrides  : pre-loaded dict of manual mappings (keys already lowercased)

    Returns the slug string, or None if unresolvable.
    """
    # Step 1 — Manual override on the full original name (case-insensitive)
    if tech_name.lower() in overrides:
        return overrides[tech_name.lower()]

    # Step 2 — Expand the name into candidates.
    # 'Amazon Web Services (AWS)' → ['Amazon Web Services', 'AWS']
    # 'Python'                    → ['Python']
    candidates = _extract_name_candidates(tech_name)

    # Build all slug variants for every candidate up front.
    # Collecting them first means we check the entire local topic set before
    # making any API calls, keeping the API call count as low as possible.
    all_slugs = []
    seen = set()  # deduplicate identical slugs across candidates
    for candidate in candidates:
        for slug in _slugify(candidate):
            if slug and slug not in seen:
                all_slugs.append(slug)
                seen.add(slug)

    # Step 3 — Check all slugs against the local topic list (no API cost)
    for slug in all_slugs:
        if slug in topic_set:
            return slug

    # Step 4 — GitHub API fallback for any slug not in the local list
    for slug in all_slugs:
        if topic_exists_on_github(slug):
            return slug

    return None


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_tech_dimension_table(
    so_path: str,
    topics_path: str,
    override_path: str,
) -> list[dict]:
    """
    Read tech_list.json and produce one dimension row per technology.

    Each row contains:
      index        — 1-based row number (stable across runs if SO list order is stable)
      StackOverflow — exact name from the SO Developer Survey
      Adzuna       — uppercased version used for keyword matching in job data
      Github_Topic — resolved slug for GitHub Search API queries (None = unresolved)
    """
    # Validate all input files exist before doing any work
    for label, file_path in [
        ("SO tech list",      so_path),
        ("GitHub topics file", topics_path),
        ("Override file",      override_path),
    ]:
        if not path.exists(file_path):
            sys.exit(f"[ERROR] {label} not found: {file_path}")

    # Load shared lookup data ONCE here, outside the loop.
    # Passing them into resolve_github_topic avoids re-reading the same
    # files 141 times (once per tech name).
    topic_set = load_topic_set(topics_path)
    overrides  = load_overrides(override_path)

    with open(so_path, "r", encoding="utf-8") as f:
        tech_names = json.load(f)

    table      = []
    unresolved = []

    for index, tech_name in enumerate(tech_names, start=1):
        github_slug = resolve_github_topic(tech_name, topic_set, overrides)

        if github_slug is None:
            unresolved.append(tech_name)
            print(f"  [MISS] No GitHub topic resolved for: '{tech_name}'")

        row = {
            "index":         index,
            "StackOverflow": tech_name,
            "Adzuna":        tech_name.upper(),
            "Github_Topic":  github_slug,
        }
        table.append(row)

    # Summary of unresolved entries — these need manual override entries
    if unresolved:
        print(f"\n[SUMMARY] {len(unresolved)} unresolved tech(s).")
        print("Add them to github_override.json with their correct slug:")
        for name in unresolved:
            print(f'  "{name}": "<correct-github-slug>"')

    return table


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Building tech dimension table...\n")

    tech_table = build_tech_dimension_table(
        SO_TECH_LIST_PATH,
        GITHUB_TOPICS_PATH,
        OVERRIDE_PATH,
    )

    with open(TECH_TABLE_PATH, "w", encoding="utf-8") as f:
        json.dump(tech_table, f, indent=4, ensure_ascii=False)

    print(f"\nDone. {len(tech_table)} rows written to:\n  {TECH_TABLE_PATH}")