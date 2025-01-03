from venv import logger
import ee
import ee.batch
import logging
from gee_toolbox.gee import assets
from datetime import date
from dateutil.relativedelta import relativedelta

from observatorio_ipa.defaults import (
    DEFAULT_TERRA_COLLECTION,
    DEFAULT_AQUA_COLLECTION,
    DEFAULT_START_DT,
    DEFAULT_CHI_PROJECTION,
    DEFAULT_SCALE,
)
from observatorio_ipa.gee import utils
from observatorio_ipa.processes import reclass_and_impute

logger = logging.getLogger(__name__)


def _create_ym_sequence(start_date: date, end_date: date) -> list[str]:
    """
    Create a list of year-month strings between two dates (inclusive) in the format "YYYY-MM"

    Args:
    start_date (datetime.date): Start date
    end_date (datetime.date): End date

    Returns:
    list[str]: List of distinct year-month strings
    """
    start_year = start_date.year
    start_month = start_date.month
    end_year = end_date.year
    end_month = end_date.month

    year_month_sequence = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == start_year and month < start_month:
                continue
            if year == end_year and month > end_month:
                continue
            year_month_sequence.append(f"{year}-{str(month).zfill(2)}")

    # Assure no duplicates
    year_month_sequence = list(set(year_month_sequence))
    year_month_sequence.sort()

    return year_month_sequence


def _monthly_images_pending_export(
    expected_dates: list[str], monthly_collection_path: str, name_prefix: str
) -> list[str]:
    """
    Get the dates of images that have not been exported to assets

    Args:
        expected_dates (list[str]): List of expected dates in the format "YYYY-MM"
        monthly_collection_path (str): Path to asset collection or folder with exported images
        name_prefix (str): Prefix of the image names

    Raises:
        TypeError: If expected_dates is not a list

    Returns:
        list[str]: List of dates that have not been exported
    """
    # ? What error does it raise if monthly_collection_path doesn't exist?
    # ? what error does it raise if monthly_collection_path is not a collection or folder?

    if not isinstance(expected_dates, list):
        raise TypeError("expected_dates must be a list")

    # Get names of images already exported to assets
    exported_images = assets.list_assets(
        parent=monthly_collection_path, asset_types=["Image"]
    )
    exported_images = assets.get_asset_names(exported_images)
    exported_images = [img.split("/")[-1] for img in exported_images]

    # Get only images that start with the required prefix
    exported_images = [img for img in exported_images if img.startswith(name_prefix)]

    # Get Year-month from image names. Expects names to end with "YYYY_MM"
    exported_image_dts = [img[-7:] for img in exported_images]
    exported_image_dts = [img.replace("_", "-") for img in exported_image_dts]

    # Get dates of images that have not been exported
    images_pending_export = list(set(expected_dates) - set(exported_image_dts))
    images_pending_export.sort()

    return images_pending_export


def _get_month_range_dates(
    month: str, trailing_days: int = 0, leading_days: int = 0
) -> dict:
    """
    Get the first, last dates in a month including trailing and leading buffer days.

    Dates are returned in in string format "YYYY-MM-DD"

    Args:
    month (str): Year-month string in the format "YYYY-MM"
    trailing_days (int, optional): Number of trailing days to include. Defaults to 0.
    leading_days (int, optional): Number of leading days to include. Defaults to 0.

    Returns:
    dict: a dictionary with dates in string format "YYYY-MM-DD"

    Raises:
    TypeError: If month is not a string, trailing_days or leading_days are not integers
    ValueError: If month is not in the format "YYYY-MM"

    """

    if not isinstance(month, str):
        raise TypeError("month must be a string")

    if not isinstance(trailing_days, int) or not isinstance(leading_days, int):
        raise TypeError("trailing_days and leading_days must be integers")

    if trailing_days < 0 or leading_days < 0:
        raise ValueError("trailing_days and leading_days must be positive integers")

    if (
        not month[0:4].isdigit()
        or not month[5:7].isdigit()
        or month[4] != "-"
        or len(month) != 7
    ):
        raise ValueError("month must be in the format 'YYYY-MM'")

    month_range = {}
    first_day = date.fromisoformat(month + "-01")
    month_range["first_day"] = str(first_day)

    last_day = first_day + relativedelta(months=1, days=-1)
    month_range["last_day"] = str(last_day)

    month_range["trailing_dates"] = utils.get_buffer_dates(
        str(first_day), trailing_days=trailing_days, leading_days=0
    )
    month_range["leading_dates"] = utils.get_buffer_dates(
        str(last_day), leading_days=leading_days, trailing_days=0
    )

    if trailing_days > 0:
        month_range["min_trailing_date"] = min(month_range["trailing_dates"])
    else:
        month_range["min_trailing_date"] = month_range["first_day"]

    if leading_days > 0:
        month_range["max_leading_date"] = max(month_range["leading_dates"])
    else:
        month_range["max_leading_date"] = month_range["last_day"]

    return month_range


