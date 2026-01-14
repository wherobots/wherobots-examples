#!/usr/bin/env python3
"""
Generate Mintlify navigation configuration for converted notebook examples.

This script scans MDX files and generates the navigation structure needed
for the Examples tab in docs.json. It outputs a JSON snippet that can be
merged into the main docs.json configuration.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional


# Map directory names to display titles and icons
CATEGORY_CONFIG = {
    "Getting_Started": {
        "title": "Getting Started",
        "icon": "rocket",
        "order": 1,
    },
    "Analyzing_Data": {
        "title": "Analyzing Data",
        "icon": "chart-line",
        "order": 2,
    },
    "Reading_and_Writing_Data": {
        "title": "Reading & Writing Data",
        "icon": "database",
        "order": 3,
    },
    "Open_Data_Connections": {
        "title": "Open Data Connections",
        "icon": "plug",
        "order": 4,
    },
    "Foreign_Catalogs": {
        "title": "Foreign Catalogs",
        "icon": "folder-tree",
        "order": 5,
    },
    "scala": {
        "title": "Scala",
        "icon": "code",
        "order": 6,
    },
}


def extract_title_from_mdx(mdx_path: Path) -> Optional[str]:
    """Extract the title from MDX frontmatter."""
    try:
        with open(mdx_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for title in frontmatter
        match = re.search(
            r'^---\s*\n.*?^title:\s*["\']?([^"\'\n]+)["\']?\s*$.*?^---',
            content,
            re.MULTILINE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
    except Exception:
        pass

    # Fallback to filename
    return mdx_path.stem.replace("_", " ").replace("-", " ")


def get_sort_key(filename: str) -> tuple:
    """Generate a sort key for ordering files."""
    # Extract any leading number (e.g., "Part_1_" -> 1)
    match = re.match(r"(?:Part_)?(\d+)", filename)
    if match:
        return (0, int(match.group(1)), filename.lower())
    return (1, 0, filename.lower())


def generate_navigation(examples_dir: Path) -> dict:
    """Generate navigation structure from MDX files."""
    categories = {}

    # Scan for MDX files
    for mdx_path in examples_dir.rglob("*.mdx"):
        rel_path = mdx_path.relative_to(examples_dir)
        parts = rel_path.parts

        if len(parts) >= 2:
            category = parts[0]
            # Page path for Mintlify (relative to docs root, no extension)
            page_path = f"examples/{rel_path.with_suffix('')}"
        else:
            category = "Other"
            page_path = f"examples/{rel_path.with_suffix('')}"

        if category not in categories:
            categories[category] = []

        categories[category].append(
            {
                "path": str(page_path),
                "filename": mdx_path.stem,
                "title": extract_title_from_mdx(mdx_path),
            }
        )

    # Sort pages within each category
    for category in categories:
        categories[category].sort(key=lambda x: get_sort_key(x["filename"]))

    # Build navigation groups
    groups = []
    sorted_categories = sorted(
        categories.keys(), key=lambda c: CATEGORY_CONFIG.get(c, {}).get("order", 99)
    )

    for category in sorted_categories:
        config = CATEGORY_CONFIG.get(
            category, {"title": category.replace("_", " "), "icon": "file"}
        )
        pages = [p["path"] for p in categories[category]]

        group = {
            "group": config["title"],
            "pages": pages,
        }

        if "icon" in config:
            group["icon"] = config["icon"]

        groups.append(group)

    return {
        "tab": "Examples",
        "icon": "book-open-cover",
        "groups": groups,
    }


def generate_full_examples_tab(examples_dir: Path) -> str:
    """Generate the complete Examples tab configuration as JSON."""
    nav = generate_navigation(examples_dir)
    return json.dumps(nav, indent=2)


def update_docs_json(docs_json_path: Path, examples_dir: Path) -> None:
    """Update docs.json with the Examples tab navigation."""
    # Read existing docs.json
    with open(docs_json_path, "r", encoding="utf-8") as f:
        docs_config = json.load(f)

    # Generate new examples navigation
    examples_tab = generate_navigation(examples_dir)

    # Get or create navigation structure
    navigation = docs_config.get("navigation", {})

    # Handle different navigation structures
    if "tabs" in navigation:
        # Find and replace/add Examples tab
        tabs = navigation["tabs"]
        examples_index = None

        for i, tab in enumerate(tabs):
            if tab.get("tab") == "Examples":
                examples_index = i
                break

        if examples_index is not None:
            tabs[examples_index] = examples_tab
        else:
            tabs.append(examples_tab)

    else:
        # If no tabs structure, we need to create one
        # This preserves existing content as the first tab
        existing_content = {}
        for key in ["groups", "pages", "anchors"]:
            if key in navigation:
                existing_content[key] = navigation.pop(key)

        if existing_content:
            navigation["tabs"] = [
                {
                    "tab": "Documentation",
                    "icon": "book",
                    **existing_content,
                },
                examples_tab,
            ]
        else:
            navigation["tabs"] = [examples_tab]

    docs_config["navigation"] = navigation

    # Write updated docs.json
    with open(docs_json_path, "w", encoding="utf-8") as f:
        json.dump(docs_config, f, indent=2)
        f.write("\n")  # Add trailing newline


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: generate_navigation.py <examples_directory> [docs.json]")
        print("")
        print("If docs.json is provided, it will be updated in place.")
        print("Otherwise, the Examples tab JSON is printed to stdout.")
        sys.exit(1)

    examples_dir = Path(sys.argv[1])

    if not examples_dir.exists():
        print(f"Error: Directory does not exist: {examples_dir}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        docs_json_path = Path(sys.argv[2])
        if not docs_json_path.exists():
            print(f"Error: docs.json not found: {docs_json_path}", file=sys.stderr)
            sys.exit(1)

        update_docs_json(docs_json_path, examples_dir)
        print(f"Updated: {docs_json_path}")
    else:
        # Just print the Examples tab configuration
        print(generate_full_examples_tab(examples_dir))


if __name__ == "__main__":
    main()
