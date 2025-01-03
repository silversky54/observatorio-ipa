import pytest
import json
import runpy

from observatorio_ipa.main import main
from observatorio_ipa.utils.messaging import EmailSender


@pytest.fixture
def mock_config():
    return {
        "service_credentials_file": "path/to/credentials.json",
        "daily_assets_path": "path/to/daily",
        "monthly_assets_path": "path/to/monthly",
        "yearly_assets_path": "path/to/yearly",
        "daily_image_prefix": "daily",
        "monthly_image_prefix": "monthly",
        "yearly_image_prefix": "yearly",
        "aoi_asset_path": "path/to/aoi",
        "dem_asset_path": "path/to/dem",
        "days_list": ["2023-01-01"],
        "months_list": ["2023-01"],
        "years_list": ["2023"],
        "enable_email": True,
        "smtp_user": "user",
        "smtp_password": "password",
        "smtp_server": "smtp.server.com",
        "smtp_port": 587,
        "smtp_from_address": "from@osn.com",
        "smtp_to_address": "to@osn.com",
    }


@pytest.fixture
def mock_set_argument_parser(mocker):
    mock_parser = mocker.patch("observatorio_ipa.main.command_line.set_argument_parser")
    mock_args = mocker.Mock()
    mock_args.service_credentials_file = "path/to/credentials.json"
    mock_args.daily_assets_path = "path/to/daily"
    mock_args.monthly_assets_path = "path/to/monthly"
    mock_args.yearly_assets_path = "path/to/yearly"
    mock_args.daily_image_prefix = "daily"
    mock_args.monthly_image_prefix = "monthly"
    mock_args.yearly_image_prefix = "yearly"
    mock_args.aoi_asset_path = "path/to/aoi"
    mock_args.dem_asset_path = "path/to/dem"
    mock_args.days_list = ["2023-01-01"]
    mock_args.months_list = ["2023-01"]
    mock_args.years_list = ["2023"]
    mock_args.enable_email = True
    mock_args.smtp_user = "user"
    mock_args.smtp_password = "password"
    mock_args.smtp_server = "smtp.server.com"
    mock_args.smtp_port = 587
    mock_args.smtp_from_address = "from@osn.com"
    mock_args.smtp_to_address = "to@osn.com"
    mock_parser.return_value.parse_args.return_value = mock_args
    return mock_parser


@pytest.fixture
def mock_init_email_config(mocker, mock_config):
    return mocker.patch(
        "observatorio_ipa.main.scripting.init_email_config", return_value=mock_config
    )


@pytest.fixture
def mock_email_service(mocker):
    return mocker.MagicMock(spec=EmailSender)


@pytest.fixture
def mock_init_email_service(mocker, mock_email_service):
    return mocker.patch(
        "observatorio_ipa.utils.messaging.init_email_service",
        return_value=mock_email_service,
    )


@pytest.fixture
def mock_check_required_config(mocker, mock_config):
    return mocker.patch(
        "observatorio_ipa.main.scripting.check_required_config",
        return_value=mock_config,
    )


@pytest.fixture
def mock_check_required_assets(mocker):
    return mocker.patch("observatorio_ipa.utils.scripting.check_required_assets")


@pytest.fixture
def mock_open_service_account_file(mocker):
    return mocker.patch(
        "builtins.open",
        mocker.mock_open(read_data=json.dumps({"client_email": "test_email"})),
    )


@pytest.fixture
def mock_json_load(mocker):
    return mocker.patch(
        "observatorio_ipa.main.json.load", return_value={"client_email": "test_email"}
    )


@pytest.fixture
def mock_ee(mocker):
    mock_ee = mocker.patch("observatorio_ipa.main.ee")
    mock_ee._helpers.ServiceAccountCredentials.return_value = mocker.Mock()
    mock_ee.Initialize.return_value = None
    return mock_ee


@pytest.fixture
def mock_terminate_error(mocker):
    return mocker.patch("observatorio_ipa.utils.scripting.terminate_error")


@pytest.fixture
def mock_monthly_export_proc(mocker):
    return mocker.patch(
        "observatorio_ipa.main.monthly_export.monthly_export_proc",
        return_value={
            "images_pending_export": ["2024-11"],
            "images_excluded": [],
            "images_to_export": ["2024-11"],
            "export_tasks": [
                {
                    "task": "mock_task",
                    "image": "image_2024_11",
                    "target": "GEE Asset",
                    "status": "created",
                }
            ],
        },
    )


