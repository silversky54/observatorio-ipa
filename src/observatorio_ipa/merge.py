"""
This module includes functions to merge the LandCover_class bands from two 
collections and calculate TAC and QA_CR bands for the joined collection

This module implements the fist step of Gafurov & Bardossy

Combines Terra (MOD10A1) and Aqua (MYD10A1) MODIS collections 6
Temporal Aggregation (TAC)

It implements the preprocessing steps of Gafurov & Bardossy
uses Terra (MOD10A1) and Aqua (MYD10A1) images from collection 6 of MODIS
The scale used for Terra (MOD10A1) and Aqua (MYD10A1) is 463.31271652791656, both projected on 'SR-ORG:6974'

This is based on the js code from - users/observatorionieves/modules/CR/Merge.js

These functions use the following bands:
- NDSI_Snow_Cover: Snow cover percentage. Values between 0 - 100
- Snow_Albedo_Daily_Tile_Class: Snow albedo percentage - Values between 1 - 100 (## VERIFY ##)
- NDSI_Snow_Cover_Algorithm_Flags_QA: Types of land covers. Used for snow, cloud, and original QA bands

The following conventions are used:
- All server side variables are prefixed with 'ee_'
- Image, ImageCollection and FeatureCollections are sufficed with '_img', '_ic' and '_fc' when possible

GLOSSARY
TAC: Terra-Aqua Classification?
QA_CR: Quality Assessment - C? R?
LandCover_T: is equal to 'LandCover_class' bands calculated for MODIS Terra images
LandCover_A: is equal to 'LandCover_class' bands calculated for MODIS Aqua images
LandCover_class: is the band that contains the classification of the land cover for MODIS images. This band
is calculated in the function binary.img_snow_landcover_reclass()

"""

# TODO: Move DEFAULT_PROJECTION and DEFAULT_SCALE to a configuration file

import ee

DEFAULT_PROJECTION = "SR-ORG:6974"
DEFAULT_SCALE = 463.31271652791656


def calculate_TAC(image: ee.image.Image) -> ee.image.Image:
    """
    Adds a new band 'TAC' for Terra Aqua Classification (TAC) to an image.

    TAC is calculated by taking the maximum value between 'LandCover_T' and 'LandCover_A' bands.

    This function expects the original image to have the bands 'LandCover_T' and 'LandCover_A' where
    'LandCover_T' and 'LandCover_A' are equal to the 'LandCover_class' bands calculated for
    Terra and Aqua images respectively
    TAC band should have values of 0, 50 or 100

    Args:
        image (ee.image.Image): Image with bands 'LandCover_T' and 'LandCover_A'

    Returns:
        ee.image.Image: Image with a new band 'TAC'
    """
    # ? What is TAC? is it short for 'Terra Aqua Classification'?

    # Calculate the TAC by taking the maximum value between 'LandCover_T' and 'LandCover_A'
    ee_TAC_img = (
        image.select("LandCover_T", "LandCover_A")
        .reduce(ee.reducer.Reducer.max())
        .rename("TAC")
        .reproject(DEFAULT_PROJECTION, None, DEFAULT_SCALE)
    )

    return image.addBands(ee_TAC_img)


def calculate_TA_QA(image: ee.image.Image) -> ee.image.Image:
    """
    Adds a new band 'QA_CR' for Terra-Aqua Quality Assessment (QA) for an image.

    QA_CA combines and recodes values of 'LandCover_T' and 'LandCover_A' to indicate if only Terra,
    only Aqua, or both images indicate Snow Cover. QA values are 10 (only Terra), 11 (only Aqua),
    or 12 (both Terra and Aqua)

    This function expects the original image to have the bands 'LandCover_T' and 'LandCover_A' where
    'LandCover_T' and 'LandCover_A' are equal to the 'LandCover_class' bands calculated for
    Terra and Aqua images respectively

    Args:
        image (ee.image.Image): Image with bands 'LandCover_T' and 'LandCover_A'

    Returns:
        ee.image.Image: Image with a new band 'QA_CR'
    """
    # ? What does CR stand for in QA_CR?
    # ? Why is LandCover_T multiplied by 10 to get QA
    # ? QA remap is susceptible to finger error, can this be changed to a formula?
    # ? Research how QA recode values work.
    # ? Most likely 'Only Terra' really means that Terra>Aqua, and 'Only Aqua' means Aqua>Terra.
    # ? Both means Terra==Aqua.

    # ------QA------#
    # Categoría sumatoria                 Valores banda QA
    # 1) Solo Terra                       500, 1000 y 1050 -> (10)
    # 2) Solo Aqua                          50, 100 y 600  -> (11)
    # 3) Ambos                              0, 550 y 1100  -> (12)

    # Combine the Terra and Aqua bands into a single image. Multiply Terra by 10
    ee_terra_temp_img = image.select("LandCover_T").multiply(10)
    ee_aqua_temp_img = image.select("LandCover_A")
    ee_TA_img = ee.image.Image.cat([ee_terra_temp_img, ee_aqua_temp_img])

    # Sum the values of the Terra and Aqua bands
    ee_QA_sum_img = ee_TA_img.reduce(ee.reducer.Reducer.sum()).rename("QA_sum")

    # Remap the values of the QA band to recode the values
    ee_QA_img = ee_QA_sum_img.remap(
        [0, 50, 100, 500, 550, 600, 1000, 1050, 1100],  # Original values in QA Band
        [12, 11, 11, 10, 12, 11, 10, 10, 12],  # Remapped values in QA band
        None,
        "QA_sum",
    ).rename("QA_CR")

    return image.addBands(ee_QA_img)


