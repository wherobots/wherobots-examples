# Wherobots Examples

This repository contains the notebook examples that Wherobots provide for customers.
Those examples provide various examples of spatial analytics and spatial data
processing use cases showcasing the capabilites of [Apache Sedona](https://sedona.apache.org)
and [WherobotsDB](https://wherobots.com/wherobots-db/).

## Support

For questions and support on those examples, please use the
[Wherobots Community](https://community.wherobots.com) if you are a Community Edition user,
or your direct support channel if you are a Professional or Enterprise Edition customer.

## Repository structure

```
.
├── Analyzing_Data            # Explore WherobotsDB and WherobotsAI features: clustering, spatial statistics, map matching, joins, outlier detection, model inference, object detection, raster processing.
│   ├── assets
│   │   ├── conf
│   │   └── img
│   ├── Bring_Your_Own_Model_Raster_Inference.ipynb
│   ├── Clustering_DBSCAN.ipynb
│   ├── Getis_Ord_Gi*.ipynb
│   ├── GPS_Map_Matching.ipynb
│   ├── K_Nearest_Neighbor_Join.ipynb
│   ├── Local_Outlier_Factor.ipynb
│   ├── Object_Detection.ipynb
│   ├── Raster_Classification.ipynb
│   └── Raster_Segmentation.ipynb
├── Getting_Started           # 4 part introduction to Wherobots environment: loading, reading, accelerating, and joining geospatial data.
│   ├── assets
│   │   └── conf
│   ├── Part_1_Loading_Data.ipynb
│   ├── Part_2_Reading_Spatial_Files.ipynb
│   ├── Part_3_Accelerating_Geospatial_Datasets.ipynb
│   └── Part_4_Spatial_Joins.ipynb
├── Open_Data_Connections     # Connect to open datasets in Wherobots: ESA WorldCover, Foursquare Places, Overture Maps.
│   ├── assets
│   │   ├── conf
│   │   └── img
│   ├── ESA_WorldCover.ipynb
│   ├── Foursquare_Places.ipynb
│   └── Overture_Maps.ipynb
├── Reading_and_Writing_Data  # Read and write with multiple data formats: spatial files, map tiles, STAC data.
│   ├── Loading_Common_Spatial_File_Types.ipynb
│   ├── Map_Tile_Generation.ipynb
│   └── STAC_Reader.ipynb
└── README.md
```

### Assets folder

The following describes the purpose of each assets' subfolder:

- `.../assets/conf` - Map style configurations and other notebook settings
- `.../assets/img` -  Images used in the notebooks.
