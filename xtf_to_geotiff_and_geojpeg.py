"""
Example of how to convert a single-channel sonar sidescan XTF file to a georeferenced tiff and jpeg with sidecar-files.
Toggle resize_half_width if your image width needs to be resized to half width.
Toggle concatenate_channel weighted argument to fit your data requirements.
"""

import numpy as np
from PIL import Image
import rasterio
from pathlib import Path
import os

import pyxtf

import utils # Local utility-file

# Choose output
keep_normal_tif = False # Keep normal tif in addition to geotiff
output_normal_jpeg = False # Also output normal jpeg without georeferences
output_georef_jpeg_sidecar = False # Also output georeference sidecar files for jpeg

# Select folders
input_folder = Path(f"xtfs")
output_folder = Path(f"output")

# Set parameters
bitdepth = 8 # Use 8 or 16 bits to store the pixel values
resize_half_width = True # Resize image, half width
weighted = True # Toggle concatenate_channel weighted argument to fit your data input requirements
nadir_gap = 0.0 # meters to remove from data from where the sonar is
column_threshold = 0.0 # remove all columns below this value average. Set to 0.0 to preserve all columns, or 0.1 to remove the blackest.
# NB: Removed columns are not corrected for in georeferencing - not yet at least

def calculate_outermost_latlon_from_ping(file_header: pyxtf.XTFFileHeader, ping_header: pyxtf.XTFPingChanHeader, is_starboard=None):
    sensor_lat, sensor_lon = ping_header.SensorYcoordinate, ping_header.SensorXcoordinate
    acoustic_bearing_radians = utils.calculate_acoustic_bearing_radians(ping_header.SensorHeading, is_starboard)
    
    ping_chan_header = ping_header.ping_chan_headers[0]
    GroundRange = ping_chan_header.GroundRange

    outermost_lat, outermost_lon = utils.calculate_outermost_latlon(sensor_lat, sensor_lon, acoustic_bearing_radians, GroundRange)
    return sensor_lat, sensor_lon, outermost_lat, outermost_lon

def make_sidescan_sonar_image(fh, p, is_starboard, bitdepth=8, resize_half_width=False, weighted=False):
    # make_sonar_image()
    # Will read any bitdepth that pyxtf accepts and scale values to 8 or 16 bits

    # Get GroundRange
    sonar_ch = p[pyxtf.XTFHeaderType.sonar]
    first_ping_chan_header = sonar_ch[0].ping_chan_headers[0]
    GroundRange = first_ping_chan_header.GroundRange

    upper_limit_16bit = 2 ** 16 - 1 # 0-65535
    upper_limit_8bit = 2 ** 8 - 1 # 0-255

    np_chan = pyxtf.concatenate_channel(p[pyxtf.XTFHeaderType.sonar], file_header=fh, channel=0, weighted=weighted)

    full_column_width = np_chan.shape[1]
    print("Columns before cleanup:", full_column_width)
    print("GroundRange meters", GroundRange)
    
    # Start cutting columns where average value is below column_threshold, used to remove black sides
    average_along_columns = np.mean(np_chan, axis=0)

    if is_starboard: # NADIR is left in image
        print("Starboard, left to right")
        left_to_right_indices = []
        for i in range(len(average_along_columns)):
            if average_along_columns[i] < column_threshold:
                left_to_right_indices.append(i)
            else:
                break  # Stop as soon as a column above threshold is found

        empty_columns = np.array(left_to_right_indices)
        meters_of_empty_data = (len(empty_columns)/full_column_width)*GroundRange
        print("Columns with no data", len(empty_columns), ", meters of no data", meters_of_empty_data)
    else: # NADIR is right in image
        print("Port, right to left")
        right_to_left_indices = []
        for i in range(len(average_along_columns) - 1, -1, -1):
            if average_along_columns[i] < column_threshold:
                right_to_left_indices.append(i)
            else:
                break  # Stop as soon as a column above threshold is found

        empty_columns = np.array(right_to_left_indices[::-1])  # Reverse to maintain order
        meters_of_empty_data = (len(empty_columns)/full_column_width)*GroundRange
        print("Columns with no data", len(empty_columns), ", meters of no data", meters_of_empty_data)
        

    empty_columns = np.where(average_along_columns < column_threshold)[0]
    print(f"Removing {len(empty_columns)} columns with value below column_threshold={column_threshold}")
    np_chan = np.delete(np_chan, empty_columns, axis=1)
    
    print("Columns after cleanup:", np_chan.shape[1])

    np_chan.clip(0, upper_limit_16bit, out=np_chan) # Clipping values outside valid range
    np_chan = np.log10(np_chan + 1, dtype=np.float32)

    vmin = np_chan.min()
    vmax = np_chan.max()
    print(f"vmin={vmin}, vmax={vmax}")

    if bitdepth==8:
        np_chan = ((np_chan - vmin) / (vmax - vmin)) * upper_limit_8bit # Scaling values to fit datatype uint8
        np_chan = np.clip(np_chan, 0, upper_limit_8bit) # Clipping values outside valid range
        img = Image.fromarray(np_chan.astype(np.uint8))
    elif bitdepth==16: 
        np_chan = ((np_chan - vmin) / (vmax - vmin)) * upper_limit_16bit # Scaling values to fit datatype uint16
        np_chan = np.clip(np_chan, 0, upper_limit_16bit) # Clipping values outside valid range
        img = Image.fromarray(np_chan.astype(np.uint16))
    else:
        print("make_sonar_image() invalid bitdepth, only 8 or 16 accepted. Is", bitdepth)
        exit(-1)

    if resize_half_width: # Some sonar data may be wrong ratio, this will reduce width by half
        img = img.resize((int(img.size[0]/2), img.size[1]))

    return img

