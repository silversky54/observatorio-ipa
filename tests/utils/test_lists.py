import pytest
from observatorio_ipa.utils.lists import csv_to_list


class TestCsvToList:
    def test_single_value(self):
        csv_string = "value1"
        expected = ["value1"]
        assert csv_to_list(csv_string) == expected

    def test_multiple_values(self):
        csv_string = "value1, value2, value3"
        expected = ["value1", "value2", "value3"]
        assert csv_to_list(csv_string) == expected

    def test_values_with_spaces(self):
        csv_string = " value1 , value2 , value3 "
        expected = ["value1", "value2", "value3"]
        assert csv_to_list(csv_string) == expected

    def test_values_with_quotes(self):
        csv_string = '"value1", "value2", "value3"'
        expected = ["value1", "value2", "value3"]
        assert csv_to_list(csv_string) == expected

    def test_values_with_single_quotes(self):
        csv_string = "'value1', 'value2', 'value3'"
        expected = ["value1", "value2", "value3"]
        assert csv_to_list(csv_string) == expected

    def test_empty_values(self):
        csv_string = "value1, , value3"
        expected = ["value1", "value3"]
        assert csv_to_list(csv_string) == expected

    def test_empty_string(self):
        csv_string = ""
        expected = []
        assert csv_to_list(csv_string) == expected

    def test_only_empty_values(self):
        csv_string = ", , ,"
        expected = []
        assert csv_to_list(csv_string) == expected
