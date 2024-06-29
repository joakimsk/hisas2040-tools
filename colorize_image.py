import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

my_colormap = LinearSegmentedColormap.from_list('mycolormap', ["#000000", "#ffa500", "#FFFFFF"], N=255)

greyscale_image_path = 'tiffs\sasi-P-upper-20240314-110550-wrk_l1.tiff'
greyscale_image = Image.open(greyscale_image_path)
# Image must be uint8, not uint16

# Convert the image to a numpy array
greyscale_array = np.array(greyscale_image)

print(np.min(greyscale_array), np.max(greyscale_array))

# Apply a colormap
colorized_array = my_colormap(greyscale_array)
print(np.min(colorized_array), np.max(colorized_array))

colored_image_uint8 = (colorized_array[:, :, :3] * 255).astype(np.uint8)  # Discard alpha channel if present
print(np.min(colored_image_uint8), np.max(colored_image_uint8))

rgb_image = Image.fromarray(colored_image_uint8)
rgb_image.save('copper_image.tiff')