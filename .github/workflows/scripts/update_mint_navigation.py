#!/usr/bin/env python3
"""
Update mint.json navigation with converted MDX notebooks.

This script scans the docs/notebooks directory and updates the mint.json
navigation structure to include all notebooks organized by category.
"""

import json
from pathlib import Path


# Mapping of MDX filename prefixes/patterns to category groups
CATEGORY_MAPPINGS = {
    "Part-": "Getting Started",
    "RasterFlow-": "RasterFlow",
    "Clustering-": "Analyzing Data",
    "Getis-": "Analyzing Data",
    "GPS-": "Analyzing Data",
    "Isochrones": "Analyzing Data",
    "K-Nearest-": "Analyzing Data",
    "Local-Outlier-": "Analyzing Data",
    "PMTiles-": "Analyzing Data",
    "Zonal-": "Analyzing Data",
    "Loading-Common-": "Reading and Writing Data",
    "Map-Tile-": "Reading and Writing Data",
    "STAC-": "Reading and Writing Data",
    "Unity-": "Reading and Writing Data",
    "ESA-": "Open Data Connections",
    "Foursquare-": "Open Data Connections",
    "NOAA-": "Open Data Connections",
    "Overture-": "Open Data Connections",
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
    for prefix, category in CATEGORY_MAPPINGS.items():
        if filename.startswith(prefix):
            return category
    # Default to Scala for Getting-Started (scala version)
    if filename == "Getting-Started":
        return "Scala"
    return "Other"


def main():
    docs_dir = Path("docs")
    notebooks_dir = docs_dir / "notebooks"
    mint_json_path = docs_dir / "mint.json"

    # Collect all MDX files
    mdx_files = sorted(notebooks_dir.glob("*.mdx"))

    if not mdx_files:
        print("No MDX files found in docs/notebooks/")
        return

    # Organize by category
    categories: dict[str, list[str]] = {cat: [] for cat in CATEGORY_ORDER}
    categories["Other"] = []

    for mdx_file in mdx_files:
        name = mdx_file.stem  # filename without extension
        category = get_category(name)
        page_path = f"notebooks/{name}"

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

    # Build full mint.json structure
    mint_config = {
        "$schema": "https://mintlify.com/schema.json",
        "name": "Wherobots Examples",
        "navigation": [
            {
                "group": "Spatial Analytics Tutorials",
                "pages": [{"group": "Example Notebooks", "pages": notebook_groups}],
            }
        ],
    }

    # Write mint.json
    with open(mint_json_path, "w", encoding="utf-8") as f:
        json.dump(mint_config, f, indent=2)
        f.write("\n")

    print(
        f"Updated {mint_json_path} with {len(mdx_files)} notebooks in {len([c for c in categories.values() if c])} categories"
    )


if __name__ == "__main__":
    main()
