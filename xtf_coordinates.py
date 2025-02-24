import pyxtf
import numpy as np
import geopy
import pandas as pd

def calculate_ground_range(slant_range, altitude):
    """
    Calculate the ground range from slant range and altitude.
    """
    return np.sqrt(slant_range**2 - altitude**2)

def calculate_local_coordinates(ground_range, beam_angle):
    """
    Calculate local coordinates from ground range and beam angle.
    """
    x = ground_range * np.cos(np.deg2rad(beam_angle))
    y = ground_range * np.sin(np.deg2rad(beam_angle))
    return x, y

def transform_to_global_coordinates(vessel_position, heading, local_x, local_y):
    """
    Transform local coordinates to global coordinates using vessel position and heading.
    """
    heading_rad = np.deg2rad(heading)
    
    # Rotate local coordinates based on heading
    x_global = local_x * np.cos(heading_rad) - local_y * np.sin(heading_rad)
    y_global = local_x * np.sin(heading_rad) + local_y * np.cos(heading_rad)
    
    # Translate to global coordinates
    origin = (vessel_position['latitude'], vessel_position['longitude'])
    new_position = geopy.distance.distance(meters=y_global).destination(origin, heading=0)  # North
    new_position = geodesic(meters=x_global).destination(new_position, heading=90)  # East
    
    return new_position.latitude, new_position.longitude

def process_xtf_file(file_path):
    """
    Process an XTF file to calculate the coordinates of individual pixels.
    """
    # Load the XTF file
    xtf_file = pyxtf.xtf_file(file_path)
    
    global_coords = []

    for packet in xtf_file:
        if packet.header.packet_type == pyxtf.packet.SIDESCAN:
            ping_data = packet.body
            
            # Extract relevant data from the ping
            timestamp = packet.header.datetime
            latitude = packet.header.navigation.latitude
            longitude = packet.header.navigation.longitude
            heading = packet.header.heading
            altitude = packet.header.altitude
            slant_ranges = ping_data.slant_range
            time_delays = ping_data.time_delay
            beam_angles = np.linspace(-30, 30, len(time_delays))  # Adjust based on actual data
            
            vessel_position = {
                'latitude': latitude,
                'longitude': longitude
            }
            
            for slant_range, time_delay, beam_angle in zip(slant_ranges, time_delays, beam_angles):
                ground_range = calculate_ground_range(slant_range, altitude)
                local_x, local_y = calculate_local_coordinates(ground_range, beam_angle)
                lat, lon = transform_to_global_coordinates(vessel_position, heading, local_x, local_y)
                global_coords.append((timestamp, lat, lon))
    
    # Convert to DataFrame for easier handling
    global_coords_df = pd.DataFrame(global_coords, columns=['timestamp', 'latitude', 'longitude'])
    return global_coords_df

# Example usage:
file_path = 'tiffs\sasi-P-upper-20240314-110550-wrk_l1.tiff'
global_coords_df = process_xtf_file(file_path)
print(global_coords_df)
