# ForestVitalityQuest

## TODO

- Move to STAC access for the data via stacstac 

## Description

DLR project

ML4Earth

ForestVitalityQuest

Data from KIT

Data CRS:

Cubo:
- cut is somewhere west of city Halle at 12 degrees
- EPSG:32633
- EPSG:32632

deadwood data:
- EPSG:3035

Shapefiles:
- EPSG:3035

-> So better convert cubo stuff to the corresponding UTM grid until things work out better.
-> For future: Deadwood data and shapefiles should be converted to UTM as well.

## Requirements

```bash
conda create -n forestvitalityquest python pip
conda activate forestvitalityquest
conda install -n forestvitalityquest -c conda-forge cubo xarray spyndex importlib_metadata ipykernel matplotlib dask sen2nbar numpy gdal rasterio scipy scikit-learn netcdf4 h5netcdf scikit-image pandas zarr

python -Xfrozen_modules=off -m ipykernel install --user --name "ForestVitalityQuest" --display-name "Forest Vitality Quest Kernel"
```

conversions of the files to netcdf with convert.bat

then conversion to a datacube with createDatacube.py

```bash
python createDatacube --input_dir /path/to/input [--output_dir /path/to/output] [--save_zarr]
```