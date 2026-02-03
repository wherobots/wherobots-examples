#!/usr/bin/env python3
"""
Update docs.json navigation with converted MDX notebooks.

This script updates the wherobots/docs docs.json file to include
example notebooks under the "Spatial Analytics Tutorials" tab.
"""

import json
import argparse
from pathlib import Path


# Mapping of notebook filename (stem) to its location path in docs.json navigation.
# Each path is a list of group names to traverse to reach the target pages list.
# Empty list means notebook is not included in navigation.
NOTEBOOK_LOCATIONS = {
    # Getting Started (top-level group)
    "Part-1-Loading-Data": ["Getting Started"],
    "Part-2-Reading-Spatial-Files": ["Getting Started"],
    "Part-3-Accelerating-Geospatial-Datasets": ["Getting Started"],
    "Part-4-Spatial-Joins": ["Getting Started"],
    # WherobotsDB > Vector Tiles (PMTiles)
    "PMTiles-railroad": ["WherobotsDB", "Vector Tiles (PMTiles)"],
    # Data Connections
    "Unity-Catalog-Delta-Tables": ["Data Connections"],
    "STAC-Reader": ["Data Connections"],
    "ESA-WorldCover": ["Data Connections"],
    "Foursquare-Places": ["Data Connections"],
    "NOAA-SWDI": ["Data Connections"],
    "Overture-Maps": ["Data Connections"],
    # RasterFlow
    "RasterFlow-CHM": ["RasterFlow"],
    "RasterFlow-Chesapeake": ["RasterFlow"],
    "RasterFlow-FTW": ["RasterFlow"],
    "RasterFlow-Tile2Net": ["RasterFlow"],
    "RasterFlow-Bring-Your-Own-Model": ["RasterFlow"],
    # Advanced Topics
    "Isochrones": ["Advanced Topics"],
    "Zonal-Stats-ESAWorldCover-Texas": ["Advanced Topics"],
    "Loading-Common-Spatial-File-Types": ["Advanced Topics"],
    "Map-Tile-Generation": ["Advanced Topics"],
    "Getting-Started": ["Advanced Topics"],  # Scala notebook
    # WherobotsAI > Spatial Statistics
    "Clustering-DBSCAN": ["WherobotsAI", "Spatial Statistics"],
    "Getis-Ord-Gi*": ["WherobotsAI", "Spatial Statistics"],
    "Local-Outlier-Factor": ["WherobotsAI", "Spatial Statistics"],
    "K-Nearest-Neighbor-Join": ["WherobotsAI", "Spatial Statistics"],
    # WherobotsAI (direct child)
    "GPS-Map-Matching": ["WherobotsAI"],
}

# Notebooks to exclude from navigation entirely
EXCLUDED_NOTEBOOKS = {"index"}


def find_group(pages: list, group_path: list[str]) -> list | None:
    """
    Find a nested group's pages list by following the path.

    Args:
        pages: The pages list to search within
        group_path: List of group names to traverse (e.g., ["WherobotsAI", "Spatial Statistics"])

    Returns:
        The pages list of the target group, or None if not found
    """
    current = pages
    for group_name in group_path:
        found = None
        for item in current:
            if isinstance(item, dict) and item.get("group") == group_name:
                found = item.get("pages", [])
                break
        if found is None:
            return None
        current = found
    return current


def collect_notebook_paths(notebooks_dir: Path) -> dict[str, str]:
    """
    Collect all MDX notebooks and return a mapping of filename stem to page path.

    Returns:
        Dict mapping notebook stem (e.g., "Part-1-Loading-Data") to
        page path (e.g., "tutorials/example-notebooks/Part-1-Loading-Data")
    """
    mdx_files = sorted(notebooks_dir.glob("*.mdx"))
    result = {}

    for mdx_file in mdx_files:
        name = mdx_file.stem
        if name not in EXCLUDED_NOTEBOOKS:
            result[name] = f"tutorials/example-notebooks/{name}"

    return result


def update_docs_json(docs_json_path: Path, notebook_paths: dict[str, str]) -> None:
    """
    Update docs.json by inserting notebook pages into their mapped locations.

    Args:
        docs_json_path: Path to the docs.json file
        notebook_paths: Dict mapping notebook stem to page path
    """
    with open(docs_json_path, "r", encoding="utf-8") as f:
        docs_config = json.load(f)

    # Find the "Spatial Analytics Tutorials" tab
    tabs = docs_config.get("navigation", {}).get("tabs", [])
    tutorials_tab = None

    for tab in tabs:
        if tab.get("tab") == "Spatial Analytics Tutorials":
            tutorials_tab = tab
            break

    if not tutorials_tab:
        print("Error: Could not find 'Spatial Analytics Tutorials' tab")
        return

    tutorials_pages = tutorials_tab.get("pages", [])
    inserted_count = 0
    skipped_notebooks = []

    # Insert each notebook into its mapped location
    for notebook_name, page_path in notebook_paths.items():
        if notebook_name not in NOTEBOOK_LOCATIONS:
            skipped_notebooks.append(notebook_name)
            continue

        group_path = NOTEBOOK_LOCATIONS[notebook_name]
        target_pages = find_group(tutorials_pages, group_path)

        if target_pages is None:
            print(
                f"Warning: Could not find group path {group_path} for {notebook_name}"
            )
            continue

        # Only add if not already present
        if page_path not in target_pages:
            target_pages.append(page_path)
            inserted_count += 1

    if skipped_notebooks:
        print(f"Skipped notebooks not in NOTEBOOK_LOCATIONS: {skipped_notebooks}")

    # Write back
    with open(docs_json_path, "w", encoding="utf-8") as f:
        json.dump(docs_config, f, indent=2)
        f.write("\n")

    print(f"Updated {docs_json_path}: inserted {inserted_count} notebook(s)")


def main():
    parser = argparse.ArgumentParser(description="Update docs.json navigation")
    parser.add_argument("--docs-json", required=True, help="Path to docs.json")
    parser.add_argument(
        "--notebooks-dir", required=True, help="Path to notebooks MDX directory"
    )

    args = parser.parse_args()

    docs_json_path = Path(args.docs_json)
    notebooks_dir = Path(args.notebooks_dir)

    if not docs_json_path.exists():
        print(f"Error: {docs_json_path} not found")
        return

    notebook_paths = collect_notebook_paths(notebooks_dir)

    if notebook_paths:
        update_docs_json(docs_json_path, notebook_paths)
    else:
        print("No notebooks to add to navigation")


if __name__ == "__main__":
    main()