def add_missing_band(image: ee.image.Image, band: str) -> ee.image.Image:
    """
    Adds a new band to an image with a constant value of (0?).

    args:
        image (ee.image.Image): Image to add the new band
        band (str): Name of the new band

    returns:
        ee.image.Image: Image with the new band
    """
    # ? Was the intention to add a new band with Null values or 0 values?
    # TODO: If this function truly adds value, move to auxiliary functions in separate module

    ee_new_band_img_tmp = ee.image.Image().rename(
        band
    )  #! rename what? doesn't this error out?
    ee_new_band_img = ee.image.Image([ee_new_band_img_tmp])
    return image.addBands(ee_new_band_img)


def merge(
    MOD_ic: ee.imagecollection.ImageCollection,
    MYD_ic: ee.imagecollection.ImageCollection,
):
    """
    Calculates the Terra-Aqua Classification (TAC) and Terra-Aqua Quality Assessment (QA) for band LandCover_class
    after combining image collections with MODIS Terra (MOD) and Aqua (MYD) images.

    This function expects two image collections 'ic_MOD' and 'ic_MYD' each with a band named 'LandCover_class'
    where ic_MOD represents images derived from MODIS Terra (MOD) and ic_MYD images from MODIS Aqua (MYD).

    See function binary.img_snow_landcover_reclass() for more information on the 'LandCover_class' band.

    The Image Collections are joining by the 'system:time_start' property.

    args:
        ic_MOD (ee.imagecollection.ImageCollection): Image collection derived from MODIS Terra images
        ic_MYD (ee.imagecollection.ImageCollection): Image collection derived from MODIS Aqua images

    returns:
        ee.imagecollection.ImageCollection: Image collection with bands 'TAC' and 'QA_CR'

    """
    # ? Confirm how ee.join.Join works. Returns a FeatureCollection
    # ? What does MOD stand for
    # ? What does MYD stand for
    # ? What does MCD stand for
    # ? This function merges by date, should it check that there are no duplicate dates?
    # ? step (5) says rename, but it's really only adding the bands from the oposite collection
    # TODO: Replace invertedJoin with a custom "exclusive left join" function
    # TODO: Check bands produced in the process and final image collection

    ###### STEP 1: #######
    # Rename 'LandCover_class' bands from MOD_ic and MYD_ic image collections to avoid conflicts
    ee_MOD_ic = MOD_ic.select(["LandCover_class"], ["LandCover_T"])  # Terra
    ee_MYD_ic = MYD_ic.select(["LandCover_class"], ["LandCover_A"])  # Aqua

    # -------- JOIN COLLECTIONS --------#
    # (1) Join ImageCollections by 'system:time_start'
    # See https://developers.google.com/earth-engine/guides/joins_inner for reference
    ee_innerJoin = ee.join.Join.inner()
    ee_filterTimeEq = ee.filter.Filter.equals(
        leftField="system:time_start", rightField="system:time_start"
    )
    ee_MCD_inner_ic = ee_innerJoin.apply(ee_MOD_ic, ee_MYD_ic, ee_filterTimeEq).map(
        lambda feature: ee.image.Image.cat(
            feature.get("primary"), feature.get("secondary")
        )
    )

    # (2) Identify images not present in the other collection
    # (3) Add Aqua bands to the collection in order to duplicate the bands
    # (4) Rename the duplicate bands to match the collection with the inner join number of Aqua bands (8 bands)
    invertedJoin = ee.join.Join.inverted()

    # Collection of Terra (MOD) images that are not in Aqua (MYD) collection
    ee_MOD_excluding_MYD_ic = ee.imagecollection.ImageCollection(
        invertedJoin.apply(ee_MOD_ic, ee_MYD_ic, ee_filterTimeEq)
    ).map(lambda image: add_missing_band(image, band="LandCover_A"))

    # Collection of Aqua (MYD) images that are not in Terra (MOD) collection
    ee_MYD_excluding_MOD_fc = ee.imagecollection.ImageCollection(
        invertedJoin.apply(ee_MYD_ic, ee_MOD_ic, ee_filterTimeEq)
    ).map(lambda image: add_missing_band(image, band="LandCover_T"))

    # (5) Merge and sort the collections
    # The result should be an ImageCollection with 8 bands apparently.
    ee_join_all_ic = (
        ee_MCD_inner_ic.merge(ee_MOD_excluding_MYD_ic)
        .merge(ee_MYD_excluding_MOD_fc)
        .sort("system:time_start")
    )

    # -------- ADD TAC & QA BANDS --------#

    ee_collectionTAC_step_01_ic = (
        ee_join_all_ic.map(calculate_TAC).map(calculate_TA_QA).select(["TAC", "QA_CR"])
    )

    return ee_collectionTAC_step_01_ic
