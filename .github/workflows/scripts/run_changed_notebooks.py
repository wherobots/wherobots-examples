#!/usr/bin/env python3
"""Execute the notebooks whose code cells changed in a PR as Wherobots job runs.

Each notebook is converted to a Python script with the same nbconvert config used
by the release workflow, submitted with `wherobots job-runs create`, and polled
until it reaches a terminal state. A notebook whose markdown cells changed but
whose code cells did not is skipped -- prose edits don't need compute.

Writes a markdown report (for the PR comment) and exits non-zero if any run
failed, so the check can gate the PR.
"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NBCONVERT_CONFIG = REPO_ROOT / ".github/workflows/config/nbconvert_config.py"
NBCONVERT_TEMPLATE = REPO_ROOT / ".github/workflows/config/python_nomagic"

# Scala notebooks run on a different kernel and are submitted as JARs, not scripts.
EXCLUDED_PREFIXES = ("scala/",)

TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}
RUN_ID_LOCK = threading.Lock()
COMMENT_MARKER = "<!-- notebook-job-run-gate -->"

# Log-parsing markers used to pull a readable failure out of a job run log.
TRACEBACK_HEADER = "Traceback (most recent call last):"
HARNESS_MARKER = "run-scripts/run_submit.py"
EXIT_CODE_MARKER = "Subprocess finished with return code:"
JVM_FRAME = re.compile(r"\s*at [\w$.]+\(.*\)\s*$")
EXCEPTION_LINE = re.compile(r"\S.*(Error|Exception)\b.*:")


@dataclass
class Result:
    notebook: str
    status: str = "SKIPPED"
    run_id: str | None = None
    detail: str = ""
    seconds: float = 0.0
    log_excerpt: str = ""

    @property
    def passed(self) -> bool:
        return self.status in ("COMPLETED", "SKIPPED")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)


def git(*args: str) -> str:
    proc = run(["git", *args], cwd=REPO_ROOT)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def changed_notebooks(base: str) -> list[str]:
    """Notebooks added, copied, modified or renamed between base and the checkout."""
    out = git("diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD", "--", "*.ipynb")
    paths = [line.strip() for line in out.splitlines() if line.strip()]
    return sorted(p for p in paths if not p.startswith(EXCLUDED_PREFIXES))


def code_cells(source: str) -> list[str]:
    """Source of every code cell, in order. Markdown and raw cells are ignored."""
    try:
        nb = json.loads(source)
    except json.JSONDecodeError:
        # An unparseable notebook is a change worth running rather than skipping.
        return ["<unparseable>"]
    cells = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        cells.append("".join(src) if isinstance(src, list) else src)
    return cells


def code_changed(path: str, base: str) -> bool:
    """True if the notebook is new, or if any code cell's source differs from base."""
    before = run(["git", "show", f"{base}:{path}"], cwd=REPO_ROOT)
    if before.returncode != 0:
        return True  # new file at this path
    after = (REPO_ROOT / path).read_text(encoding="utf-8")
    return code_cells(before.stdout) != code_cells(after)


