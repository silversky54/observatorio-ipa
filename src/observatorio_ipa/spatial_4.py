"""
This module includes functions to impute values for TAC using 4 neighboring pixels, and 
update QA_CR values for imputed points. 


The module uses a default scale of 463.31271652791656, projected on 'SR-ORG:6974'
Which is consistent what is being used for Modis Terra and Aqua images

This is based on the js code from - users/observatorionieves/modules/CR/Spatial_4.js
- Step 4 of ??

The following conventions are used:
- All server side variables are prefixed with 'ee_'
- Image, ImageCollection and FeatureCollections are sufficed with '_img', '_ic' and '_fc' when possible

GLOSSARY
TAC: Terra-Aqua Classification?
QA_CR: Quality Assessment - C? R?

"""

# TODO: Move DEFAULT_PROJECTION and DEFAULT_SCALE to a configuration file


import ee

DEFAULT_PROJECTION = "SR-ORG:6974"
DEFAULT_SCALE = 463.31271652791656


def impute_TAC_kernel4(
    image: ee.image.Image,
    ee_projection: ee.projection.Projection,
    ee_kernel_w: ee.kernel.Kernel,
) -> ee.image.Image:
    """
    Imputes values for 'TAC' band where TAC==0 (nodata) using the values of adjacent pixels
    and a kernel of 4 neighboring pixels (above, below, left, right). Sets QA_CR to a value
    of 40 for all points where 'Original TAC'==0 and 'New TAC'>0.

    This function only sets QA_CR to 40 for points that imputed to a value>0 for TAC. If the
    imputed TAC is also 0 then QA_CR continues with it's original value (10, 11 or 12)

    It's expected that the original image has bands 'TAC' and 'QA_RC'. For information about
    these bands see module binary.py documentation

    Args:
        image (ee.image.Image): Image with a 'TAC' and 'QA_RC' bands.
        projection (ee.Projection): Projection to reproject the image.
        kernel_w (ee.Kernel): Kernel with weights for the 4 neighboring pixels.

    Returns:
        ee.image.Image: Original image with imputed 'TAC' and 'QA_RC' values.


    """
    # ? What logic is being used to reclassify the sum_masked values back to 0, 50, 100?
    # ? original QA_CR had values of 10, 11, 12 the new masked values are 40
    # ? this would leave the new values as 10, 11, 12 and 40
    # ? at the end why is a select statement used but all bands are commented out?
    # ? What's the purpose of setting dem_snow_max and dem_snow_min to None?
    # ? why is it not setting QA_CR to 40 for points where Original TAC==0 and new TAC==0?
    # ? these are still imputed values that re-affirm the original TAC==0 values

    # ----------IMPUTE TAC----------------

    # Reclassify TAC band values, by numbers that do not have a common multiple:
    # 100: Snow --> 9
    # 50 : Land --> 7
    # 0  : Nodata --> 0

    ee_TAC_original_img = image.select("TAC").reproject(ee_projection)
    ee_TAC_reclassified_img = ee_TAC_original_img.remap(
        [0, 50, 100],  # Original values of the TAC band
        [0, 7, 9],  # New reclassified values
        None,
        "TAC",
    ).rename(
        "TACReclass"
    )  #! Does this end with Two bands or one?

    # impute TAC values
    ee_sum_img = ee_TAC_reclassified_img.reduceNeighborhood(
        reducer=ee.reducer.Reducer.sum(),
        kernel=ee_kernel_w,
    ).reproject(DEFAULT_PROJECTION, None, DEFAULT_SCALE)

    # keep only pixels where original TAC==0
    ee_sum_masked_img = ee_sum_img.updateMask(
        ee_TAC_original_img.eq(0)  # Keep only were origina TAC==0: Nodata (or cloud?)
    )

    ee_masked_reclass_img = ee_sum_masked_img.remap(
        [0, 7, 9, 14, 16, 18, 21, 23, 25, 27, 28, 30, 32, 34, 36],
        [0, 0, 0, 0, 0, 0, 50, 0, 0, 100, 50, 50, 0, 100, 100],
        None,
        "TACReclass_sum",
    ).rename("TAC_step_4")

    # Combine original and imputed TAC bands into one image
    ee_TAC_new_img = (
        ee.image.Image.cat([ee_TAC_original_img, ee_masked_reclass_img])
        .reduce(ee.reducer.Reducer.max())
        .rename("TAC")
    )

    # ----------UPDATE QA_CR FOR IMPUTED VALUES----------------

    ee_QA_original_img = image.select("QA_CR")

    # Set QA for points with imputed TAC to 40 where new TAC are >0 to 40
    # Imputed TAC points are those where originally TAC==0 and now TAC>0
    QA_mask = ee_masked_reclass_img.gt(0)
    QAmasked = ee.image.Image(40).updateMask(QA_mask)  # Between 1 and 40, values 40

    # Join original and imputed QA bands and combine
    ee_QA_new_img = (
        ee.image.Image.cat([ee_QA_original_img, QAmasked])
        .reduce(ee.reducer.Reducer.max())
        .rename("QA_CR")
    )

    return (
        image.select(
            [
                #'NDSI_T',
                #'NDSI_A',
                #'Albedo_T',
                #'Albedo_A',
                #'LandCover_T',
                #'LandCover_A',
                #'QA_T',
                #'QA_A'
            ]
        )
        .addBands(ee_TAC_new_img)
        .addBands(ee_QA_new_img)
        .set("DEM_snow_max", None)
        .set("DEM_snow_min", None)
        .set(
            "system:time_start_date",
            ee.ee_date.Date(image.get("system:time_start")).format("YYYY_MM_dd"),
        )
    )


def spatial_4(coll):
    # ----------------------------------
    # -- PASO 4
    # ----------------------------------
    # -- Reclass band TAC

    # ----------------------------------

    # ? Whats the purpose of declaring weights, kernel and projection at the ImageCollection level
    # ? if it's only used at the Image level?

    # Define kernel cells (4 neighboring pixels)
    weights = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]

    kernel_w = ee.kernel.Kernel.fixed(weights=ee.ee_list.List(weights))

    # Incorporate MODIS projection and adjust scale
    projection = ee.projection.Projection(DEFAULT_PROJECTION).atScale(DEFAULT_SCALE)

    collectionTAC_step_04 = coll.map(
        lambda image: impute_TAC_kernel4(image, projection, kernel_w)
    )

    return collectionTAC_step_04
