import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps  
from pathlib import Path
import argparse
import logging
import matplotlib.pyplot as plt

# Open the TIFF image using Pillow
image = Image.open('tiffs\\sasi-S-upper-20241207-135406-his05.tiff')

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