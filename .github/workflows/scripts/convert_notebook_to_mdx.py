#!/usr/bin/env python3
"""
Convert Jupyter notebooks to MDX format with rendered output.

This script converts .ipynb files to .mdx files suitable for Mintlify documentation,
preserving both code and output cells in a format compatible with Mintlify's MDX parser.
"""

import json
import re
import sys
import base64
import argparse
from pathlib import Path
from typing import Optional


def escape_mdx_text(text: str) -> str:
    """Escape special MDX/JSX characters in plain text output."""
    # Escape curly braces which are special in MDX/JSX
    text = text.replace("{", "\\{").replace("}", "\\}")
    return text


def fix_html_void_elements(text: str) -> str:
    """Convert HTML void elements to self-closing format for MDX/JSX compatibility.

    MDX requires all HTML tags to be properly closed. Void elements like <img>, <br>,
    <hr>, etc. must use self-closing syntax: <img /> instead of <img>.
    """
    # List of HTML void elements that need to be self-closed
    void_elements = ['img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']

    for element in void_elements:
        # Match tags that are not already self-closed
        # Pattern matches <element ...> but not <element ... /> or <element .../>
        pattern = rf'<({element})\s*([^>]*?)(?<!/)\s*>'
        replacement = rf'<\1 \2 />'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Clean up any double spaces introduced
        text = re.sub(rf'<({element})\s+/>', rf'<\1 />', text, flags=re.IGNORECASE)

    return text


def process_markdown_cell(cell: dict) -> str:
    """Process a markdown cell and return MDX-compatible content."""
    source = "".join(cell.get("source", []))
    # Fix HTML void elements for MDX compatibility
    source = fix_html_void_elements(source)
    return source + "\n\n"


def process_code_cell(cell: dict, show_output: bool = True) -> str:
    """Process a code cell with its outputs and return MDX-compatible content."""
    source = "".join(cell.get("source", []))
    outputs = cell.get("outputs", [])

    result = []

    # Add the code block with python syntax highlighting
    if source.strip():
        result.append(f"```python\n{source}\n```\n")

    if not show_output:
        return "\n".join(result) + "\n"

    # Process outputs
    for output in outputs:
        output_type = output.get("output_type", "")

        if output_type == "stream":
            # Standard output/error
            text = "".join(output.get("text", []))
            if text.strip():
                result.append(
                    f'\n<Expandable title="Output">\n```\n{text.rstrip()}\n```\n</Expandable>\n'
                )

        elif output_type == "execute_result" or output_type == "display_data":
            data = output.get("data", {})

            # Handle different mime types in order of preference
            if "image/png" in data:
                # Embed base64 image using Mintlify's Frame component
                img_data = data["image/png"]
                result.append(
                    f'\n<Frame>\n  <img src="data:image/png;base64,{img_data}" alt="Output" />\n</Frame>\n'
                )

            elif "image/jpeg" in data:
                img_data = data["image/jpeg"]
                result.append(
                    f'\n<Frame>\n  <img src="data:image/jpeg;base64,{img_data}" alt="Output" />\n</Frame>\n'
                )

            elif "image/svg+xml" in data:
                svg_data = "".join(data["image/svg+xml"])
                result.append(f"\n<Frame>\n{svg_data}\n</Frame>\n")

            elif "text/html" in data:
                html_content = "".join(data["text/html"])
                # For HTML tables and other output, wrap in expandable
                if "<table" in html_content.lower():
                    result.append(
                        f'\n<Expandable title="Table Output">\n```html\n{html_content}\n```\n</Expandable>\n'
                    )
                else:
                    result.append(
                        f'\n<Expandable title="HTML Output">\n```html\n{html_content}\n```\n</Expandable>\n'
                    )

            elif "text/plain" in data:
                text = "".join(data["text/plain"])
                if text.strip():
                    result.append(
                        f'\n<Expandable title="Output">\n```\n{text.rstrip()}\n```\n</Expandable>\n'
                    )

        elif output_type == "error":
            # Error output
            ename = output.get("ename", "Error")
            traceback = output.get("traceback", [])

            # Clean ANSI codes from traceback
            tb_text = "\n".join(traceback)
            tb_text = re.sub(r"\x1b\[[0-9;]*m", "", tb_text)

            result.append(
                f'\n<Expandable title="Error: {ename}">\n```\n{tb_text}\n```\n</Expandable>\n'
            )

    return "\n".join(result) + "\n"


