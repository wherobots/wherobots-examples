# Wherobots Examples

This repository contains the notebook examples that Wherobots provide for customers.
Those examples provide various examples of spatial analytics and spatial data
processing use cases showcasing the capabilites of [Apache Sedona](https://sedona.apache.org)
and [WherobotsDB](https://wherobots.com/wherobots-db/).

## Contributing
When raising a PR, make sure to run pre-commit hooks to the notebookes are cleaned and the readme is updated.
```bash
pre-commit run --all-files
```
Sometimes this will fail and update your notebooks or the readme file. Generally, you can rerun the command and it
will pass as the pre-commit hooks will fix the issues it finds.

## Support

For questions and support on those examples, please use the
[Wherobots Community](https://community.wherobots.com) if you are a Community Edition user,
or your direct support channel if you are a Professional or Enterprise Edition customer.

## Repository structure

```
.
|-- Analyzing_Data
|   |-- Bring_Your_Own_Model_Raster_Inference.ipynb
|   |-- Clustering_DBSCAN.ipynb
|   |-- GPS_Map_Matching.ipynb
|   |-- Getis_Ord_Gi*.ipynb
|   |-- Isochrones.ipynb
|   |-- K_Nearest_Neighbor_Join.ipynb
|   |-- Local_Outlier_Factor.ipynb
|   |-- Object_Detection.ipynb
|   |-- Raster_Classification.ipynb
|   |-- Raster_Segmentation.ipynb
|   |-- Raster_Text_To_Segments_Airplanes.ipynb
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
`-- Reading_and_Writing_Data
    |-- Loading_Common_Spatial_File_Types.ipynb
    |-- Map_Tile_Generation.ipynb
    `-- STAC_Reader.ipynb

```

### Assets folder

The following describes the purpose of each assets' subfolder:

- `.../assets/conf` - Map style configurations and other notebook settings
- `.../assets/img` -  Images used in the notebooks.
