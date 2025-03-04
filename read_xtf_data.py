import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import argparse
import logging

import pyxtf

file_path = Path("input_xtfs\\sasi-P-upper-20241212-095257-his_1_01.xtf")

# Read file header and packets
(fh, p) = pyxtf.xtf_read(file_path)
packets_in_file = str([key.name + ':{}'.format(len(v)) for key, v in p.items()])
print(f'Packets found in file: {packets_in_file}')

print("------------------------------------")
print("File header for ", file_path.stem)
print("------------------------------------")
print(fh)

n_channels = fh.channel_count(verbose=True)
if n_channels != 1:
    print("Warning: pyxtf conversion only supports single channel XTF. You have", n_channels)
    
for i in range(0, n_channels):
    print("------------------------------------")
    print("Actual channel info channel #",i)
    print("------------------------------------")
    actual_chan_info = fh.ChanInfo[i]
    print(actual_chan_info)

chan_type = fh.ChanInfo[0].TypeOfChannel
if chan_type == pyxtf.XTFChannelType.stbd:
    print("XTF Channel is Starboard")
    starboard = True
elif chan_type == pyxtf.XTFChannelType.port:
    print("XTF Channel is Port")
    port = True
else:
    exit("Unknown XTF channel type")

# Get sonar if present
if pyxtf.XTFHeaderType.sonar in p:
    upper_limit = 2 ** 16

    logging.info(f"Concatenating pings in channel")
    np_chan = pyxtf.concatenate_channel(p[pyxtf.XTFHeaderType.sonar], file_header=fh, channel=0, weighted=True)

    np.set_printoptions(threshold=np.inf, linewidth=200, precision=3, formatter={'float': '{:,.0f}'.format}, suppress=True)  # Ensure entire array is displayed

    print("Columns", np_chan.shape[1])
    # Start cutting columns where average value is below column_threshold, used to remove black sides
    average_along_columns = np.mean(np_chan, axis=0)
    # Clip to range (max cannot be used due to outliers)
    # More robust methods are possible (through histograms / statistical outlier removal)
    np_chan.clip(0, upper_limit - 1, out=np_chan)
    
    # The sonar data is logarithmic (dB), add small value to avoid log10(0)
    np_chan = np.log10(np_chan + 1, dtype=np.float32)

    # Need to find minimum and maximum value for scaling
    vmin = np_chan.min()
    vmax = np_chan.max()

    print("Values before scaling; min, vmax", vmin, vmax)
    
    # Scaling values to fit datatype uint16
    np_chan = ((np_chan - vmin) / (vmax - vmin)) * 65535
    np_chan = np.clip(np_chan, 0, 65535)

    # Resample as necessary after histogram equalization, it is already in uin16

    vmin = np_chan.min()
    vmax = np_chan.max()

    print("Min and max values", vmin, vmax)