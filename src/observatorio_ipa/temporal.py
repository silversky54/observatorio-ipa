# STEP 1

import ee

MILLISECONDS_IN_DAY = 24 * 60 * 60 * 1000

# Join products MOD and MYD


def img_impute_temporal(
    ee_date: ee.ee_date.Date,
    ee_collection: ee.imagecollection.ImageCollection,
    tac_new_name: str,
    qa_new_name: str,
    qa_value: int,
    lead_buffer: int = 1,
    trail_buffer: int = 1,
):
    """
    Imputes missing TAC values in an image by comparing TAC values from leading and trailing images in a timeseries.

    The function uses the TAC values from the leading and trailing images where the target image had TAC==0 (missing).
    If the TAC values are the same in the leading and trailing images, the maximum value is used as the imputed value.
    The function also updates the QA band with a value where TAC values were successfully imputed.

    leading and trailing buffer dates are relative to the date of the image under evaluation.

    args:
        ee_date (ee.ee_date.Date): Date of the target image
        ee_collection (ee.imagecollection.ImageCollection): Image collection with TAC and QA_CR bands
        tac_new_name (str): Name of the new TAC band
        qa_new_name (str): Name of the new QA band
        qa_value (int): Value to set in the QA band where TAC values were successfully imputed
        lead_buffer (int): Number of days to move forward to select the leading image.
        trail_buffer (int): Number of days to move back to select the trailing image

    returns:
        ee.image.Image: Image with the new TAC and QA bands

    """
    # TODO: Add error control for when leading or trailing image doesn't exist
    # TODO: Change MAX join of trailing and leading images to just mask one of the images with the matching mask
    # ? Why is TAC band renamed for trailing and leading images, the name doesn't seem to be used
    # ? does an empty list in a select remove all bands?

    # Select target, leading and trailing images from collection
    ee_target_dt = ee.ee_number.Number(ee_date)
    ee_trailing_dt = ee_target_dt.subtract(trail_buffer * MILLISECONDS_IN_DAY)
    ee_leading_dt = ee_target_dt.add(lead_buffer * MILLISECONDS_IN_DAY)

    ee_target_img = ee_collection.filterDate(ee_target_dt).first()
    ee_trailing_img = (
        ee_collection.select(["TAC"], ["trailing_TAC"])
        .filterDate(ee_trailing_dt)
        .first()
    )
    ee_leading_img = (
        ee_collection.select(["TAC"], ["leading_TAC"]).filterDate(ee_leading_dt).first()
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

    # Merge Trailing and leading images and get the max TAC value #!
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
    return (
        ee_target_img.select(
            [
                #'NDSI_T',
                #'NDSI_A',
                #'CoverClass_T',
                #'CoverClass_A',
                #'LandCover_T',
                #'LandCover_A',
                #'QA_T',
                #'QA_A'
            ]
        )
        .addBands(ee_new_tac_img)
        .addBands(ee_new_qa_img)
    )


def temporal(ee_collection: ee.imagecollection.ImageCollection):
    # ? What is ImageCollection.aggregate_array()?
    # ? Aggregate_array already returns an ee_list, why is it being casted again?
    # NOTE: changed dateEndSub1 to dateEndSub2 since it's buffering 2 days not 1

    # Get date of first Image in the Collection
    ee_first_img_dt = ee.ee_date.Date(
        ee_collection.sort(prop="system:time_start", ascending=True)
        .first()
        .get("system:time_start")
    )

    # Get date of last Image in the Collection
    ee_last_img_dt = ee.ee_date.Date(
        ee_collection.sort(prop="system:time_start", ascending=False)
        .first()
        .get("system:time_start")
    )

    # Move first date 2 days forward and last date 2 days back
    dateIniAdd2 = ee_first_img_dt.advance(2, "day")
    dateEndSub2 = ee_last_img_dt.advance(-2, "day")

    # Get list of unique dates in the Collection (dates are in milliseconds)
    ee_image_dates_list = (
        ee.ee_list.List(
            ee_collection.filterDate(dateIniAdd2, dateEndSub2).aggregate_array(
                "system:time_start"
            )
        )
        .distinct()
        .sort()
    )

    def addDates(ee_date: ee.ee_date.Date):
        # ? Why add or subtract days in milliseconds, why not use ee.Date.advance()?
        # TODO: Simplify function and separate. It does the same thing 3 times but with different leading/trailing dates
        #! order of trailing/leading pairs seems incorrect
        #!  1. trailing 1d, leading 1d
        #!  2. trailing 2d, leading 2d but does trailing 2d, leading 1d
        #!  3. trailing 1d, leading 2d but does trailing 1d, leading 1d (again)

        millisec_x_day = 1 * 24 * 60 * 60 * 1000  # Milliseconds in a day
        ee_target_dt = ee.ee_number.Number(ee_date)
        ee_trailing_1d = ee_target_dt.subtract(millisec_x_day)
        ee_trailing_2d = ee_target_dt.subtract(2 * millisec_x_day)
        ee_leading_1d = ee_target_dt.add(millisec_x_day)
        ee_leading_2d = ee_target_dt.add(2 * millisec_x_day)
        ee_target_img = ee_collection.filterDate(ee_target_dt).first()
        ee_trailing_1d_img = (
            ee_collection.select(["TAC"], ["TAC_S1"]).filterDate(ee_trailing_1d).first()
        )
        ee_trailing_2d_img = (
            ee_collection.select(["TAC"], ["TAC_S2"]).filterDate(ee_trailing_2d).first()
        )
        ee_leading_1d_img = (
            ee_collection.select(["TAC"], ["TAC_A1"]).filterDate(ee_leading_1d).first()
        )
        ee_leading_2d_img = (
            ee_collection.select(["TAC"], ["TAC_A2"]).filterDate(ee_leading_2d).first()
        )

        # -------------------------Ecuación 01 (GB02)-------------------------
        # ------------------------- -1 día y +1 día---------------------------
        # -----------------------------S1 y A1 -------------------------------

        # Get TAC and QA original values
        TAC_T0 = ee_target_img.select("TAC")
        old_QA = ee_target_img.select("QA_CR")

        # Keep TAC values from leading and Trailing images where Target Image had TAC==0 (missing)
        maskT0 = ee_target_img.select(["TAC"]).eq(0)
        S1_EC01 = ee_trailing_1d_img.updateMask(maskT0)
        A1_EC01 = ee_leading_1d_img.updateMask(maskT0)

        # Identify points from Trailing and leading images where TAC values are the same and TAC>0
        coincidence = S1_EC01.eq(A1_EC01).updateMask(S1_EC01.gt(0))

        # Merge Trailing and leading images and get the max TAC value
        # Use points where values where the same as a mask for the max TAC value
        #! Getting MAX might be unnecessary since we will only keep values that are the same in both images
        update = (
            ee.image.Image.cat([S1_EC01, A1_EC01])
            .reduce(ee.reducer.Reducer.max())
            .updateMask(coincidence)
        )

        # Update TAC of target image with new values
        TACEC01 = (
            ee.image.Image.cat([TAC_T0, update])
            .reduce(ee.reducer.Reducer.max())
            .rename("TAC_EC01")
        )

        # Update QA band with value 20 where TAC values were successfully imputed
        testEC01 = ee.image.Image(20)
        preQA = testEC01.updateMask(coincidence)
        QA01 = (
            ee.image.Image.cat([old_QA, preQA])
            .reduce(ee.reducer.Reducer.max())
            .rename("QA_EC01")
        )

        # -------------------------Ecuación 02 (GB02)-------------------------
        # ------------------------- -2 día y +1 día---------------------------
        # -----------------------------S2 y A1 -------------------------------

        # Keep TAC values from Trailing and leading images where Target Image had TAC==0 (missing)
        # Start with image with imputed values from previous step
        #! Shouldn't this be leading 2d?
        maskNewTAC = TACEC01.eq(0)
        S2_EC02 = ee_trailing_2d_img.updateMask(maskNewTAC)
        A1NewMask = ee_leading_1d_img.updateMask(maskNewTAC)

        # Identify points from Trailing and leading images where TAC values are the same and TAC>0
        coincidenceEC02 = S2_EC02.eq(A1NewMask).updateMask(S2_EC02.gt(0))

        # Merge Trailing and leading images and get the max TAC value
        # Use points where values where the same as a mask for the max TAC value
        #! Getting MAX might be unnecessary since we will only keep values that are the same in both images
        updateEC02 = (
            ee.image.Image.cat([S2_EC02, A1NewMask])
            .reduce(ee.reducer.Reducer.max())
            .updateMask(coincidenceEC02)
        )

        # Update TAC of target image with new values
        TACEC02 = (
            ee.image.Image.cat([TACEC01, updateEC02])
            .reduce(ee.reducer.Reducer.max())
            .rename("TAC_EC02")
        )

        # Update QA band with value 21 where TAC values were successfully imputed
        testEC02 = ee.image.Image(21)
        preQAEC02 = testEC02.updateMask(coincidenceEC02)
        NewQAEC02 = (
            ee.image.Image.cat([QA01, preQAEC02])
            .reduce(ee.reducer.Reducer.max())
            .rename("QA_EC02")
        )

        # -------------------------Ecuación 03 (GB02)-------------------------
        # ------------------------- -2 día y +1 día---------------------------
        # -----------------------------S2 y A1 -------------------------------

        # Keep TAC values from Trailing and leading images where Target Image had TAC==0 (missing)
        # Start with image with imputed values from previous step
        maskNewTACEC03 = TACEC02.eq(0)  # New TAC mask
        S1_EC03 = ee_trailing_1d_img.updateMask(maskNewTACEC03)
        A2NewMask = ee_leading_2d_img.updateMask(maskNewTACEC03)

        # Identify points from Trailing and leading images where TAC values are the same and TAC>0
        coincidenceEC03 = S1_EC03.eq(A2NewMask).updateMask(S1_EC03.gt(0))

        updateEC03 = (
            ee.image.Image.cat([S1_EC03, A2NewMask])
            .reduce(ee.reducer.Reducer.max())
            .updateMask(coincidenceEC03)
        )

        # Update TAC of target image with new values
        TACEC03 = (
            ee.image.Image.cat([TACEC02, updateEC03])
            .reduce(ee.reducer.Reducer.max())
            .rename("TAC")
        )

        # Update QA band with value 22 where TAC values were successfully imputed
        testEC03 = ee.image.Image(22)
        preQAEC03 = testEC03.updateMask(coincidenceEC03)
        NewQAEC03 = (
            ee.image.Image.cat([NewQAEC02, preQAEC03])
            .reduce(ee.reducer.Reducer.max())
            .rename("QA_CR")
        )  # Replace with 12 in all places that were changed and there's a coincidence

        return (
            ee_target_img.select(
                [
                    #'NDSI_T',
                    #'NDSI_A',
                    #'CoverClass_T',
                    #'CoverClass_A',
                    #'LandCover_T',
                    #'LandCover_A',
                    #'QA_T',
                    #'QA_A'
                ]
            )
            .addBands(TACEC03)
            .addBands(NewQAEC03)
        )
        # EC 03 bands TAC and QA

    # Final TAC collection GB 02
    collectionTAC_step_02 = ee.imagecollection.ImageCollection.fromImages(
        ee_image_dates_list.map(addDates)
    )

    return collectionTAC_step_02
