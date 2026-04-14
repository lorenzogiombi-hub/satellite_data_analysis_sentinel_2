"""
Extract MODIS MOD13A3 monthly NDVI climatology for Helsinki region with Google Earth Engine.
Use to build a statistically grounded reference curve for validating
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

import ee # Google Earth Engine Python API
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
ee.Initialize(project='ndvi-project-491409') # open GEE session with your project ID; connects Python script to GEE
print("GEE initialised successfully.")

# ── 2. Define region of interest ──────────────────────────────────────────────
# Helsinki city centre coordinates: 60.1699° N, 24.9384° E
# Buffer of 25 km covers the full metropolitan area includingnEspoo, Vantaa, and surrounding forests
# Note: GEE uses (lon, lat) order for coordinates
# Create a circular buffer around the city centre point
helsinki = ee.Geometry.Point([24.9384, 60.1699]).buffer(2000)  # 2 km radius 

# ── 3. Load MODIS MOD13A3 collection ──────────────────────────────────────────
# MOD13A3: monthly composites, 1 km resolution, global coverage
# NDVI band is stored as integer; multiply by 0.0001 to get true NDVI [-1, 1]
modis = (                                     # modis is an instance (object) of the class ee.ImageCollection, which represents a collection of images (in this case, monthly NDVI composites) that we can filter and process
    ee.ImageCollection("MODIS/061/MOD13A3")
    .filterDate("2010-01-01", "2024-01-01")   # 14 years
    .filterBounds(helsinki) # spatial filter to Helsinki region
    .select("NDVI") # select only the NDVI band
    .map(lambda img: img.multiply(0.0001)      # apply scale factor
                        .copyProperties(img, ["system:time_start"])) # preserve original timestamp for later use
)

print("MODIS collection loaded.")
# Result: collection of monthly NDVI images (scaled, time-aware)

# ── 4. Extract monthly mean NDVI over Helsinki ────────────────────────────────
def extract_mean(image):
    """Reduce image to mean NDVI over Helsinki region."""
    stats = image.reduceRegion(                       # Reduces the whole image to one number
        reducer=ee.Reducer.mean().combine(            # Compute mean NDVI and std dev together to save time
            ee.Reducer.stdDev(), sharedInputs=True
        ),
        geometry=helsinki,
        scale=1000,          # MODIS native resolution
        maxPixels=1e9
    )
    return ee.Feature(None, {                               # Creates a data record (like a row). No geometry, just properties
        "date"     : image.date().format("YYYY-MM-dd"),     # formatted date string for easier handling in Python
        "month"    : image.date().get("month"),
        "year"     : image.date().get("year"),
        "ndvi_mean": stats.get("NDVI_mean"),
        "ndvi_std" : stats.get("NDVI_stdDev"),
    })                                                      # returns {date, month, year, mean NDVI, std NDVI}                                      

features = modis.map(extract_mean)   # apply the extraction function to each image in the collection.
                                     # results in a collection of features (one per month) with mean and std NDVI values

# ── 5. Download results ───────────────────────────────────────────────────────
print("Extracting data from GEE (this may take 1-2 minutes)...")

data = features.getInfo()  # GEE runs on the cloud. .getInfo() pulls data to your local Python environment. 
                           # This is a synchronous call that waits until all data is ready and then returns it as a Python dictionary. For large datasets, this can take some time, but here we have only 14 years × 12 months = 168 records, so it should be manageable.

# print(data)
records = [] # list for storing the extracted data in a structured format (list of dictionaries) that we will convert to a DataFrame later
for f in data["features"]:     # each feature corresponds to one monthly observation with properties defined in the extract_mean function
                               # eg. f --> {'type': 'Feature', 'geometry': None, 'id': '2010_01_01', 'properties': {'date': '2010-01-01', 'month': 1, 'ndvi_mean': -0.044863956639566396, 'ndvi_std': 0.036761848359538295, 'year': 2010}} 
    p = f["properties"]        # access the properties of the feature, which contain our extracted data (date, month, year, mean NDVI, std NDVI)
    records.append({
        "date"     : p["date"],
        "month"    : int(p["month"]),
        "year"     : int(p["year"]),
        "ndvi_mean": float(p["ndvi_mean"]) if p["ndvi_mean"] is not None else np.nan,
        "ndvi_std" : float(p["ndvi_std"])  if p["ndvi_std"]  is not None else np.nan,
    })

df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)  # Convert the list of dictionaries into a pandas DataFrame (table) for easier analysis and visualization. Sort by date to ensure chronological order and reset index for clean numbering.
print(f"Downloaded {len(df)} monthly observations.")
print(df.head(12).to_string())



# ── 6. Compute climatology (long-term monthly mean) ───────────────────────────
climatology = (
    df.groupby("month")["ndvi_mean"]                # Group the data by month (1–12) and compute statistics on the mean NDVI for each month across all years
                                                    # after .groupby, "month" becomes the index
    .agg(["mean", "std", "count"])                  # Compute mean NDVI (climatology), standard deviation (interannual variability), and count of observations (number of years contributing to each month)
    .rename(columns={"mean": "ndvi_clim_mean",      # Rename columns for clarity: "mean" → "ndvi_clim_mean",
                     "std" : "ndvi_clim_std",
                     "count": "n_years"})
    .reset_index()                                  # Reset index to turn "month" back into a regular column instead of an index, making it easier to work with in subsequent steps
                                                    # Convert grouped result back to table format with columns: month, ndvi_clim_mean, ndvi_clim_std, n_years
)


print("\n===== MODIS NDVI Climatology — Helsinki (2010–2023) =====")
month_names = np.array(["Jan","Feb","Mar","Apr","May","Jun",
                        "Jul","Aug","Sep","Oct","Nov","Dec"])

climatology["month_name"] = month_names[climatology["month"].values - 1]

climatology["formatted"] = (
    climatology["month_name"].str.rjust(3) +
    "  mean=" + climatology["ndvi_clim_mean"].round(3).astype(str) +
    "  std="  + climatology["ndvi_clim_std"].round(3).astype(str) +
    "  (n="   + climatology["n_years"].astype(str) + " years)"
)

print("\n".join(climatology["formatted"]))

# ── 7. Save climatology to CSV ────────────────────────────────────────────────
climatology["month_name"] = [month_names[m-1] for m in climatology["month"]]
climatology.to_csv("modis_ndvi_reference.csv", index=False)
print("\nClimatology saved to modis_ndvi_reference.csv")

# Also save the full time series
df.to_csv("modis_ndvi_timeseries_full.csv", index=False)
print("Full time series saved to modis_ndvi_timeseries_full.csv")

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