#!/usr/bin/env bash
# Post (or update) a single sticky comment on the PR with notebook job run results.
set -euo pipefail

MARKER='<!-- notebook-job-run-gate -->'
REPORT="notebook-run-results/report.md"

if [[ ! -f "$REPORT" ]]; then
  # The runner never got far enough to write a report -- say so rather than
  # leaving a red check with no explanation.
  mkdir -p "$(dirname "$REPORT")"
  {
    echo "$MARKER"
    echo "## Notebook job runs"
    echo
    echo "The notebook gate did not complete (job status: \`${JOB_STATUS}\`), so no"
    echo "notebook was validated. See the [workflow run](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}) for details."
  } > "$REPORT"
fi

# Nothing changed that needed a run, and no prior comment to update: stay quiet.
existing=$(gh api "repos/${GITHUB_REPOSITORY}/issues/${PR}/comments" --paginate \
  --jq "[.[] | select(.body | contains(\"$MARKER\")) | .id] | first // empty")

if grep -q "no job runs were needed" "$REPORT" && [[ -z "$existing" ]]; then
  echo "No code cell changes and no existing comment; skipping."
  exit 0
fi

{
  echo
  echo "---"
  echo "[Workflow run](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}) · commit \`${GITHUB_SHA:0:7}\`"
} >> "$REPORT"

if [[ -n "$existing" ]]; then
  gh api --method PATCH "repos/${GITHUB_REPOSITORY}/issues/comments/${existing}" \
    -F "body=@${REPORT}" > /dev/null
  echo "Updated comment $existing"
else
  gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${PR}/comments" \
    -F "body=@${REPORT}" > /dev/null
  echo "Created new comment"
fi
