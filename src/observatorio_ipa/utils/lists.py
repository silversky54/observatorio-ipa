def csv_to_list(csv_string: str) -> list:
    """
    Converts a comma-separated string to a list of strings.

    Args:
        csv_string: A string of comma-separated values.

    Returns:
        A list of strings.
    """
    csv_list = [item.strip().strip(" \"'") for item in csv_string.split(",")]

    # Remove empty strings from list
    csv_list = list(filter(None, csv_list))
    return csv_list
