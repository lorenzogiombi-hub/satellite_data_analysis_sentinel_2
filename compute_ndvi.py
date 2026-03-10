# This script computes the Normalized Difference Vegetation Index (NDVI) from Sentinel-2 satellite imagery.
# It automatically detects the red (B04) and near-infrared (B08) bands, computes NDVI, visualizes it, and saves the result as a new GeoTIFF file.
# Dataset contains Sentinel-2 bands in the "Browser_images" folder. Make sure to have the required libraries installed (rasterio, numpy, matplotlib) and adjust the DATA_FOLDER path if necessary.
# Band 4 = Red light (~665 nm). Plants absorb red light during photosynthesis.
# Band 8 = Near-Infrared (NIR) light (~842 nm). Plant leaves strongly reflect near-infrared light because of their internal structure.
# 
# 
# compute NDVI = (NIR - Red) / (NIR + Red)
#  NDVI values range from -1 to +1, where higher values indicate healthier vegetation. Values close to zero or negative indicate non-vegetated surfaces (e.g., water, urban areas, bare soil).
# 
# Author: Lorenzo Giombi  
# Date: 2026-03-10


import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import matplotlib as mpl

# =====================================
# Cosmetic parameters and plotting settings
# =====================================

plt.rc('text', usetex=True)
plt.rc('font', family='serif')

font_size = 16
mpl.rcParams.update({'font.size': font_size})
mpl.rcParams.update({'lines.linewidth': 1.5})
mpl.rcParams.update({'axes.linewidth': 1.})
mpl.rcParams.update({'axes.labelsize': font_size+1})
mpl.rcParams.update({'xtick.labelsize': font_size})
mpl.rcParams.update({'ytick.labelsize': font_size})
# but make legend smaller
mpl.rcParams.update({'legend.fontsize': 16})


# Folder containing satellite bands
DATA_FOLDER = "Copernicus_images"

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
    bounds = red_src.bounds          # get the spatial extent of the image (left, bottom, right, top) in the coordinate reference system defined by 'crs'

with rasterio.open(nir_path) as nir_src:
    nir = nir_src.read(1).astype(float)  # read the first band and convert to float for calculations

# Avoid division errors
np.seterr(divide='ignore', invalid='ignore')

# Compute NDVI
ndvi = (nir - red) / (nir + red)

# Plot NDVI
extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (8, 8))
im = ax.imshow(ndvi, cmap="RdYlGn", extent=extent)
fig.colorbar(im, ax=ax)
ax.set_title("NDVI Vegetation Index")
ax.axis("off")

# from rasterio.plot import show

# fig, ax = plt.subplots(figsize=(8,8))
# show(ndvi, transform=profile['transform'], cmap="RdYlGn", ax=ax)
# ax.set_title("NDVI Vegetation Index")
# ax.axis("off")

# Plot NDVI thresholded to show dense vegetation areas (NDVI > 0.4)
vegetation = ndvi > 0.4

fig_v, ax_v = plt.subplots(nrows=1, ncols=1, figsize = (8, 8))
im_v =  ax_v.imshow(vegetation, cmap="Greens")
# fig_v.colorbar(im_v, ax=ax_v)
ax_v.set_title(r"Dense Vegetation Areas (NDVI $>$ 0.4)")
ax_v.axis("off")

plt.show()

# Save NDVI to new GeoTIFF
profile.update(dtype=rasterio.float32, count=1) # update the profile to reflect the new data type and number of bands for NDVI output

output_path = "ndvi_output.tiff"

with rasterio.open(output_path, "w", **profile) as dst:
    dst.write(ndvi.astype(rasterio.float32), 1)

print("NDVI saved to:", output_path)

fig.savefig("ndvi_map.png")
fig_v.savefig("ndvi_vegetation.png")
