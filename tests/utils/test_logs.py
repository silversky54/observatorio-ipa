from unittest import mock
import pytest
import logging
from observatorio_ipa.utils.logs import get_log_level, update_logs_config, print_and_log


class TestGetLogLevel:
    def test_default_log_level(self):
        assert get_log_level() == logging.INFO

    def test_debug_log_level(self):
        assert get_log_level("DEBUG") == logging.DEBUG

    def test_info_log_level(self):
        assert get_log_level("INFO") == logging.INFO

    def test_warning_log_level(self):
        assert get_log_level("WARNING") == logging.WARNING

    def test_error_log_level(self):
        assert get_log_level("ERROR") == logging.ERROR

    def test_invalid_log_level(self):
        assert get_log_level("INVALID") == logging.INFO

    def test_none_log_level(self):
        assert get_log_level(None) == logging.INFO  # type: ignore


class TestUpdateLogsConfig:
    def test_default_config(self):
        config = update_logs_config()
        assert config["loggers"]["observatorio_ipa"]["level"] == "INFO"
        assert config["handlers"]["file"]["filename"] == "./observatorio_ipa.log"

    def test_update_log_level(self):
        config = update_logs_config({"log_level": "DEBUG"})
        assert config["loggers"]["observatorio_ipa"]["level"] == "DEBUG"

    def test_update_log_file(self):
        config = update_logs_config({"log_file": "new_log_file.log"})
        assert config["handlers"]["file"]["filename"] == "new_log_file.log"

    def test_update_both_log_level_and_file(self):
        config = update_logs_config({"log_level": "ERROR", "log_file": "error_log.log"})
        assert config["loggers"]["observatorio_ipa"]["level"] == "ERROR"
        assert config["handlers"]["file"]["filename"] == "error_log.log"

    def test_update_invalid_log_level(self):
        config = update_logs_config({"log_level": "INVALID"})
        assert config["loggers"]["observatorio_ipa"]["level"] == "INFO"


class TestPrintAndLog:
    def test_print_and_log_info(self, capsys, mocker):
        mock_logger = mocker.patch("observatorio_ipa.utils.logs.logger.info")
        print_and_log("Test message", "INFO")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        mock_logger.assert_called_once_with("Test message")

    def test_print_and_log_debug(self, capsys, mocker):
        mock_logger = mocker.patch("observatorio_ipa.utils.logs.logger.debug")
        print_and_log("Test message", "DEBUG")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        mock_logger.assert_called_once_with("Test message")

    def test_print_and_log_warning(self, capsys, mocker):
        mock_logger = mocker.patch("observatorio_ipa.utils.logs.logger.warning")
        print_and_log("Test message", "WARNING")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        mock_logger.assert_called_once_with("Test message")

    def test_print_and_log_error(self, capsys, mocker):
        mock_logger = mocker.patch("observatorio_ipa.utils.logs.logger.error")
        print_and_log("Test message", "ERROR")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        mock_logger.assert_called_once_with("Test message")

    def test_print_and_log_invalid_level(self, capsys, mocker):
        # Patch all loggers
        loggers = {
            "info": mocker.patch("observatorio_ipa.utils.logs.logger.info"),
            "debug": mocker.patch("observatorio_ipa.utils.logs.logger.debug"),
            "warning": mocker.patch("observatorio_ipa.utils.logs.logger.warning"),
            "error": mocker.patch("observatorio_ipa.utils.logs.logger.error"),
        }

        print_and_log("Test message", "INVALID")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

        # Assert no logger was called
        for logger in loggers.values():
            logger.assert_not_called()
