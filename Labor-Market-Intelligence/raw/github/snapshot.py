"""
snapshot.py
-----------
Computes ecosystem snapshot metrics from a list of classified + scored repo records.

All metrics defined per github_ecosystem_process.md sections 10–13.
This module is pure computation — no I/O, no API calls.

Inputs:
    repos           list of fully classified repo dicts (from github_extractor.py)
    prev_repo_ids   set of repo IDs from the previous snapshot (for turnover calculation)
                    Pass an empty set if this is the first snapshot.

Output:
    A single dict representing one ecosystem snapshot row.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any

from config import ACTIVE_WINDOW_DAYS, ECOSYSTEM_STATES
from classifier import is_usable_repo


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _days_since(timestamp_str: str | None) -> int | None:
    """Parse an ISO-8601 timestamp and return days since then. None on error."""
    if not timestamp_str:
        return None
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return None


def _star_concentration(usable_repos: list[dict], top_n: int) -> float:
    """
    Share of total usable-repo stars held by the top_n most-starred repos.
    Returns 0.0 if there are no usable repos or total stars == 0.
    """
    if not usable_repos:
        return 0.0
    sorted_by_stars = sorted(
        usable_repos, key=lambda r: r.get("stargazers_count") or 0, reverse=True
    )
    total_stars = sum(r.get("stargazers_count") or 0 for r in usable_repos)
    if total_stars == 0:
        return 0.0
    top_stars = sum(r.get("stargazers_count") or 0 for r in sorted_by_stars[:top_n])
    return round(top_stars / total_stars, 4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_snapshot(
    technology: str,
    snapshot_date: str,
    repos: list[dict[str, Any]],
    prev_repo_ids: set[int],
    observed_count: int,
) -> dict[str, Any]:
    """
    Compute an ecosystem snapshot from classified repo records.

    Parameters
    ----------
    technology      : canonical technology name
    snapshot_date   : ISO date string (YYYY-MM-DD) of this snapshot
    repos           : list of repo dicts, each with classification fields added
    prev_repo_ids   : set of repo IDs from the previous snapshot (empty = first run)
    observed_count  : total_count from GitHub Search API response

    Returns
    -------
    A flat dict with all snapshot metrics, ready to write to JSON.
    """
    usable = [r for r in repos if is_usable_repo(r)]
    usable_count = len(usable)

    # ── Median stars & forks ──────────────────────────────────────────────
    stars_list = [r.get("stargazers_count") or 0 for r in usable]
    forks_list = [r.get("forks_count") or 0 for r in usable]

    median_stars = round(statistics.median(stars_list), 1) if stars_list else 0.0
    median_forks = round(statistics.median(forks_list), 1) if forks_list else 0.0

    # ── Active repository ratio ───────────────────────────────────────────
    active_count = sum(
        1 for r in usable
        if ((_days_since(r.get("pushed_at"))) or 999) <= ACTIVE_WINDOW_DAYS
    )
    active_ratio = round(active_count / usable_count, 4) if usable_count else 0.0

    # ── Star concentration ────────────────────────────────────────────────
    top1_concentration = _star_concentration(usable, 1)
    top5_concentration = _star_concentration(usable, 5)

    # ── New-to-top-100 turnover ───────────────────────────────────────────
    # How many usable repo IDs this snapshot were NOT in the previous snapshot.
    # Only meaningful when prev_repo_ids is non-empty.
    current_ids = {r.get("id") for r in usable if r.get("id") is not None}
    if prev_repo_ids:
        new_ids = current_ids - prev_repo_ids
        turnover_ratio = round(len(new_ids) / usable_count, 4) if usable_count else 0.0
    else:
        # First snapshot — no previous to compare against
        new_ids = set()
        turnover_ratio = None  # explicitly None, not 0, to signal "no prior snapshot"

    return {
        "technology":              technology,
        "snapshot_date":           snapshot_date,
        "observed_repositories":   observed_count,
        "usable_repositories":     usable_count,
        "median_stars":            median_stars,
        "median_forks":            median_forks,
        "active_repository_ratio": active_ratio,
        "top1_star_concentration": top1_concentration,
        "top5_star_concentration": top5_concentration,
        "new_to_top100_ratio":     turnover_ratio,
        # Metadata for debugging / staging
        "_active_window_days":     ACTIVE_WINDOW_DAYS,
        "_new_repo_ids":           list(new_ids),
        "_usable_repo_ids":        list(current_ids),
    }


def compute_trend(
    current: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute delta metrics between two consecutive snapshots.

    Parameters
    ----------
    current  : snapshot dict from this run
    previous : snapshot dict from the previous run

    Returns
    -------
    Dict with delta fields + an ecosystem_state label.
    """

    def _safe_delta(curr_val, prev_val):
        """Return absolute and percent delta; None if either value is missing."""
        if curr_val is None or prev_val is None:
            return None, None
        abs_delta = curr_val - prev_val
        pct_delta = (abs_delta / prev_val) if prev_val != 0 else None
        return round(abs_delta, 4), round(pct_delta, 4) if pct_delta is not None else None

    repos_abs, repos_pct = _safe_delta(
        current.get("usable_repositories"), previous.get("usable_repositories")
    )
    stars_abs, stars_pct = _safe_delta(
        current.get("median_stars"), previous.get("median_stars")
    )
    forks_abs, forks_pct = _safe_delta(
        current.get("median_forks"), previous.get("median_forks")
    )
    active_abs, _ = _safe_delta(
        current.get("active_repository_ratio"), previous.get("active_repository_ratio")
    )
    turnover_abs, _ = _safe_delta(
        current.get("new_to_top100_ratio"), previous.get("new_to_top100_ratio")
    )
    conc_abs, _ = _safe_delta(
        current.get("top5_star_concentration"), previous.get("top5_star_concentration")
    )

    # ── Ecosystem state label ─────────────────────────────────────────────
    state = _classify_state(repos_pct, stars_pct)

    return {
        "technology":                current.get("technology"),
        "current_snapshot_date":     current.get("snapshot_date"),
        "previous_snapshot_date":    previous.get("snapshot_date"),
        "delta_usable_repositories": repos_abs,
        "delta_usable_repos_pct":    repos_pct,
        "delta_median_stars":        stars_abs,
        "delta_median_stars_pct":    stars_pct,
        "delta_median_forks":        forks_abs,
        "delta_active_ratio":        active_abs,
        "delta_turnover":            turnover_abs,
        "delta_concentration":       conc_abs,
        "ecosystem_state":           state,
    }


def _classify_state(repos_pct: float | None, stars_pct: float | None) -> str:
    """
    Map (repos_delta_pct, stars_delta_pct) to an ecosystem state label.
    Thresholds defined in config.ECOSYSTEM_STATES.
    Returns 'unknown' when either delta is None (e.g. first snapshot).
    """
    if repos_pct is None or stars_pct is None:
        return "unknown"

    # Walk states from most positive to most negative
    state_order = ["thriving", "growing", "stable", "mature", "weakening", "declining"]
    for state in state_order:
        thresholds = ECOSYSTEM_STATES.get(state, {})
        if (repos_pct >= thresholds.get("min_repos_delta", float("-inf")) and
                stars_pct >= thresholds.get("min_stars_delta", float("-inf"))):
            return state

    return "declining"