def xtf_to_geotiff_and_geojpeg(xtf_file, output_folder):

    file_stem = xtf_file.stem
    #xtf_input = Path(f"xtfs/{filename}") # Input XTF file
    
    # Output filepaths
    output_folder.mkdir(parents=True, exist_ok=True)
    tif_output = output_folder / Path(f"{file_stem}.tif")
    jpeg_output = output_folder / Path(f"{file_stem}.jpeg")
    jgw_output = output_folder / Path(f"{file_stem}.jgw")
    aux_xml_output = output_folder / Path(f"{file_stem}.jpeg.aux.xml")
    geotiff_output = output_folder / Path(f"{file_stem}_geotiff.tif")

    (fh, p) = pyxtf.xtf_read(xtf_file)

    if pyxtf.XTFHeaderType.sonar in p:
        n_channels = fh.channel_count(verbose=True)
        
        if n_channels > 1:
            print("Not implemented for more than one channel (either port or starboard, not both)")
            exit(-1)

        NavUnits = fh.NavUnits # If 0, then SensorYcoordinate and SensorXcoordinate is in meters. If 3, then in Lat/Long
        if NavUnits != 3:
            print("fh.NavUnits != 3, coordinates are in meters. Not implemented yet.")
            exit(-1)

        is_starboard = None
        actual_channel_info = fh.ChanInfo[0]
        ChannelName = str(actual_channel_info.ChannelName)

        print(actual_channel_info)
        #exit()

        if 'starboard' in ChannelName:
            is_starboard = True
            print("Data detected as starboard")
        elif 'port' in ChannelName:
            is_starboard = False
            print("Data detected as port")
        else:
            print("Unable to detect port or starboard in channel name.")
            exit(-1)

        sonar_image = make_sidescan_sonar_image(fh, p, is_starboard=is_starboard, bitdepth=bitdepth, resize_half_width=resize_half_width, weighted=weighted, )

        sonar_image.save(tif_output)
        print("TIF without georeference saved:", tif_output)
        # Write sonar image data to files, no georeferencing at this stage


        if output_normal_jpeg:
            sonar_image.save(jpeg_output)
            print("JPEG without georeference saved:", jpeg_output)

        sonar_ch = p[pyxtf.XTFHeaderType.sonar]

        first_ping = sonar_ch[0]
        fp_s_lat, fp_s_lon, fp_o_lat, fp_o_lon = calculate_outermost_latlon_from_ping(fh, first_ping, is_starboard)

        last_ping = sonar_ch[-1]
        lp_s_lat, lp_s_lon, lp_o_lat, lp_o_lon = calculate_outermost_latlon_from_ping(fh, last_ping, is_starboard)

        points = [(fp_s_lon, fp_s_lat), (fp_o_lon, fp_o_lat), (lp_s_lon, lp_s_lat), (lp_o_lon, lp_o_lat)]
        print("Outermost points:", points)

        try:
            src = rasterio.open(tif_output) # NotGeoreferencedWarning can be ignored
        except Exception as e:
            print("Unable to load source tif for conversion to geotiff")
            exit(-1)
        
        data = src.read(1)
        height, width = src.height, src.width

        # Copy the source metadata profile for use in the output
        profile = src.profile.copy()
        src.close()

        sensor_pos_first_ping = (fp_s_lon, fp_s_lat)
        sensor_pos_last_ping = (lp_s_lon, lp_s_lat)
        outer_pos_first_ping = (fp_o_lon, fp_o_lat)
        outer_pos_last_ping = (lp_o_lon, lp_o_lat)

        # Calculate and compute an Affine transform
        gcps = utils.create_gcps(sensor_pos_first_ping, sensor_pos_last_ping, outer_pos_first_ping, outer_pos_last_ping, is_starboard, height, width)
        transform = rasterio.transform.from_gcps(gcps)

        target_crs = rasterio.CRS.from_epsg(4326)
        srs_wkt = target_crs.to_wkt()

        if output_georef_jpeg_sidecar:
            print("Writing sidecar files for jpeg")
            # Write worldfiles, sidecar files for the jpeg to position and transform the jpeg in the map

            utils.write_pam_aux_xml(aux_xml_output, srs_wkt, transform)
            utils.write_jgw(jgw_output, transform)

        profile.update({
            'crs': target_crs, # EPSG:4326 is assumed
            'transform': transform
        })

        with rasterio.open(geotiff_output, "w", **profile) as dst:
            dst.write(data, 1)
        print("Geotiff output saved:", geotiff_output)
        
        if not keep_normal_tif:
            print("Removing normal .tif")
            os.remove(tif_output) 

def process_file(file, output_folder):
    print(f"Processing: {file}")
    xtf_to_geotiff_and_geojpeg(file, output_folder)


def process_folder(input_folder, output_folder):
    print(f"Processing folder: {input_folder}")
    for file in input_folder.iterdir():
        if file.is_file():
            process_file(file, output_folder)

def main():
    print("Trying to process folder")
    process_folder(input_folder, output_folder)


if __name__ == "__main__":
    main()