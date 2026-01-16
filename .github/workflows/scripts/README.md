# Notebook to MDX Conversion Tool

Automatically converts Jupyter notebooks from `wherobots-examples` to Mintlify MDX files and syncs them to the `wherobots/docs` repository as an **Examples** tab.

**Key feature:** Notebooks are executed in Wherobots Cloud before conversion, so **cell outputs are included** in the documentation.

## How It Works

```
┌─────────────────────────┐      ┌──────────────────────────┐      ┌─────────────────────────┐
│  wherobots-examples     │      │   Wherobots Cloud        │      │   wherobots/docs        │
│  ─────────────────────  │      │   ────────────────────── │      │   ─────────────────────  │
│                         │      │                          │      │                         │
│  *.ipynb files          │─────▶│  Execute notebooks       │      │                         │
│                         │      │  (via Runs API)          │      │                         │
│                         │◀─────│  Return with outputs     │      │                         │
│                         │      │                          │      │                         │
│  GitHub Actions:        │      └──────────────────────────┘      │                         │
│  1. Upload to S3        │                                        │                         │
│  2. Trigger execution   │                                        │                         │
│  3. Download results    │                                        │                         │
│  4. Convert to MDX      │───────────────────────────────────────▶│  examples/*.mdx         │
│  5. Create PR           │                                        │  docs.json (updated)    │
└─────────────────────────┘                                        └─────────────────────────┘
```

### Workflow

1. **Edit/Add notebooks** in `wherobots-examples`
2. **Push to main** (or merge a PR)
3. **GitHub Action automatically**:
   - Uploads notebooks to S3
   - Triggers Wherobots Cloud to execute notebooks (captures outputs)
   - Downloads executed notebooks
   - Converts all notebooks to MDX format
   - Generates the Examples tab navigation
   - Creates a PR in `wherobots/docs`
4. **Merge the docs PR** to publish

**That's it!** No manual editing of navigation or MDX files required.

## Quick Start

### Preview Locally

```bash
# Install Mintlify CLI
npm i -g mint

# Preview all notebooks (without outputs - execution requires Wherobots Cloud)
.github/workflows/scripts/preview_notebooks.sh

# Preview specific notebook
.github/workflows/scripts/preview_notebooks.sh -n Getting_Started/Part_1_Loading_Data.ipynb
```

The preview server starts at `http://localhost:3000` with a fully functional Mintlify site.

### Preview with Outputs

To preview notebooks with cell outputs locally, first download executed notebooks from S3:

```bash
# After a workflow run, download executed notebooks
aws s3 sync s3://YOUR_BUCKET/notebook-runs/<run-id>/output/ ./executed_notebooks/

# Preview with outputs
.github/workflows/scripts/preview_notebooks.sh --source ./executed_notebooks
```

### Convert Without Preview

```bash
# Convert single notebook
python .github/workflows/scripts/convert_notebook_to_mdx.py \
  Getting_Started/Part_1_Loading_Data.ipynb \
  ./output

# Convert all notebooks
python .github/workflows/scripts/convert_notebook_to_mdx.py . ./output --verbose
```

## Setup

### 1. Create S3 Bucket

Create an S3 bucket for storing notebooks during execution:

```bash
aws s3 mb s3://wherobots-notebook-execution --region us-west-2
```

### 2. Create IAM User for GitHub Actions

