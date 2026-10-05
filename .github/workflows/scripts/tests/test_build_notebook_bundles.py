"""python -m unittest discover -s .github/workflows/scripts/tests"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_notebook_bundles as bundles  # noqa: E402

NOTEBOOK = "Getting_Started/Part_1_Loading_Data.ipynb"
IMAGE = "assets/img/header-logo.png"


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


class BundleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        self.write(NOTEBOOK, b'{"cells": ["tagged"]}')
        self.write(IMAGE, bytes(range(256)))
        self.write("README.md", b"examples\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "tagged")
        git(self.repo, "tag", "v2.35.2")
        self.write(NOTEBOOK, b'{"cells": ["main"]}')
        self.write("Analyzing_Data/New.ipynb", b"{}")
        (self.repo / "untracked.txt").write_text("not in git")
        git(self.repo, "add", NOTEBOOK, "Analyzing_Data/New.ipynb")
        git(self.repo, "commit", "-q", "-m", "main")

    def write(self, path, body):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)

    def make_zip(self, name, entries):
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            for entry, body in entries.items():
                archive.writestr(entry, body)
        return path

    def test_archive_matches_github_tag_zip_layout(self):
        out = self.root / "archive"
        bundles.build_archives(self.repo, ["v2.35.2"], out)
        with zipfile.ZipFile(out / "v2.35.2.zip") as archive:
            files = {n for n in archive.namelist() if not n.endswith("/")}
            self.assertEqual(
                files,
                {
                    f"wherobots-examples-2.35.2/{p}"
                    for p in (NOTEBOOK, IMAGE, "README.md")
                },
            )
            self.assertEqual(
                archive.read(f"wherobots-examples-2.35.2/{NOTEBOOK}"),
                b'{"cells": ["tagged"]}',
            )
            self.assertEqual(
                archive.read(f"wherobots-examples-2.35.2/{IMAGE}"), bytes(range(256))
            )

    def test_archive_rejects_tags_that_are_not_versions(self):
        with self.assertRaisesRegex(ValueError, "converted-notebooks"):
            bundles.build_archives(
                self.repo, ["converted-notebooks"], self.root / "archive"
            )

    def test_tree_mirrors_tracked_files_with_a_github_style_manifest(self):
        out = self.root / "main"
        started = time.time()
        bundles.build_tree(self.repo, "HEAD", out)

        self.assertEqual((out / NOTEBOOK).read_bytes(), b'{"cells": ["main"]}')
        self.assertEqual((out / IMAGE).read_bytes(), bytes(range(256)))
        self.assertFalse((out / "untracked.txt").exists())
        # Fresh mtimes, so `aws s3 sync` re-uploads same-size edits.
        self.assertGreaterEqual((out / NOTEBOOK).stat().st_mtime, started - 1)

        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["sha"], git(self.repo, "rev-parse", "HEAD"))
        self.assertFalse(manifest["truncated"])
        entries = {e["path"]: e for e in manifest["tree"]}
        self.assertEqual(
            {p for p, e in entries.items() if e["type"] == "blob"},
            {NOTEBOOK, IMAGE, "README.md", "Analyzing_Data/New.ipynb"},
        )
        self.assertEqual(
            {p for p, e in entries.items() if e["type"] == "tree"},
            {"Getting_Started", "assets", "assets/img", "Analyzing_Data"},
        )
        self.assertEqual(entries[IMAGE]["size"], 256)
        self.assertEqual(
            entries[IMAGE]["sha"], git(self.repo, "rev-parse", f"HEAD:{IMAGE}")
        )

    def test_compare_ignores_the_top_folder(self):
        ours = self.make_zip("ours.zip", {f"a-1/{NOTEBOOK}": "{}", "a-1/README.md": "x"})
        github = self.make_zip(
            "github.zip", {f"b-2/{NOTEBOOK}": "{}", "b-2/README.md": "x"}
        )
        self.assertEqual(bundles.compare_archives(ours, github), [])

    def test_compare_reports_changed_missing_and_extra_files(self):
        ours = self.make_zip(
            "ours.zip", {f"a/{NOTEBOOK}": "{}", "a/README.md": "x", "a/extra.txt": ""}
        )
        github = self.make_zip(
            "github.zip", {f"b/{NOTEBOOK}": "changed", "b/README.md": "x", "b/gone.md": ""}
        )
        self.assertEqual(
            bundles.compare_archives(ours, github),
            [
                f"content differs: {NOTEBOOK}",
                "only in ours.zip: extra.txt",
                "only in github.zip: gone.md",
            ],
        )


if __name__ == "__main__":
    unittest.main()
