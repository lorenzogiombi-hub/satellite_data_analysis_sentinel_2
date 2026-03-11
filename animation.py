import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib.pyplot as plt
import matplotlib.animation as animation

DATA_FOLDER = "Copernicus_images/Helsinki/2025"

def compute_ndvi(red_path, nir_path):
    with rasterio.open(red_path) as r:
        red = r.read(1).astype(np.float32)
        profile = r.profile
        bounds = r.bounds

    with rasterio.open(nir_path) as n:
        nir = n.read(1).astype(np.float32)

    # Reproject to north-up grid
    transform, width, height = calculate_default_transform(
        profile["crs"], profile["crs"],
        profile["width"], profile["height"],
        *bounds,
        resolution=10
    )

    red_r = np.empty((height, width), dtype=np.float32)
    nir_r = np.empty((height, width), dtype=np.float32)

    reproject(red, red_r,
              src_transform=profile["transform"],
              src_crs=profile["crs"],
              dst_transform=transform,
              dst_crs=profile["crs"],
              resampling=Resampling.bilinear)

    reproject(nir, nir_r,
              src_transform=profile["transform"],
              src_crs=profile["crs"],
              dst_transform=transform,
              dst_crs=profile["crs"],
              resampling=Resampling.bilinear)

    ndvi = (nir_r - red_r) / (nir_r + red_r)
    return ndvi, transform

# Collect NDVI frames
dates = sorted(f for f in os.listdir(DATA_FOLDER) if not f.startswith('.'))
ndvi_frames = []
transforms = []

# Avoid division errors
np.seterr(divide='ignore', invalid='ignore')


for d in dates:
    folder = os.path.join(DATA_FOLDER, d)
    for file in os.listdir(folder):
        if "B04" in file and file.endswith(".tiff"):       # Band 4 = Red light (~665 nm). Plants absorb red light during photosynthesis.
            red_path = os.path.join(folder, file)
        if "B08" in file and file.endswith(".tiff"):       # Band 8 = Near-Infrared (NIR) light (~842 nm). Plant leaves strongly reflect near-infrared light because of their internal structure.
            nir_path = os.path.join(folder, file)
    # red = os.path.join(folder, "B04.tiff")
    # nir = os.path.join(folder, "B08.tiff")

    if red_path is None or nir_path is None:
        print(f"Skipping {d}: missing B04 or B08")
        continue

    ndvi, transform = compute_ndvi(red_path, nir_path)
    ndvi_frames.append(ndvi)
    transforms.append(transform)

# Create animation
fig, ax = plt.subplots(figsize=(8, 8))
# Create a colorbar axis
cbar_ax = fig.add_axes([0.88, 0.15, 0.03, 0.7])

def update(frame):
    ax.clear()
    cbar_ax.clear()
    im = ax.imshow(ndvi_frames[frame], cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_title(f"NDVI — {dates[frame]}")
    ax.axis("off")

    # Add colorbar
    fig.colorbar(im, cax=cbar_ax)
    return [im]

ani = animation.FuncAnimation(fig, update, frames=len(ndvi_frames), interval=800)

ani.save("ndvi_timeseries.gif", writer="pillow")
print("Saved NDVI time-series animation as ndvi_timeseries.gif")


ndvi_stack = np.stack(ndvi_frames, axis=0)

# Compute baseline (mean NDVI)
baseline = np.nanmean(ndvi_stack, axis=0)

# Compute anomaly for each date
anomalies = [ndvi - baseline for ndvi in ndvi_frames]

# Plot one anomaly map
from rasterio.plot import show
idx = 6  # choose which date to visualize
fig_a, ax_a = plt.subplots(figsize=(8, 8))
cbar_axa = fig_a.add_axes([0.88, 0.15, 0.03, 0.7])

# show(anomalies[idx], transform=transforms[idx], cmap="bwr", ax=ax_a)
# ax_a.set_title(f"NDVI Anomaly — {dates[idx]}")
# ax_a.axis("off")
# plt.show()


def update_anomalies(frame):
    ax_a.clear()
    cbar_axa.clear()
    ima = ax_a.imshow(anomalies[frame], cmap="bwr", vmin=-1, vmax=1)
    ax_a.set_title(f"NDVI Anomaly — {dates[frame]}")
    ax_a.axis("off")

    # Add colorbar
    fig_a.colorbar(ima, cax=cbar_axa)
    return [ima]

print(len(ndvi_frames), len(transforms), len(anomalies))
ani_anomaly = animation.FuncAnimation(fig_a, update_anomalies, frames=len(ndvi_frames), interval=800)
ani_anomaly.save("ndvi_anomalies.gif", writer="pillow")
print("Saved NDVI anomaly animation as ndvi_anomalies.gif")

plt.show()