def _check_months_are_complete(
    months: list[str],
    reference_dates: list[str],
    trailing_days: int = 0,
    leading_days: int = 0,
) -> list[str]:
    """
    Check if months are 'complete' within a list of reference_dates, including required leading and trailing buffer days.

    A complete month is a month were all expected images that compose that month, plus the required
     leading and trailing buffer dates are already in the reference set and no new images are expected
    in the future for that given month.

    Args:
    months (list[str]): List of year-month strings in the format "YYYY-MM"
    reference_dates (list[str]): List of dates in the format "YYYY-MM-DD"
    trailing_days (int, optional): Number of trailing days to include. Defaults to 0.
    leading_days (int, optional): Number of leading days to include. Defaults to 0..

    Returns:
    list[str]: List of months that are complete in the reference dates
    """

    if not isinstance(months, list) or not isinstance(reference_dates, list):
        raise TypeError("months and reference_dates must be lists")

    if not months:
        return []

    images_to_export = []
    for target_month in months:
        month_range_dts = _get_month_range_dates(
            target_month, trailing_days=trailing_days, leading_days=leading_days
        )

        # if there are no images in reference_dates within month range, skip
        _month_ref_images = [
            _date
            for _date in reference_dates
            if _date >= month_range_dts["min_trailing_date"]
            and _date <= month_range_dts["max_leading_date"]
        ]

        if not _month_ref_images:
            continue

        # if there's at least 1 image >= max lead date, keep month for export and days to filter
        if any(
            [_date >= month_range_dts["max_leading_date"] for _date in reference_dates]
        ):
            images_to_export.append(target_month)

        images_to_export.sort()

    return images_to_export


def _make_month_dates_seq(
    month: str, trailing_days: int = 0, leading_days: int = 0
) -> list[str]:
    """
    Create a list of dates in a month including trailing and leading buffer days.

    Args:
    month (str): Year-month string in the format "YYYY-MM"
    trailing_days (int, optional): Number of trailing days to include. Defaults to 0.
    leading_days (int, optional): Number of leading days to include. Defaults to 0.


    """

    month_range_dts = _get_month_range_dates(
        month, trailing_days=trailing_days, leading_days=leading_days
    )
    start_date = date.fromisoformat(month_range_dts["min_trailing_date"])
    end_date = date.fromisoformat(month_range_dts["max_leading_date"])

    month_dates_seq = utils.make_dates_seq(start_date, end_date)

    return month_dates_seq


def _ic_monthly_mean(
    ee_ym,
    ee_collection: ee.imagecollection.ImageCollection,
    ee_aoi_fc: ee.featurecollection.FeatureCollection,
):
    """
    Calculate the monthly mean of bands Snow_TAC and Cloud_TAC from an image collection for a given year-month

    Args:
    ee_ym (str): Year-month string in the format "YYYY-MM"
    ee_collection (ee.imagecollection.ImageCollection): Image collection to calculate the monthly mean
    ee_aoi_fc (ee.featurecollection.FeatureCollection): Area of interest feature collection

    Returns:
    ee.image.Image: Image with the monthly mean of the input collection
    """

    # split year-month and convert to ee objects
    ee_ym = ee.ee_string.String(ee_ym)
    i_year = ee.ee_number.Number.parse(ee_ym.slice(0, 4))
    i_month = ee.ee_number.Number.parse(ee_ym.slice(5))

    selected = ee_collection.filter(
        ee.filter.Filter.calendarRange(i_year, i_year, "year")
    ).filter(ee.filter.Filter.calendarRange(i_month, i_month, "month"))

    ee_snow_mean_img = selected.select("Snow_TAC").mean()
    ee_cloud_mean_img = selected.select("Cloud_TAC").mean()
    return (
        ee.image.Image([ee_snow_mean_img, ee_cloud_mean_img])
        .clip(ee_aoi_fc)
        .set("year", i_year)
        .set("month", i_month)
        .set("system:time_start", ee.ee_date.Date.fromYMD(i_year, i_month, 1).millis())
    )


