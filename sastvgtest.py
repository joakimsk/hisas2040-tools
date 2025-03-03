import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps  
from pathlib import Path
import argparse
import logging
import matplotlib.pyplot as plt
from pyxtf import xtf_read, concatenate_channel, XTFHeaderType, XTFChannelType
import numpy as np
import matplotlib.pyplot as plt
import pyxtf
import numpy as np
from scipy.signal import resample_poly


def plot_image_and_graph(image_data, residual_tvg, beam_pattern):
    """
    Plots an 8-bit sonar image next to a graph showing residual TVG and beam pattern corrections.
    """
    # Normalize image data to 8-bit range (0-255)
    normalized_image = (255 * (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data))).astype(np.uint8)

    # Create the figure
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={'width_ratios': [2, 1]})

    # Plot the 8-bit image
    axes[0].imshow(normalized_image, cmap='gray', aspect='auto')
    axes[0].set_title('Corrected Sonar Image (8-bit)')
    axes[0].set_xlabel('Across-Track Distance')
    axes[0].set_ylabel('Along-Track Distance')
    axes[0].colorbar = plt.colorbar(axes[0].images[0], ax=axes[0], fraction=0.046, pad=0.04, label='Amplitude')

    # Plot the graph with TVG and Beam Pattern
    axes[1].plot(residual_tvg, label='Residual TVG', color='blue')
    axes[1].plot(beam_pattern, label='Beam Pattern', color='green')
    axes[1].set_title('Correction Factors')
    axes[1].set_xlabel('Sample Index')
    axes[1].set_ylabel('Amplitude')
    axes[1].legend()
    axes[1].grid(True)

def read_xtf(file_path):
    """Read XTF file and extract sonar data."""
    xtf_file = pyxtf.xtf_file(file_path)
    sonar_records = [record for record in xtf_file if isinstance(record, pyxtf.xtf_ping)]
    return sonar_records

def resample_scanline(scanline, reference_altitude, current_altitude):
    """Resample a single scanline to align with the reference altitude."""
    scaling_factor = reference_altitude / current_altitude
    resampled = resample_poly(scanline, up=int(scaling_factor * 1000), down=1000)
    return resampled

def calculate_residual_tvg(sonar_data, ref_profile):
    """Estimate residual TVG corrections."""
    residuals = []
    for scanline in sonar_data:
        correction = scanline / ref_profile  # Normalize by reference profile
        residuals.append(np.mean(correction, axis=0))
    return np.array(residuals)

def calculate_beam_pattern(data, residual_tvg_corrections):
    """Calculate the beam pattern based on corrected data."""
    corrected_data = data / residual_tvg_corrections
    beam_pattern = np.mean(corrected_data, axis=0)
    return beam_pattern

def apply_corrections(data, tvg_corrections, beam_pattern):
    """Apply TVG and beam pattern corrections to sonar data."""
    corrected_data = data / (tvg_corrections * beam_pattern)
    return corrected_data

def correct_sonar_data(file_path):
    """Main function to read, process, and correct sonar data."""
    sonar_data = read_xtf(file_path)

    # Assuming the first scanline is at reference altitude
    reference_altitude = sonar_data[0].altitude
    corrected_data = []

    # Process each scanline
    for record in sonar_data:
        current_altitude = record.altitude
        scanline = record.data

        # Resample for alignment
        resampled_scanline = resample_scanline(scanline, reference_altitude, current_altitude)

        # Store corrected scanline
        corrected_data.append(resampled_scanline)

    # Estimate residual TVG
    ref_profile = corrected_data[0]  # Example: Using the first scanline as a reference
    residual_tvg = calculate_residual_tvg(corrected_data, ref_profile)

    # Estimate beam pattern
    beam_pattern = calculate_beam_pattern(corrected_data, residual_tvg)

    # Apply corrections
    final_corrected_data = apply_corrections(corrected_data, residual_tvg, beam_pattern)

    return final_corrected_data


(fh, p) = xtf_read('xtfs\\sasi-S-upper-20241207-135406-his05.xtf')
n_channels = fh.channel_count(verbose=True)
actual_chan_info = [fh.ChanInfo[i] for i in range(0, n_channels)]

if n_channels != 1:
    exit("Converting only implemented for single channel XTF, you have", n_channels)

packets_in_file = str([key.name + ':{}'.format(len(v)) for key, v in p.items()])

chan_type = fh.ChanInfo[0].TypeOfChannel
if chan_type == XTFChannelType.stbd:
    print("XTF Channel is Starboard")
    starboard = True
elif chan_type == XTFChannelType.port:
    print("XTF Channel is Port, only test for starboard")
    port = True
    exit(-1)
else:
    exit("Unknown XTF channel type")

# Get sonar if present
if XTFHeaderType.sonar in p:
    upper_limit = 2 ** 16

    logging.info(f"Concatenating pings in channel")
    np_chan = concatenate_channel(p[XTFHeaderType.sonar], file_header=fh, channel=0, weighted=True)

min_value = np.min(np_chan)  # Get the minimum pixel value
max_value = np.max(np_chan)  # Get the maximum pixel value

# Stretch values
image_array = ((np_chan - min_value) / (max_value - min_value)) * 65535

column_averages = np.mean(image_array, axis=0)  # Compute the average of each row along the columns axis
print(column_averages)

min_value = np.min(image_array)  # Get the minimum pixel value
max_value = np.max(image_array)  # Get the maximum pixel value


img = Image.fromarray(image_array.astype(np.uint8))

plot_image_and_graph(img)

print(f"{min_value}, {max_value}")

# Plot the 1D array
plt.plot(image_array)
plt.title('1D NumPy Array Plot')
plt.xlabel('Index')
plt.ylabel('Value')
plt.grid(True)
plt.show()