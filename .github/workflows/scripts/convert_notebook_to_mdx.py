#!/usr/bin/env python3
"""
Convert Jupyter notebooks to MDX format with rendered output.

This script converts .ipynb files to .mdx files suitable for Mintlify documentation,
using nbconvert to render outputs properly, then adding MDX-compatible frontmatter.

Requirements:
    - nbconvert>=7.0.0
"""

import re
import sys
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def fix_html_void_elements(text: str) -> str:
    """Convert HTML void elements to self-closing format for MDX/JSX compatibility.

    MDX requires all HTML tags to be properly closed. Void elements like <img>, <br>,
    <hr>, etc. must use self-closing syntax: <img /> instead of <img>.
    """
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
        # Match tags that are not already self-closed
        pattern = rf"<({element})\s*([^>]*?)(?<!/)\s*>"
        replacement = rf"<\1 \2 />"
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Clean up any double spaces introduced
        text = re.sub(rf"<({element})\s+/>", rf"<\1 />", text, flags=re.IGNORECASE)

    return text


def sanitize_for_mdx(content: str) -> str:
    """Sanitize content to be MDX-compatible.

    MDX is strict about JSX syntax. This function:
    1. Removes <script> tags (not allowed in MDX)
    2. Removes <style> tags (not allowed in MDX)
    3. Escapes curly braces outside of code blocks
    4. Removes HTML comments
    5. Removes widget output that can't be rendered statically
    """
    # Split content into code blocks and non-code blocks
    # We need to preserve code blocks as-is
    parts = re.split(r"(```[\s\S]*?```)", content)

    sanitized_parts = []
    for i, part in enumerate(parts):
        if part.startswith("```"):
            # This is a code block - keep as-is
            sanitized_parts.append(part)
        else:
            # This is regular content - sanitize it

            # Remove <script>...</script> blocks (including multiline)
            part = re.sub(
                r"<script[^>]*>[\s\S]*?</script>", "", part, flags=re.IGNORECASE
            )

            # Remove <style>...</style> blocks (including multiline)
            part = re.sub(
                r"<style[^>]*>[\s\S]*?</style>", "", part, flags=re.IGNORECASE
            )

            # Remove HTML comments
            part = re.sub(r"<!--[\s\S]*?-->", "", part)

            # Remove div tags with data attributes (widget containers)
            part = re.sub(
                r"<div[^>]*data-[^>]*>[\s\S]*?</div>", "", part, flags=re.IGNORECASE
            )

            # Remove empty div tags
            part = re.sub(r"<div[^>]*>\s*</div>", "", part, flags=re.IGNORECASE)

            # Remove FloatProgress and other widget text output
            part = re.sub(r"FloatProgress\([^)]*\)", "[Progress indicator]", part)
            part = re.sub(r"HBox\([^)]*\)", "[Widget]", part)
            part = re.sub(r"VBox\([^)]*\)", "[Widget]", part)

            # Escape curly braces (JSX interprets them as expressions)
            # But be careful not to double-escape
            part = part.replace("{", "\\{").replace("}", "\\}")

            # Clean up multiple blank lines
            part = re.sub(r"\n{3,}", "\n\n", part)

            sanitized_parts.append(part)

    return "".join(sanitized_parts)


def extract_title(content: str) -> str:
    """Extract title from first H1 heading."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Untitled"


def extract_description(content: str) -> str:
    """Extract first meaningful paragraph after H1 as description."""
    # Find position of first H1
    h1_match = re.search(r"^#\s+.+$", content, re.MULTILINE)
    if not h1_match:
        return ""

    # Get content after H1
    after_h1 = content[h1_match.end() :]

    # Find first non-empty, non-header, non-code paragraph
    lines = after_h1.split("\n")
    paragraph = []

    for line in lines:
        line_stripped = line.strip()
        # Skip empty lines before we start collecting
        if not line_stripped and not paragraph:
            continue
        # Stop at empty line if we have content
        if not line_stripped and paragraph:
            break
        # Skip headings, HTML, code blocks
        if (
            line_stripped.startswith("#")
            or line_stripped.startswith("<")
            or line_stripped.startswith("```")
        ):
            if paragraph:
                break
            continue

        paragraph.append(line_stripped)
        if len(" ".join(paragraph)) > 200:
            break

    desc = " ".join(paragraph)
    # Remove markdown links for cleaner description
    desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)
    # Remove HTML sup tags
    desc = re.sub(r"<sup>\d+</sup>", "", desc)
    # Remove other HTML tags
    desc = re.sub(r"<[^>]+>", "", desc)
    # Truncate
    if len(desc) > 160:
        desc = desc[:157] + "..."
    return desc


def run_nbconvert(notebook_path: Path, output_dir: Path) -> Path:
    """Run nbconvert to convert notebook to markdown.

    Args:
        notebook_path: Path to the input notebook
        output_dir: Directory for the markdown output

    Returns:
        Path to the generated markdown file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "nbconvert",
        "--to",
        "markdown",
        "--output-dir",
        str(output_dir),
        str(notebook_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"nbconvert failed: {result.stderr}")

    # Return path to generated markdown file
    return output_dir / f"{notebook_path.stem}.md"


