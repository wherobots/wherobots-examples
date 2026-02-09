#!/usr/bin/env python3
"""
Update docs.json navigation with converted MDX notebooks.

This script updates the wherobots/docs docs.json file to include
example notebooks under the "Spatial Analytics Tutorials" tab.
"""

import json
import argparse
from pathlib import Path


# Full mapping of MDX filenames (without extension) to category groups
# Filenames are lowercase with hyphens (converted from notebook names)
FILENAME_TO_CATEGORY = {
    # Getting Started
    "part-1-loading-data": "Getting Started",
    "part-2-reading-spatial-files": "Getting Started",
    "part-3-accelerating-geospatial-datasets": "Getting Started",
    "part-4-spatial-joins": "Getting Started",
    # Analyzing Data
    "clustering-dbscan": "Analyzing Data",
    "getis-ord-gi*": "Analyzing Data",
    "gps-map-matching": "Analyzing Data",
    "isochrones": "Analyzing Data",
    "k-nearest-neighbor-join": "Analyzing Data",
    "local-outlier-factor": "Analyzing Data",
    "pmtiles-railroad": "Analyzing Data",
    "zonal-stats-esaworldcover-texas": "Analyzing Data",
    # RasterFlow
    "rasterflow-bring-your-own-model": "RasterFlow",
    "rasterflow-bring-your-own-rasters-naip": "RasterFlow",
    "rasterflow-changedetection": "RasterFlow",
    "rasterflow-chesapeake": "RasterFlow",
    "rasterflow-chm": "RasterFlow",
    "rasterflow-ftw": "RasterFlow",
    "rasterflow-s2-mosaic": "RasterFlow",
    "rasterflow-tile2net": "RasterFlow",
    # Reading and Writing Data
    "loading-common-spatial-file-types": "Reading and Writing Data",
    "map-tile-generation": "Reading and Writing Data",
    "stac-reader": "Reading and Writing Data",
    "unity-catalog-delta-tables": "Reading and Writing Data",
    # Open Data Connections
    "esa-worldcover": "Open Data Connections",
    "foursquare-places": "Open Data Connections",
    "noaa-swdi": "Open Data Connections",
    "overture-maps": "Open Data Connections",
    # Scala
    "getting-started": "Scala",
}

# Order of categories in navigation
CATEGORY_ORDER = [
    "Getting Started",
    "Analyzing Data",
    "RasterFlow",
    "Reading and Writing Data",
    "Open Data Connections",
    "Scala",
]


def get_category(filename: str) -> str:
    """Determine category for a notebook based on filename."""
    return FILENAME_TO_CATEGORY.get(filename, "Other")


def build_notebook_navigation(notebooks_dir: Path) -> list:
    """Build navigation structure for notebooks."""
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
    from collections import defaultdict

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

    # Group notebooks by their target location to avoid redundant find_group() calls
    notebooks_by_location: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for notebook_name, page_path in notebook_paths.items():
        if notebook_name not in NOTEBOOK_LOCATIONS:
            skipped_notebooks.append(notebook_name)
            continue
        location = tuple(NOTEBOOK_LOCATIONS[notebook_name])
        notebooks_by_location[location].append(page_path)

    # Insert notebooks, one find_group() call per unique location
    for group_path, page_paths in notebooks_by_location.items():
        target_pages = find_group(tutorials_pages, list(group_path))

        if target_pages is None:
            print(f"Warning: Could not find group path {list(group_path)}")
            continue

        for page_path in page_paths:
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
