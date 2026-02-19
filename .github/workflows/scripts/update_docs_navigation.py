#!/usr/bin/env python3
"""
Update docs.json navigation with converted MDX notebooks.

This script updates the wherobots/docs docs.json file to include
example notebooks under the "Spatial Analytics Tutorials" tab.

It uses NOTEBOOK_LOCATIONS to map each notebook to its target location
in the docs.json navigation structure, supporting the nested group
hierarchy from wherobots/docs PR #144.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Optional


# Notebooks to exclude from navigation (e.g., deprecated or WIP)
EXCLUDED_NOTEBOOKS: set[str] = set()

# Mapping of notebook stems (lowercase with hyphens) to their target location
# in the docs.json navigation hierarchy. Each value is a list of group names
# representing the path to traverse to find the target "pages" array.
#
# These locations align with the new docs.json structure from wherobots/docs PR #144.
NOTEBOOK_LOCATIONS: dict[str, list[str]] = {
    # Getting Started group (top-level)
    "part-1-loading-data": ["Getting Started"],
    "part-2-reading-spatial-files": ["Getting Started"],
    "part-3-accelerating-geospatial-datasets": ["Getting Started"],
    "part-4-spatial-joins": ["Getting Started"],
    # WherobotsDB -> Vector Tiles (PMTiles)
    "pmtiles-railroad": ["WherobotsDB", "Vector Tiles (PMTiles)"],
    # Data Connections group (top-level)
    "unity-catalog-delta-tables": ["Data Connections"],
    "stac-reader": ["Data Connections"],
    "esa-worldcover": ["Data Connections"],
    "foursquare-places": ["Data Connections"],
    "noaa-swdi": ["Data Connections"],
    "overture-maps": ["Data Connections"],
    # RasterFlow group (top-level)
    "rasterflow-chm": ["RasterFlow"],
    "rasterflow-chesapeake": ["RasterFlow"],
    "rasterflow-changedetection": ["RasterFlow"],
    "rasterflow-ftw": ["RasterFlow"],
    "rasterflow-s2-mosaic": ["RasterFlow"],
    "rasterflow-tile2net": ["RasterFlow"],
    "rasterflow-bring-your-own-rasters-naip": ["RasterFlow"],
    "rasterflow-bring-your-own-model": ["RasterFlow"],
    # Advanced Topics group (top-level)
    "isochrones": ["Advanced Topics"],
    "zonal-stats-esaworldcover-texas": ["Advanced Topics"],
    "loading-common-spatial-file-types": ["Advanced Topics"],
    "map-tile-generation": ["Advanced Topics"],
    "getting-started": ["Advanced Topics"],  # Scala getting started
    # WherobotsAI -> Spatial Statistics
    "clustering-dbscan": ["WherobotsAI", "Spatial Statistics"],
    "getis-ord-gi*": ["WherobotsAI", "Spatial Statistics"],
    "local-outlier-factor": ["WherobotsAI", "Spatial Statistics"],
    "k-nearest-neighbor-join": ["WherobotsAI", "Spatial Statistics"],
    # GPS Map Matching is under WherobotsAI in PR #144
    "gps-map-matching": ["WherobotsAI"],
}


def find_group(pages: list, group_path: list[str]) -> Optional[list]:
    """
    Traverse the navigation structure to find the target group's pages array.

    Args:
        pages: The current level's pages array to search
        group_path: List of group names to traverse (e.g., ["WherobotsAI", "Spatial Statistics"])

    Returns:
        The target group's "pages" list if found, None otherwise
    """
    if not group_path:
        return pages

    target_group = group_path[0]
    remaining_path = group_path[1:]

    for item in pages:
        if isinstance(item, dict) and item.get("group") == target_group:
            nested_pages = item.setdefault("pages", [])
            if remaining_path:
                # Continue traversing deeper
                return find_group(nested_pages, remaining_path)
            else:
                # Found the target group, return its pages array
                return nested_pages

    return None


def collect_notebook_paths(notebooks_dir: Path) -> dict[str, str]:
    """
    Collect notebook MDX files and build a mapping of stem to page path.

    Args:
        notebooks_dir: Directory containing converted MDX notebook files

    Returns:
        Dict mapping notebook stem (e.g., "clustering-dbscan") to
        page path (e.g., "tutorials/example-notebooks/clustering-dbscan")
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
    Update docs.json by inserting notebook pages into their mapped locations
    and removing stale notebook entries that are no longer discovered.

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

    tutorials_pages = tutorials_tab.setdefault("pages", [])
    inserted_count = 0
    removed_count = 0
    skipped_notebooks = []

    # Collect all valid notebook page paths for stale entry detection
    all_valid_paths = set(notebook_paths.values())

    # Group notebooks by their target location to avoid redundant find_group() calls
    notebooks_by_location: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for notebook_name, page_path in notebook_paths.items():
        if notebook_name not in NOTEBOOK_LOCATIONS:
            skipped_notebooks.append(notebook_name)
            continue
        location = tuple(NOTEBOOK_LOCATIONS[notebook_name])
        notebooks_by_location[location].append(page_path)

    # Collect all group paths that have mapped notebooks (for stale removal)
    all_group_paths = set(notebooks_by_location.keys())
    # Also include group paths from NOTEBOOK_LOCATIONS that may have no current notebooks
    for loc in NOTEBOOK_LOCATIONS.values():
        all_group_paths.add(tuple(loc))

    # Insert notebooks and remove stale entries, one find_group() call per unique location
    # Sort by group_path for deterministic output
    for group_path in sorted(all_group_paths):
        target_pages = find_group(tutorials_pages, list(group_path))

        if target_pages is None:
            continue

        # Remove stale notebook entries (auto-inserted paths no longer in discovery set)
        stale = [
            p
            for p in target_pages
            if isinstance(p, str)
            and p.startswith("tutorials/example-notebooks/")
            and p not in all_valid_paths
        ]
        for p in stale:
            target_pages.remove(p)
            removed_count += 1

        # Insert new notebooks for this location
        page_paths = sorted(notebooks_by_location.get(group_path, []))
        for page_path in page_paths:
            # Only add if not already present
            if page_path not in target_pages:
                target_pages.append(page_path)
                inserted_count += 1

    if skipped_notebooks:
        print(
            f"Skipped notebooks not in NOTEBOOK_LOCATIONS: {sorted(skipped_notebooks)}"
        )

    # Write back
    with open(docs_json_path, "w", encoding="utf-8") as f:
        json.dump(docs_config, f, indent=2)
        f.write("\n")

    print(
        f"Updated {docs_json_path}: inserted {inserted_count}, removed {removed_count} notebook(s)"
    )


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

    if not notebooks_dir.exists():
        print(f"Error: {notebooks_dir} not found")
        return

    notebook_paths = collect_notebook_paths(notebooks_dir)

    if notebook_paths:
        update_docs_json(docs_json_path, notebook_paths)
    else:
        print("No notebooks to add to navigation")


if __name__ == "__main__":
    main()
