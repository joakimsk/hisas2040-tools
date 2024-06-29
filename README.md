### HiSAS 2040 XTF Tools
Under development, useful tools to look at and convert Kongsberg HiSAS 2040 XTF imagery.

###### Dependencies
The project depends on numpy, pillow, matplotlib and pyxtf

pyxtf release 1.4.1 does not work, use this fork for the time being: [https://github.com/joakimsk/pyxtf]

###### Short summary
Synthetic aperture processing is done by proprietary Kongsberg software, output is XTF.
Data encoded with unknown bit size, seems to be up to 16 bit.
The full synthetic ping seems to be stored in ~13000 values to each side. It reaches ~100 meters, giving ~130 pixels per meter before resampling.
We half the width by resampling, to get proper aspect ratio on the image.

xtf2tiff.py reads a folder containing single-channel (starboard or port only, NOT combined!) sidescan XTF.
All pings in a file are concatenated, and "empty" columns are deleted.
Optional processing (histogram equalization and halfing in across-track direction resolution) is done.
Data is stored as a greyscale tiff with either 8 or 16 bit resolution.

###### Usage
Put .xtf into "xtfs"

Run with defaults or add options for histogram equalization
xtf2tiff.py -heq

###### Sample data
This project contains sample data gathered by Institute of Marine Research using a Kongsberg Munin+ 1500m AUV with a Kongsberg HiSAS 2040 synthetic aperture sonar.
The research cruise and AUV dive was arranged by the MAREANO project [https://mareano.no/en/about_mareano] in international waters, spring 2024.

###### Attribution
This project is using some code copied from pyxtf [https://github.com/oysstu/pyxtf] which is under MIT License.
This project has also used snippets from ChatGPT, copyright violation not intended, but please take contact if you see something violating your copyright.