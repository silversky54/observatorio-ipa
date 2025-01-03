# STEP 1

import ee

from observatorio_ipa.gee import utils as gee_utils
from observatorio_ipa.defaults import MILLISECONDS_IN_DAY


# Join products MOD and MYD


def impute_tac_temporal(
    ee_date,
    qa_value: int,
    ee_reference_ic: ee.imagecollection.ImageCollection,
    ee_collection: ee.imagecollection.ImageCollection | None = None,
    trail_buffer: int = 1,
    lead_buffer: int = 1,
    tac_new_name: str | None = None,
    qa_new_name: str | None = None,
):
    """
    Imputes missing TAC values in an image by comparing TAC values from leading and trailing images in a timeseries.

    The function uses the TAC values from the leading and trailing images where the target image had TAC==0 (missing).
    If the TAC values are the same in the leading and trailing images, this value is used as the imputed missing value.
    The function also updates the QA band with a value where TAC values were successfully imputed.

    If the parameter ee_collection is provided these images are used to get the target image whose pixel values
    need to be imputed. Leading and trailing images for imputation are always taken from the original ee_reference_ic collection.

    If no ee_collection is provided, the reference collection is used for both the target image and the leading
    and trailing images.

    leading and trailing buffer dates are relative to the date of the image under evaluation.

    args:
        ee_date (ee.ee_date.Date): Date of the target image
        ee_reference_ic (ee.imagecollection.ImageCollection): Image collection with Original TAC and QA_CR bands
        ee_collection (ee.imagecollection.ImageCollection): Optional Image collection with TAC and QA_CR bands already imputed
        qa_value (int): Value to set in the QA band where TAC values were successfully imputed
        trail_buffer (int): Number of days to move back to select the trailing image
        lead_buffer (int): Number of days to move forward to select the leading image.
        tac_new_name Optional(str): New name for the TAC band
        qa_new_name Optional(str): New name for the QA band


    returns:
        ee.image.Image: Image with the new TAC and QA bands

    """

    # TODO: Change MAX join of trailing and leading images to just mask one of the images with the matching mask

    # IF target image Collection is none. Use the reference collection
    if ee_collection is None:
        ee_collection = ee_reference_ic

    # KEEP TAC and QA_CR band names if no alternative names provided
    if tac_new_name is None:
        tac_new_name = "TAC"
    if qa_new_name is None:
        qa_new_name = "QA_CR"

    # Select target, leading and trailing images from collection
    ee_target_dt = ee.ee_number.Number(ee_date)
    ee_trailing_dt = ee_target_dt.subtract(trail_buffer * MILLISECONDS_IN_DAY)
    ee_leading_dt = ee_target_dt.add(lead_buffer * MILLISECONDS_IN_DAY)

    ee_target_img = ee_collection.filterDate(ee_target_dt).first()
    ee_trailing_img = (
        ee_reference_ic.select(["TAC"], ["trailing_TAC"])
        .filterDate(ee_trailing_dt)
        .first()
    )

    ee_leading_img = (
        ee_reference_ic.select(["TAC"], ["leading_TAC"])
        .filterDate(ee_leading_dt)
        .first()
    )

    # Get TAC and QA original values
    ee_original_tac_img = ee_target_img.select("TAC")
    ee_original_QA_img = ee_target_img.select("QA_CR")

    # Keep TAC values from leading and Trailing images where Target Image had TAC==0 (missing)
    ee_mask_t0 = ee_target_img.select(["TAC"]).eq(0)
    ee_masked_trailing_img = ee_trailing_img.updateMask(ee_mask_t0)
    ee_masked_leading_img = ee_leading_img.updateMask(ee_mask_t0)

    # Identify points from Trailing and leading images where TAC values are the same and TAC>0
    ee_tac_value_match_img = ee_masked_trailing_img.eq(
        ee_masked_leading_img
    ).updateMask(ee_masked_trailing_img.gt(0))

    # Merge Trailing and leading images and get the max TAC value
    ee_imputed_tac_img = (
        ee.image.Image.cat([ee_masked_trailing_img, ee_masked_leading_img])
        .reduce(ee.reducer.Reducer.max())
        .updateMask(ee_tac_value_match_img)
    )

    # Update TAC of target image with new values
    ee_new_tac_img = (
        ee.image.Image.cat([ee_original_tac_img, ee_imputed_tac_img])
        .reduce(ee.reducer.Reducer.max())
        .rename(tac_new_name)
    )

    # Update QA band with value 20 where TAC values were successfully imputed
    ee_imputed_qa_img = ee.image.Image(qa_value).updateMask(ee_tac_value_match_img)
    ee_new_qa_img = (
        ee.image.Image.cat([ee_original_QA_img, ee_imputed_qa_img])
        .reduce(ee.reducer.Reducer.max())
        .rename(qa_new_name)
    )
    return ee_target_img.select([]).addBands(ee_new_tac_img).addBands(ee_new_qa_img)


