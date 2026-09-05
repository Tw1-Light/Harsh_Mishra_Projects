
import pandas as pd
import os
import json

# --- Paths ---
SURVEY_CSV_PATH = os.path.join(os.path.dirname(__file__), 'survey_result.csv')
TECH_LIST_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'tech_list.json')

# Columns from the SO survey that contain technology names (semicolon-delimited per row)
TECH_COLUMNS = [
    "LanguageHaveWorkedWith", "LanguageWantToWorkWith", "LanguageAdmired",
    "DatabaseHaveWorkedWith", "DatabaseWantToWorkWith", "DatabaseAdmired",
    "WebframeHaveWorkedWith", "WebframeWantToWorkWith", "WebframeAdmired",
    "PlatformHaveWorkedWith", "PlatformWantToWorkWith", "PlatformAdmired"
]

# Each group maps a category label to its source columns.
# These will be merged per category before deduplication.
CATEGORY_SOURCE_MAP = {
    'Language': ["LanguageHaveWorkedWith", "LanguageWantToWorkWith", "LanguageAdmired"],
    'Database': ["DatabaseHaveWorkedWith", "DatabaseWantToWorkWith", "DatabaseAdmired"],
    'Webframe': ["WebframeHaveWorkedWith", "WebframeWantToWorkWith", "WebframeAdmired"],
    'Platform': ["PlatformHaveWorkedWith", "PlatformWantToWorkWith", "PlatformAdmired"],
}


def extract_unique_technologies(df, category_source_map):
    """
    From a DataFrame of semicolon-delimited SO survey tech columns,
    merge related columns per category, explode into individual tech names,
    and return a sorted list of unique technology names across all categories.

    Args:
        df: DataFrame containing only the tech columns.
        category_source_map: dict mapping category label -> list of source column names.

    Returns:
        Sorted list of unique, non-empty technology name strings.
    """
    # Build an intermediate DataFrame with one merged column per category.
    # Each cell becomes a list of tech names (split from the semicolon-joined row).
    merged_df = pd.DataFrame()
    for category, source_cols in category_source_map.items():
        merged_df[category] = (
            df[source_cols]
            .agg(lambda row: ';'.join(row.dropna()), axis=1)
            .str.split(';')
        )

    # Explode each category column and collect all unique tech names into a set
    unique_techs = set()
    for category in merged_df.columns:
        unique_techs.update(merged_df[category].explode())

    # Discard empty strings that arise when an entire row had no values
    unique_techs.discard('')

    return sorted(unique_techs)


if __name__ == '__main__':
    # Load only the technology columns from the survey (avoids loading 80+ irrelevant columns)
    survey_df = pd.read_csv(SURVEY_CSV_PATH, usecols=TECH_COLUMNS)

    # Extract deduplicated, sorted list of all unique technology names
    unique_tech_list = extract_unique_technologies(
        df=survey_df,
        category_source_map=CATEGORY_SOURCE_MAP
    )

    # Persist to JSON — consumed by the GitHub extractor as its query input list
    with open(TECH_LIST_OUTPUT_PATH, 'w') as f:
        json.dump(unique_tech_list, f, indent=2)

    print(f"Saved {len(unique_tech_list)} unique technologies to {TECH_LIST_OUTPUT_PATH}")