def monthly_export_proc(
    monthly_collection_path: str,
    aoi_path: str,
    dem_path: str,
    name_prefix: str,
    months_list: list[str] | None = None,
):
    # TODO: include full image name in results (to export, excluded, etc)
    # TODO: Improve Error handling
    # No error control added here since it's expected that all paths and parameters have been checked in main.py
    # This process will not overwrite an image if it already exists in the target collection

    logger.info("Starting Monthly Export Process")

    # Fix name prefix if doesn't end with "_" or "-"
    if not name_prefix.endswith("_") and not name_prefix.endswith("-"):
        name_prefix += "_"

    results_dict = {
        "frequency": "monthly",
        "images_pending_export": [],
        "images_excluded": [],
        "images_to_export": [],
        "export_tasks": [],
    }

    # Get terra and aqua image collections, aoi and dem image
    ee_terra_ic = ee.imagecollection.ImageCollection(DEFAULT_TERRA_COLLECTION)
    ee_aqua_ic = ee.imagecollection.ImageCollection(DEFAULT_AQUA_COLLECTION)
    ee_aoi_fc = ee.featurecollection.FeatureCollection(aoi_path)
    ee_dem_img = ee.image.Image(dem_path)
    trailing_days = 2  # hardcode for now
    leading_days = 2  # hardcode for now

    if months_list:
        year_month_sequence = months_list
    else:
        # define the date range for the images to be exported
        year_month_sequence = _create_ym_sequence(
            start_date=date.fromisoformat(DEFAULT_START_DT), end_date=date.today()
        )

    # Identify images that have not been exported
    images_pending_export = _monthly_images_pending_export(
        expected_dates=year_month_sequence,
        monthly_collection_path=monthly_collection_path,
        name_prefix=name_prefix,
    )

    logger.info(f"Images pending export: {images_pending_export}")

    # Only report excluded existing if months_list is provided
    if months_list:
        excluded_existing = list(set(year_month_sequence) - set(images_pending_export))
        excluded_existing = [
            {_month: "already exported"} for _month in excluded_existing
        ]
        if excluded_existing:
            logger.info(f"Images excluded: {excluded_existing}")
            results_dict["images_excluded"].extend(excluded_existing)

    if not images_pending_export:
        return results_dict

    results_dict["images_pending_export"] = images_pending_export

    terra_image_dates = utils.get_collection_dates(ee_terra_ic)
    aqua_image_dates = utils.get_collection_dates(ee_aqua_ic)

    # keep only months that are 'complete' in Terra and  Aqua and not expecting any additional images for that month
    t_images_to_export = _check_months_are_complete(
        images_pending_export,
        terra_image_dates,
        trailing_days=trailing_days,
        leading_days=leading_days,
    )
    a_images_to_export = _check_months_are_complete(
        images_pending_export,
        aqua_image_dates,
        trailing_days=trailing_days,
        leading_days=leading_days,
    )

    images_to_export = list(
        set(t_images_to_export).intersection(set(a_images_to_export))
    )
    images_excluded_incomplete = list(
        set(images_pending_export) - set(images_to_export)
    )
    images_excluded_incomplete = [
        {_month: "Month incomplete"} for _month in images_excluded_incomplete
    ]
    results_dict["images_excluded"].extend(images_excluded_incomplete)
    if images_excluded_incomplete:
        logger.info(f"Images excluded: {images_excluded_incomplete}")

    if images_to_export:
        logger.info(f"Images to export: {images_to_export}")

    if not images_to_export:
        return results_dict

    results_dict["images_to_export"] = images_to_export

    # Keep only dates of interest in Terra and Aqua image collections
    ic_filter_dates = []
    for _month in images_to_export:
        _month_dates = _make_month_dates_seq(
            _month, trailing_days=trailing_days, leading_days=leading_days
        )
        ic_filter_dates.extend(_month_dates)
    ic_filter_dates = list(set(ic_filter_dates))
    ic_filter_dates.sort()

    ee_filtered_terra_ic = utils.filter_collection_by_dates(
        ee_terra_ic, ic_filter_dates
    )
    ee_filtered_aqua_ic = utils.filter_collection_by_dates(ee_aqua_ic, ic_filter_dates)

    # APPLY MAIN PROCESS: Snow landcover reclassification and impute process
    ee_cloud_snow_ic = reclass_and_impute.tac_reclass_and_impute(
        ee_filtered_terra_ic, ee_filtered_aqua_ic, ee_aoi_fc, ee_dem_img
    )

    # Calculate Monthly means
    ee_monthly_imgs_list = ee.ee_list.List(images_to_export)
    ee_monthly_tac_ic = ee.imagecollection.ImageCollection.fromImages(
        ee_monthly_imgs_list.map(
            lambda ym: _ic_monthly_mean(ym, ee_cloud_snow_ic, ee_aoi_fc)
        )
    )

    # Create list of Export tasks for monthly images
    monthly_img_dates = utils.get_collection_dates(ee_monthly_tac_ic)
    monthly_img_dates.sort()

    export_tasks = []
    for _month in monthly_img_dates:
        image_name = name_prefix + _month[0:7].replace("-", "_")
        try:
            ee_image = ee_monthly_tac_ic.filterDate(_month).first()
            # ee_task = ee.batch.Export.image.toAsset(
            #     image=ee_image,
            #     description=image_name,
            #     assetId=pathlib.Path(monthly_collection_path, image_name).as_posix(),
            #     region=ee_aoi_fc,
            #     scale=CHI_DEFAULT_SCALE,
            #     crs=CHI_DEFAULT_PROJECTION,
            #     max_pixels=180000000,
            # )
            ee_task = "mock_task"
            export_tasks.append(
                {
                    "task": ee_task,
                    "image": image_name,
                    "target": "GEE Asset",
                    "status": "mock_created",
                }
            )
            logger.debug(f"Export task created for image: {image_name}")
        except Exception as e:
            export_tasks.append(
                {
                    "task": None,
                    "image": image_name,
                    "target": "GEE Asset",
                    "status": "failed_to_create",
                    "error": str(e),
                }
            )
            logger.debug(f"Export task creation failed for image: {image_name}")

    results_dict["export_tasks"] = export_tasks
    return results_dict
