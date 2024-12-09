"""
This module includes functions to impute values for TAC using 8 neighboring pixels, and 
update QA_CR values for imputed points. 


The module uses a default scale of 463.31271652791656, projected on 'SR-ORG:6974'
Which is consistent what is being used for Modis Terra and Aqua images

This is based on the js code from - users/observatorionieves/modules/CR/Spatial_8.js
- Step 5 of ??

The following conventions are used:
- All server side variables are prefixed with 'ee_'
- Image, ImageCollection and FeatureCollections are sufficed with '_img', '_ic' and '_fc' when possible

GLOSSARY
TAC: Terra-Aqua Classification?
QA_CR: Quality Assessment - C? R?
DEM: Digital Elevation Model

"""

# TODO: Move DEFAULT_PROJECTION and DEFAULT_SCALE to a configuration file


import ee

DEFAULT_PROJECTION = "SR-ORG:6974"
DEFAULT_SCALE = 463.31271652791656


# Set a mask with cloud and snow class then apply it to the DEM
def step05(image, DEM_reproject, kernel_w):
    """
    Impute TAC values using DEM data and an 8 pixel kernel.

    Imputes values for 'TAC' band where TAC==0 (nodata) using DEM information of
    neighboring pixels using a a kernel of 8 neighboring pixels. Sets QA_CR to a value
    of 50 for all points where 'Original TAC'==0 and 'New TAC'>0.

    The function uses elevation data to impute values for the "TAC" band where TAC == 0 (nodata)
     by using the elevation information of neighboring pixels. The elevation data is also used
     to infer the minimum height of snow pixels and to compare cloud height data with the minimum
     snow height data to potentially reclassify cloud pixels as snow.

    """

    # ? What is DEM_reproject?
    # ? Why are masks multiplied by 100? shouldn't masks be  0, 1?
    # ? Should this function check if image and DEM use the same projection and scale?
    # ? What exactly does DEM hight mean

    # Select DEM points where there's no data (TAC==0 -> nodata) and set to 100
    mask_nodata = image.select("TAC").eq(0).multiply(100)  # Mask values [0,100]
    DEM_nodata = DEM_reproject.updateMask(mask_nodata).rename("DEM_nodata")

    # select DEM points where there's snow  (TAC==100 -> snow) and set to 100
    mask_snow = image.select("TAC").eq(100).multiply(100)  # Mask values [0,100]
    DEM_snow = DEM_reproject.updateMask(mask_snow).rename("DEM_snow")

    # Recalculate DEM for all pixels using only DEM values of neighboring pixels that had snow (TAC==100).
    # This is done to infer the possible "minimum" height in that pixel that would indicate presence of snow.
    kernel_snow_min = DEM_snow.reduceNeighborhood(
        reducer=ee.reducer.Reducer.min(), kernel=kernel_w, skipMasked=False
    ).reproject(DEFAULT_PROJECTION, None, DEFAULT_SCALE)

    # if the DEM value in pixels where theres no data (clouds) is greater than the minimum DEM hight that
    #  would indicate presence of snow then the pixel is reclassified as snow
    ee_comparison_img = (
        DEM_nodata.gt(kernel_snow_min)
        .multiply(100)
        .rename("comparison")  # values [0,100], 100=snow
    )

    # Combine original and imputed TAC bands into one image
    ee_TAC_original_img = image.select("TAC")
    ee_TAC_new_img = (
        ee.image.Image.cat([ee_TAC_original_img, ee_comparison_img])
        .reduce(ee.reducer.Reducer.max())
        .rename("TAC")
    )

    # ----------UPDATE QA_CR FOR IMPUTED VALUES----------------

    ee_QA_original_img = image.select("QA_CR")

    # Set QA for points with imputed TAC to 40 where new TAC are >0 to 40
    # Imputed TAC points are those where originally TAC==0 and now TAC>0
    QA_mask = ee_comparison_img.gt(0)
    QAmasked = ee.image.Image(50).updateMask(QA_mask)
    # Join original and imputed QA bands and combine
    ee_QA_new_img = (
        ee.image.Image.cat([ee_QA_original_img, QAmasked])
        .reduce(ee.reducer.Reducer.max())
        .rename("QA_CR")
    )

    return (
        image.select([])
        .addBands(ee_TAC_new_img)
        .addBands(ee_QA_new_img)
        .set(
            "system:time_start_date",
            ee.ee_date.Date(image.get("system:time_start")).format("YYYY_MM_dd"),
        )
    )


def spatial_8(
    collection,
    DEM_reproject,
):
    # Define the kernel cells (8 neighboring pixels)
    weights = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
    kernel_w = ee.kernel.Kernel.fixed(weights=weights)

    collectionTAC_step_05 = collection.map(
        lambda image: step05(image, DEM_reproject, kernel_w)
    )
    return collectionTAC_step_05
