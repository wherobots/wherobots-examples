#!/usr/bin/env python3
"""
Build the example notebook bundles published to s3://wherobots-examples/notebooks/.

Notebook instances, the VS Code extension and the wbc-images notebook tests read
these bundles from S3 instead of from GitHub:

  archive  <tag>.zip laid out like GitHub's tag zip (a single
           wherobots-examples-<version>/ folder), which the jupyter-spark-lab
           init container downloads and unpacks.
  tree     every tracked file at a ref plus manifest.json, shaped like GitHub's
           git/trees?recursive=1 response, which the VS Code extension browses.
  compare  check that two archives hold the same files, ignoring the top folder,
           e.g. ours against GitHub's before replacing it.
"""

import argparse
import json
import subprocess
import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True
    ).stdout


def build_archives(repo: Path, tags: list[str], out: Path) -> None:
    """Write <out>/<tag>.zip for each v<version> tag."""
    for tag in tags:
        if not tag.startswith("v"):
            raise ValueError(f"not a version tag: {tag}")
    out.mkdir(parents=True, exist_ok=True)
    for tag in tags:
        prefix = f"wherobots-examples-{tag[1:]}/"
        git(
            repo,
            "archive",
            "--format=zip",
            f"--prefix={prefix}",
            "-o",
            str((out / f"{tag}.zip").resolve()),
            tag,
        )


def build_tree(repo: Path, ref: str, out: Path) -> None:
    """Write every file tracked at `ref` under `out`, plus out/manifest.json."""
    out.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=BytesIO(git(repo, "archive", "--format=tar", ref))) as tar:
        for member in tar.getmembers():
            if member.isfile():
                target = out / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                # Written fresh rather than extracted, so mtimes are now and
                # `aws s3 sync` uploads same-size edits too.
                target.write_bytes(tar.extractfile(member).read())

    entries = []
    for line in git(repo, "ls-tree", "-r", "-t", "-l", "-z", ref).split(b"\0"):
        if not line:
            continue
        meta, path = line.decode().split("\t", 1)
        mode, kind, sha, size = meta.split()
        if kind == "commit":
            continue
        entry = {"path": path, "mode": mode, "type": kind, "sha": sha}
        if kind == "blob":
            entry["size"] = int(size)
        entries.append(entry)
    manifest = {
        "sha": git(repo, "rev-parse", f"{ref}^{{commit}}").decode().strip(),
        "tree": entries,
        "truncated": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


def _files_by_relative_path(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as archive:
        return {
            info.filename.split("/", 1)[1]: info.CRC
            for info in archive.infolist()
            if not info.is_dir() and "/" in info.filename
        }


def compare_archives(ours: Path, theirs: Path) -> list[str]:
    """Differences between two archives, ignoring their top-level folders."""
    a, b = _files_by_relative_path(ours), _files_by_relative_path(theirs)
    differences = [f"content differs: {p}" for p in sorted(a.keys() & b.keys()) if a[p] != b[p]]
    differences += [f"only in {ours.name}: {p}" for p in sorted(a.keys() - b.keys())]
    differences += [f"only in {theirs.name}: {p}" for p in sorted(b.keys() - a.keys())]
    return differences


def main():
    parser = argparse.ArgumentParser(description="Build example notebook bundles for S3")
    commands = parser.add_subparsers(dest="command", required=True)

    archive = commands.add_parser("archive", help="Write <tag>.zip for each version tag")
    archive.add_argument("tags", nargs="+")
    archive.add_argument("--out", type=Path, required=True)

    tree = commands.add_parser("tree", help="Mirror the files at a ref with manifest.json")
    tree.add_argument("ref")
    tree.add_argument("--out", type=Path, required=True)

    compare = commands.add_parser("compare", help="Compare two archives")
    compare.add_argument("ours", type=Path)
    compare.add_argument("theirs", type=Path)

    args = parser.parse_args()
    repo = Path.cwd()
    if args.command == "archive":
        build_archives(repo, args.tags, args.out)
    elif args.command == "tree":
        build_tree(repo, args.ref, args.out)
    else:
        differences = compare_archives(args.ours, args.theirs)
        for difference in differences:
            print(difference)
        sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
