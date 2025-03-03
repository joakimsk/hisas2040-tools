import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# Load the image
image = Image.open('tiffs\\sasi-S-upper-20241207-135406-his05.tiff')
image_array = np.array(image, dtype=np.float32)

# Apply a logarithmic transformation to stretch the dark areas
c = 255 / np.log(1 + np.max(image_array))  # Calculate scale factor
log_stretched = c * np.log(1 + image_array)  # Apply the log transformation

# Convert to uint8 and clip to ensure values are in the correct range
log_stretched = np.clip(log_stretched, 0, 255).astype(np.uint8)

# Show the result
plt.imshow(log_stretched, cmap='gray')
plt.title('Logarithmic Stretched Image')
plt.show()