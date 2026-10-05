#!/usr/bin/env python3
"""
Update docs.json navigation with converted MDX notebooks.

This script updates the wherobots/docs docs.json file to include
example notebooks under the legacy "Spatial Analytics Tutorials" tab or
the "Examples" tab and its nested root group.

It uses NOTEBOOK_LOCATIONS to map each notebook to its target location
in the docs.json navigation structure, supporting nested group hierarchies.
"""

import json
import argparse
from pathlib import Path
from typing import Optional


# Notebooks to exclude from navigation (e.g., deprecated or WIP)
EXCLUDED_NOTEBOOKS: set[str] = set()

# Mapping of notebook stems (lowercase with hyphens) to their target location
# in the docs.json navigation hierarchy. Each value is a list of group names
# representing the path to traverse to find the target "pages" array.
#
# These locations must match the actual group names in the "Spatial Analytics
# Tutorials" tab of docs.json.
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
    "noaa-swdi": ["Data Connections"],
    "overture-maps": ["Data Connections"],
    # RasterFlow group (top-level)
    "rasterflow-chm": ["RasterFlow"],
    "rasterflow-chesapeake": ["RasterFlow"],
    "rasterflow-changedetection": ["RasterFlow"],
    "rasterflow-ftw": ["RasterFlow"],
    "rasterflow-s2-mosaic": ["RasterFlow"],
    "rasterflow-naip-mosaic": ["RasterFlow"],
    "rasterflow-sam3": ["RasterFlow"],
    "rasterflow-tile2net": ["RasterFlow"],
    "rasterflow-bring-your-own-rasters-naip": ["RasterFlow"],
    "rasterflow-bring-your-own-model": ["RasterFlow"],
    # Advanced Topics group (top-level)
    "isochrones": ["Advanced Topics"],
    "california-coastal-flood-risk-analysis": ["Advanced Topics"],
    "zonal-stats-esaworldcover-texas": ["Advanced Topics"],
    "loading-common-spatial-file-types": ["Advanced Topics"],
    "map-tile-generation": ["Advanced Topics"],
    "getting-started": ["Advanced Topics"],  # Scala getting started
    # WherobotsAI -> Spatial Statistics
    "clustering-dbscan": ["GeoStats & Map Matching", "Spatial Statistics"],
    "getis-ord-gi*": ["GeoStats & Map Matching", "Spatial Statistics"],
    "local-outlier-factor": ["GeoStats & Map Matching", "Spatial Statistics"],
    "k-nearest-neighbor-join": ["GeoStats & Map Matching", "Spatial Statistics"],
    # GPS Map Matching is under WherobotsAI
    "gps-map-matching": ["GeoStats & Map Matching"],
}


EXAMPLES_GROUPS = {
    "Getting Started": "Beginner learning path",
    "WherobotsDB": "Spatial SQL and visualization",
    "Data Connections": "Data sources",
    "RasterFlow": "Raster imagery",
    "Advanced Topics": "Spatial SQL and visualization",
    "GeoStats & Map Matching": "Statistics and routing",
}


def notebook_location(name: str, examples: bool) -> list[str]:
    location = NOTEBOOK_LOCATIONS[name]
    if not examples:
        return location
    if name == "isochrones":
        return ["Statistics and routing"]
    chapter = EXAMPLES_GROUPS[location[0]]
    if location[-1] == "Spatial Statistics":
        return [chapter, "Spatial Statistics"]
    return [chapter]


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
        aliases = {target_group}
        if target_group == "GeoStats & Map Matching":
            aliases.add("WherobotsAI")
        if isinstance(item, dict) and item.get("group") in aliases:
            nested_pages = item.get("pages")
            if not isinstance(nested_pages, list):
                return None
            if remaining_path:
                # Continue traversing deeper
                return find_group(nested_pages, remaining_path)
            else:
                # Found the target group, return its pages array
                return nested_pages

    return None


def remove_stale_notebooks(pages: list, valid_paths: set[str]) -> int:
    removed = 0
    kept = []
    for item in pages:
        if isinstance(item, str) and item.startswith("tutorials/example-notebooks/") and item not in valid_paths:
            removed += 1
            continue
        if isinstance(item, dict) and isinstance(item.get("pages"), list):
            removed += remove_stale_notebooks(item["pages"], valid_paths)
        kept.append(item)
    pages[:] = kept
    return removed


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
    if not notebook_paths:
        raise ValueError("No converted notebooks discovered; refusing to remove notebook navigation")

    with open(docs_json_path, "r", encoding="utf-8") as f:
        docs_config = json.load(f)

    tabs = docs_config.get("navigation", {}).get("tabs", [])
    matches = [tab for tab in tabs if tab.get("tab") in {"Spatial Analytics Tutorials", "Examples"}]
    if len(matches) != 1:
        raise ValueError("Expected exactly one 'Spatial Analytics Tutorials' or 'Examples' tab")
    tutorials_tab = matches[0]
    tutorials_pages = tutorials_tab.get("pages")
    examples = tutorials_tab["tab"] == "Examples"
    if not isinstance(tutorials_pages, list):
        raise ValueError("Notebook tab must have a pages array")
    if examples:
        tutorials_pages = find_group(tutorials_pages, ["Examples"])
        if tutorials_pages is None:
            raise ValueError("Could not find the 'Examples' root group")

    unknown = sorted(set(notebook_paths) - set(NOTEBOOK_LOCATIONS))
    if unknown:
        raise ValueError(f"Add notebook routing to NOTEBOOK_LOCATIONS for: {unknown}")

    # Resolve every destination before changing any navigation or writing the file.
    destinations = {}
    for notebook_name in sorted(notebook_paths):
        location = notebook_location(notebook_name, examples)
        target_pages = find_group(tutorials_pages, location)
        if target_pages is None:
            raise ValueError(f"Could not find notebook group: {' > '.join(location)}")
        destinations[notebook_name] = target_pages

    inserted_count = 0
    removed_count = remove_stale_notebooks(tutorials_pages, set(notebook_paths.values()))
    for notebook_name, target_pages in destinations.items():
        page_path = notebook_paths[notebook_name]
        if page_path not in target_pages:
            target_pages.append(page_path)
            inserted_count += 1

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

    if not docs_json_path.is_file():
        parser.error(f"{docs_json_path} is not a file")

    if not notebooks_dir.is_dir():
        parser.error(f"{notebooks_dir} is not a directory")

    notebook_paths = collect_notebook_paths(notebooks_dir)

    try:
        update_docs_json(docs_json_path, notebook_paths)
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
