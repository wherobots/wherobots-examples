# Wherobots Examples

This repository contains the notebook examples that Wherobots provide for customers.
Those examples provide various examples of spatial analytics and spatial data
processing use cases showcasing the capabilities of [Apache Sedona](https://sedona.apache.org)
and [WherobotsDB](https://wherobots.com/wherobots-db/).

## Contributing

When raising a PR, make sure to run pre-commit hooks to the notebooks are cleaned and the README is updated.

```bash
pre-commit run --all-files
```

Sometimes this will fail and update your notebooks or the README file. Generally, you can rerun the command and it
will pass as the pre-commit hooks will fix the issues it finds.

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
|   |-- RasterFlow_CHM.ipynb
|   |-- RasterFlow_ChangeDetection.ipynb
|   |-- RasterFlow_Chesapeake.ipynb
|   |-- RasterFlow_FTW.ipynb
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
