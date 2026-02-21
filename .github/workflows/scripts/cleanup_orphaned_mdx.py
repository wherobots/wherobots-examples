#!/usr/bin/env python3
"""
Clean up orphaned MDX files that no longer have corresponding notebooks.

This script compares MDX files in the docs repo against notebooks in the
examples repo and removes any MDX files that are orphans (their source
notebook was deleted or renamed).
"""

import argparse
import sys
from pathlib import Path


def get_expected_mdx_names(notebook_dirs: list[Path], exclude_prefix: str) -> set[str]:
    """Get the set of expected MDX filenames from existing notebooks.

    Returns filenames without extension, using dash-separated lowercase format
    (matching the to_page_slug() logic in notebook_to_mdx.py).
    """
    expected = set()

    for notebook_dir in notebook_dirs:
        if not notebook_dir.exists():
            continue

        for notebook in notebook_dir.rglob("*.ipynb"):
            # Skip excluded notebooks
            if exclude_prefix and notebook.name.startswith(exclude_prefix):
                continue

            # Convert notebook name to expected MDX name
            # (underscores to dashes, lowercase — matching to_page_slug())
            mdx_name = notebook.stem.replace("_", "-").lower()
            expected.add(mdx_name)

    return expected


def get_existing_mdx_names(mdx_dir: Path) -> set[str]:
    """Get the set of existing MDX filenames (without extension)."""
    if not mdx_dir.exists():
        return set()

    return {mdx_file.stem for mdx_file in mdx_dir.glob("*.mdx")}


def cleanup_orphaned_files(
    mdx_dir: Path,
    orphaned_names: set[str],
    dry_run: bool = False,
    verbose: bool = False,
) -> list[Path]:
    """Remove orphaned MDX files and their associated images.

    Returns list of removed files.
    """
    removed = []
    images_dir = mdx_dir / "images"

    for name in sorted(orphaned_names):
        # Remove MDX file
        mdx_file = mdx_dir / f"{name}.mdx"
        if mdx_file.exists():
            if verbose:
                print(f"Removing orphaned MDX: {mdx_file}")
            if not dry_run:
                mdx_file.unlink()
            removed.append(mdx_file)

        # Remove associated images (prefixed with notebook slug)
        # Images are named: {notebook-slug}-{image-name}.{ext}
        slug = name.lower()
        if images_dir.exists():
            for image_file in images_dir.glob(f"{slug}-*"):
                if verbose:
                    print(f"Removing orphaned image: {image_file}")
                if not dry_run:
                    image_file.unlink()
                removed.append(image_file)

    return removed


def main():
    parser = argparse.ArgumentParser(
        description="Clean up orphaned MDX files from deleted/renamed notebooks"
    )
    parser.add_argument(
        "notebook_dirs",
        nargs="+",
        help="Directories containing source notebooks",
    )
    parser.add_argument(
        "--mdx-dir",
        required=True,
        help="Directory containing MDX files to clean",
    )
    parser.add_argument(
        "--exclude-prefix",
        default="Raster_Inference",
        help="Exclude notebooks with this filename prefix",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without removing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--output-file",
        help="Write list of removed MDX files (names only) to this file",
    )

    args = parser.parse_args()

    notebook_dirs = [Path(d) for d in args.notebook_dirs]
    mdx_dir = Path(args.mdx_dir)

    # Get expected and existing MDX names
    expected_names = get_expected_mdx_names(notebook_dirs, args.exclude_prefix)
    existing_names = get_existing_mdx_names(mdx_dir)

    if args.verbose:
        print(f"Found {len(expected_names)} notebooks (expected MDX files)")
        print(f"Found {len(existing_names)} existing MDX files")

    # Find orphans: existing MDX files with no corresponding notebook
    orphaned_names = existing_names - expected_names

    if not orphaned_names:
        print("No orphaned MDX files found")
        return

    print(f"Found {len(orphaned_names)} orphaned MDX file(s):")
    for name in sorted(orphaned_names):
        print(f"  - {name}.mdx")

    if args.dry_run:
        print("\nDry run - no files removed")
        return

    # Remove orphaned files
    removed = cleanup_orphaned_files(
        mdx_dir, orphaned_names, dry_run=args.dry_run, verbose=args.verbose
    )

    print(f"\nRemoved {len(removed)} file(s)")

    # Output removed files for git operations
    for path in removed:
        print(f"REMOVED: {path}")

    # Write removed MDX names to file if requested (for PR descriptions)
    if args.output_file:
        mdx_names = sorted(orphaned_names)
        with open(args.output_file, "w") as f:
            f.write("\n".join(mdx_names))
        if args.verbose:
            print(f"Wrote {len(mdx_names)} removed MDX names to {args.output_file}")


if __name__ == "__main__":
    main()
