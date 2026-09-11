#!/usr/bin/env python3
"""
Fail if any notebook or Python file in the repository uses GeoPandas or DuckDB.

These examples exist to showcase WherobotsDB (Apache Sedona). GeoPandas and DuckDB
overlap with that functionality, so notebooks should stay on Sedona DataFrames and
Spatial SQL for reading, writing, analyzing, and visualizing spatial data.

Checked:
  * ``import geopandas`` / ``from geopandas import ...`` and ``import duckdb`` /
    ``from duckdb import ...`` in Python files, notebook code cells, and fenced code
    blocks inside notebook markdown cells.
  * ``.mosaic_index_gdf`` from ``rasterflow_remote``, which reads the mosaic index
    with GeoPandas under the hood. Use ``.mosaic_index_df`` instead.

Usage: check_forbidden_imports.py [FILE ...]   (defaults to every .ipynb/.py in the repo)
"""

import json
import re
import sys
from pathlib import Path

FORBIDDEN = [
    (
        re.compile(r"^\s*(import\s+geopandas\b|from\s+geopandas\b)", re.MULTILINE),
        "imports geopandas; use Sedona DataFrames / Spatial SQL instead",
    ),
    (
        re.compile(r"^\s*(import\s+duckdb\b|from\s+duckdb\b)", re.MULTILINE),
        "imports duckdb; use Sedona DataFrames / Spatial SQL instead",
    ),
    (
        re.compile(r"\.mosaic_index_gdf\b"),
        "uses rasterflow_remote's GeoPandas accessor; use `.mosaic_index_df` instead",
    ),
]

FENCED_CODE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def code_snippets(path: Path):
    """Yield (label, code) pairs for every executable-looking chunk of a file."""
    if path.suffix == ".py":
        yield path.name, path.read_text(encoding="utf-8")
        return

    notebook = json.loads(path.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook.get("cells", [])):
        source = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code":
            yield f"cell {index}", source
        elif cell.get("cell_type") == "markdown":
            for block in FENCED_CODE.findall(source):
                yield f"cell {index} (markdown code block)", block


def find_violations(path: Path, root: Path):
    shown = path.resolve().relative_to(root) if path.resolve().is_relative_to(root) else path
    for label, code in code_snippets(path):
        for pattern, reason in FORBIDDEN:
            for match in pattern.finditer(code):
                line = code.count("\n", 0, match.start()) + 1
                yield f"{shown}: {label}, line {line}: {reason}\n    {match.group(0).strip()}"


def default_targets(root: Path):
    for pattern in ("**/*.ipynb", "**/*.py"):
        for path in sorted(root.glob(pattern)):
            if any(part.startswith(".") or part == "_deprecated" for part in path.parts):
                continue
            yield path


def main(argv):
    root = Path(__file__).resolve().parent.parent
    targets = [Path(arg) for arg in argv] if argv else list(default_targets(root))
    targets = [path for path in targets if path.suffix in {".ipynb", ".py"} and path.exists()]

    violations = [line for path in targets if path.resolve() != Path(__file__).resolve() for line in find_violations(path, root)]
    if violations:
        print("GeoPandas/DuckDB usage found. These examples should use WherobotsDB (Sedona) instead:\n")
        print("\n".join(violations))
        return 1
    print(f"No GeoPandas or DuckDB usage found in {len(targets)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
