import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

from skimage import io
from skimage import util
from skimage import color
from skimage import exposure
from skimage import filters


def apply_tvg(image, alpha=0.5):
    """
    Apply Time Varying Gain (TVG) to a sonar image.
    Args:
        image (2D array): Input sonar image.
        alpha (float): Gain factor controlling the correction intensity.
    Returns:
        2D array: TVG-corrected sonar image.
    """
    rows, cols = image.shape
    gain = np.linspace(1, alpha, cols)  # TVG gain applied along the X-axis
    print(gain)
    tvg_image = image * gain  # Amplify each column by the gain
    return np.clip(tvg_image, 0, 250)  # Ensure values remain in [0, 250]


my_colormap = LinearSegmentedColormap.from_list('mycolormap', ["#000000", "#ffa500", "#FFFFFF"], N=255)

greyscale_image_path = 'tiffs\sasi-S-upper-20241207-135406-his05.tiff'
greyscale_image = Image.open(greyscale_image_path)
# Image must be uint8, not uint16


img_adapteq = exposure.equalize_adapthist(np.clip(gain_adjusted_ffc, 0.0, 1.0), nbins=255, kernel_size=(img_width/factor, img_height/factor), clip_limit=clip_limit)


# Convert the image to a numpy array
greyscale_array = np.array(greyscale_image)

print(np.min(greyscale_array), np.max(greyscale_array))

tvg_image = apply_tvg(greyscale_array, alpha=2.0)

# Apply a colormap
#colorized_array = my_colormap(greyscale_array)
#print(np.min(colorized_array), np.max(colorized_array))

#colored_image_uint8 = (colorized_array[:, :, :3] * 255).astype(np.uint8)  # Discard alpha channel if present
#print(np.min(colored_image_uint8), np.max(colored_image_uint8))

#rgb_image = Image.fromarray(colored_image_uint8)
#rgb_image.save('sasi-S-upper-20241207-135406-his05.tiff_copper.tiff')

plt.figure(figsize=(14, 7))

# Original Sonar Image
plt.subplot(1, 2, 1)
plt.title("Original Sonar Image")
plt.imshow(greyscale_image, cmap='viridis', aspect='auto')
plt.colorbar(label='Intensity')
plt.axis('off')

# TVG-Enhanced Image
plt.subplot(1, 2, 2)
plt.title("TVG-Enhanced Sonar Image")
plt.imshow(tvg_image, cmap='viridis', aspect='auto')
plt.colorbar(label='Intensity')
plt.axis('off')

plt.tight_layout()
plt.show()