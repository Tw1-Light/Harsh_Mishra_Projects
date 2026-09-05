"""
classifier.py
-------------
Rule-based quality classifier and technology relevance scorer for GitHub repos.

Two independent scores — per github_ecosystem_process.md section 7:
  quality_score    → maps to quality_class (project/educational/collection/other/uncertain)
  relevance_score  → float 0..N based on how relevant the repo is to the target technology

Design decisions:
  - Uses only Repository Search fields (name, description, topics, language,
    fork, archived, disabled, stargazers_count, pushed_at).
  - Does NOT fetch READMEs, commits, contributors, or any extra endpoints.
  - Weights are in config.py so they can be tuned after validation without
    touching this file.
  - classify_repo() and score_relevance() are pure functions — no I/O,
    easy to unit-test in isolation.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from config import (
    ACTIVE_WINDOW_DAYS,
    CONTAMINATION_WEIGHTS,
    HARD_EXCLUDE_FLAGS,
    QUALITY_POSITIVE,
    QUALITY_THRESHOLDS,
    RELEVANCE_THRESHOLD,
    RELEVANCE_WEIGHTS,
    STAR_SIGNAL_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _searchable_text(repo: dict[str, Any]) -> str:
    """
    Build a single normalised lowercase string from the fields used for
    contamination detection: name, description, topics.

    Topics is a list of strings; join with spaces so keyword matching works
    uniformly across all three fields.
    """
    name = repo.get("name") or ""
    desc = repo.get("description") or ""
    topics: list[str] = repo.get("topics") or []
    combined = f"{name} {desc} {' '.join(topics)}"
    return combined.lower()


def _tokenize(text: str) -> list[str]:
    """
    Split text into tokens, treating hyphens and underscores as word
    separators in addition to whitespace. This catches variants like
    'awesome-list' appearing as a single token or split.
    """
    return re.split(r"[\s\-_]+", text)


def _contamination_score(repo: dict[str, Any]) -> tuple[float, str | None]:
    """
    Score contamination signals from name+description+topics.

    Returns:
        (score, dominant_class) where dominant_class is 'educational' or
        'collection' if one category clearly dominates, else None.

    Score = sum of weights for every matched contamination keyword.
    Matched against the searchable text AND against individual topic slugs
    (topic slugs are exact strings like 'awesome-list', so they must be
    checked by exact containment rather than tokenized word matching).
    """
    text = _searchable_text(repo)
    topics: list[str] = [t.lower() for t in (repo.get("topics") or [])]

    total_score = 0.0
    collection_score = 0.0
    educational_score = 0.0

    collection_keywords = {
        "awesome-list", "awesome_list", "curated", "resource-collection",
        "resource_collection", "resources", "awesome", "collection",
        "collections", "books", "book",
    }
    educational_keywords = set(CONTAMINATION_WEIGHTS.keys()) - collection_keywords

    for keyword, weight in CONTAMINATION_WEIGHTS.items():
        matched = False
        # Check exact topic match first (topics are already lowercase slugs)
        if keyword in topics:
            matched = True
        # Then check tokenized text match
        elif keyword.replace("-", " ").replace("_", " ") in text.replace("-", " ").replace("_", " "):
            matched = True

        if matched:
            total_score += weight
            if keyword in collection_keywords:
                collection_score += weight
            else:
                educational_score += weight

    dominant: str | None = None
    if collection_score >= 4.0 or "awesome-list" in topics or "awesome_list" in topics:
        dominant = "collection"
    elif educational_score >= 5.0:
        dominant = "educational"

    return total_score, dominant


def _positive_quality_bonus(repo: dict[str, Any]) -> float:
    """
    Calculate positive quality signal score to offset weak contamination.
    """
    bonus = 0.0

    if repo.get("description"):
        bonus += QUALITY_POSITIVE["has_description"]

    if repo.get("topics"):
        bonus += QUALITY_POSITIVE["has_topics"]

    pushed_at_str = repo.get("pushed_at")
    if pushed_at_str:
        try:
            pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - pushed_at).days
            if age_days <= ACTIVE_WINDOW_DAYS:
                bonus += QUALITY_POSITIVE["recent_push"]
        except (ValueError, TypeError):
            pass

    if (repo.get("stargazers_count") or 0) > STAR_SIGNAL_THRESHOLD:
        bonus += QUALITY_POSITIVE["high_star_count"]

    return bonus


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_repo(repo: dict[str, Any]) -> dict[str, Any]:
    """
    Classify a single repo record and return classification fields.

    Returns a dict with:
        hard_excluded    bool   — True if fork/archived/disabled
        exclude_reason   str|None
        quality_class    str    — project/educational/collection/other/uncertain
        quality_score    float  — raw net score (contamination - bonus); lower = better
        quality_notes    str    — human-readable explanation of the top signals

    The caller merges this dict into the repo record before writing to disk.
    """
    # Hard exclusion check — these are not scored, just flagged
    for flag in HARD_EXCLUDE_FLAGS:
        if repo.get(flag):
            return {
                "hard_excluded":  True,
                "exclude_reason": flag,
                "quality_class":  "excluded",
                "quality_score":  None,
                "quality_notes":  f"Hard-excluded: {flag}=True",
            }

    contamination, dominant = _contamination_score(repo)
    bonus = _positive_quality_bonus(repo)
    net_score = contamination - bonus

    # Determine quality_class from net_score and dominant signal
    if dominant == "collection":
        quality_class = "collection"
    elif dominant == "educational":
        quality_class = "educational"
    elif net_score >= QUALITY_THRESHOLDS["educational"]:
        quality_class = "educational"
    elif net_score >= QUALITY_THRESHOLDS["uncertain"]:
        quality_class = "uncertain"
    elif not repo.get("description") and not repo.get("topics"):
        # No contamination signal AND no positive signals → other (not enough info)
        quality_class = "other"
    else:
        quality_class = "project"

    notes_parts = []
    if contamination > 0:
        notes_parts.append(f"contamination={contamination:.1f}")
    if bonus > 0:
        notes_parts.append(f"bonus={bonus:.1f}")
    if dominant:
        notes_parts.append(f"dominant={dominant}")

    return {
        "hard_excluded":  False,
        "exclude_reason": None,
        "quality_class":  quality_class,
        "quality_score":  round(net_score, 2),
        "quality_notes":  "; ".join(notes_parts) if notes_parts else "no strong signals",
    }


def score_relevance(repo: dict[str, Any], tech_config: dict[str, Any]) -> dict[str, Any]:
    """
    Score how relevant a repo is to the target technology.

    tech_config must contain:
        canonical_name  str
        aliases         list[str]        (may be empty)
        languages       list[str]        (e.g. ['Python'])
        topics          list[str]        (e.g. ['python', 'django'])

    Returns a dict with:
        relevance_score  float   — sum of matched signal weights; higher = more relevant
        relevance_notes  str     — matched signals for auditability
        is_usable        bool    — relevance_score >= RELEVANCE_THRESHOLD

    Scoring is additive: language match + topic matches + name/desc matches.
    A repo can exceed RELEVANCE_THRESHOLD through multiple weak signals.
    """
    canonical: str = (tech_config.get("canonical_name") or "").lower()
    aliases: list[str] = [a.lower() for a in (tech_config.get("aliases") or [])]
    target_languages: list[str] = [l.lower() for l in (tech_config.get("languages") or [])]
    target_topics: list[str] = [t.lower() for t in (tech_config.get("topics") or [])]

    repo_language = (repo.get("language") or "").lower()
    repo_topics: list[str] = [t.lower() for t in (repo.get("topics") or [])]
    repo_name = (repo.get("name") or "").lower()
    repo_desc = (repo.get("description") or "").lower()

    score = 0.0
    matched: list[str] = []

    # Language match
    if repo_language and repo_language in target_languages:
        score += RELEVANCE_WEIGHTS["language_exact_match"]
        matched.append(f"language:{repo_language}")

    # Topic matches (additive per topic — up to N topics can match)
    for topic in target_topics:
        if topic in repo_topics:
            score += RELEVANCE_WEIGHTS["topic_exact_match"]
            matched.append(f"topic:{topic}")

    # Name matches
    if canonical and canonical in repo_name:
        score += RELEVANCE_WEIGHTS["name_canonical_match"]
        matched.append("name:canonical")
    for alias in aliases:
        if alias and alias in repo_name:
            score += RELEVANCE_WEIGHTS["name_alias_match"]
            matched.append(f"name:alias:{alias}")

    # Description matches
    if canonical and canonical in repo_desc:
        score += RELEVANCE_WEIGHTS["desc_canonical_match"]
        matched.append("desc:canonical")
    for alias in aliases:
        if alias and alias in repo_desc:
            score += RELEVANCE_WEIGHTS["desc_alias_match"]
            matched.append(f"desc:alias:{alias}")

    return {
        "relevance_score": round(score, 2),
        "relevance_notes": ", ".join(matched) if matched else "no signals matched",
        "is_usable":       score >= RELEVANCE_THRESHOLD,
    }


def is_usable_repo(classified: dict[str, Any]) -> bool:
    """
    Returns True if a fully classified repo (combined quality + relevance fields)
    should be counted in the ecosystem snapshot.

    A usable repo must:
      - not be hard-excluded
      - have quality_class == 'project' or 'uncertain' (not educational/collection/other)
      - have is_usable == True (relevance_score >= threshold)
    """
    if classified.get("hard_excluded"):
        return False
    if classified.get("quality_class") not in ("project", "uncertain"):
        return False
    return classified.get("is_usable", False)