def convert(path: str, out_dir: Path) -> Path | None:
    """Convert a notebook to a Python script. Returns None if nothing executable is left."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_]+", "_", path.replace(".ipynb", ""))
    proc = run(
        [
            "jupyter", "nbconvert",
            "--config", str(NBCONVERT_CONFIG),
            "--to", "python",
            "--template", str(NBCONVERT_TEMPLATE),
            str(REPO_ROOT / path),
            "--output", stem,
            f"--output-dir={out_dir}",
        ],
        cwd=REPO_ROOT,
    )
    script = out_dir / f"{stem}.py"
    if proc.returncode != 0 or not script.exists():
        raise RuntimeError(f"nbconvert failed for {path}: {proc.stderr.strip()[:1000]}")
    # The nbconvert config blanks visualization cells; a notebook that is entirely
    # visualization converts to a file with no statements left to run.
    body = [ln for ln in script.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    return script if body else None


def wb(*args: str) -> subprocess.CompletedProcess:
    return run(["wherobots", *args])


def submit(script: Path, name: str, runtime: str, timeout: int) -> str:
    proc = wb(
        "job-runs", "create", str(script),
        "--name", name,
        "--runtime", runtime,
        "--timeout", str(timeout),
        "--output", "json",
        "--yes",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"job submission failed: {(proc.stderr or proc.stdout).strip()[:1000]}")
    # The CLI prints upload progress before the JSON payload, so take the last
    # line that parses as an object carrying an id.
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            run_id = json.loads(line).get("id")
        except json.JSONDecodeError:
            continue
        if run_id:
            return run_id
    raise RuntimeError(f"could not parse job run id from: {proc.stdout.strip()[:500]}")


def poll(run_id: str, deadline: float, interval: int = 20) -> str:
    """Poll until the run reaches a terminal status. Returns the final status."""
    status = "PENDING"
    while time.time() < deadline:
        time.sleep(interval)
        proc = wb("api", "runs", "get-job-run", "--run-id", run_id)
        if proc.returncode != 0:
            continue  # transient API error; keep polling until the deadline
        try:
            status = json.loads(proc.stdout).get("status", status)
        except json.JSONDecodeError:
            continue
        if status in TERMINAL_STATUSES:
            return status
    return "TIMED_OUT"


def fetch_logs(run_id: str, page_size: int = 500, max_pages: int = 60) -> list[str]:
    lines: list[str] = []
    cursor = None
    for _ in range(max_pages):
        cmd = ["api", "runs", "logs", "get-job-run-logs", "--run-id", run_id, "--size", str(page_size)]
        if cursor:
            cmd += ["--cursor", cursor]
        proc = wb(*cmd)
        if proc.returncode != 0:
            break
        try:
            page = json.loads(proc.stdout)
        except json.JSONDecodeError:
            break
        items = page.get("items") or []
        lines.extend(item.get("raw", "") for item in items)
        nxt = page.get("next_page")
        if not items or not nxt or nxt == cursor:
            break
        cursor = nxt
    return lines


def failure_excerpt(lines: list[str], script_name: str = "", max_lines: int = 50) -> str:
    """The slice of the log that explains why the run failed.

    A failed job emits two Python tracebacks: the notebook's own, and the one from
    Wherobots' `run_submit.py` harness reporting a non-zero exit. Only the first is
    useful to a notebook author, so prefer it and drop the JVM frames that Spark
    interleaves around it.
    """
    if not lines:
        return "(no logs were returned for this run)"

    useful = [ln for ln in lines if not JVM_FRAME.match(ln)]

    starts = [i for i, ln in enumerate(useful) if ln.lstrip().startswith(TRACEBACK_HEADER)]
    blocks = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(useful)
        blocks.append(useful[start:end])

    chosen: list[str] = []
    if blocks:
        # The notebook's own traceback names the converted script; the harness
        # traceback names run_submit.py. Prefer the former.
        named = [b for b in blocks if script_name and any(script_name in ln for ln in b)]
        not_harness = [b for b in blocks if not any(HARNESS_MARKER in ln for ln in b)]
        chosen = (named or not_harness or blocks)[0]
        # Stop at the exception line; anything after it belongs to the harness.
        for i, ln in enumerate(chosen):
            if i and EXCEPTION_LINE.match(ln):
                chosen = chosen[: i + 1]
                break
    else:
        chosen = [ln for ln in useful if ln.strip()][-max_lines:]

    excerpt = chosen[:max_lines]
    exit_line = next((ln for ln in reversed(useful) if EXIT_CODE_MARKER in ln), None)
    if exit_line and exit_line not in excerpt:
        excerpt = excerpt + ["", exit_line.strip()]
    return "\n".join(excerpt)


def record_run_id(work_dir: str, run_id: str) -> None:
    """Append a submitted run id so the workflow can cancel it if it is interrupted."""
    with RUN_ID_LOCK:
        path = Path(work_dir) / "run_ids.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(run_id + "\n")


def execute(path: str, args) -> Result:
    result = Result(notebook=path)
    started = time.time()
    try:
        script = convert(path, Path(args.work_dir) / "scripts")
    except RuntimeError as exc:
        result.status = "CONVERT_FAILED"
        result.detail = str(exc)
        return result
    if script is None:
        result.detail = "converts to no executable code (visualization-only notebook)"
        return result

    name = f"pr-{args.pr}-{Path(path).stem}"[:60]
    try:
        result.run_id = submit(script, name, args.runtime, args.timeout)
    except RuntimeError as exc:
        result.status = "SUBMIT_FAILED"
        result.detail = str(exc)
        return result

    record_run_id(args.work_dir, result.run_id)
    print(f"submitted {path} as run {result.run_id}", flush=True)
    result.status = poll(result.run_id, deadline=started + args.timeout + 600)
    result.seconds = time.time() - started
    if not result.passed:
        result.log_excerpt = failure_excerpt(fetch_logs(result.run_id), script.name)
    return result


def render(results: list[Result], args) -> str:
    if not results:
        return (
            f"{COMMENT_MARKER}\n## Notebook job runs\n\n"
            "No notebook code cells changed in this PR, so no job runs were needed.\n"
        )

    failures = [r for r in results if not r.passed]
    header = "All changed notebooks ran successfully." if not failures else (
        f"{len(failures)} of {len(results)} changed notebook(s) failed to run. "
        "The notebook code in this PR does not execute as written."
    )

    lines = [
        COMMENT_MARKER,
        "## Notebook job runs",
        "",
        header,
        "",
        "| Notebook | Result | Job run | Duration |",
        "| --- | --- | --- | --- |",
    ]
    for r in sorted(results, key=lambda r: (r.passed, r.notebook)):
        label = {"COMPLETED": "passed", "SKIPPED": "skipped"}.get(r.status, f"**{r.status}**")
        duration = f"{r.seconds / 60:.1f} min" if r.seconds else "-"
        lines.append(f"| `{r.notebook}` | {label} | `{r.run_id or '-'}` | {duration} |")

    for r in failures:
        lines += ["", f"### `{r.notebook}` — {r.status}", ""]
        if r.run_id:
            lines.append(f"Job run `{r.run_id}` (runtime: {args.runtime})")
            lines.append("")
        if r.detail:
            lines += ["```", r.detail[:2000], "```", ""]
        if r.log_excerpt:
            lines += ["```", r.log_excerpt, "```"]

    skipped = [r for r in results if r.status == "SKIPPED"]
    if skipped:
        lines += ["", "Skipped notebooks converted to no executable code."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--pr", default="local")
    parser.add_argument("--runtime", default="tiny")
    parser.add_argument("--timeout", type=int, default=3600, help="per-notebook job timeout, seconds")
    parser.add_argument("--max-parallel", type=int, default=4)
    parser.add_argument("--work-dir", default="notebook-run-results")
    parser.add_argument("--report", default="notebook-run-results/report.md")
    args = parser.parse_args()

    if not os.environ.get("WHEROBOTS_API_KEY"):
        print("WHEROBOTS_API_KEY is not set; cannot run notebooks.", file=sys.stderr)
        return 2

    candidates = changed_notebooks(args.base_sha)
    if not candidates:
        print("No notebooks changed.")
        to_run = []
    else:
        to_run = [p for p in candidates if code_changed(p, args.base_sha)]
        for path in candidates:
            verdict = "code changed" if path in to_run else "markdown only, skipping"
            print(f"{path}: {verdict}")

    results: list[Result] = []
    if to_run:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as pool:
            results = list(pool.map(lambda p: execute(p, args), to_run))

    report = render(results, args)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print("\n" + report)

    failures = [r for r in results if not r.passed]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
