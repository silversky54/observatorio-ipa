from datetime import date, datetime, timedelta
import logging


def check_valid_date(date_string: str) -> bool:
    """
    Checks if a string is a valid date format.

    Args:
        date_string: String that represents a date

    Returns:
        Returns TRUE if the string has a valid date format
    """
    if not isinstance(date_string, str):
        return False

    # padding if needed
    if len(date_string) < 10:
        date_string_split = date_string.split("-")
        if len(date_string_split) < 3:
            return False
        date_string_split[1] = date_string_split[1].zfill(2)
        date_string_split[2] = date_string_split[2].zfill(2)
        date_string = "-".join(date_string_split)

    try:
        valid_date = date.fromisoformat(date_string)
        return True
    except Exception as e:
        logging.warning(e)
        return False


def check_valid_date_list(date_list: list[str] | str) -> bool:
    """
    Checks if a list of strings only has valid date formats. Returns false if at least one of of the items in the list has an invalid format.

    Args:
        date_list: list of strings representing dates

    Returns:
        Returns TRUE if all the stings in the list are valid dates
    """
    if type(date_list) is str:
        date_list = [date_list]

    return all(map(check_valid_date, date_list))


def check_valid_month(month_string: str) -> bool:
    """
    Checks if a string is a valid month format YYYY-MM or YYYY-M.

    Args:
        month_string: String that represents a month

    Returns:
        Returns TRUE if the string has a valid month format
    """
    if not isinstance(month_string, str):
        return False

    # zero padding if needed
    if len(month_string) < 7:
        month_string_split = month_string.split("-")
        if len(month_string_split) < 2:
            return False
        month_string_split[1] = month_string_split[1].zfill(2)
        month_string = "-".join(month_string_split)

    try:
        valid_month = date.fromisoformat(f"{month_string}-01")
        return True
    except Exception as e:
        logging.warning(e)
        return False


def check_valid_month_list(month_list: list[str] | str) -> bool:
    """
    Checks if a list of strings only has valid month formats.

    Valid month formats are YYYY-MM or YYYY-M.

    Args:
        month_list: list of strings representing months

    Returns:
        bool: Returns TRUE if all the stings in the list are valid months
    """
    if type(month_list) is str:
        month_list = [month_list]

    return all(map(check_valid_month, month_list))


def check_valid_year(year_string: str | int) -> bool:
    """
    Checks if a string is a valid year format YYYY.

    Args:
        year_string: String that represents a year

    Returns:
        Returns TRUE if the string has a valid year format
    """
    # Using date.fromisoformat to avoid checking if number and length of digits are correct
    if isinstance(year_string, int):
        year_string = str(year_string)

    try:
        valid_year = date.fromisoformat(year_string + "-01-01")
        return True
    except Exception as e:
        logging.warning(e)
        return False


def check_valid_year_list(year_list: list[str] | list[int] | str) -> bool:
    """
    Checks if a list of strings only has valid year formats.

    Valid year formats are YYYY.

    Args:
        year_list: list of strings representing years

    Returns:
        bool: Returns TRUE if all the stings in the list are valid years
    """
    if type(year_list) is str:
        year_list = [year_list]

    try:
        year_list = list(map(str, year_list))
    except Exception as e:
        return False

    return all(map(check_valid_year, year_list))


def current_year_month() -> str:
    """
    Returns the current year and month from local machine time as a string with format YYYY-MM
    e.g. 2022-12
    """
    _today = datetime.today()

    return str(_today.year) + "-" + str(_today.month).zfill(2)


def prev_month_last_date() -> date:
    """
    Returns the last day of the previous month relative to the current date

    Current date is taken from datetime.today()

    Returns:
        Returns a datetime.date object
    """

    return datetime.today().date().replace(day=1) - timedelta(days=1)
