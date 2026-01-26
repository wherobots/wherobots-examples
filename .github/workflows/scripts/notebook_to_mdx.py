#!/usr/bin/env python3
"""
Convert Jupyter notebooks to MDX format for Mintlify documentation.

This script converts .ipynb files to .mdx files, extracting only the source code
and markdown content (no execution outputs). It generates MDX-compatible frontmatter,
sanitizes content for JSX compatibility, and copies images to the output directory.
"""

import base64
import json
import re
import shutil
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


def remove_table_of_contents(text: str) -> str:
    """Remove Table of Contents sections from markdown.

    Mintlify automatically generates a TOC, so we don't need manual ones.
    Matches patterns like:
    - ## Table of Contents followed by numbered/bulleted list items with links
    """
    # Pattern: "## Table of Contents" followed by list items until next heading or ---
    # This handles numbered lists like "1. [Section](#section)"
    pattern = r"## Table of Contents\n+(?:(?:\d+\.\s*\[[^\]]+\]\([^)]+\)\n*)+)"
    text = re.sub(pattern, "", text)

    # Also handle bullet point TOCs
    pattern = r"## Table of Contents\n+(?:(?:-\s*\[[^\]]+\]\([^)]+\)\n*)+)"
    text = re.sub(pattern, "", text)

    return text


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


def process_images(
    source: str,
    cell: dict,
    notebook_path: Path,
    images_dir: Path,
    notebook_slug: str,
    verbose: bool = False,
) -> str:
    """Process images in markdown content.

    Handles two types of images:
    1. Local file references (./assets/img/...) - copies to images_dir
    2. Embedded attachments (attachment:...) - extracts and saves to images_dir

    Returns updated markdown with corrected image paths.
    """
    # Create images directory if needed
    images_dir.mkdir(parents=True, exist_ok=True)

    # Get attachments from cell
    attachments = cell.get("attachments", {})

    def replace_image(match: re.Match) -> str:
        alt_text = match.group(1)
        image_path = match.group(2)

        # Skip header-logo images (they're branding, not content)
        if "header-logo" in image_path:
            return ""  # Remove the image entirely

        # Handle embedded attachments
        if image_path.startswith("attachment:"):
            attachment_name = image_path.replace("attachment:", "")
            if attachment_name in attachments:
                attachment_data = attachments[attachment_name]
                # Get the first mime type (usually image/png or image/jpeg)
                for mime_type, base64_data in attachment_data.items():
                    # Determine extension from mime type
                    ext = mime_type.split("/")[-1]
                    if ext == "jpeg":
                        ext = "jpg"

                    # Create a unique filename
                    safe_name = re.sub(
                        r"[^a-zA-Z0-9]", "-", attachment_name.split(".")[0]
                    )
                    new_filename = f"{notebook_slug}-{safe_name}.{ext}"
                    new_path = images_dir / new_filename

                    # Decode and save
                    image_bytes = base64.b64decode(base64_data)
                    with open(new_path, "wb") as f:
                        f.write(image_bytes)

                    if verbose:
                        print(f"    Extracted attachment: {new_filename}")

                    # Return updated markdown with relative path
                    return f"![{alt_text}](/tutorials/example-notebooks/images/{new_filename})"

            # Attachment not found, return as-is
            return match.group(0)

        # Handle local file references
        # Normalize path (handle ./ and ../)
        if image_path.startswith("./"):
            image_path = image_path[2:]

        # Resolve the image path relative to the notebook
        if image_path.startswith("../"):
            # Go up from notebook directory
            source_image = notebook_path.parent.parent / image_path[3:]
        else:
            source_image = notebook_path.parent / image_path

        if source_image.exists():
            # Create a unique filename to avoid collisions
            new_filename = f"{notebook_slug}-{source_image.name}"
            new_path = images_dir / new_filename

            # Copy the image
            shutil.copy2(source_image, new_path)

            if verbose:
                print(f"    Copied image: {new_filename}")

            # Return updated markdown with absolute path from docs root
            return f"![{alt_text}](/tutorials/example-notebooks/images/{new_filename})"
        else:
            if verbose:
                print(f"    Warning: Image not found: {source_image}")
            # Return original if image not found
            return match.group(0)

    # Match markdown image syntax: ![alt](path)
    updated_source = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_image, source)

    # Also handle HTML <img> tags
    def replace_html_img(match: re.Match) -> str:
        full_tag = match.group(0)
        src_match = re.search(r'src=["\']([^"\']+)["\']', full_tag)
        if not src_match:
            return full_tag

        image_path = src_match.group(1)

        # Skip header-logo images
        if "header-logo" in image_path:
            return ""

        # Normalize path
        if image_path.startswith("./"):
            image_path = image_path[2:]

        # Resolve the image path relative to the notebook
        if image_path.startswith("../"):
            source_image = notebook_path.parent.parent / image_path[3:]
        else:
            source_image = notebook_path.parent / image_path

        if source_image.exists():
            new_filename = f"{notebook_slug}-{source_image.name}"
            new_path = images_dir / new_filename

            shutil.copy2(source_image, new_path)

            if verbose:
                print(f"    Copied image: {new_filename}")

            # Convert to markdown image syntax for MDX compatibility
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', full_tag)
            alt_text = alt_match.group(1) if alt_match else ""
            return f"![{alt_text}](/tutorials/example-notebooks/images/{new_filename})"
        else:
            if verbose:
                print(f"    Warning: Image not found: {source_image}")
            return full_tag

    # Match HTML img tags
    updated_source = re.sub(r"<img\s+[^>]*>", replace_html_img, updated_source)

    return updated_source


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

    # Generate notebook slug for unique image names
    notebook_slug = notebook_path.stem.replace("_", "-").lower()

    # Images directory
    images_dir = output_dir / "images"

    # Extract metadata
    title = extract_title_from_markdown(cells)

    # Get programming language from notebook metadata
    metadata = notebook.get("metadata", {})
    language = (
        metadata.get("language_info", {}).get("name")
        or metadata.get("kernelspec", {}).get("language")
        or "python"  # Default to python
    )

    # Build MDX content
    mdx_parts = []

    # Add frontmatter (title only, no description for now)
    mdx_parts.append("---")
    mdx_parts.append(f'title: "{title}"')
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
            # Process images first (before sanitization)
            source = process_images(
                source, cell, notebook_path, images_dir, notebook_slug, verbose
            )

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
            source = remove_table_of_contents(source)
            sanitized = sanitize_markdown_for_mdx(source)
            if sanitized.strip():
                mdx_parts.append(sanitized)
                mdx_parts.append("")

        elif cell_type == "code":
            # Add code block with appropriate syntax highlighting
            mdx_parts.append(f"```{language}")
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
