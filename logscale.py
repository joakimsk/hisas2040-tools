import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

# Based on response from ChatGPT
# Load the image
image_path = Path("output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff.tif")
image = Image.open(image_path)
image_array = np.array(image, dtype=np.float32)

# Apply a logarithmic transformation to stretch the dark areas
c = 255 / np.log(1 + np.max(image_array))  # Calculate scale factor
log_stretched = c * np.log(1 + image_array)  # Apply the log transformation

# Convert to uint8 and clip to ensure values are in the correct range
log_stretched = np.clip(log_stretched, 0, 255).astype(np.uint8)

plt.figure(figsize=(14, 7))

# Original Sonar Image
plt.subplot(1, 2, 1)
plt.title("Original Sonar Image")
plt.imshow(image, cmap='gray', aspect='auto')
plt.colorbar(label='Intensity')
plt.axis('off')

# TVG-Enhanced Image
plt.subplot(1, 2, 2)
plt.title("Log-stretched image")
plt.imshow(log_stretched, cmap='gray', aspect='auto')
plt.colorbar(label='Intensity')
plt.axis('off')

plt.tight_layout()
plt.show()