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

    if not mdx_files:
        print("No MDX files found")
        return []

    # Organize by category
    categories: dict[str, list[str]] = {cat: [] for cat in CATEGORY_ORDER}
    categories["Other"] = []

    for mdx_file in mdx_files:
        name = mdx_file.stem  # filename without extension
        category = get_category(name)
        # Path relative to docs root (tutorials/example-notebooks/filename)
        page_path = f"tutorials/example-notebooks/{name}"

        if category not in categories:
            categories[category] = []
        categories[category].append(page_path)

    # Build navigation structure
    notebook_groups = []
    for category in CATEGORY_ORDER:
        pages = categories.get(category, [])
        if pages:
            notebook_groups.append({"group": category, "pages": sorted(pages)})

    # Add "Other" if it has pages
    if categories.get("Other"):
        notebook_groups.append({"group": "Other", "pages": sorted(categories["Other"])})

    return notebook_groups


def update_docs_json(docs_json_path: Path, notebook_groups: list) -> None:
    """Update docs.json with notebook navigation."""
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

    # Check if "Example Notebooks" group already exists
    pages = tutorials_tab.get("pages", [])
    example_notebooks_idx = None

    for i, page in enumerate(pages):
        if isinstance(page, dict) and page.get("group") == "Example Notebooks":
            example_notebooks_idx = i
            break

    # Build the Example Notebooks group
    example_notebooks_group = {"group": "Example Notebooks", "pages": notebook_groups}

    if example_notebooks_idx is not None:
        # Update existing
        pages[example_notebooks_idx] = example_notebooks_group
    else:
        # Add new - insert at the end
        pages.append(example_notebooks_group)

    # Write back
    with open(docs_json_path, "w", encoding="utf-8") as f:
        json.dump(docs_config, f, indent=2)
        f.write("\n")

    print(f"Updated {docs_json_path} with Example Notebooks navigation")


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

    notebook_groups = build_notebook_navigation(notebooks_dir)

    if notebook_groups:
        update_docs_json(docs_json_path, notebook_groups)
    else:
        print("No notebooks to add to navigation")


if __name__ == "__main__":
    main()
