import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps  
from pathlib import Path
import argparse
import logging
import matplotlib.pyplot as plt

from pyxtf import xtf_read, concatenate_channel, XTFHeaderType, XTFChannelType


# Based on response from ChatGPT
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

print(f"{min_value}, {max_value}")

# Plot the 1D array
plt.plot(column_averages)
plt.title('1D NumPy Array Plot')
plt.xlabel('Index')
plt.ylabel('Value')
plt.grid(True)
plt.show()