# Wherobots Examples

This repository contains the notebook examples that Wherobots provide for customers.
Those examples provide various examples of spatial analytics and spatial data
processing use cases showcasing the capabilities of [Apache Sedona](https://sedona.apache.org)
and [WherobotsDB](https://wherobots.com/wherobots-db/).

## Contributing

When raising a PR, make sure to run pre-commit hooks to ensure that the notebooks are cleaned and the `README` is updated.

```bash
pre-commit run --all-files
```

Sometimes this will fail and update your notebooks or the `README` file. Generally, you can re-run the
command and it will pass as the pre-commit hooks will fix the issues it finds.

## Documentation publishing

Notebooks in this repository are automatically converted to MDX format and published to the [Wherobots documentation](https://docs.wherobots.com) site. This happens via a GitHub Actions workflow (`.github/workflows/convert-notebooks.yml`) that runs when notebooks are modified on the `main` branch.

### How it works

1. **Conversion**: The `notebook_to_mdx.py` script converts `.ipynb` files to `.mdx` format, extracting markdown and code cells while generating appropriate frontmatter.
2. **Navigation**: The `update_docs_navigation.py` script updates the docs navigation structure to include the converted notebooks under "Spatial Analytics Tutorials" > "Example Notebooks".
3. **Publishing**: A PR is automatically created against the `wherobots/docs` repository with the converted files.

### Adding a new notebook

When you add a new notebook to this repository, you **must** update the navigation mapping so it appears in the correct category in the documentation:

1. Edit `.github/workflows/scripts/update_docs_navigation.py`
2. Add your notebook to the `FILENAME_TO_CATEGORY` dictionary with the appropriate category
3. The filename key should be lowercase with hyphens (e.g., `My_New_Notebook.ipynb` becomes `"my-new-notebook"`)

Example:
```python
FILENAME_TO_CATEGORY = {
    # ... existing entries ...
    "my-new-notebook": "Analyzing Data",  # Add your notebook here
}
```

Available categories:
- `"Getting Started"`
- `"Analyzing Data"`
- `"RasterFlow"`
- `"Reading and Writing Data"`
- `"Open Data Connections"`
- `"Scala"`

If you don't add your notebook to the mapping, it will appear under an "Other" category in the documentation.

**Note**: Notebooks with the `Raster_Inference_` prefix are excluded from documentation publishing.

## Local preview

You can preview how notebooks will look on the docs site locally using the Makefile targets. This requires the [`wherobots/docs`](https://github.com/wherobots/docs) repo cloned alongside this repo (at `../docs` by default).

### Prerequisites

- Python 3.x
- Node.js (for Mintlify CLI via `npx`)
- `wherobots/docs` repo cloned at `../docs`

### Make targets

| Target | Description |
|---|---|
| `make preview` | Full local preview workflow. Syncs the docs repo to `main`, converts notebooks to MDX, updates navigation, and starts the Mintlify dev server at `http://localhost:3000`. |
| `make preview-branch DOCS_BRANCH=<branch>` | Same as `preview` but checks out a specific docs repo branch instead of `main`. Useful when redesigning the tutorials section on a feature branch. |
| `make convert` | Converts notebooks to MDX files in the docs repo. Cleans previous output first. |
| `make update-nav` | Updates `docs.json` navigation to include converted notebooks. |
| `make sync-docs` | Checks out and pulls the target branch (default: `main`) in the docs repo. |
| `make clean` | Removes generated MDX files from the docs repo. |

### Configuration

| Variable | Default | Description |
|---|---|---|
| `DOCS_DIR` | `../docs` | Path to the `wherobots/docs` repo clone |
| `DOCS_BRANCH` | `main` | Docs repo branch to sync to |

### Examples

```bash
# Standard preview against docs main branch
make preview

# Preview against a feature branch in the docs repo
make preview-branch DOCS_BRANCH=redesign-tutorials

# Just convert notebooks without starting the server
make convert

# Use a different docs repo location
make preview DOCS_DIR=~/projects/docs
```

## Repository structure

```
.
|-- Analyzing_Data
|   |-- Clustering_DBSCAN.ipynb
|   |-- GPS_Map_Matching.ipynb
|   |-- Getis_Ord_Gi*.ipynb
|   |-- Isochrones.ipynb
|   |-- K_Nearest_Neighbor_Join.ipynb
|   |-- Local_Outlier_Factor.ipynb
|   |-- PMTiles-railroad.ipynb
|   |-- RasterFlow_Bring_Your_Own_Model.ipynb
|   |-- RasterFlow_Bring_Your_Own_Rasters_NAIP.ipynb
|   |-- RasterFlow_CHM.ipynb
|   |-- RasterFlow_ChangeDetection.ipynb
|   |-- RasterFlow_Chesapeake.ipynb
|   |-- RasterFlow_FTW.ipynb
|   |-- RasterFlow_S2_Mosaic.ipynb
|   |-- RasterFlow_Tile2Net.ipynb
|   |-- Raster_Inference_Bring_Your_Own_Model.ipynb
|   |-- Raster_Inference_Classification.ipynb
|   |-- Raster_Inference_Object_Detection.ipynb
|   |-- Raster_Inference_Segmentation.ipynb
|   |-- Raster_Inference_Text_To_Segments_Airplanes.ipynb
|   `-- Zonal_Stats_ESAWorldCover_Texas.ipynb
|-- CONTRIBUTING.md
|-- Getting_Started
|   |-- Part_1_Loading_Data.ipynb
|   |-- Part_2_Reading_Spatial_Files.ipynb
|   |-- Part_3_Accelerating_Geospatial_Datasets.ipynb
|   `-- Part_4_Spatial_Joins.ipynb
|-- Makefile
|-- Open_Data_Connections
|   |-- ESA_WorldCover.ipynb
|   |-- Foursquare_Places.ipynb
|   |-- NOAA_SWDI.ipynb
|   `-- Overture_Maps.ipynb
|-- Reading_and_Writing_Data
|   |-- Loading_Common_Spatial_File_Types.ipynb
|   |-- Map_Tile_Generation.ipynb
|   |-- STAC_Reader.ipynb
|   `-- Unity_Catalog_Delta_Tables.ipynb
`-- scala
    |-- Getting_Started.ipynb
    `-- packaging-example-project
        |-- pom.xml
        `-- src
            |-- main
            `-- test

```

### Assets folder

The following describes the purpose of each assets' subfolder:

- `.../assets/conf` - Map style configurations and other notebook settings
- `.../assets/img` -  Images used in the notebooks.
