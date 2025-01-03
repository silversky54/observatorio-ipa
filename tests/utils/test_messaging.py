from venv import logger
from more_itertools import side_effect
import pytest
import logging
from pathlib import Path
from datetime import datetime
from email_validator import EmailNotValidError
from observatorio_ipa.utils.messaging import (
    EmailSender,
    init_email_service,
    parse_emails,
    get_template,
    email_results,
)


class TestEmailSender:
    def test_init_success(self, mocker):
        mock_smtp = mocker.patch("observatorio_ipa.utils.messaging.smtplib.SMTP")
        mock_smtp.return_value.noop.return_value = (250, "OK")
        email_sender = EmailSender(
            smtp_server="smtp.server.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="password",
            from_address="from@osn.com",
            to_address=["to@osn.com"],
        )
        assert email_sender.smtp_server == "smtp.server.com"
        assert email_sender.smtp_port == 587
        assert email_sender.smtp_username == "user"
        assert email_sender.smtp_password == "password"
        assert email_sender.from_address == "from@osn.com"
        assert email_sender.to_address == ["to@osn.com"]

    def test_connect_failure(self, mocker):
        mocker.patch(
            "observatorio_ipa.utils.messaging.smtplib.SMTP.starttls",
            side_effect=Exception("Connection failed."),
        )
        with pytest.raises(
            Exception, match="Failed to create EmailSender class: Connection failed."
        ):
            email_service = EmailSender(
                smtp_server="smtp.server.com",
                smtp_port=587,
                smtp_username="user",
                smtp_password="password",
                from_address="from@osn.com",
                to_address=["to@osn.com"],
            )

    def test_init_failure(self, mocker):
        mock_smtp = mocker.patch("smtplib.SMTP")
        mock_smtp.return_value.noop.return_value = (500, "Error")
        with pytest.raises(
            Exception, match="Failed to create EmailSender class: Connection failed."
        ):
            EmailSender(
                smtp_server="smtp.server.com",
                smtp_port=587,
                smtp_username="user",
                smtp_password="password",
                from_address="from@osn.com",
                to_address=["to@osn.com"],
            )

    def test_send_email_success(self, mocker):
        mock_smtp = mocker.patch("smtplib.SMTP")
        mock_smtp.return_value.noop.return_value = (250, "OK")
        email_sender = EmailSender(
            smtp_server="smtp.server.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="password",
            from_address="from@osn.com",
            to_address=["to@osn.com"],
        )
        email_sender.send_email(subject="Test Subject", body="Test Body")
        assert mock_smtp.return_value.send_message.called

    def test_send_email_failure(self, mocker):
        mock_smtp = mocker.patch("smtplib.SMTP")
        mock_smtp.return_value.noop.return_value = (250, "OK")
        mock_smtp.return_value.send_message.side_effect = Exception(
            "Error sending email"
        )
        email_sender = EmailSender(
            smtp_server="smtp.server.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="password",
            from_address="from@osn.com",
            to_address=["to@osn.com"],
        )
        email_sender.send_email(subject="Test Subject", body="Test Body")
        assert mock_smtp.return_value.send_message.called

    def test_send_email_connection_failure(self, mocker):
        mock_smtp = mocker.patch("observatorio_ipa.utils.messaging.smtplib.SMTP")
        mock_smtp.return_value.noop.return_value = (250, "OK")
        subject = "Test Subject"
        body = "Test Body"

        email_sender = EmailSender(
            smtp_server="smtp.server.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="password",
            from_address="from@osn.com",
            to_address=["to@osn.com"],
        )

        mock_smtp.side_effect = (Exception("Connection failed"),)
        result = email_sender.send_email(subject=subject, body=body)
        assert result is None

    def test_close_connection_fails(self, mocker):
        mock_smtp = mocker.patch("smtplib.SMTP")
        mock_smtp.return_value.noop.return_value = (250, "OK")
        mock_smtp.return_value.quit.side_effect = Exception("Error closing connection")
        mock_logger = mocker.patch("observatorio_ipa.utils.messaging.logger.error")
        email_sender = EmailSender(
            smtp_server="smtp.server.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="password",
            from_address="from@osn.com",
            to_address=["to@osn.com"],
        )
        email_sender._close_connection()
        assert mock_smtp.return_value.quit.called
        assert mock_logger.called
        assert email_sender.smtp_connection is None


class TestInitEmailService:
    def test_init_email_service_enabled(self, mocker):
        mock_email_sender = mocker.patch("observatorio_ipa.utils.messaging.EmailSender")
        config = {
            "enable_email": True,
            "smtp_server": "smtp.server.com",
            "smtp_port": 587,
            "smtp_user": "user",
            "smtp_password": "password",
            "smtp_from_address": "from@osn.com",
            "smtp_to_address": ["to@osn.com"],
        }
        email_sender = init_email_service(config)
        assert email_sender is not None
        mock_email_sender.assert_called_once_with(
            smtp_server="smtp.server.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="password",
            from_address="from@osn.com",
            to_address=["to@osn.com"],
        )

    def test_init_email_service_disabled(self):
        config = {
            "enable_email": False,
            "smtp_server": "smtp.server.com",
            "smtp_port": 587,
            "smtp_user": "user",
            "smtp_password": "password",
            "smtp_from_address": "from@osn.com",
            "smtp_to_address": ["to@osn.com"],
        }
        email_sender = init_email_service(config)
        assert email_sender is None

    def test_init_email_service_fails(self, mocker):
        mock_email_sender = mocker.patch("observatorio_ipa.utils.messaging.EmailSender")
        mock_email_sender.side_effect = Exception("Error initializing EmailSender")
        config = {
            "enable_email": True,
            "smtp_server": "smtp.server.com",
            "smtp_port": 587,
            "smtp_user": "user",
            "smtp_password": "password",
            "smtp_from_address": "from@osn.com",
            "smtp_to_address": ["to@osn.com"],
        }
        email_sender = init_email_service(config)
        assert email_sender is None


