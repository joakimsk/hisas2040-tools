import os
import numpy as np
import tifffile as tiff
import cv2  # OpenCV for histogram equalization
from pathlib import Path
import matplotlib.pyplot as plt

# Based on response from ChatGPT
# Define input and output directories
input_folder = Path(f"output")
output_folder = Path(f"output")

# Set to None in order to use folder (use comments)
#image_path = Path("output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff.tif")
image_path = None

# Create output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

def compute_global_mean_intensity(file_list):
    """
    Compute the average column-wise mean intensity across all images.
    Ensures all images have the same width before averaging.
    """
    all_means = []
    max_width = 0

    # Find the maximum width across all images
    for file in file_list:
        image = tiff.imread(file)
        max_width = max(max_width, image.shape[1])  # Assuming (height, width)

    for file in file_list:
        image = tiff.imread(file)

        # If width is smaller, pad with zeros
        if image.shape[1] < max_width:
            pad_width = max_width - image.shape[1]
            image = np.pad(image, ((0, 0), (0, pad_width)), mode='constant', constant_values=0)

        # Compute column mean
        column_mean = np.mean(image, axis=0)
        all_means.append(column_mean)

    # Compute the global mean
    global_mean = np.mean(all_means, axis=0)

    # Avoid division by zero
    global_mean[global_mean == 0] = 1

    return global_mean, max_width

def empirical_gain_normalization(image, mean_intensity, target_width):
    """
    Apply Empirical Gain Normalization (EGN) using the given mean intensity.
    """
    # If image width is smaller than target, pad it to match
    if image.shape[1] < target_width:
        pad_width = target_width - image.shape[1]
        image = np.pad(image, ((0, 0), (0, pad_width)), mode='constant', constant_values=0)

    # Normalize each pixel by the mean intensity of its column
    normalized_image = image / mean_intensity

    # Scale the normalized image to maintain brightness consistency
    normalized_image *= np.mean(mean_intensity)

    # Clip values to the valid range (0 to 255 for 8-bit images)
    normalized_image = np.clip(normalized_image, 0, 255).astype(np.uint8)

    return normalized_image

def apply_histogram_equalization(image):
    """
    Apply histogram equalization to enhance contrast.
    Works for both grayscale and multi-channel images.
    """
    if len(image.shape) == 2:  # Grayscale image
        return cv2.equalizeHist(image)
    
    elif len(image.shape) == 3:  # Multi-channel image (e.g., RGB)
        channels = cv2.split(image)
        eq_channels = [cv2.equalizeHist(ch) for ch in channels]
        return cv2.merge(eq_channels)

    return image  # Return unchanged if format is unknown

def compare_plot_images(img1, img2):
    plt.figure(figsize=(14, 7))

    # Original Sonar Image
    plt.subplot(1, 2, 1)
    plt.title("Original Sonar Image")
    plt.imshow(img1, cmap='gray', aspect='auto')
    plt.colorbar(label='Intensity')
    plt.axis('off')

    # TVG-Enhanced Image
    plt.subplot(1, 2, 2)
    plt.title("Modified image")
    plt.imshow(img2, cmap='gray', aspect='auto')
    plt.colorbar(label='Intensity')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

# List all TIFF files in the input directory
if image_path == None:
    file_list = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith((".tif", ".tiff"))]
else:
    file_list = [image_path]

# Ask user whether to use global mean intensity or per-image normalization
use_global_mean = input("Use global mean intensity across all images? (yes/no): ").strip().lower() == "yes"

# Ask whether to apply histogram equalization
apply_hist_eq = input("Apply histogram equalization after normalization? (yes/no): ").strip().lower() == "yes"

# Ask whether to apply histogram equalization
show_plot_images = input("Show plot of input and output image? (yes/no): ").strip().lower() == "yes"

# Compute global mean intensity if needed
global_mean_intensity, target_width = compute_global_mean_intensity(file_list) if use_global_mean else (None, None)

# Process each TIFF file
for file_path in file_list:
    # Load the image
    image = tiff.imread(file_path)

    # Determine mean intensity to use
    if use_global_mean:
        mean_intensity = global_mean_intensity  # Use precomputed global mean
    else:
        mean_intensity = np.mean(image, axis=0)
        mean_intensity[mean_intensity == 0] = 1  # Avoid division by zero
        target_width = image.shape[1]  # Use image's width for processing

    # Apply empirical gain normalization
    normalized_image = empirical_gain_normalization(image, mean_intensity, target_width)

    # Apply histogram equalization if selected
    if apply_hist_eq:
        normalized_image = apply_histogram_equalization(normalized_image)

    if show_plot_images:
        compare_plot_images(image, normalized_image)

    output_filename = Path(file_path).stem + "_egn" + ".tif"

    output_path = output_folder / output_filename
    tiff.imwrite(output_path, normalized_image)

    print(f"Processed and saved: {output_path}")

print("Batch processing completed.")