Create an IAM user with this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::wherobots-notebook-execution",
        "arn:aws:s3:::wherobots-notebook-execution/*"
      ]
    }
  ]
}
```

Generate access keys for the IAM user.

### 3. Configure Wherobots S3 Storage Integration

In Wherobots Cloud:
1. Go to **Settings > Storage Integrations**
2. Click **Add Integration**
3. Enter your bucket name
4. Follow the IAM role setup instructions provided by Wherobots

This allows Wherobots runtimes to access your S3 bucket during notebook execution.

### 4. Add GitHub Secrets

Go to **wherobots/wherobots-examples → Settings → Secrets and variables → Actions**

**Secrets:**
| Name | Description |
|------|-------------|
| `WHEROBOTS_API_KEY` | Your Wherobots API key (from cloud.wherobots.com > API Keys) |
| `AWS_ACCESS_KEY_ID` | IAM user access key (from step 2) |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key (from step 2) |
| `DOCS_REPO_TOKEN` | GitHub PAT with write access to `wherobots/docs` |

**Variables:**
| Name | Description |
|------|-------------|
| `NOTEBOOKS_BUCKET` | Your S3 bucket name (e.g., `wherobots-notebook-execution`) |

### 5. One-Time docs.json Setup (Optional)

If the docs repository doesn't have a tabs-based navigation yet, you may need to restructure it. The workflow will automatically add/update the Examples tab.

## File Structure

```
.github/workflows/
├── convert-notebooks-to-mdx.yml    # Main workflow
└── scripts/
    ├── execute_notebooks.py        # Runs in Wherobots Cloud to execute notebooks
    ├── convert_notebook_to_mdx.py  # Notebook → MDX converter
    ├── generate_navigation.py      # Auto-generates navigation
    ├── preview_notebooks.sh        # Local preview tool
    └── README.md                   # This file
```

## Output Structure in Docs

```
wherobots/docs/
├── docs.json                       # Navigation auto-updated
└── examples/
    ├── Getting_Started/
    │   ├── Part_1_Loading_Data.mdx
    │   ├── Part_2_Reading_Spatial_Files.mdx
    │   └── ...
    ├── Analyzing_Data/
    │   ├── Clustering_DBSCAN.mdx
    │   └── ...
    ├── Reading_and_Writing_Data/
    │   └── ...
    └── Open_Data_Connections/
        └── ...
```

## Excluded Notebooks

Files prefixed with `Raster_Inference` are excluded from conversion:

| Excluded File | Reason |
|--------------|--------|
| `Raster_Inference_*.ipynb` | Contains sensitive inference examples |

To modify exclusions, edit `should_exclude_notebook()` in `convert_notebook_to_mdx.py`.

## Command Reference

### execute_notebooks.py

Runs inside Wherobots Cloud. Not intended for local use.

```bash
python execute_notebooks.py \
  --s3-input-prefix s3://bucket/input/ \
  --s3-output-prefix s3://bucket/output/ \
  --timeout 900

Arguments:
  --s3-input-prefix    S3 prefix containing input notebooks
  --s3-output-prefix   S3 prefix for output notebooks
  --timeout            Timeout per notebook in seconds (default: 900)
  --manifest-key       S3 key for execution manifest (default: manifest.json)
```

### convert_notebook_to_mdx.py

```bash
python convert_notebook_to_mdx.py <input> <output> [options]

Arguments:
  input              Notebook file or directory
  output             Output directory for MDX files

Options:
  --no-output        Exclude cell outputs
  --verbose, -v      Show detailed progress
  --category NAME    Category for icon selection
```

### generate_navigation.py

```bash
python generate_navigation.py <examples_dir> [docs.json]

Arguments:
  examples_dir       Directory containing MDX files
  docs.json          Path to docs.json (optional, updates in place)
```

### preview_notebooks.sh

```bash
./preview_notebooks.sh [options]

Options:
  -n, --notebook     Convert specific notebook only
  -s, --source       Source directory for notebooks (default: repo root)
  -a, --all          Convert all notebooks (default)
  -p, --port         Preview server port (default: 3000)
  -o, --output       Output directory (default: .preview)
  -h, --help         Show help
```

## MDX Features

The converter produces Mintlify-compatible MDX with:

### Frontmatter
```yaml
---
title: "Notebook Title"
description: "Auto-extracted description"
icon: "chart-line"
---
```

### Code Blocks
```python
# Python code with syntax highlighting
df = sedona.read.format("parquet").load("s3://...")
```

### Output Rendering
- **Text output**: Collapsible `<Expandable>` sections
- **Images**: Wrapped in `<Frame>` component
- **Tables**: HTML output in expandable sections
- **Errors**: Displayed with ANSI codes stripped

## Troubleshooting

### Preview won't start

```bash
# Check Mintlify CLI version
mint --version

