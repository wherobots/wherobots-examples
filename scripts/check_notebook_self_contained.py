#!/usr/bin/env python3
"""Pre-commit hook that checks notebooks are self-contained.

Notebooks must not reference local files because the VS Code extension
downloads individual .ipynb files and sends them to a remote Jupyter
server — co-located repo files will not be present.

Checks:
  1. Code cells must not read local files (open(), json.load from path, etc.)
  2. Markdown cells must not reference local image paths (use attachment: instead)
"""

import json
import re
import sys

# ---------------------------------------------------------------------------
# Patterns for code cells – detect reads of local, relative-path files.
# We intentionally avoid flagging writes (to_csv, save, etc.) or /tmp paths,
# since those are transient runtime artefacts that work fine on a remote server.
# ---------------------------------------------------------------------------

# open('some/relative/path' ...) or open("some/relative/path" ...)
# Excludes http(s):// and s3:// URLs, absolute paths starting with /tmp
_OPEN_LOCAL = re.compile(
    r"""\bopen\(\s*(['"])(?!https?://|s3://|/tmp)([^'"]+)\1""",
)

# json.load(open(...)) is caught by the above, but also catch standalone
# pd.read_csv / read_json / read_parquet / gpd.read_file with a local path
_READ_LOCAL = re.compile(
    r"""\bread_(?:csv|json|parquet|file)\(\s*(['"])(?!https?://|s3://|/tmp)([^'"]+)\1""",
)

# Path("relative/...") – but not Path("/tmp/...")
_PATH_LOCAL = re.compile(
    r"""\bPath\(\s*(['"])(?!https?://|s3://|/tmp|/)([^'"]+)\1""",
)

CODE_PATTERNS = [
    (_OPEN_LOCAL, "open() with local path"),
    (_READ_LOCAL, "read_*() with local path"),
    (_PATH_LOCAL, "Path() with local relative path"),
]

# ---------------------------------------------------------------------------
# Patterns for markdown cells – detect local image paths.
# Allowed: attachment:, http(s)://, data:
# ---------------------------------------------------------------------------

# ![alt](path)
_MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
# <img src="path" ...>
_HTML_IMG = re.compile(r'<img\s+[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)

_ALLOWED_IMG_PREFIXES = ("attachment:", "http://", "https://", "data:")


def check_notebook(path: str) -> list[str]:
    """Return a list of violation messages for a single notebook."""
    violations = []

    with open(path, "r") as f:
        try:
            nb = json.load(f)
        except json.JSONDecodeError as exc:
            return [f"{path}: invalid JSON: {exc}"]

    for cell_idx, cell in enumerate(nb.get("cells", [])):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", []))

        if cell_type == "code":
            for pattern, label in CODE_PATTERNS:
                for match in pattern.finditer(source):
                    local_path = match.group(2)
                    violations.append(
                        f"{path}: code cell {cell_idx} — {label}: {local_path!r}"
                    )

        elif cell_type == "markdown":
            for match in _MD_IMG.finditer(source):
                img_path = match.group(1)
                if not img_path.startswith(_ALLOWED_IMG_PREFIXES):
                    violations.append(
                        f"{path}: markdown cell {cell_idx} — "
                        f"local image path: {img_path!r} "
                        f"(use attachment: format instead)"
                    )

            for match in _HTML_IMG.finditer(source):
                img_path = match.group(1)
                if not img_path.startswith(_ALLOWED_IMG_PREFIXES):
                    violations.append(
                        f"{path}: markdown cell {cell_idx} — "
                        f"local <img> src: {img_path!r} "
                        f"(use attachment: format instead)"
                    )

    return violations


def main() -> int:
    files = sys.argv[1:]
    all_violations = []

    for path in files:
        if not path.endswith(".ipynb"):
            continue
        all_violations.extend(check_notebook(path))

    if all_violations:
        print("Notebooks must be self-contained (no local file references).")
        print("See CONTRIBUTING.md for details.\n")
        for v in all_violations:
            print(f"  {v}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
