# HiSAS 2040 XTF Tools
Under development, useful tools to look at and convert Kongsberg HiSAS 2040 XTF imagery.

## Dependencies
The project depends on numpy, pillow, matplotlib, pyxtf, python-opencv and more stuff.

## Short summary
Synthetic aperture processing is done by proprietary Kongsberg software, output is XTF.
Data encoded with seems to be up to 16 bit.
The full synthetic ping seems to be stored in ~13000 values to each side. It reaches ~120 meters, giving ~108 pixels per meter before resampling.
We half the width by resampling, to get proper aspect ratio on the image. ~6500 pixels width.

## Usage xtf_to_geotiff_and_geojpeg.py
See code for options and parameters. Takes all XTF in xtfs-folder and makes output geotiffs.

In short, this is the algorithm used to convert XTF to Geotiff
1. Read XTF-file, ensure it is single-channeled, either port or starboard, not two channels in one, as pyxtf cannot handle it directly.
2. Populate a numpy-matrix with all data (16 bit per sample), remove outliers and clip/scale values to 8 bit if wanted
3. Convert numpy-matrix to image, resample if needed (reduce width for aspect ratio)
4. Possibly remove black columns near NADIR, not yet affecting georeferencing though.
5. Get GroundRange from XTF-file, and sensor heading. GroundRange can also be calculated from SlantRange and Altitude.
6. Calculate using sensor lat/lon, and acoustic bearing (90 degrees on sensor heading), inverse haversine to find lat/lon of outer sample for each ping. We get two outer coordinates, assuming all data is within the four coordinates. First and last ping, inner (sensor lat/lon) and outer (last measurement) sample.
7. Using rasterio, calculate Affine transform and write geotiff using these four coordinate pairs.
8. Can also make .jpeg with sidecar-files, these are space-saving, but lossy.

## Processing of tiffs
Several scripts try to work on the tiffs to improve visual quality:
time_variable_gain.py
apply_clahe.py
apply_empirical_gain_normalization.py
apply_sidescan_transperancy.py
apply_clahe.py
apply_gamme_correct.py
colorize_image.py

Other scripts are for modifying and analyzing:
apply_sidescan_transparency.py - used to create alpha mask either by column number or by average threshold value
resize_geotiff.py - reduce size of geotiff, preserve coordinates
concat_tiff.py

Other scripts should be made; for example "beam pattern compensation" and other normalization methods that work based on data stored in the XTF-files.

Much of these scripts may or may not work as intended; and deserve some more work.

## Usage xtf2tiff.py
xtf2tiff.py reads a folder containing single-channel (starboard or port only, NOT combined!) sidescan XTF.
All pings in a file are concatenated, and "empty" columns are deleted.
Optional processing (histogram equalization and halfing in across-track direction resolution) is done.
Data is stored as a greyscale tiff with either 8 or 16 bit resolution.

Put .xtf into "xtfs", output comes in folder "output".

Run with defaults or add options for histogram equalization
xtf2tiff.py -heq

Sonar image without histogram equalization:
![Alt text](media/sample.jpg?raw=true "Sample without histogram equalization")

Sonar image with histogram equalization:
![Alt text](media/sample_heq.jpg?raw=true "Sample with histogram equalization")

## Usage colorize_image.py
Change code to new .tiff. Run, output is copper_image.tiff.
The colormap is defined with three colors, for the range 0-255. Thus, the input image must be uint8.

![Alt text](media/sample_heq_copper.jpg?raw=true "Sample with histogram equalization + copper color")

## Usage concat_tiff.py
Script will try to combine all tiffs vertically. This requires the same width, which is not commonly the case now after deleting empty columns.

## Usage click_crop.py
Target cropping, opens an image in full resolution. Click on an object to make an roi, saved as roi_x.png. Press q on keyboard to quit.

## Usage click_crop_tk.py
Target cropping, opens an image in full resolution. Click on an object to make an roi, saved as roi_x.png, and a csv-file with ROIs.

## Sample data
This project contains sample data gathered by Institute of Marine Research using a Kongsberg Munin+ 1500m AUV with a Kongsberg HiSAS 2040 synthetic aperture sonar.

The research cruise and AUV dive was arranged by the [MAREANO project](https://mareano.no/en/about_mareano) in international waters, spring 2024.

## Attribution
This project is using some lines of code copied from [pyxtf](https://github.com/oysstu/pyxtf) which is under MIT License.

This project has also used snippets from ChatGPT, copyright violation not intended, but please take contact if you see something violating your copyright.