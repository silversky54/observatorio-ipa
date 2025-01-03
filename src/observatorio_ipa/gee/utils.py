import ee
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from datetime import UTC as datetime_UTC


def set_date_property(image: ee.image.Image) -> ee.image.Image:
    """Sets a date property named 'simpleTime' with the image's date in string format YYYY-MM-dd

    Args:
    image (ee.Image): Image to set the date property

    Returns:
    ee.Image

    """
    date = ee.ee_date.Date(image.date().format("YYYY-MM-dd"))
    return ee.image.Image(
        image.set("simpleTime", date)
    )  # Wrapping in ee.Image to avoid cast error


def remove_date_property(image):
    return (
        ee.image.Image()  # Image without any bands or properties
        .addBands(image)  # add bands
        .copyProperties(
            source=image, exclude=["simpleTime"]
        )  # add properties excluding simpleTime
    )


def filter_collection_by_dates(
    ee_collection: ee.imagecollection.ImageCollection, dates_list: list[str]
) -> ee.imagecollection.ImageCollection:
    """
    Filter an image collection by a list of dates

    Args:
    ee_collection: ee.ImageCollection to filter
    dates_list: list of dates in format "YYYY-MM-DD"

    Returns:
    ee.ImageCollection
    """

    # add property with image date in string format "YYYY-MM-DD"
    ee_collection = ee_collection.map(set_date_property)

    # create ee.List of dates
    ee_dates_list = ee.ee_list.List([ee.ee_date.Date(i_date) for i_date in dates_list])

    # filter collection by dates
    ee_filtered_ic = ee_collection.filter(
        ee.filter.Filter.inList("simpleTime", ee_dates_list)
    )

    # remove simpleTime property Not working
    # ee_filtered_collection = ee_filtered_collection.map(remove_date_property)

    return ee_filtered_ic


def get_buffer_dates(
    target_date: str, leading_days: int = 2, trailing_days: int = 2
) -> list[str]:
    """Returns a list of dates around a target date

    Args:
    target_date (str): Date in format "YYYY-MM-DD"
    leading_days (int): Number of days before the target date
    trailing_days (int): Number of days after the target date

    Returns:
    list[str]: List of dates in format "YYYY-MM-DD"

    Raises:
    ValueError: If the target date is not in the correct format
    """

    target_date_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    buffer_dates = [
        str(target_date_dt + timedelta(days=delta))
        for delta in range(-trailing_days, leading_days + 1)
    ]
    buffer_dates.remove(target_date)
    buffer_dates.sort()
    return buffer_dates


def get_collection_dates(
    ee_collection: ee.imagecollection.ImageCollection,
) -> list[str]:
    """Get the dates in string format 'YYYY-MM-DD' of the images in an ImageCollection

    Args:
    ee_collection (ee.imagecollection.ImageCollection): ImageCollection to get the dates from

    Returns:
    list[str]: List of dates in format "YYYY-MM-DD"

    Raises:
    ValueError: If the Images don't have the property 'system:time_start'
    """
    # get "system:time_start" of all images in image collection
    image_dates_in_ms = ee_collection.aggregate_array("system:time_start").getInfo()

    if not image_dates_in_ms:
        raise ValueError(
            "Couldn't get system:time_start property from image collection"
        )

    # convert milliseconds to date
    image_dates_in_ms = [
        datetime.fromtimestamp(date / 1000, datetime_UTC).strftime("%Y-%m-%d")
        for date in image_dates_in_ms
    ]
    return image_dates_in_ms


def get_image_date(ee_image: ee.image.Image) -> str:
    """Get the date of an image in string format 'YYYY-MM-DD'

    Args:
    image (ee.Image): Image to get the date from

    Returns:
    str: Date in format "YYYY-MM-DD"

    Raises:
    ValueError: If the image doesn't have the property 'system:time_start'
    """

    img_date_in_ms = ee_image.get("system:time_start").getInfo()

    if img_date_in_ms is None:
        raise ValueError("Image does not have a 'system:time_start' property")

    return datetime.fromtimestamp(img_date_in_ms / 1000, datetime_UTC).strftime(
        "%Y-%m-%d"
    )


def make_dates_seq(start_dt: date, end_dt: date) -> list[str]:
    """
    Create a list of dates between two dates (inclusive) in the format "YYYY-MM-DD"

    Args:
    start_dt (datetime.date): Start date
    end_dt (datetime.date): End date

    Returns:
    list[str]: List of dates in format "YYYY-MM-DD"
    """
    if not isinstance(start_dt, date) or not isinstance(end_dt, date):
        raise TypeError("start_dt and end_dt must be datetime.date objects")

    return [
        str(start_dt + relativedelta(days=i))
        for i in range((end_dt - start_dt).days + 1)
    ]
