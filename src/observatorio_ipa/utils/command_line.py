import argparse
import os

# TODO: See if it's possible to take value from an environment variable if not provided in the command line for required fields
# TODO: See if we can enable option to log-in with regular user (not service user)
# NOTE: Some arguments are required but not forcing it since they can also be read from environment variables


def set_argument_parser() -> argparse.ArgumentParser:
    """
    Creates an argument parser for the command line interface.

    Returns:
        argparse.ArgumentParser: An argument parser object.
    """
    # Create the parser
    parser = argparse.ArgumentParser()

    # Service user
    parser.add_argument(
        "-u",
        "--user",
        dest="user",
        default=os.getenv("OSN_USER"),
        help="User ID. Can also be set via the OSN_USER environment variable.",
    )

    # Service credentials
    parser.add_argument(
        "-c",
        "--service-credentials",
        dest="service_credentials_file",
        default=os.getenv("OSN_SERVICE_CREDENTIALS"),
        help="Service account credentials file location",
    )

    # GEE Asset Paths for daily, monthly and yearly images
    parser.add_argument(
        # "-d",
        "--day-assets-path",
        dest="daily_assets_path",
        default=os.getenv("OSN_DAILY_ASSETS_PATH"),
        help="GEE asset path where daily images will be saved",
    )

    parser.add_argument(
        "--day-image-prefix",
        dest="daily_image_prefix",
        default=os.getenv("OSN_DAILY_IMAGE_PREFIX"),
        help="Prefix for daily images",
    )

    parser.add_argument(
        # "-m",
        "--month-assets-path",
        dest="monthly_assets_path",
        default=os.getenv("OSN_MONTHLY_ASSETS_PATH"),
        help="GEE asset path where monthly images will be saved",
    )

    parser.add_argument(
        "--month-image-prefix",
        dest="monthly_image_prefix",
        default=os.getenv("OSN_MONTHLY_IMAGE_PREFIX"),
        help="Prefix for monthly images",
    )

    parser.add_argument(
        # "-y",
        "--year-assets-path",
        dest="yearly_assets_path",
        default=os.getenv("OSN_YEARLY_ASSETS_PATH"),
        help="GEE asset path where yearly images will be saved",
    )

    parser.add_argument(
        "--year-image-prefix",
        dest="yearly_image_prefix",
        default=os.getenv("OSN_YEARLY_IMAGE_PREFIX"),
        help="Prefix for yearly images",
    )

    # # Google Drive Path where images will be saved
    # parser.add_argument(
    #     "-d",
    #     "--drive-path",
    #     dest="drive_path",
    #     help="Google Drive path for saving images",
    # )

    # GEE Asset Path for reading regions FeatureCollection
    parser.add_argument(
        # "-r",
        "--aoi-asset-path",
        dest="aoi_asset_path",
        default=os.getenv("OSN_AOI_ASSET_PATH"),
        help="GEE asset path for AOI FeatureCollection",
    )

    parser.add_argument(
        "--dem-asset-path",
        dest="dem_asset_path",
        default=os.getenv("OSN_DEM_ASSET_PATH"),
        help="GEE asset path for DEM image",
    )

    # # Options for exporting images
    # parser.add_argument(
    #     "-e",
    #     "--export-to",
    #     dest="export_to",
    #     help="Where to export images. Valid options [toAsset | toDrive | toAssetAndDrive]. Default=toAsset ",
    #     choices=["toAsset", "toDrive", "toAssetAndDrive"],
    # )

    parser.add_argument(
        "--days-to-export",
        dest="days_list",
        default=os.getenv("OSN_DAYS_LIST"),
        help="comma-separated string of days to export '2022-11-1, 2022-10-22'",
    )

    parser.add_argument(
        "--months-to-export",
        dest="months_list",
        default=os.getenv("OSN_MONTHS_LIST"),
        help="comma-separated string of months to export '2022-11, 2022-10'.",
    )

    parser.add_argument(
        "--years-to-export",
        dest="years_list",
        default=os.getenv("OSN_YEARS_LIST"),
        help="comma-separated string of years to export '2022, 2021'.",
    )

    # Logging arguments
    parser.add_argument(
        "-l",
        "--log-level",
        dest="log_level",
        default=os.getenv("OSN_LOG_LEVEL", "INFO"),
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    # Enable email notifications
    parser.add_argument(
        "--enable-email",
        dest="enable_email",
        const="True",
        default=os.getenv("OSN_ENABLE_EMAIL", "False"),
        help="Enable email notifications",
        action="store_const",
    )

    # Email arguments
    parser.add_argument(
        "--smtp-server",
        dest="smtp_server",
        default=os.getenv("OSN_SMTP_SERVER"),
        help="SMTP server for sending email",
    )

    parser.add_argument(
        "--smtp-port",
        dest="smtp_port",
        default=os.getenv("OSN_SMTP_PORT"),
        type=int,
        help="SMTP port for sending email",
    )

    parser.add_argument(
        "--smtp-user",
        dest="smtp_user",
        default=os.getenv("OSN_SMTP_USER"),
        help="SMTP user for connecting to server",
    )

    parser.add_argument(
        "--smtp-password",
        dest="smtp_password",
        default=os.getenv("OSN_SMTP_PASSWORD"),
        help="SMTP password for connecting to server",
    )

    parser.add_argument(
        "--smtp-user-file",
        dest="smtp_user_file",
        default=os.getenv("OSN_SMTP_USER_FILE"),
        help="file with SMTP user for connecting to server",
    )

    parser.add_argument(
        "--smtp-password-file",
        dest="smtp_password_file",
        default=os.getenv("OSN_SMTP_PASSWORD_FILE"),
        help="file with SMTP password for connecting to server",
    )

    parser.add_argument(
        "--from-address",
        dest="smtp_from_address",
        default=os.getenv("OSN_SMTP_FROM"),
        help="From email address for sending email",
    )

    parser.add_argument(
        "--to-address",
        dest="smtp_to_address",
        default=os.getenv("OSN_SMTP_TO"),
        help="Comma-separated list of email addresses to send email to. e.g 'email1@example.com, email2@default.com'",
    )

    return parser
