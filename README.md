# ForestVitalityQuest

## Description

DLR project

ML4Earth

ForestVitalityQuest

Data from KIT

## Requirements

```bash
conda create -n forestvitalityquest python pip
conda activate forestvitalityquest
conda install -n forestvitalityquest -c conda-forge cubo xarray spyndex importlib_metadata ipykernel matplotlib dask sen2nbar numpy gdal rasterio scipy scikit-learn netcdf4 h5netcdf scikit-image pandas zarr

python -Xfrozen_modules=off -m ipykernel install --user --name "ForestVitalityQuest" --display-name "Forest Vitality Quest Kernel"
```

conversions of the files to netcdf

```bash
gdalwarp -t_srs EPSG:4326 input.tif output.tif
gdal_translate -of NETCDF input.tif output.nc
gdalwarp -t_srs EPSG:4326 -of NetCDF input.tif output.nc
gdalwarp -t_srs EPSG:4326 -of NetCDF input1.tif input2.tif output.nc
```

Then run the following command to create the datacube

```bash
python createDatacube --input_dir /path/to/input [--output_dir /path/to/output] [--save_zarr]
```