def convert_markdown_to_mdx(
    markdown_path: Path, output_path: Path, category: Optional[str] = None
) -> None:
    """Convert nbconvert markdown output to MDX with frontmatter.

    Args:
        markdown_path: Path to the markdown file from nbconvert
        output_path: Path for the output MDX file
        category: Category for icon selection
    """
    content = markdown_path.read_text(encoding="utf-8")

    # Remove papermill error message at the top (if present)
    content = re.sub(r'^<span style="color:red.*?</span>\s*\n*', "", content)

    # Sanitize content for MDX compatibility (remove scripts, styles, escape braces)
    content = sanitize_for_mdx(content)

    # Fix HTML void elements for MDX
    content = fix_html_void_elements(content)

    # Extract metadata before modifying content
    title = extract_title(content)
    description = extract_description(content)

    # Remove just the H1 line (keep content after it)
    content = re.sub(r"^#\s+.+\n+", "", content, count=1, flags=re.MULTILINE)

    # Build frontmatter
    icon_map = {
        "Getting_Started": "rocket",
        "Analyzing_Data": "chart-line",
        "Reading_and_Writing_Data": "database",
        "Open_Data_Connections": "plug",
        "Foreign_Catalogs": "folder-tree",
        "scala": "code",
    }
    icon = icon_map.get(category, "book") if category else "book"

    # Escape quotes in description
    description_escaped = description.replace('"', '\\"')

    frontmatter = f'''---
title: "{title}"
description: "{description_escaped}"
icon: "{icon}"
---

'''

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(frontmatter + content, encoding="utf-8")


def convert_notebook_to_mdx(
    notebook_path: Path,
    output_dir: Path,
    category: Optional[str] = None,
    verbose: bool = False,
) -> Path:
    """Convert a Jupyter notebook to Mintlify MDX format using nbconvert.

    Args:
        notebook_path: Path to the input notebook
        output_dir: Directory for the output MDX file
        category: Category for icon selection
        verbose: Print progress information

    Returns:
        Path to the generated MDX file
    """
    # Create a temporary directory for nbconvert output
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        if verbose:
            print(f"Running nbconvert on {notebook_path.name}...")

        # Run nbconvert to get markdown
        markdown_path = run_nbconvert(notebook_path, temp_path)

        if verbose:
            print(f"Converting markdown to MDX...")

        # Convert markdown to MDX
        output_path = output_dir / f"{notebook_path.stem}.mdx"
        convert_markdown_to_mdx(markdown_path, output_path, category)

        return output_path


def should_exclude_notebook(notebook_path: Path) -> bool:
    """Check if a notebook should be excluded from conversion."""
    filename = notebook_path.name

    # Exclude files prefixed with "Raster_Inference"
    if filename.startswith("Raster_Inference"):
        return True

    return False


def convert_all_notebooks(
    source_dir: Path, output_dir: Path, verbose: bool = False
) -> tuple:
    """Convert all notebooks in source directory to MDX files."""
    converted = []
    skipped = []

    for notebook_path in source_dir.rglob("*.ipynb"):
        if should_exclude_notebook(notebook_path):
            skipped.append(notebook_path)
            if verbose:
                print(f"Skipping excluded: {notebook_path.name}")
            continue

        # Determine category from parent directory
        rel_path = notebook_path.relative_to(source_dir)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else None

        # Create output subdirectory matching source structure
        output_subdir = output_dir / rel_path.parent
        output_subdir.mkdir(parents=True, exist_ok=True)

        try:
            output_path = convert_notebook_to_mdx(
                notebook_path, output_subdir, category, verbose
            )
            converted.append((notebook_path, output_path))
            if verbose:
                print(f"Converted: {notebook_path} -> {output_path}")

        except Exception as e:
            print(f"Error converting {notebook_path}: {e}", file=sys.stderr)

    return converted, skipped


def main():
    """Main entry point for the conversion script."""
    parser = argparse.ArgumentParser(
        description="Convert Jupyter notebooks to Mintlify MDX format"
    )
    parser.add_argument(
        "input", type=Path, help="Input notebook file or directory containing notebooks"
    )
    parser.add_argument("output", type=Path, help="Output directory for MDX files")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed conversion progress",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Category for the notebook (used for icon selection)",
    )

    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.is_file():
        # Single file conversion
        if should_exclude_notebook(input_path):
            print(f"Skipping excluded notebook: {input_path.name}")
            sys.exit(0)

        try:
            output_path = convert_notebook_to_mdx(
                input_path, output_dir, args.category, args.verbose
            )
            print(f"Converted: {input_path} -> {output_path}")

        except Exception as e:
            print(f"Error converting {input_path}: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # Directory conversion
        converted, skipped = convert_all_notebooks(input_path, output_dir, args.verbose)

        print(f"\nConversion complete:")
        print(f"  Converted: {len(converted)} notebooks")
        print(f"  Skipped:   {len(skipped)} notebooks (excluded)")


if __name__ == "__main__":
    main()