# Reinstall if needed
npm i -g mint@latest

# Try different port
./preview_notebooks.sh -p 3333
```

### Workflow fails to create PR

1. Verify `DOCS_REPO_TOKEN` secret exists
2. Check token has write access to `wherobots/docs`
3. Ensure token hasn't expired
4. Check workflow logs for specific errors

### Wherobots execution fails

1. Check the Wherobots run in [cloud.wherobots.com/job-runs](https://cloud.wherobots.com/job-runs)
2. Verify `WHEROBOTS_API_KEY` secret is valid
3. Verify S3 Storage Integration is configured in Wherobots
4. Check that AWS credentials have access to the S3 bucket
5. Review the run logs in the GitHub Actions output

### Notebook execution timeout

Individual notebooks have a 15-minute timeout by default. If a notebook needs more time:
1. The workflow will continue with other notebooks
2. The failed notebook will be included without outputs
3. Consider simplifying the notebook or breaking it into smaller parts

### MDX rendering issues

- Check for unescaped `{`, `}`, `<`, `>` in markdown
- Verify images are valid base64
- Run `mint broken-links` to find issues

### Navigation not updating

The workflow regenerates navigation from scratch each time. If pages are missing:
1. Check the notebook converted successfully
2. Verify the MDX file exists in the PR
3. Check for errors in `generate_navigation.py` output

## Development

### Testing Locally

```bash
# Full end-to-end test (without outputs)
./preview_notebooks.sh

# Test conversion only
python convert_notebook_to_mdx.py . /tmp/test-output --verbose

# Test navigation generation
python generate_navigation.py /tmp/test-output
```

### Modifying Conversion

Key functions in `convert_notebook_to_mdx.py`:

| Function | Purpose |
|----------|---------|
| `process_markdown_cell()` | Convert markdown cells |
| `process_code_cell()` | Convert code + outputs |
| `generate_frontmatter()` | Create MDX frontmatter |
| `should_exclude_notebook()` | Filter notebooks |

### Modifying Execution

Key functions in `execute_notebooks.py`:

| Function | Purpose |
|----------|---------|
| `execute_notebook()` | Run notebook with papermill |
| `list_s3_notebooks()` | Find notebooks in S3 |
| `download_notebook()` | Download from S3 |
| `upload_notebook()` | Upload to S3 |

### Modifying Navigation

Edit `CATEGORY_CONFIG` in `generate_navigation.py` to:
- Change category display names
- Update icons
- Adjust sort order

## FAQ

**Q: What happens when I delete a notebook?**
A: The workflow syncs all notebooks fresh each time. Deleted notebooks will be removed from the docs PR.

**Q: Can I manually edit the MDX files?**
A: You can, but changes will be overwritten on the next sync. Edit the source notebook instead.

**Q: How do I add a new category?**
A: Just create a new folder in `wherobots-examples`. The navigation generator will pick it up automatically.

**Q: What if the docs PR has conflicts?**
A: Close the PR and trigger a new workflow run. The new PR will have the latest state.

**Q: Why are there no outputs in my local preview?**
A: Notebook execution requires Wherobots Cloud. For local preview with outputs, download executed notebooks from S3 after a workflow run and use `--source ./executed_notebooks`.

**Q: What happens if a notebook fails to execute?**
A: The workflow continues with other notebooks. Failed notebooks are included in the docs without outputs. Check the execution manifest in S3 for details.

**Q: How much does notebook execution cost?**
A: Execution uses a `medium` Wherobots runtime. Check your Wherobots pricing for hourly rates. Typical execution takes 1-2 hours for ~30 notebooks.

**Q: Can I skip notebook execution?**
A: Yes, use manual dispatch with `skip_execution: true`. This converts notebooks without outputs (same as local preview).
