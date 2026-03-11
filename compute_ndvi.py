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
from rasterio.plot import show
import matplotlib.pyplot as plt
import matplotlib as mpl


# Cosmetic parameters and plotting settings
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

font_size = 16
mpl.rcParams.update({'font.size': font_size})
mpl.rcParams.update({'lines.linewidth': 1.5})
mpl.rcParams.update({'axes.linewidth': 1.})
mpl.rcParams.update({'axes.labelsize': font_size+1})
mpl.rcParams.update({'xtick.labelsize': font_size})
mpl.rcParams.update({'ytick.labelsize': font_size})
mpl.rcParams.update({'legend.fontsize': 16})


# Folder containing satellite bands
DATA_FOLDER = "Copernicus_images/Helsinki/2025/Helsinki_2025_07_17"  # Adjust this path to your data folder

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

fig, ax = plt.subplots(figsize = (8, 8))
image = show(
    ndvi,
    transform=profile["transform"],
    cmap="RdYlGn",
    ax=ax
)

im = image.get_images()[0]  # get the image object from the plot to use for colorbar
ax.set_aspect("equal") # set the aspect ratio to equal to ensure that the spatial dimensions are represented accurately (1 unit in x is equal to 1 unit in y)
fig.colorbar(im, ax=ax)
ax.set_title("NDVI Vegetation Index")
ax.axis("off")



# Plot NDVI thresholded to show dense vegetation areas (NDVI > 0.4)
vegetation = ndvi > 0.4

fig_v, ax_v = plt.subplots(nrows=1, ncols=1, figsize = (8, 8))
im_v =  show(
    vegetation.astype(np.uint8),
    transform=profile["transform"],
    cmap="Greens",
    ax=ax_v
)
# fig_v.colorbar(im_v, ax=ax_v)
ax_v.set_title(r"Dense Vegetation Areas (NDVI $>$ 0.4)")
ax_v.axis("off")
ax_v.set_aspect("equal") 


plt.show()




# # Save NDVI to new GeoTIFF
# profile.update(dtype=rasterio.float32, count=1) # update the profile to reflect the new data type and number of bands for NDVI output

# output_path = "ndvi_output.tiff"

# with rasterio.open(output_path, "w", **profile) as dst:
#     dst.write(ndvi.astype(rasterio.float32), 1)

# print("NDVI saved to:", output_path)


# Save NDVI with color map (RGB GeoTIFF) for QGIS visualization
profile.update(dtype=rasterio.float32, count=1) # update the profile to reflect the new data type and number of bands for NDVI output
output_cmap_path = "ndvi_colormap.tiff"

# Create a color map (256 colors)
import matplotlib.colors as colors

cmap = mpl.colormaps.get_cmap("RdYlGn")
norm = colors.Normalize(vmin=-1, vmax=1)

# Convert NDVI to 0–255 indices
ndvi_scaled = ((ndvi + 1) / 2 * 255).astype(np.uint8)     # nvdi+1 scales to 0–2, then /2 scales to 0–1, then *255 scales to 0–255, 
                                                          # and finally convert to uint8 for saving as an image format. 
                                                          # Values outside the range [-1, 1] will be clipped to 0 or 255.
# Build rasterio colormap dictionary
colormap = {
    i: tuple(int(c*255) for c in cmap(norm(i/255))[:3]) # for i in range(256)  
                                                        # creates a dictionary mapping each index (0–255) to an RGB color tuple based on the colormap.
                                                        # norm scales the index 1/255 in 0-1 to the range of NDVI values, i.e. -1 to +1, 
                                                        # cmap maps it to a color RGBA, and cmap[:3] extracts the RGB values. 
                                                        # Finally the RGB values are converted from [0, 1] to [0, 255] for saving as an image format.
    for i in range(256)
}

profile_cmap = profile.copy()
profile_cmap.update({
    "dtype": "uint8",
    "count": 1
})

with rasterio.open(output_cmap_path, "w", **profile_cmap) as dst:
    dst.write(ndvi_scaled, 1)
    dst.write_colormap(1, colormap)

print("Color‑mapped NDVI saved to:", output_cmap_path)



# NDVI Histogram + Statistics

valid = ndvi[~np.isnan(ndvi)] # filter out NaN values that may arise from division by zero or invalid pixels. 
                              # This ensures that the statistics and histogram are computed only on valid NDVI values, 
                              # Returns True if an element is NaN, and False if it is not NaN. 
                              # The ~ operator negates the boolean array, so we get True for valid values and False for NaN values.

ndvi_min = float(np.nanmin(valid))       # returns the minimum value in the array, ignoring NaN values.
ndvi_max = float(np.nanmax(valid))       # returns the maximum value in the array, ignoring NaN values.
ndvi_mean = float(np.nanmean(valid))     # returns the mean (average) value of the array, ignoring NaN values.
ndvi_median = float(np.nanmedian(valid)) # returns the median value of the array, ignoring NaN values.

veg_fraction = float(np.sum(valid > 0.4) / valid.size) # calculates the fraction of valid NDVI pixels that are greater than 0.4.

print("\n===== NDVI Statistics =====")
print(f"Min NDVI:     {ndvi_min:.3f}")
print(f"Max NDVI:     {ndvi_max:.3f}")
print(f"Mean NDVI:    {ndvi_mean:.3f}")
print(f"Median NDVI:  {ndvi_median:.3f}")
print(f"Vegetation >0.4: {veg_fraction*100:.2f}% of pixels")

# Plot histogram
fig_h, ax_h = plt.subplots(figsize=(8, 5))
ax_h.hist(valid, bins=50, color="green", alpha=0.7)
ax_h.set_title("NDVI Histogram")
ax_h.set_xlabel("NDVI")
ax_h.set_ylabel("Pixel Count")
ax_h.grid(True, linestyle="--", alpha=0.4)

plt.show()
fig.savefig("ndvi_map.png")
fig_v.savefig("ndvi_vegetation.png")
