"""
functions to create a new band for snow landcover classification using the  
'NDSI_Snow_Cover' and 'Snow_Albedo_Daily_Tile_Class' bands from MODIS.
Pixels are re-classified as 0 (cloud), 50 (land), and 100 (snow). 

It implements the pre-processing steps of Gafurov & Bardossy.
Uses Terra (MOD10A1) and Aqua (MYD10A1) images from collection 6 of MODIS
The scale used for Terra (MOD10A1) and Aqua (MYD10A1) is 463.31271652791656, both
 projected on 'SR-ORG:6974'

This is based on the js code from - users/observatorionieves/modules/CR/Binary.js

These module use the following bands:
- NDSI_Snow_Cover: Snow cover percentage. Values between 0 - 100
- Snow_Albedo_Daily_Tile_Class: Snow albedo percentage - Values between 1 - 100 (## VERIFY ##)
- NDSI_Snow_Cover_Algorithm_Flags_QA: Types of land covers. Used for snow, cloud, and original QA bands

The following conventions are used:
- All server side variables are prefixed with 'ee_'
- Image, ImageCollection and FeatureCollections are sufficed with '_img', '_ic' and '_fc' when possible

"""

#! Couldn't find where NDSI_Snow_Cover_Algorithm_Flags_QA is used in the code.

import ee
from ee.image import Image
from ee.imagecollection import ImageCollection
from ee.featurecollection import FeatureCollection


# Initialize the Earth Engine module.
# ee.Initialize()

# Example usage:
# collection = ee.ImageCollection('MODIS/006/MOD10A1')
# AOI = ee.FeatureCollection('path/to/AOI')
# Threshold_NDSI = ee.Number(40)
# result = binary(collection, AOI, Threshold_NDSI)


def img_snow_landcover_reclass(
    ee_img: Image, threshold_ndsi: int | ee.ee_number.Number = 40
) -> ee.image.Image:
    """
    Adds a band 'LandCover_class' to the image for Snow landcover classification.

    Uses MODIS bands 'NDSI_Snow_Cover' and 'Snow_Albedo_Daily_Tile_Class' to define a three level
    classification of snow landcover 'LandCover_class': 0 (cloud), 50 (land), and 100 (snow).

    Args:
        img (ee.image.Image): MODIS image.
        threshold_ndsi (int | ee.ee_number.Number): NDSI threshold, must be between 0 and 100.

    returns:
        ee.image.Image: Original image with one new band 'LandCover_class'.
    """
    if not isinstance(ee_img, ee.image.Image):
        raise TypeError("Input must be an ee.Image")

    if not isinstance(threshold_ndsi, int | ee.ee_number.Number):
        raise TypeError("Threshold_NDSI must be an integer or ee.Number")

    # if threshold_ndsi is not an ee.Number, convert it to one.
    if not isinstance(threshold_ndsi, ee.ee_number.Number):
        ee_threshold_ndsi = ee.ee_number.Number(threshold_ndsi)
    else:
        ee_threshold_ndsi = threshold_ndsi

    # Recode 'Snow_Albedo_Daily_Tile_Class' band to 'nodata'.
    # nodata = 0 (cloud/no decision/ missing etc), 50 (land/ocean/inland water), None (any other value)
    ee_nodata_img = ee_img.remap(
        from_=[101, 111, 125, 137, 139, 150, 151, 250, 251, 252, 253, 254],
        to=[0, 0, 50, 50, 50, 0, 0, 0, 50, 0, 50, 0],
        defaultValue=None,
        bandName="Snow_Albedo_Daily_Tile_Class",
    ).rename("nodata")

    # Recode 'NDSI_Snow_Cover' band to 'SnowReclass'.
    # Pixels above the threshold are set to 100 (Snow), below to 50 (no snow).
    ee_snow_img = (
        ee_img.select("NDSI_Snow_Cover")
        .gte(ee_threshold_ndsi)
        .multiply(100)
        .rename("snow")
    )
    ee_snow_reclassify_img = ee_snow_img.remap(
        from_=[0, 100], to=[50, 100], defaultValue=None, bandName="snow"
    ).rename("SnowReclass")

    # Join bands and reduce to one band 'LandCover_class'
    ee_snow_temp_img = ee.image.Image([ee_nodata_img, ee_snow_reclassify_img])
    ee_landcover_img = ee_snow_temp_img.reduce(ee.reducer.Reducer.max()).rename(
        "LandCover_class"
    )

    # Join "LandCover_class' band to original image and set threshold as a property
    return ee.image.Image(
        ee_img.addBands(ee_landcover_img).set("Threshold_NDSI", ee_threshold_ndsi)
    )


def ic_snow_landcover_reclass(
    ee_collection: ImageCollection,
    ee_aoi: FeatureCollection,
    threshold_ndsi: int | ee.ee_number.Number = 40,
):
    """
    Clips images in an ImageCollection to an area of Interest and adds a band for
    Snow landcover classification 'LandCover_class'

    Images in the original ImageCollection must have the bands 'NDSI_Snow_Cover', 'Snow_Albedo_Daily_Tile_Class'
    and NDSI_Snow_Cover_Algorithm_Flags_QA.
    'LandCover_class' has three values: 0 (cloud), 50 (land), and 100 (snow).

    Args:
        ee_collection (ee.imagecollection.ImageCollection): MODIS image collection.
        ee_aoi (ee.featurecollection.FeatureCollection): Feature collection with Area of interest.
        threshold_ndsi (int | ee.ee_number.Number): NDSI threshold, must be between 0 and 100.

    Returns:
        ee.imagecollection.ImageCollection: Original image collection with one new band 'LandCover_class'.
    """

    # TODO: Add a check for the threshold_ndsi value here or downstream
    # TODO: Check if ee_aoi can be made optional

    # Select bands of interest and clip to AOI.
    ee_clipped_ic = ee_collection.select(
        selectors=[
            "NDSI_Snow_Cover",
            "Snow_Albedo_Daily_Tile_Class",
            "NDSI_Snow_Cover_Algorithm_Flags_QA",
        ]
    ).map(lambda image: image.clip(ee_aoi))

    # Aplicar la función ReclassifyModis a la colección de imágenes denominada selected
    ee_reclassified_ic = ee_clipped_ic.map(
        lambda img: img_snow_landcover_reclass(img, threshold_ndsi)
    ).select("LandCover_class")

    return ee_reclassified_ic
