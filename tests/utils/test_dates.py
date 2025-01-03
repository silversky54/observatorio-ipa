import pytest
from datetime import date, datetime

from observatorio_ipa.utils.dates import (
    check_valid_date,
    check_valid_date_list,
    check_valid_month,
    check_valid_month_list,
    check_valid_year,
    check_valid_year_list,
    current_year_month,
    prev_month_last_date,
)


class TestCheckValidDate:
    def test_valid_date(self):
        assert check_valid_date("2023-01-01") == True

    def test_invalid_date(self):
        assert check_valid_date("2023-13-01") == False

    def test_single_digit_month(self):
        assert check_valid_date("2023-1-01") == True

    def test_single_digit_day(self):
        assert check_valid_date("2023-01-1") == True

    def test_invalid_date_with_month(self):
        assert check_valid_date("2023-01") == False

    def test_invalid_date_with_year(self):
        assert check_valid_date("2023") == False

    def test_empty_string(self):
        assert check_valid_date("") == False

    def test_non_string_input(self):
        assert check_valid_date(20230101) == False  # type: ignore


class TestCheckValidDateList:
    def test_single_valid_date(self):
        assert check_valid_date_list("2023-01-01") == True

    def test_multiple_valid_dates(self):
        assert check_valid_date_list(["2023-01-01", "2023-02-01"]) == True

    def test_single_invalid_date(self):
        assert check_valid_date_list("2023-13-01") == False

    def test_multiple_dates_with_one_invalid(self):
        assert check_valid_date_list(["2023-01-01", "2023-13-01"]) == False

    def test_empty_list(self):
        assert check_valid_date_list([]) == True

    def test_non_string_input(self):
        assert check_valid_date_list([20230101, 20230201]) == False  # type: ignore


class TestCheckValidMonth:
    def test_valid_month(self):
        assert check_valid_month("2023-01") == True

    def test_invalid_month(self):
        assert check_valid_month("2023-13") == False

    def test_single_digit_month(self):
        assert check_valid_month("2023-1") == True

    def test_invalid_month_with_date(self):
        assert check_valid_month("2023-01-01") == False

    def test_empty_string(self):
        assert check_valid_month("") == False

    def test_non_string_input(self):
        assert check_valid_month(202301) == False  # type: ignore


class TestCheckValidMonthList:
    def test_single_valid_month(self):
        assert check_valid_month_list("2023-01") == True

    def test_multiple_valid_months(self):
        assert check_valid_month_list(["2023-01", "2023-02"]) == True

    def test_single_invalid_month(self):
        assert check_valid_month_list("2023-13") == False

    def test_multiple_months_with_one_invalid(self):
        assert check_valid_month_list(["2023-01", "2023-13"]) == False

    def test_single_month_with_single_digit(self):
        assert check_valid_month_list("2023-1") == True

    def test_invalid_month_with_date(self):
        assert check_valid_month_list("2023-01-01") == False

    def test_empty_list(self):
        assert check_valid_month_list([]) == True

    def test_non_string_input(self):
        assert check_valid_month_list([202301, 202302]) == False  # type: ignore


class TestCheckValidYear:
    def test_valid_year(self):
        assert check_valid_year("2023") == True

    def test_invalid_year(self):
        assert check_valid_year("20a3") == False

    def test_full_date(self):
        assert check_valid_year("2023-01-01") == False

    def test_month(self):
        assert check_valid_year("2023-01") == False

    def test_empty_string(self):
        assert check_valid_year("") == False

    def test_non_string_input(self):
        assert check_valid_year(2023) == True


class TestCheckValidYearList:
    def test_single_valid_year(self):
        assert check_valid_year_list("2023") == True

    def test_multiple_valid_years(self):
        assert check_valid_year_list(["2023", "2022"]) == True

    def test_single_invalid_year(self):
        assert check_valid_year_list("20a3") == False

    def test_multiple_years_with_one_invalid(self):
        assert check_valid_year_list(["2023", "20a3"]) == False

    def test_empty_list(self):
        assert check_valid_year_list([]) == True

    def test_non_string_input(self):
        assert check_valid_year_list([2023, 2022]) == True

    def test_year_to_str_error(self, mocker):
        mocker.patch("observatorio_ipa.utils.dates.map", side_effect=Exception("Error"))
        assert check_valid_year_list(["2023", "2022"]) == False


class TestCurrentYearMonth:
    def test_current_year_month(self, mocker):
        mock_datetime = mocker.patch("observatorio_ipa.utils.dates.datetime")
        mock_datetime.today.return_value = datetime(2023, 1, 1)
        assert current_year_month() == "2023-01"


class TestPrevMonthLastDate:
    def test_prev_month_last_date(self, mocker):
        mock_datetime = mocker.patch("observatorio_ipa.utils.dates.datetime")
        mock_datetime.today.return_value = datetime(2023, 1, 1)
        assert prev_month_last_date() == date(2022, 12, 31)
