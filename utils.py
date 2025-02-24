import math
import xml.etree.ElementTree as ET
import rasterio
from haversine import inverse_haversine, Unit

def degrees_to_centimeters(degree_value, latitude, for_longitude=True):
    """
    Converts a degree value to centimeters.
    
    Parameters:
      degree_value (float): The size in degrees.
      latitude (float): The latitude at which to convert (affects longitude conversion).
      for_longitude (bool): True if converting longitude; False for latitude.
    
    Returns:
      float: The approximate linear size in centimeters.
    """
    # Approximate conversion constants (in meters per degree)
    meters_per_degree_lat = 111320   # For latitude
    meters_per_degree_lon = 111320 * math.cos(math.radians(latitude))  # For longitude
    
    if for_longitude:
        meters = degree_value * meters_per_degree_lon
    else:
        meters = degree_value * meters_per_degree_lat

    centimeters = meters * 100  # 1 m = 100 cm
    return centimeters

def write_jgw(jgw_output, transform):
    tfw = open(jgw_output, 'wt')
    tfw.write(f"{transform.a}\n")
    tfw.write(f"{transform.d}\n")
    tfw.write(f"{transform.b}\n")
    tfw.write(f"{transform.e}\n")
    tfw.write(f"{transform.c}\n")
    tfw.write(f"{transform.f}\n")
    tfw.close()

def write_pam_aux_xml(aux_xml_output, srs_txt, transform):
    root = ET.Element("PAMDataset")
    srs = ET.SubElement(root, "SRS", attrib={"dataAxisToSRSAxisMapping": "2,1"}) # Input to GDAL, "2,1" tells that the first data axis (rows) shall be interpreted as second SRS axis (Y/Latitude); and the other way around
    srs.text = srs_txt
    geotransform = ET.SubElement(root, "GeoTransform")
    geotransform.text = f"{transform.c}, {transform.a}, {transform.b}, {transform.f}, {transform.d}, {transform.e}"
    metadata = ET.SubElement(root, "Metadata")
    mdi_area = ET.SubElement(metadata, "MDI", attrib={"key": "AREA_OR_POINT"})
    mdi_area.text = "Area"
    pamrasterband = ET.SubElement(root, "PAMRasterBand", attrib={"band": "1"})
    band_metadata = ET.SubElement(pamrasterband, "Metadata", attrib={"domain": "IMAGE_STRUCTURE"})
    mdi_compression = ET.SubElement(band_metadata, "MDI", attrib={"key": "COMPRESSION"})
    mdi_compression.text = "JPEG"

    ET.indent(root)

    tree = ET.ElementTree(root)
    tree.write(aux_xml_output, encoding="utf-8", xml_declaration=False)

def calculate_acoustic_bearing_radians(SensorHeading, BEARING_90_DEG_STARBOARD):
    # Calculate offset to sensor heading, this is acoustic bearing (radians), depends on channel port or starboard
    acoustic_bearing_radians = None
    if BEARING_90_DEG_STARBOARD:
        acoustic_bearing_radians = math.radians(SensorHeading + 90)
    else:
        acoustic_bearing_radians = math.radians(SensorHeading - 90)

    return acoustic_bearing_radians

def calculate_outermost_latlon(sensor_lat, sensor_lon, acoustic_bearing_radians, groundrange):
    # Calculate the latitude and longitude of the GroundRange outermost point, in the acoustic bearing
    p1 = (sensor_lat, sensor_lon)
    p2 = inverse_haversine(p1, groundrange, acoustic_bearing_radians, Unit.METERS)
    return p2

def create_gcps(sensor_pos_first_ping, sensor_pos_last_ping, outer_pos_first_ping, outer_pos_last_ping, is_starboard, height, width):
    # Create GroundControlPoint, four points used to translate the image pixels onto the map
    #
    # Assumptions:
    # Data captured from starboard:
    # Bottom left pixel is sensor position first ping
    # Top left pixel is sensor position last ping
    #
    # Data captured from port:
    # Bottom right pixel is sensor position first ping
    # Top right pixel is sensor position last ping

    gcps = None
    if is_starboard == True:
        gcps = [ # X is longitude, Y is latitude
            rasterio.control.GroundControlPoint(row=0,         col=0,         x=sensor_pos_last_ping[0],         y=sensor_pos_last_ping[1],    z=0), # top left pixel
            rasterio.control.GroundControlPoint(row=0,         col=width - 1, x=outer_pos_last_ping[0],   y=outer_pos_last_ping[1],    z=0), # top right pixel
            rasterio.control.GroundControlPoint(row=height - 1, col=width - 1, x=outer_pos_first_ping[0],   y=outer_pos_first_ping[1], z=0), # bottom right pixel
            rasterio.control.GroundControlPoint(row=height - 1, col=0,         x=sensor_pos_first_ping[0],         y=sensor_pos_first_ping[1], z=0) # bottom left pixel
        ]
    else: # Port
        gcps = [ # X is longitude, Y is latitude
            rasterio.control.GroundControlPoint(row=0,         col=0,         x=outer_pos_last_ping[0],         y=outer_pos_last_ping[1],    z=0), # top left pixel
            rasterio.control.GroundControlPoint(row=0,         col=width - 1, x=sensor_pos_last_ping[0],   y=sensor_pos_last_ping[1],    z=0), # top right pixel
            rasterio.control.GroundControlPoint(row=height - 1, col=width - 1, x=sensor_pos_first_ping[0],   y=sensor_pos_first_ping[1], z=0), # bottom right pixel
            rasterio.control.GroundControlPoint(row=height - 1, col=0,         x=outer_pos_first_ping[0],         y=outer_pos_first_ping[1], z=0) # bottom left pixel
        ]
    return gcps