def extract_description(cells: list) -> str:
    """Extract a description from the notebook's first markdown cell after the title."""
    found_title = False
    for cell in cells:
        if cell.get("cell_type") == "markdown":
            source = "".join(cell.get("source", []))
            lines = source.strip().split("\n")

            for line in lines:
                line = line.strip()
                # Skip the title line
                if line.startswith("# ") and not found_title:
                    found_title = True
                    continue
                # Skip empty lines, headings, and HTML tags (like <img>)
                if not line or line.startswith("#") or line.startswith("<"):
                    continue
                # Return first valid text line as description
                # Clean up the line for use as description
                desc = line.strip()
                # Remove markdown formatting
                desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)  # Links
                desc = re.sub(r"\*\*([^*]+)\*\*", r"\1", desc)  # Bold
                desc = re.sub(r"\*([^*]+)\*", r"\1", desc)  # Italic
                desc = re.sub(r"`([^`]+)`", r"\1", desc)  # Code
                # Skip if only HTML remains after cleaning
                if desc.startswith("<") or not desc:
                    continue
                # Truncate if too long
                if len(desc) > 160:
                    desc = desc[:157] + "..."
                return desc
    return ""


def generate_frontmatter(
    notebook_path: Path, notebook: dict, category: Optional[str] = None
) -> str:
    """Generate Mintlify-compatible MDX frontmatter from notebook metadata."""
    cells = notebook.get("cells", [])

    # Try to extract title from first markdown cell or use filename
    title = notebook_path.stem.replace("_", " ").replace("-", " ")

    for cell in cells:
        if cell.get("cell_type") == "markdown":
            source = "".join(cell.get("source", []))
            # Look for H1 heading
            match = re.match(r"^#\s+(.+)$", source, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                break

    # Extract description
    description = extract_description(cells)

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f'title: "{title}"',
    ]

    if description:
        # Escape quotes in description
        description = description.replace('"', '\\"')
        frontmatter_lines.append(f'description: "{description}"')

    # Add icon based on category
    icon_map = {
        "Getting_Started": "rocket",
        "Analyzing_Data": "chart-line",
        "Reading_and_Writing_Data": "database",
        "Open_Data_Connections": "plug",
        "Foreign_Catalogs": "folder-tree",
        "scala": "code",
    }

    if category and category in icon_map:
        frontmatter_lines.append(f'icon: "{icon_map[category]}"')

    frontmatter_lines.append("---")
    frontmatter_lines.append("")

    return "\n".join(frontmatter_lines) + "\n"


def convert_notebook_to_mdx(
    notebook_path: Path, show_output: bool = True, category: Optional[str] = None
) -> str:
    """Convert a Jupyter notebook to Mintlify MDX format."""
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    mdx_content = []

    # Add frontmatter
    mdx_content.append(generate_frontmatter(notebook_path, notebook, category))

    cells = notebook.get("cells", [])
    skip_first_h1 = True  # Skip first H1 since it's in frontmatter

    for cell in cells:
        cell_type = cell.get("cell_type", "")

        if cell_type == "markdown":
            content = process_markdown_cell(cell)

            # Skip the first H1 heading since it's used as the title
            if skip_first_h1 and re.match(r"^#\s+", content):
                skip_first_h1 = False
                # Remove just the first H1 line
                content = re.sub(r"^#\s+.+\n*", "", content, count=1)
                if content.strip():
                    mdx_content.append(content)
            else:
                mdx_content.append(content)

        elif cell_type == "code":
            mdx_content.append(process_code_cell(cell, show_output))

    return "".join(mdx_content)


def should_exclude_notebook(notebook_path: Path) -> bool:
    """Check if a notebook should be excluded from conversion."""
    filename = notebook_path.name

    # Exclude files prefixed with "Raster_Inference"
    if filename.startswith("Raster_Inference"):
        return True

    return False


def convert_all_notebooks(
    source_dir: Path, output_dir: Path, show_output: bool = True, verbose: bool = False
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

        # Create output subdirectory
        output_subdir = output_dir / rel_path.parent
        output_subdir.mkdir(parents=True, exist_ok=True)

        try:
            mdx_content = convert_notebook_to_mdx(notebook_path, show_output, category)
            output_path = output_subdir / f"{notebook_path.stem}.mdx"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(mdx_content)

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
        "--no-output", action="store_true", help="Exclude cell outputs from conversion"
    )
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
    show_output = not args.no_output

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.is_file():
        # Single file conversion
        if should_exclude_notebook(input_path):
            print(f"Skipping excluded notebook: {input_path.name}")
            sys.exit(0)

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            mdx_content = convert_notebook_to_mdx(
                input_path, show_output, args.category
            )
            output_path = output_dir / f"{input_path.stem}.mdx"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(mdx_content)

            print(f"Converted: {input_path} -> {output_path}")

        except Exception as e:
            print(f"Error converting {input_path}: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # Directory conversion
        converted, skipped = convert_all_notebooks(
            input_path, output_dir, show_output, args.verbose
        )

        print(f"\nConversion complete:")
        print(f"  Converted: {len(converted)} notebooks")
        print(f"  Skipped:   {len(skipped)} notebooks (excluded)")


if __name__ == "__main__":
    main()
