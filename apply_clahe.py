import numpy as np
import rasterio
import cv2

# Based on Chatgpt repsonse

def apply_clahe_to_geotiff(input_tif, output_tif, clip_limit=3.0, tile_grid_size=(8, 8)):
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to a GeoTIFF file.
    
    Parameters:
    - input_tif (str): Path to the input GeoTIFF file.
    - output_tif (str): Path to save the enhanced GeoTIFF.
    - clip_limit (float): Threshold for contrast limiting in CLAHE.
    - tile_grid_size (tuple): Size of the grid for CLAHE (affects local contrast enhancement).
    """

    # Open the GeoTIFF file
    with rasterio.open(input_tif) as src:
        profile = src.profile  # Preserve metadata
        image = src.read()  # Read image bands
        dtype = src.dtypes[0]  # Get original data type

    # CLAHE only works on 8-bit images, so we normalize if needed
    def normalize_to_8bit(band):
        band_min, band_max = band.min(), band.max()
        return ((band - band_min) / (band_max - band_min) * 255).astype(np.uint8)

    # Create CLAHE object
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    # Apply CLAHE to each band
    processed_bands = []
    for band in image:
        band_8bit = normalize_to_8bit(band)  # Convert to 8-bit
        enhanced_band = clahe.apply(band_8bit)  # Apply CLAHE
        # Normalize back to original dtype range
        enhanced_band = (enhanced_band.astype(np.float32) / 255.0) * (band.max() - band.min()) + band.min()
        processed_bands.append(enhanced_band.astype(dtype))  # Convert back to original dtype

    # Stack processed bands back
    enhanced_image = np.stack(processed_bands)

    # Save the result while preserving georeferencing
    with rasterio.open(output_tif, "w", **profile) as dst:
        dst.write(enhanced_image)

    print(f"CLAHE applied and saved to {output_tif}")

# Example usage
apply_clahe_to_geotiff("output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff.tif", "output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff_clahe.tif")
