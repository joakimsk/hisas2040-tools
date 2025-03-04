import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from pathlib import Path

from skimage import io
from skimage import util
from skimage import color
from skimage import exposure
from skimage import filters

# Based on response from ChatGPT

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

    # Right to left
    gain = np.linspace(1, alpha, cols)  # TVG gain applied along the X-axis
    
    # Left to left    
    #gain = np.linspace(alpha, 1, cols)  # Reverse TVG gain along the X-axis

    print(gain)
    tvg_image = image * gain  # Amplify each column by the gain
    return np.clip(tvg_image, 0, 250)  # Ensure values remain in [0, 250]

my_colormap = LinearSegmentedColormap.from_list('mycolormap', ["#000000", "#ffa500", "#FFFFFF"], N=255)

greyscale_image_path = Path("output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff.tif")
greyscale_image = Image.open(greyscale_image_path)

greyscale_array = np.array(greyscale_image)

print(np.min(greyscale_array), np.max(greyscale_array))

tvg_image = apply_tvg(greyscale_array, alpha=2.0)

plt.figure(figsize=(14, 7))

# Original Sonar Image
plt.subplot(1, 2, 1)
plt.title("Original Sonar Image")
plt.imshow(greyscale_image, cmap='gray', aspect='auto')
plt.colorbar(label='Intensity')
plt.axis('off')

# TVG-Enhanced Image
plt.subplot(1, 2, 2)
plt.title("TVG-Enhanced Sonar Image")
plt.imshow(tvg_image, cmap='gray', aspect='auto')
plt.colorbar(label='Intensity')
plt.axis('off')

plt.tight_layout()
plt.show()