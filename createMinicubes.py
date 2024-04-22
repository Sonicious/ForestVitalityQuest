# libraries
import xarray as xr
import rioxarray
import geopandas as gpd
import rasterio.features
import numpy as np
import cubo
from sen2nbar.nbar import nbar_cubo
import spyndex
from PIL import Image

# plotting
import matplotlib.pyplot as plt

# Parameters
important_indices = ['NDVI']
startdate = "2018-01-01"
enddate = "2021-12-31"

## Load Shapefile

# load the shapefile which has many polygons. Explicitely use utf8 encoding
# Then bring everything to the corresponding UTM grid and calculate the center and edge size for cubo
# save everything to sitesExtended
sites = gpd.read_file('data/AreaSites/AreaSites.shp', encoding='utf-8')
sitesExtended = sites.assign(UTM='tt').assign(edgesize=0.0).assign(center_x=0.0).assign(center_y=0.0)
for rowIdx in sitesExtended.index:
    site = sites.loc[[rowIdx]]
    centroid = site.centroid.to_crs(epsg=4326).iloc[0]
    utm_zone = int((centroid.x + 180) // 6) + 1
    utm_crs = f'epsg:326{utm_zone}' if centroid.y >= 0 else f'epsg:327{utm_zone}'
    site_utm = site.to_crs(utm_crs)
    bounds_utm = site_utm.geometry.total_bounds
    min_x, min_y, max_x, max_y = bounds_utm
    width = max_x - min_x
    height = max_y - min_y
    edge_size = max(width, height)
    sitesExtended.at[rowIdx, 'UTM'] = utm_crs
    sitesExtended.at[rowIdx, 'edgesize'] = edge_size
    sitesExtended.at[rowIdx, 'center_x'] = centroid.x
    sitesExtended.at[rowIdx, 'center_y'] = centroid.y
    sitesExtended.at[rowIdx, 'Geometry'] = site_utm.geometry.iloc[0]

## Load Deadwood Data and prepare

deadwood = xr.open_zarr('data/MD.zarr').deadwood
deadwood = deadwood.rio.write_crs('EPSG:3035')

## this will move to the loop
for testsite in sitesExtended.index:
    print(f"Processing site {testsite}")
    try:
        data_sentinel2 = cubo.create(
            lat = sitesExtended.loc[[testsite]].center_y.values[0],
            lon = sitesExtended.loc[[testsite]].center_x.values[0],
            collection = 'sentinel-2-l2a',
            # NDVI: B08, B04
            # RGB: B04, B03, B02
            bands = ['B04', 'B08'],
            start_date = startdate,
            end_date = enddate,
            edge_size = sitesExtended.loc[[testsite]].edgesize.values[0] / 10 + 5, # 1 pixel is 10 m. so we need to convert meters to pixels. adding some extra
            resolution = 10,
            query = {"eo:cloud_cover": {"lt": 10}}
        )
        
        if data_sentinel2.rio.crs is None:
            data_sentinel2.rio.write_crs('EPSG:'+str(data_sentinel2.attrs['epsg']), inplace=True)

        print("  data found:")
        print("    size: ", data_sentinel2.nbytes / 1e6, "MB")
        print("    time: ", len(data_sentinel2.time), "steps")
        data_sentinel2 = nbar_cubo(data_sentinel2)

        if len(set(data_sentinel2['time'].values)) != len(data_sentinel2['time'].values):
            data_sentinel2 = data_sentinel2.groupby("time")
            data_sentinel2 = data_sentinel2.mean(dim="time", skipna=True)
        
        # calculate NDVI
        indices = spyndex.computeIndex(
            index = important_indices,
            params = {
                "R": data_sentinel2.sel(band = "B04"),
                "N": data_sentinel2.sel(band = "B08"),
            }
        )
        
        ndvi_subset = indices.load()
            
    except Exception as e:
        print(f"Error: {e}")
        data_sentinel2 = None
        continue

    min_x, min_y, max_x, max_y = sitesExtended.loc[[testsite]].total_bounds
    target_crs = sitesExtended.loc[[testsite]].UTM.values[0]
    deadwood_subset_2018 = deadwood.sel(x=slice(min_x, max_x), y=slice(min_y, max_y)).isel(time=0).transpose('y', 'x')
    deadwood_subset_2019 = deadwood.sel(x=slice(min_x, max_x), y=slice(min_y, max_y)).isel(time=1).transpose('y', 'x')
    deadwood_subset_2020 = deadwood.sel(x=slice(min_x, max_x), y=slice(min_y, max_y)).isel(time=2).transpose('y', 'x')
    deadwood_subset_2021 = deadwood.sel(x=slice(min_x, max_x), y=slice(min_y, max_y)).isel(time=3).transpose('y', 'x')
    deadwood_reprojected_2018 = deadwood_subset_2018.rio.reproject(target_crs)
    deadwood_reprojected_2019 = deadwood_subset_2019.rio.reproject(target_crs)
    deadwood_reprojected_2020 = deadwood_subset_2020.rio.reproject(target_crs)
    deadwood_reprojected_2021 = deadwood_subset_2021.rio.reproject(target_crs)
    # grid is the same for all deadwood. Take 2018
    grid_xmin = round(min(deadwood_reprojected_2018.x.values.min(), ndvi_subset.x.values.min()))
    grid_xmax = round(max(deadwood_reprojected_2018.x.values.max(), ndvi_subset.x.values.max()))
    grid_ymin = round(min(deadwood_reprojected_2018.y.values.min(), ndvi_subset.y.values.min()))
    grid_ymax = round(max(deadwood_reprojected_2018.y.values.max(), ndvi_subset.y.values.max()))
    # amount of values in x/y
    numValues_x = round(np.mean([len(deadwood_reprojected_2018.x.values), len(ndvi_subset.x.values)]))
    numValues_y = round(np.mean([len(deadwood_reprojected_2018.y.values), len(ndvi_subset.y.values)]))

    new_y = np.linspace(grid_ymin, grid_ymax, numValues_y)
    new_x = np.linspace(grid_xmin, grid_xmax, numValues_x)

    siteNDVI = ndvi_subset.interp(y=new_y, x=new_x, method='linear')
    siteDeadwood_2018 = deadwood_reprojected_2018.interp(y=new_y, x=new_x, method='linear')
    siteDeadwood_2019 = deadwood_reprojected_2019.interp(y=new_y, x=new_x, method='linear')
    siteDeadwood_2020 = deadwood_reprojected_2020.interp(y=new_y, x=new_x, method='linear')
    siteDeadwood_2021 = deadwood_reprojected_2021.interp(y=new_y, x=new_x, method='linear')
    siteGeometry = sitesExtended.loc[[testsite]].to_crs(target_crs).geometry

    print('  same grid, same System finally')
    maskNDVI = rasterio.features.geometry_mask(
        geometries = siteGeometry,
        out_shape = (siteNDVI.y.size, siteNDVI.x.size),
        transform = siteNDVI.rio.transform(),
        invert = True
    )

    # maskDeadwood not working. Dunno why???
    # maskDeadwood = rasterio.features.geometry_mask(
    #     geometries = siteGeometry,
    #     out_shape = (siteDeadwood.y.size, siteDeadwood.x.size),
    #     transform = siteDeadwood.rio.transform(),
    #     invert = True
    # )

    finalNDVI = siteNDVI.where(maskNDVI, np.nan)
    finalDeadwood_2018 = siteDeadwood_2018.where(maskNDVI, np.nan)
    finalDeadwood_2019 = siteDeadwood_2019.where(maskNDVI, np.nan)
    finalDeadwood_2020 = siteDeadwood_2020.where(maskNDVI, np.nan)
    finalDeadwood_2021 = siteDeadwood_2021.where(maskNDVI, np.nan)
    
    finalSite = xr.Dataset(
        {
            'deadwood_2018': finalDeadwood_2018,
            'deadwood_2019': finalDeadwood_2019,
            'deadwood_2020': finalDeadwood_2020,
            'deadwood_2021': finalDeadwood_2020,
            'ndvi': xr.DataArray(
                finalNDVI.values,
                dims=['time', 'y', 'x'],
                coords = {
                    'time': siteNDVI.time, 
                    'y': siteNDVI.y, 
                    'x': siteNDVI.x
                }
            )
        },
        attrs = {
            'crs': target_crs
        }
    )      
    finalSite = finalSite.drop_vars('lambert_azimuthal_equal_area')
    finalSite.to_zarr(f'data/FinalSites/Site{testsite:03}.zarr', mode = 'w', consolidated = True)
    print(f"  Site {testsite} saved")

print("All sites processed")