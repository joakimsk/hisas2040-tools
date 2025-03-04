import rasterio
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog

# Based on response from ChatGPT
# Input a sidescan TIFF or GEOTIFF, filename decided if columns are masked from left or right side.
# Choose either threshold (average column pixel value) or number of columns to remove (n columns)
# Output is a 4-band tiff with alpha mask. 4-band tiffs are read directly by Qgis.

# Open file dialog to select input TIFF
root = tk.Tk()
root.withdraw()  # Hide the main Tkinter window
input_file = filedialog.askopenfilename(title="Select Input TIFF", filetypes=[("TIFF files", "*.tif;*.tiff")])
if not input_file:
    raise ValueError("No file selected. Please select a valid TIFF file.")

# Create output directory
output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)

# Generate output filename
input_filename = os.path.basename(input_file)
name, ext = os.path.splitext(input_filename)

# User input to determine method
method = input("Enter 'threshold' to use a threshold value or 'columns' to remove a set number of columns: ").strip().lower()
if method == "threshold":
    threshold = float(input("Enter the threshold value for column mean (default=60): ").strip() or "60")
    remove_columns = None
    output_file = os.path.join(output_dir, f"{name}_alpha_thr_{int(threshold)}{ext}")
elif method == "columns":
    remove_columns = int(input("Enter the number of columns to remove (default=1000): ").strip() or "1000")
    threshold = None
    output_file = os.path.join(output_dir, f"{name}_alpha_col_{remove_columns}{ext}")
else:
    raise ValueError("Invalid input. Please enter 'threshold' or 'columns'.")

# Determine direction based on filename
filename = os.path.basename(input_file)
if "sasi-P-" in filename:
    direction = "right_to_left"
elif "sasi-S-" in filename:
    direction = "left_to_right"
else:
    raise ValueError("Filename must contain 'sasi-P-' or 'sasi-S-' to determine direction.")

# Open the single-band GeoTIFF
with rasterio.open(input_file) as src:
    band = src.read(1)  # Read first band
    profile = src.profile
    original_columns = band.shape[1]  # Store original number of columns

    # Compute column-wise averages
    col_means = np.mean(band, axis=0)
    alpha_band = np.full_like(band, 255, dtype=np.uint8)

    removed_columns = 0
    if remove_columns is not None:
        removed_columns = remove_columns
        if direction == "left_to_right":
            alpha_band[:, :remove_columns] = 0  # Remove explicit number of columns from left
        elif direction == "right_to_left":
            alpha_band[:, -remove_columns:] = 0  # Remove explicit number of columns from right
    else:
        if direction == "left_to_right":
            for col in range(band.shape[1]):
                if col_means[col] < threshold:
                    alpha_band[:, col] = 0  # Make transparent
                    removed_columns += 1
                else:
                    break
        elif direction == "right_to_left":
            for col in range(band.shape[1] - 1, -1, -1):
                if col_means[col] < threshold:
                    alpha_band[:, col] = 0  # Make transparent
                    removed_columns += 1
                else:
                    break

    final_columns = original_columns - removed_columns  # Compute final number of columns

    # Create three identical grayscale channels
    grayscale_channels = np.stack([band, band, band], axis=0).astype(np.uint8)

    # Update profile for 4-band output (RGB + Alpha)
    profile.update(count=4, dtype=rasterio.uint8)

    # Write output raster with RGB + Alpha channel
    with rasterio.open(output_file, "w", **profile) as dst:
        dst.write(grayscale_channels[0], 1)  # Red Channel (Grayscale)
        dst.write(grayscale_channels[1], 2)  # Green Channel (Grayscale)
        dst.write(grayscale_channels[2], 3)  # Blue Channel (Grayscale)
        dst.write(alpha_band, 4)  # Alpha channel

print(f"Alpha channel and RGB channels added and saved to {output_file}")
print(f"Original number of columns: {original_columns}")
print(f"Number of columns masked by new alpha channel: {removed_columns}")
print(f"Final number of columns after alpha channel is applied: {final_columns}")