def test_main_success(
    mocker,
    mock_config,
    mock_terminate_error,
    mock_set_argument_parser,
    mock_init_email_config,
    mock_init_email_service,
    mock_check_required_config,
    mock_check_required_assets,
    mock_open_service_account_file,
    mock_json_load,
    mock_ee,
    mock_monthly_export_proc,
):

    result = main()
    assert result == 0
    mock_terminate_error.assert_not_called()
    mock_monthly_export_proc.assert_called_once_with(
        monthly_collection_path=mock_config["monthly_assets_path"],
        name_prefix=mock_config["monthly_image_prefix"],
        aoi_path=mock_config["aoi_asset_path"],
        dem_path=mock_config["dem_asset_path"],
    )


def test_main_email_config_error(
    mocker,
    mock_config,
    mock_terminate_error,
    mock_set_argument_parser,
):

    mocker.patch(
        "observatorio_ipa.main.scripting.init_email_config",
        side_effect=ValueError("Email configuration error"),
    )
    result = main()
    assert result == 1
    mock_terminate_error.assert_called_once_with(
        err_message="Email configuration error", script_start_time=mocker.ANY
    )


def test_main_required_config_not_found(
    mocker,
    mock_config,
    mock_terminate_error,
    mock_set_argument_parser,
    mock_init_email_config,
    mock_init_email_service,
    # mock_check_required_config
):
    mocker.patch(
        "observatorio_ipa.main.scripting.check_required_config",
        side_effect=ValueError("Required configuration not found"),
    )

    result = main()
    assert result == 1
    mock_terminate_error.assert_called_once_with(
        err_message="Required configuration not found",
        script_start_time=mocker.ANY,
        email_service=mock_init_email_service.return_value,
    )


def test_main_service_account_file_not_found(
    mocker,
    mock_config,
    mock_terminate_error,
    mock_set_argument_parser,
    mock_init_email_config,
    mock_init_email_service,
    mock_check_required_config,
    # mock_check_required_assets,
    # mock_json_load,
    # mock_ee,
):
    mocker.patch("observatorio_ipa.main.open", side_effect=FileNotFoundError)
    result = main()
    assert result == 1
    mock_terminate_error.assert_called_once_with(
        err_message="Service account file not found",
        script_start_time=mocker.ANY,
        email_service=mock_init_email_service.return_value,
    )


def test_main_gee_initialization_failed(
    mocker,
    mock_config,
    mock_terminate_error,
    mock_set_argument_parser,
    mock_init_email_config,
    mock_init_email_service,
    mock_check_required_config,
    mock_open_service_account_file,
    mock_json_load,
    mock_ee,
):

    mock_ee.Initialize.side_effect = Exception("GEE initialization failed")
    result = main()
    assert result == 1
    mock_terminate_error.assert_called_once_with(
        err_message="Initializing connection to GEE failed",
        script_start_time=mocker.ANY,
        email_service=mock_init_email_service.return_value,
        exception=mocker.ANY,
    )


def test_main_required_assets_not_found(
    mocker,
    mock_config,
    mock_terminate_error,
    mock_set_argument_parser,
    mock_init_email_config,
    mock_init_email_service,
    mock_check_required_config,
    mock_open_service_account_file,
    mock_json_load,
    mock_ee,
):
    mocker.patch(
        "observatorio_ipa.main.scripting.check_required_assets",
        side_effect=ValueError("Required assets not found"),
    )
    result = main()
    assert result == 1
    mock_terminate_error.assert_called_once_with(
        err_message="Required assets not found",
        script_start_time=mocker.ANY,
        email_service=mock_init_email_service.return_value,
    )


def test_main_no_images_to_export(
    mocker,
    mock_config,
    mock_terminate_error,
    mock_set_argument_parser,
    mock_init_email_config,
    mock_init_email_service,
    mock_check_required_config,
    mock_check_required_assets,
    mock_open_service_account_file,
    mock_json_load,
    mock_ee,
    capsys,
):

    mocker.patch(
        "observatorio_ipa.main.monthly_export.monthly_export_proc",
        return_value={"export_tasks": []},
    )

    # capture "No images to export" message with capsys.
    result = main()
    captured = capsys.readouterr()
    assert result == 0
    assert "No images to export" in captured.out
    mock_terminate_error.assert_not_called()


# def test_init(mocker):
#     # mock_main = mocker.patch("observatorio_ipa.main.main", return_value=0)
#     # # mock_sys_exit = mocker.patch("observatorio_ipa.main.sys.exit")
#     # runpy.run_module("observatorio_ipa.main", run_name="__main__")
#     # mock_main.assert_called_once()
#     # # mock_sys_exit.assert_called_once_with(0)
#     # def test_init():
#     from observatorio_ipa import main
#     with mocker.patch.object(main, "main", return_value=42):
#         with mocker.patch.object(main, "__name__", "__main__"):
#             with mocker.patch.object(main.sys,'exit') as mock_exit:
#                 main.init()
#             assert mock_exit.call_args[0][0] == 42
