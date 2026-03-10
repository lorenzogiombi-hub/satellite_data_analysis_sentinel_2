# This script computes the Normalized Difference Vegetation Index (NDVI) from Sentinel-2 satellite imagery.
# It automatically detects the red (B04) and near-infrared (B08) bands, computes NDVI, visualizes it, and saves the result as a new GeoTIFF file.
# Dataset contains Sentinel-2 bands in the "Browser_images" folder. Make sure to have the required libraries installed (rasterio, numpy, matplotlib) and adjust the DATA_FOLDER path if necessary.
# Band 4 = Red light (~665 nm). Plants absorb red light during photosynthesis.
# Band 8 = Near-Infrared (NIR) light (~842 nm). Plant leaves strongly reflect near-infrared light because of their internal structure.
# Examples: healthy vegetaion: Red → low
#                              NIR → high
#                       water: Red → low
#                              NIR → low
#                   Bare soil: Red → medium
#                              NIR → medium
# 
# compute NDVI = (NIR - Red) / (NIR + Red)
#  NDVI values range from -1 to +1, where higher values indicate healthier vegetation. Values close to zero or negative indicate non-vegetated surfaces (e.g., water, urban areas, bare soil).
# Interpretation of NDVI values:
#  NDVI < 0: water, snow, clouds, or non-vegetated surfaces
#  NDVI < 0.2: sparse vegetation or non-vegetated areas
#  NDVI 0.2 - 0.5: moderate vegetation
#  NDVI > 0.5: dense, healthy vegetation

# Author: Lorenzo Giombi

import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt

# Folder containing satellite bands
DATA_FOLDER = "Browser_images"

# Automatically find Sentinel-2 bands
red_path = None
nir_path = None

for file in os.listdir(DATA_FOLDER):                   # get the list of files in the data folder
    if "B04" in file and file.endswith(".tiff"):       # Band 4 = Red light (~665 nm). Plants absorb red light during photosynthesis.
        red_path = os.path.join(DATA_FOLDER, file)
    if "B08" in file and file.endswith(".tiff"):       # Band 8 = Near-Infrared (NIR) light (~842 nm). Plant leaves strongly reflect near-infrared light because of their internal structure.
        nir_path = os.path.join(DATA_FOLDER, file)

if red_path is None:
    raise Exception("Could not find B04 (red) band.")
if nir_path is None:
    raise Exception("Could not find B08 (NIR) band.")

print("Red band:", red_path)
print("NIR band:", nir_path)
# print(red_path.count("/"), nir_path.count("/"))

# Load satellite bands
with rasterio.open(red_path) as red_src:
    red = red_src.read(1).astype(float)  # read the first band and convert to float for calculations
    profile = red_src.profile            # copies the geospatial metadata {
                                                                        #  'driver': 'GTiff',         File format (GeoTIFF)
                                                                        #  'dtype': 'uint16',         Data type of pixels
                                                                        #  'width': 10980,            image size
                                                                        #  'height': 10980,           image size
                                                                        #  'count': 1,                number of bands
                                                                        #  'crs': 'EPSG:32635',       coordinate reference system
                                                                        #  'transform': Affine(...),  mapping between pixels and Earth coordinates
                                                                        #  'nodata': 0                value used for missing pixels
                                                                        # }

with rasterio.open(nir_path) as nir_src:
    nir = nir_src.read(1).astype(float)  # read the first band and convert to float for calculations

# Avoid division errors
np.seterr(divide='ignore', invalid='ignore')

# Compute NDVI
ndvi = (nir - red) / (nir + red)

# Plot NDVI
plt.figure(figsize=(8, 8))
plt.imshow(ndvi, cmap="RdYlGn")
plt.colorbar(label="NDVI")
plt.title("NDVI Vegetation Index")
plt.axis("off")
plt.show()

# Save NDVI to new GeoTIFF
profile.update(dtype=rasterio.float32, count=1) # update the profile to reflect the new data type and number of bands for NDVI output

output_path = "ndvi_output.tiff"

with rasterio.open(output_path, "w", **profile) as dst:
    dst.write(ndvi.astype(rasterio.float32), 1)

print("NDVI saved to:", output_path)