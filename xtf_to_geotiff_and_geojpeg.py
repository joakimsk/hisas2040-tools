"""
Example of how to convert a single-channel sonar sidescan XTF file to a georeferenced tiff and jpeg with sidecar-files.
Toggle resize_half_width if your image width needs to be resized to half width.
Toggle concatenate_channel weighted argument to fit your data requirements.
"""

import numpy as np
from PIL import Image
import rasterio
from pathlib import Path

import pyxtf

import utils # Local utility-file

filename = Path("sasi-S-upper-20240314-110644-wrk_l1.xtf")
file_stem = filename.stem
xtf_input = Path(f"xtfs/{filename}") # Input XTF file

bitdepth = 8 # Use 8 or 16 bits to store the pixel values
resize_half_width = True # Resize image, half width
weighted = True # Toggle concatenate_channel weighted argument to fit your data input requirements

# Output filepaths
output_path = Path(f"output")
output_path.mkdir(parents=True, exist_ok=True)

tif_output = Path(f"output/{file_stem}.tif")
jpeg_output = Path(f"output/{file_stem}.jpeg")
jgw_output = Path(f"output/{file_stem}.jgw")
aux_xml_output = Path(f"output/{file_stem}.jpeg.aux.xml")
geotiff_output = Path(f"output/{file_stem}_geotiff.tif")



def calculate_outermost_latlon_from_ping(file_header: pyxtf.XTFFileHeader, ping_header: pyxtf.XTFPingChanHeader, is_starboard=None):
    sensor_lat, sensor_lon = ping_header.SensorYcoordinate, ping_header.SensorXcoordinate
    acoustic_bearing_radians = utils.calculate_acoustic_bearing_radians(ping_header.SensorHeading, is_starboard)
    
    ping_chan_header = ping_header.ping_chan_headers[0]
    GroundRange = ping_chan_header.GroundRange

    outermost_lat, outermost_lon = utils.calculate_outermost_latlon(sensor_lat, sensor_lon, acoustic_bearing_radians, GroundRange)
    return sensor_lat, sensor_lon, outermost_lat, outermost_lon

def make_sidescan_sonar_image(fh, p, bitdepth=8, resize_half_width=False, weighted=False):
    # make_sonar_image()
    # Will read any bitdepth that pyxtf accepts and scale values to 8 or 16 bits

    upper_limit_16bit = 2 ** 16 - 1 # 0-65535
    upper_limit_8bit = 2 ** 8 - 1 # 0-255

    np_chan = pyxtf.concatenate_channel(p[pyxtf.XTFHeaderType.sonar], file_header=fh, channel=0, weighted=weighted)
    np_chan.clip(0, upper_limit_16bit, out=np_chan) # Clipping values outside valid range
    np_chan = np.log10(np_chan + 1, dtype=np.float32)

    vmin = np_chan.min()
    vmax = np_chan.max()

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

(fh, p) = pyxtf.xtf_read(xtf_input)

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
    ChannelName = str(fh.ChanInfo[0].ChannelName)
    if 'starboard' in ChannelName:
        is_starboard = True
        print("Data detected as starboard")
    elif 'port' in ChannelName:
        is_starboard = False
        print("Data detected as port")
    else:
        print("Unable to detect port or starboard in channel name.")
        exit(-1)

    sonar_image = make_sidescan_sonar_image(fh, p, bitdepth=bitdepth, resize_half_width=resize_half_width, weighted=weighted)

    # Write sonar image data to files, no georeferencing at this stage
    sonar_image.save(tif_output)
    print("TIF without georeference saved:", tif_output)
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
    
    # Write worldfiles, sidecar files for the jpeg to position and transform the jpeg in the map
    target_crs = rasterio.CRS.from_epsg(4326)
    srs_wkt = target_crs.to_wkt()
    utils.write_pam_aux_xml(aux_xml_output, srs_wkt, transform)
    utils.write_jgw(jgw_output, transform)

    profile.update({
        'crs': target_crs, # EPSG:4326 is assumed
        'transform': transform
    })

    with rasterio.open(geotiff_output, "w", **profile) as dst:
        dst.write(data, 1)
    print("Geotiff output saved:", geotiff_output)