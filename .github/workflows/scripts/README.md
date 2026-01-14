# Notebook to MDX Conversion Tool

Automatically converts Jupyter notebooks from `wherobots-examples` to Mintlify MDX files and syncs them to the `wherobots/docs` repository as an **Examples** tab.

## How It Works

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  wherobots-examples     │      │   GitHub Actions        │      │   wherobots/docs        │
│  ─────────────────────  │      │   ────────────────────  │      │   ─────────────────────  │
│                         │      │                         │      │                         │
│  *.ipynb files          │─────▶│  1. Convert to MDX      │─────▶│  examples/*.mdx         │
│                         │      │  2. Generate nav        │      │  docs.json (updated)    │
│                         │      │  3. Create PR           │      │                         │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### Workflow

1. **Edit/Add notebooks** in `wherobots-examples`
2. **Push to main** (or merge a PR)
3. **GitHub Action automatically**:
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

# Preview all notebooks
.github/workflows/scripts/preview_notebooks.sh

# Preview specific notebook
.github/workflows/scripts/preview_notebooks.sh -n Getting_Started/Part_1_Loading_Data.ipynb
```

The preview server starts at `http://localhost:3000` with a fully functional Mintlify site.

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

### 1. Create Personal Access Token

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Create a new token with:
   - **Name**: `DOCS_REPO_TOKEN`
   - **Repository access**: Select `wherobots/docs`
   - **Permissions**: Contents (Read and write)

### 2. Add Secret to Repository

1. Go to **wherobots/wherobots-examples → Settings → Secrets and variables → Actions**
2. Create new secret:
   - **Name**: `DOCS_REPO_TOKEN`
   - **Value**: Paste the token from step 1

### 3. One-Time docs.json Setup (Optional)

If the docs repository doesn't have a tabs-based navigation yet, you may need to restructure it. The workflow will automatically add/update the Examples tab.

## File Structure

```
.github/workflows/
├── convert-notebooks-to-mdx.yml    # Main workflow
└── scripts/
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
# Full end-to-end test
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
