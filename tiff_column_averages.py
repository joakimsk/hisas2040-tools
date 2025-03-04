import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps  
from pathlib import Path
import argparse
import logging
import matplotlib.pyplot as plt

# Open the TIFF image using Pillow
image = Image.open('output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff.tif')

# Convert the image to a NumPy array
image_array = np.array(image)

column_averages = np.mean(image_array, axis=0)  # Compute the average of each row along the columns axis
print(column_averages)

# Plot the 1D array
plt.plot(column_averages)
plt.title('1D NumPy Array Plot')
plt.xlabel('Index')
plt.ylabel('Value')
plt.grid(True)
plt.show()