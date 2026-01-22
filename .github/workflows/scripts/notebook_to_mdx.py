#!/usr/bin/env python3
"""
Convert Jupyter notebooks to MDX format for Mintlify documentation.

This script converts .ipynb files to .mdx files, extracting only the source code
and markdown content (no execution outputs). It generates MDX-compatible frontmatter
and sanitizes content for JSX compatibility.
"""

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Optional


def extract_title_from_markdown(cells: list) -> str:
    """Extract title from first H1 heading in notebook."""
    for cell in cells:
        if cell.get("cell_type") == "markdown":
            source = "".join(cell.get("source", []))
            match = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
            if match:
                return match.group(1).strip()
    return "Untitled"


def extract_description_from_markdown(cells: list) -> str:
    """Extract first paragraph after H1 as description."""
    found_h1 = False
    for cell in cells:
        if cell.get("cell_type") == "markdown":
            source = "".join(cell.get("source", []))
            lines = source.split("\n")

            for line in lines:
                line_stripped = line.strip()

                # Look for H1
                if line_stripped.startswith("# ") and not found_h1:
                    found_h1 = True
                    continue

                # After H1, find first non-empty, non-header line
                if found_h1 and line_stripped:
                    if line_stripped.startswith("#"):
                        continue
                    if line_stripped.startswith("!["):
                        continue
                    # Clean up markdown links for description
                    desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line_stripped)
                    # Truncate if too long
                    if len(desc) > 160:
                        desc = desc[:157] + "..."
                    return desc
    return ""


def sanitize_markdown_for_mdx(text: str) -> str:
    """Sanitize markdown content for MDX/JSX compatibility."""
    # Fix HTML void elements to be self-closing
    void_elements = [
        "img",
        "br",
        "hr",
        "input",
        "meta",
        "link",
        "area",
        "base",
        "col",
        "embed",
        "source",
        "track",
        "wbr",
    ]
    for element in void_elements:
        pattern = rf"<({element})\s*([^>]*?)(?<!/)\s*>"
        replacement = rf"<\1 \2 />"
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        text = re.sub(rf"<({element})\s+/>", rf"<\1 />", text, flags=re.IGNORECASE)

    # Escape curly braces (JSX interprets them as expressions)
    text = text.replace("{", "\\{").replace("}", "\\}")

    return text


def convert_notebook_to_mdx(
    notebook_path: Path, output_dir: Path, verbose: bool = False
) -> Optional[Path]:
    """Convert a single notebook to MDX format."""
    if verbose:
        print(f"Converting {notebook_path}...")

    # Read notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    cells = notebook.get("cells", [])
    if not cells:
        print(f"Warning: {notebook_path} has no cells, skipping")
        return None

    # Extract metadata
    title = extract_title_from_markdown(cells)
    description = extract_description_from_markdown(cells)

    # Build MDX content
    mdx_parts = []

    # Add frontmatter
    mdx_parts.append("---")
    mdx_parts.append(f'title: "{title}"')
    if description:
        # Escape quotes in description
        safe_desc = description.replace('"', '\\"')
        mdx_parts.append(f'description: "{safe_desc}"')
    mdx_parts.append("---")
    mdx_parts.append("")

    # Process cells
    skip_first_h1 = True  # Skip first H1 since it's in frontmatter

    for cell in cells:
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", []))

        if not source.strip():
            continue

        if cell_type == "markdown":
            # Check if this cell contains the first H1 we should skip
            if skip_first_h1 and re.search(r"^#\s+", source, re.MULTILINE):
                # Remove the H1 line but keep rest of cell
                lines = source.split("\n")
                filtered_lines = []
                found_h1 = False
                for line in lines:
                    if not found_h1 and re.match(r"^#\s+", line):
                        found_h1 = True
                        skip_first_h1 = False
                        continue
                    filtered_lines.append(line)
                source = "\n".join(filtered_lines)

            # Sanitize and add markdown
            sanitized = sanitize_markdown_for_mdx(source)
            if sanitized.strip():
                mdx_parts.append(sanitized)
                mdx_parts.append("")

        elif cell_type == "code":
            # Add code block with python syntax highlighting
            mdx_parts.append("```python")
            mdx_parts.append(source)
            mdx_parts.append("```")
            mdx_parts.append("")

    # Generate output filename (underscores to dashes)
    output_name = notebook_path.stem.replace("_", "-") + ".mdx"
    output_path = output_dir / output_name

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write MDX file
    mdx_content = "\n".join(mdx_parts)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mdx_content)

    if verbose:
        print(f"  -> {output_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert Jupyter notebooks to MDX")
    parser.add_argument(
        "notebooks", nargs="+", help="Notebook files or directories to convert"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output directory for MDX files"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--exclude-prefix",
        default="Raster_Inference",
        help="Exclude notebooks with this filename prefix",
    )

    args = parser.parse_args()
    output_dir = Path(args.output)

    # Collect all notebooks to convert
    notebooks = []
    for path_str in args.notebooks:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".ipynb":
            notebooks.append(path)
        elif path.is_dir():
            notebooks.extend(path.rglob("*.ipynb"))

    # Filter out excluded notebooks
    if args.exclude_prefix:
        notebooks = [
            nb for nb in notebooks if not nb.name.startswith(args.exclude_prefix)
        ]

    if not notebooks:
        print("No notebooks found to convert")
        sys.exit(1)

    print(f"Converting {len(notebooks)} notebooks...")

    converted = []
    for notebook in sorted(notebooks):
        result = convert_notebook_to_mdx(notebook, output_dir, args.verbose)
        if result:
            converted.append(result)

    print(f"Successfully converted {len(converted)} notebooks to {output_dir}")

    # Output list of converted files for use in workflow
    for path in converted:
        print(f"CONVERTED: {path}")


if __name__ == "__main__":
    main()
