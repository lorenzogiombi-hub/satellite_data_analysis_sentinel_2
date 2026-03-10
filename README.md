# Satellite Data Analysis Sentinel-2

This project computes the Normalized Difference Vegetation Index (NDVI) from Sentinel-2 satellite imagery. 
You can download images and data about your area of interest (AOI) in the open-source dataspace of Copernicus, 
which you can find following this [link](https://dataspace.copernicus.eu).

### Requirements
All you need is Python and the following libraries: numpy, matplotlib, and rasterio.
If you do not have installed them in your machine already, you can install them with:
```
pip3 install rasterio numpy matplotlib
```

## Workflow
Select your AOI and download Sentinel-2 dataset (raw images as GeoTIFF files).
Satellite sensors do not just take RGB pictures. Instead, they measure light intensity at many different wavelengths of the electromagnetic spectrum.
You need two bands, `B04` (RED ~ 665 nm) and `B08` (near infra-red, or NIR ~ 842 nm). 
Plants absorb red light during photosynthesis, so that healthy vegetation has a low red-light reflectance, while water has very low red-light reflectance, and dry soil medium red-light reflectance. 
On the opposite, plant leaves strongly reflect near-infrared light because of their internal structure, so that healthy vegetation has very high NIR reflectance, water has very low, and dry soil medium. 


Once you have the two bands, you can combine them to form the Normalized Difference Vegetation Index (NDVI) according to the formula
```math
NDVI = \frac{NIR-RED}{NIR+RED}
```
Typical NDVI values are:
| NDVI  | Meaning |
| ------------- | ------------- |
| < 0           | water         |
| 0 - 0.2       | bare soil     |
| 0.2 - 0.4     | sparse vegetation |
| > 0.4         | dense vegetation  |


## Example
Here I show an example of the NDVI computed around the metropolitan area of Helsinki on date 20 June 2025 (near midsummer). 
![NDVI around the metropolitan area of Helsinki on 20 June 2026.](https://github.com/lorenzogiombi-hub/satellite_data_analysis_sentinel_2/blob/main/ndvi_map.png)
![Dense vegetation areas around the metropolitan area of Helsinki on 20 June 2026.](https://github.com/lorenzogiombi-hub/satellite_data_analysis_sentinel_2/blob/main/ndvi_vegetation.png)