def ic_impute_tac_temporal(
    ee_collection: ee.imagecollection.ImageCollection,
) -> ee.imagecollection.ImageCollection:
    """
    Imputes missing TAC values in an image collection by comparing TAC values from leading and trailing images in a timeseries.

    Imputes missing TAC values from the leading and trailing images where the target image had TAC==0 (missing).
    The function also updates the QA band with a value where TAC values were successfully imputed.

    The function will only impute TAC values where the target image has the required leading and trailing images.
    2 days before and 2 days after the target image are required.


    args:
        ee_collection (ee.imagecollection.ImageCollection): Image collection with Original TAC and QA_CR bands

    returns:
    """

    #! Function drops all images that don't have all required leading and trailing images,
    #! but this might drop some images that should be kept. Should all images be kept?

    # keep only dates that have trailing and leading images
    collection_dates = gee_utils.get_collection_dates(ee_collection)
    keep_dates = []
    for target_date in collection_dates:
        buffer_dates = gee_utils.get_buffer_dates(
            target_date, leading_days=2, trailing_days=2
        )
        if all([date in collection_dates for date in buffer_dates]):
            keep_dates.append(target_date)

    # Convert list of dates to ee_list in milliseconds
    ee_keep_dates_list = ee.ee_list.List(
        [ee.ee_date.Date(_date) for _date in keep_dates]
    )

    # Convert the list of ee.Dates to simple list of numbers. Otherwise, map wont work
    keep_dates_list = ee_keep_dates_list.getInfo()
    if keep_dates_list:
        keep_dates_list = [item["value"] for item in keep_dates_list]
    else:
        keep_dates_list = []
    ee_keep_dates_list = ee.ee_list.List(keep_dates_list)

    # Impute values from 1 day before and 1 day after
    ee_imputed_11_ic = ee.imagecollection.ImageCollection.fromImages(
        ee_keep_dates_list.map(
            lambda ee_date: impute_tac_temporal(
                ee_date=ee_date,
                ee_collection=ee_collection,
                ee_reference_ic=ee_collection,
                qa_value=20,
                trail_buffer=1,
                lead_buffer=1,
            )
        )
    )

    # Impute values from 2 days before and 1 day after
    ee_imputed_21_ic = ee.imagecollection.ImageCollection.fromImages(
        ee_keep_dates_list.map(
            lambda ee_date: impute_tac_temporal(
                ee_date,
                ee_collection=ee_imputed_11_ic,
                ee_reference_ic=ee_collection,
                qa_value=21,
                trail_buffer=2,
                lead_buffer=1,
            )
        )
    )

    # # Impute values from 1 days before and 2 day after
    ee_imputed_12_ic = ee.imagecollection.ImageCollection.fromImages(
        ee_keep_dates_list.map(
            lambda ee_date: impute_tac_temporal(
                ee_date,
                ee_collection=ee_imputed_21_ic,
                ee_reference_ic=ee_collection,
                qa_value=22,
                trail_buffer=1,
                lead_buffer=2,
            )
        )
    )

    return ee_imputed_12_ic
