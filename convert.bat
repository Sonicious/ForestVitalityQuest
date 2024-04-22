@echo off
setlocal enabledelayedexpansion

REM Set the path to your "SN" folder
set "sourceDir=C:\Users\marti\workspace\ForestVitalityQuest\data\MD"

REM Set the path to the target directory where the NetCDF files will be saved
set "targetDir=C:\Users\marti\workspace\ForestVitalityQuest\data\MD_NC"

REM Create the target directory if it doesn't exist
if not exist "!targetDir!" mkdir "!targetDir!"

REM Change the directory to the source directory
cd /d "!sourceDir!"

REM Loop through each TIFF file in the folder
for %%f in (*.tif) do (
    REM Define the output file name by replacing the extension and adding the target directory
    set "outputName=!targetDir!\%%~nf.nc"
    
    REM Combine gdalwarp and gdal_translate to reproject and convert directly to NetCDF
    gdalwarp -of NetCDF -co "FORMAT=NC4C" "%%f" "!outputName!"
    REM gdalwarp -t_srs EPSG:3035 -of NetCDF -co "FORMAT=NC4C" -co "COMPRESS=DEFLATE" "%%f" "!outputName!"
)

echo Conversion completed.
pause
