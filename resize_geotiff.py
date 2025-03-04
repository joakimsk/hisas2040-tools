import rasterio
from rasterio.enums import Resampling

# Based on response from Chatgpt

def resize_geotiff(input_path, output_path, scale_factor=None, target_size=None):
    """
    Resizes a GeoTIFF file while maintaining its georeferencing information.
    
    Parameters:
    - input_path: str, path to the input GeoTIFF file.
    - output_path: str, path to save the resized GeoTIFF file.
    - scale_factor: float, factor to scale the image (e.g., 0.5 for half size, 2 for double size).
    - target_size: tuple, (new_width, new_height) in pixels (optional, used if scale_factor is not provided).
    """
    
    with rasterio.open(input_path) as src:
        transform = src.transform
        profile = src.profile

        # Determine new dimensions
        if scale_factor:
            new_width = int(src.width * scale_factor)
            new_height = int(src.height * scale_factor)
        elif target_size:
            new_width, new_height = target_size
        else:
            raise ValueError("Either scale_factor or target_size must be provided.")

        # Compute new transform (keeps the same georeferencing)
        new_transform = transform * transform.scale(
            (src.width / new_width),
            (src.height / new_height)
        )

        # Update profile
        profile.update({
            "width": new_width,
            "height": new_height,
            "transform": new_transform
        })

        # Resample and write output
        data = src.read(
            out_shape=(src.count, new_height, new_width),
            resampling=Resampling.bilinear  # Bilinear interpolation for smooth resizing
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)

    print(f"Resized GeoTIFF saved to {output_path}")

# Example usage
resize_geotiff("output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff.tif", "output\\sasi-P-upper-20240314-110520-wrk_l1_geotiff_reduced.tif", scale_factor=0.5)