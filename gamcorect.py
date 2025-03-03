import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# Load the image
image = Image.open('tiffs\\sasi-S-upper-20241207-135406-his05.tiff')
image_array = np.array(image, dtype=np.float32)  # Convert to float for precision

# Apply gamma correction to stretch the dark areas
gamma = 0.4  # You can experiment with different gamma values
gamma_corrected = 255 * (image_array / 255) ** gamma  # Scale and apply gamma

# Convert the image back to uint8 after correction
gamma_corrected = np.clip(gamma_corrected, 0, 255).astype(np.uint8)

# Show the result
plt.imshow(gamma_corrected, cmap='gray')
plt.title('Gamma Corrected Image')
plt.show()