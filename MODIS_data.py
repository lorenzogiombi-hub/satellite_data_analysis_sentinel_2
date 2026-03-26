"""
Extract MODIS MOD13A3 monthly NDVI climatology for Helsinki region.
Used to build a statistically grounded reference curve for validating
Sentinel-2 NDVI seasonal analysis.

Dataset : MODIS/006/MOD13A3
          Monthly NDVI at 1 km resolution
          Long-term record: 2000-present
          Scale factor: 0.0001 (applied automatically below)

Region  : Helsinki metropolitan area (~25 km radius)
Period  : 2010–2023 (14 years, avoids older sensor degradation)

Output  : modis_ndvi_reference.csv  — monthly mean ± std NDVI
          modis_ndvi_reference.png  — plot of the reference curve

Author  : Lorenzo Giombi
"""

import ee
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# ── Cosmetic parameters ────────────────────────────────────────────────────────
plt.rc('text', usetex=True)
plt.rc('font', family='serif')
font_size = 16
mpl.rcParams.update({'font.size': font_size, 'lines.linewidth': 1.5,
                     'axes.linewidth': 1., 'axes.labelsize': font_size + 1,
                     'xtick.labelsize': font_size, 'ytick.labelsize': font_size,
                     'legend.fontsize': 14})

# ── 1. Initialise GEE ─────────────────────────────────────────────────────────
ee.Initialize()
print("GEE initialised successfully.")

# ── 2. Define region of interest ──────────────────────────────────────────────
# Helsinki city centre coordinates: 60.1699° N, 24.9384° E
# Buffer of 25 km covers the full metropolitan area including
# Espoo, Vantaa, and surrounding forests
helsinki = ee.Geometry.Point([24.9384, 60.1699]).buffer(25000)  # 25 km radius

# ── 3. Load MODIS MOD13A3 collection ──────────────────────────────────────────
# MOD13A3: monthly composites, 1 km resolution, global coverage
# NDVI band is stored as integer; multiply by 0.0001 to get true NDVI [-1, 1]
modis = (
    ee.ImageCollection("MODIS/006/MOD13A3")
    .filterDate("2010-01-01", "2024-01-01")   # 14 years
    .filterBounds(helsinki)
    .select("NDVI")
    .map(lambda img: img.multiply(0.0001)      # apply scale factor
                        .copyProperties(img, ["system:time_start"]))
)

print("MODIS collection loaded.")

# ── 4. Extract monthly mean NDVI over Helsinki ────────────────────────────────
def extract_mean(image):
    """Reduce image to mean NDVI over Helsinki region."""
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            ee.Reducer.stdDev(), sharedInputs=True
        ),
        geometry=helsinki,
        scale=1000,          # MODIS native resolution
        maxPixels=1e9
    )
    return ee.Feature(None, {
        "date"     : image.date().format("YYYY-MM-dd"),
        "month"    : image.date().get("month"),
        "year"     : image.date().get("year"),
        "ndvi_mean": stats.get("NDVI_mean"),
        "ndvi_std" : stats.get("NDVI_stdDev"),
    })

features = modis.map(extract_mean)

# ── 5. Download results ───────────────────────────────────────────────────────
print("Extracting data from GEE (this may take 1-2 minutes)...")

data = features.getInfo()  # pulls data to local Python

records = []
for f in data["features"]:
    p = f["properties"]
    records.append({
        "date"     : p["date"],
        "month"    : int(p["month"]),
        "year"     : int(p["year"]),
        "ndvi_mean": float(p["ndvi_mean"]) if p["ndvi_mean"] is not None else np.nan,
        "ndvi_std" : float(p["ndvi_std"])  if p["ndvi_std"]  is not None else np.nan,
    })

df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
print(f"Downloaded {len(df)} monthly observations.")
print(df.head(12).to_string())

# ── 6. Compute climatology (long-term monthly mean) ───────────────────────────
climatology = (
    df.groupby("month")["ndvi_mean"]
    .agg(["mean", "std", "count"])
    .rename(columns={"mean": "ndvi_clim_mean",
                     "std" : "ndvi_clim_std",
                     "count": "n_years"})
    .reset_index()
)

print("\n===== MODIS NDVI Climatology — Helsinki (2010–2023) =====")
month_names = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]
for _, row in climatology.iterrows():
    m = int(row["month"])
    print(f"  {month_names[m-1]:>3}  "
          f"mean={row['ndvi_clim_mean']:.3f}  "
          f"std={row['ndvi_clim_std']:.3f}  "
          f"(n={int(row['n_years'])} years)")

# ── 7. Save climatology to CSV ────────────────────────────────────────────────
climatology["month_name"] = [month_names[m-1] for m in climatology["month"]]
climatology.to_csv("modis_ndvi_reference.csv", index=False)
print("\nClimatology saved → modis_ndvi_reference.csv")

# Also save the full time series
df.to_csv("modis_ndvi_timeseries_full.csv", index=False)
print("Full time series saved → modis_ndvi_timeseries_full.csv")

# ── 8. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(climatology["month"], climatology["ndvi_clim_mean"],
        'o-', color='forestgreen', linewidth=2, markersize=7,
        label="MODIS climatology 2010–2023")
ax.fill_between(
    climatology["month"],
    climatology["ndvi_clim_mean"] - climatology["ndvi_clim_std"],
    climatology["ndvi_clim_mean"] + climatology["ndvi_clim_std"],
    alpha=0.2, color='green', label=r"$\pm 1\sigma$ interannual variability"
)

ax.set_xticks(range(1, 13))
ax.set_xticklabels(month_names)
ax.set_xlabel("Month")
ax.set_ylabel("Mean NDVI")
ax.set_title("MODIS MOD13A3 NDVI Climatology — Helsinki region (2010–2023)")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.4)
ax.set_ylim(-0.1, 1.0)
fig.tight_layout()
fig.savefig("modis_ndvi_reference.png", dpi=300)
print("Plot saved: modis_ndvi_reference.png")

plt.show()