class TestParseEmails:
    def test_parse_emails_valid_comma(self):
        emails_str = "test1@osn.com, test2@osn.com"
        expected = ["test1@osn.com", "test2@osn.com"]
        assert parse_emails(emails_str) == expected

    def test_parse_emails_valid_semicolon(self):
        emails_str = "test1@osn.com; test2@osn.com"
        expected = ["test1@osn.com", "test2@osn.com"]
        assert parse_emails(emails_str) == expected

    def test_parse_emails_valid_mixed(self):
        emails_str = "test1@osn.com, test2@osn.com; test3@osn.com"
        expected = ["test1@osn.com", "test2@osn.com", "test3@osn.com"]
        assert parse_emails(emails_str) == expected

    def test_parse_emails_no_space(self):
        emails_str = "test1@osn.com,test2@osn.com"
        expected = ["test1@osn.com", "test2@osn.com"]
        assert parse_emails(emails_str) == expected

    def test_parse_emails_invalid(self, mocker):
        emails_str = "test1@osn.com, invalid_email"
        mocked_logger = mocker.patch("observatorio_ipa.utils.messaging.logger.warning")
        mocker.patch(
            "observatorio_ipa.utils.messaging.validate_email",
            side_effect=[mocker.Mock(normalized="test1@osn.com"), EmailNotValidError],
        )
        expected = ["test1@osn.com"]
        assert parse_emails(emails_str) == expected
        mocked_logger.assert_called_once_with(
            "Invalid email address skipped: invalid_email"
        )

    def test_parse_emails_empty(self):
        emails_str = ""
        expected = []
        assert parse_emails(emails_str) == expected


class TestGetTemplate:
    def test_get_template_success(self, mocker):
        mocker.patch(
            "observatorio_ipa.utils.messaging.resources.files",
            return_value=Path("path/to/template"),
        )
        mocker.patch.object(
            Path, "open", mocker.mock_open(read_data="Template content")
        )

        result = get_template("test_template.txt", "Default template")
        assert result == "Template content"

    def test_get_template_file_not_found(self, mocker, caplog):
        mocker.patch(
            "observatorio_ipa.utils.messaging.resources.files",
            return_value=Path("path/to/template"),
        )
        mocker.patch.object(Path, "open", side_effect=FileNotFoundError)
        default_template = "Default template"

        with caplog.at_level(logging.ERROR, logger="observatorio_ipa.utils.messaging"):
            result = get_template("non_existent_template.txt", default_template)

        assert "Template file not found" in caplog.text
        assert result == default_template

    def test_get_template_file_unknown_error(self, mocker, caplog):
        mocker.patch(
            "observatorio_ipa.utils.messaging.resources.files",
            side_effect=Exception("Unknown error"),
        )

        default_template = "Default template"

        with caplog.at_level(logging.ERROR, logger="observatorio_ipa.utils.messaging"):
            result = get_template("non_existent_template.txt", default_template)

        assert "Error reading template file" in caplog.text
        assert result == default_template


class TestEmailResults:
    def test_email_results_success(self, mocker):
        mock_email_service = mocker.Mock()
        mock_get_template = mocker.patch(
            "observatorio_ipa.utils.messaging.get_template",
            return_value="[results] [start_time] [end_time]",
        )
        mock_datetime = mocker.patch(
            "observatorio_ipa.utils.messaging.datetime", autospec=True
        )
        mock_datetime.now.return_value = datetime.fromisoformat("2023-01-01 00:00:01")
        script_start_time = "2023-01-01 00:00:00"
        results = "Export completed successfully"

        email_results(
            email_service=mock_email_service,
            script_start_time=script_start_time,
            results=results,
        )

        expected_message = (
            "Export completed successfully 2023-01-01 00:00:00 2023-01-01 00:00:01"
        )

        mock_get_template.assert_called_once_with(
            "results_email_template.txt", "[results]"
        )
        mock_email_service.send_email.assert_called_once_with(
            subject="OSN Image Processing Automation", body=expected_message
        )

    def test_email_results_no_email_service(self, mocker):
        mock_get_template = mocker.patch(
            "observatorio_ipa.utils.messaging.get_template"
        )
        script_start_time = "2023-01-01 00:00:00"
        results = "Export completed successfully"

        email_results(
            email_service=None,  # type: ignore
            script_start_time=script_start_time,
            results=results,
        )

        mock_get_template.assert_not_called()

    def test_email_results_no_start_time(self, mocker):
        mock_email_service = mocker.Mock()
        mock_get_template = mocker.patch(
            "observatorio_ipa.utils.messaging.get_template",
            return_value="[results] [start_time] [end_time]",
        )
        mock_datetime = mocker.patch(
            "observatorio_ipa.utils.messaging.datetime", autospec=True
        )
        mock_datetime.now.return_value = datetime.fromisoformat("2023-01-01 00:00:01")
        results = "Export completed successfully"

        email_results(
            email_service=mock_email_service,
            script_start_time=None,
            results=results,
        )

        expected_message = (
            "Export completed successfully Not logged 2023-01-01 00:00:01"
        )
        mock_get_template.assert_called_once_with(
            "results_email_template.txt", "[results]"
        )
        mock_email_service.send_email.assert_called_once_with(
            subject="OSN Image Processing Automation", body=expected_message
        )
