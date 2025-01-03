from math import log
import sys
import logging, logging.config
import logging_tree
import pprint
import json
from datetime import datetime
import ee
import logging_tree.format
from nbconvert import export

from observatorio_ipa.gee import exports as gee_exports
from observatorio_ipa.processes import monthly_export
from observatorio_ipa.utils import logs
from observatorio_ipa.utils import command_line
from observatorio_ipa.utils import scripting
from observatorio_ipa.utils import messaging


# TODO: Give user an option to change log file
# TODO: move string rep of datetime to functions that use it


def make_export_plan_report(export_plan: dict) -> str:
    """
    Create a report of the export plan.

    Parameters:
    -----------
    export_plan : dict
        A dictionary containing the export plan.

    Returns:
    --------
    str
        A string containing the export plan report.
    """

    export_plan_report = "\n"
    export_plan_report += "---------------------------------------------\n"
    export_plan_report += (
        f"{export_plan['frequency'].capitalize()} Images Export Plan:\n"
    )
    export_plan_report += "---------------------------------------------\n"
    export_plan_report += "Images to export\n"
    if len(export_plan["images_to_export"]) == 0:
        export_plan_report += "\t└ No images to export \n"
    else:
        for image in export_plan["images_to_export"]:
            export_plan_report += f"\t└{image} \n"
    export_plan_report += "Images excluded\n"
    if len(export_plan["images_excluded"]) == 0:
        export_plan_report += "\t└ No images excluded \n"
    else:
        for image in export_plan["images_excluded"]:
            export_plan_report += f"\t└{image} \n"

    return export_plan_report


def make_export_results_report(export_tasks: list) -> str:
    """
    Create a report of the export results.

    Parameters:
    -----------
    export_results : dict
        A dictionary containing the export results.

    Returns:
    --------
    str
        A string containing the export results report.
    """

    export_results_report = "\n"
    export_results_report += "---------------------------------------------\n"
    export_results_report += "Export Results:\n"
    export_results_report += "---------------------------------------------\n"
    if len(export_tasks) == 0:
        export_results_report += f"- No images exported \n"
    else:
        export_results_report += f"- Exporting {len(export_tasks)} images.\n"
        for task in export_tasks:
            if task.get("error", False):
                _error = f"- {task['error']}"
            else:
                _error = ""
            export_results_report += (
                f"\t└ {task['image']} : {task['status']} {_error} \n"
            )

    return export_results_report


def main():
    script_start_time = datetime.now()

    ## ------ PARSE ARGUMENTS ---------
    parser = command_line.set_argument_parser()
    args = parser.parse_args("")
    config = vars(args)
    # pprint.pprint(config)

    ## ------ Setup Logging ------------
    logger = logging.getLogger("observatorio_ipa")
    logging.config.dictConfig(logs.update_logs_config(config=config))
    # logger.propagate = False
    logger.debug("---- STARTING SCRIPT ----")

    ## ------ Setup Email ---------------
    try:
        config = scripting.init_email_config(config)
        email_service = messaging.init_email_service(config)
    except ValueError as e:
        scripting.terminate_error(
            err_message=str(e),
            script_start_time=script_start_time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return 1

    ## ------ Validate inputs -----------
    try:
        config = scripting.init_config(config)
    except ValueError as e:
        scripting.terminate_error(
            err_message=str(e),
            script_start_time=script_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            email_service=email_service,
        )
        return 1

    ## ------ GEE CONNECTION ---------
    # Connect to GEE using service account for automation
    logger.debug("Connecting to GEE")

    try:
        with open(config["service_credentials_file"], "r") as f:
            service_account_data = json.load(f)
        service_user = service_account_data["client_email"]

        credentials = ee._helpers.ServiceAccountCredentials(
            email=service_user,
            key_data=json.dumps(service_account_data),
        )
        ee.Initialize(credentials)
        logger.debug("GEE connection successful")

    except FileNotFoundError as e:
        scripting.terminate_error(
            err_message="Service account file not found",
            script_start_time=script_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            email_service=email_service,
        )
        return 1

    except Exception as e:
        scripting.terminate_error(
            err_message="Initializing connection to GEE failed",
            script_start_time=script_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            email_service=email_service,
            exception=e,
        )
        return 1

    ## ------ Validate GEE Paths ------------
    # Terminate early if assets don't exist
    try:
        scripting.check_required_assets(config)

    except ValueError as e:
        scripting.terminate_error(
            err_message=str(e),
            script_start_time=script_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            email_service=email_service,
        )
        return 1

    ## ------ EXPORT MONTHLY IMAGES ---------
    export_tasks = []
    export_results = ""
    if config.get("monthly_assets_path", False):
        monthly_export_results = monthly_export.monthly_export_proc(
            monthly_collection_path=config["monthly_assets_path"],
            name_prefix=config["monthly_image_prefix"],
            aoi_path=config["aoi_asset_path"],
            dem_path=config["dem_asset_path"],
            months_list=config["months_list"],
        )
        export_tasks.extend(monthly_export_results["export_tasks"])
        export_results += make_export_plan_report(monthly_export_results)

    else:
        logger.debug("Skipping Monthly Export Process")
    ## ------- EXPORT YEARLY IMAGES ---------
    if config.get("yearly_assets_path", False):
        logger.debug("Starting Yearly Export Process")
        # TODO: Implement yearly export
    else:
        logger.debug("Skipping Yearly Export Process")

    ## ------- EXPORT DAILY IMAGES ---------
    if config.get("daily_assets_path", False):
        logger.debug("Starting Daily Export Process")
        # TODO: Implement daily export  - Daily requirement is still TBD
    else:
        logger.debug("Skipping Daily Export Process")

    ## ------- START & TRACK EXPORTS ---------
    export_tasks = gee_exports.track_exports(export_tasks)

    ## ------- REPORT RESULTS ---------
    export_results += make_export_results_report(export_tasks)
    print(export_results)

    if email_service:
        messaging.email_results(
            email_service=email_service,
            script_start_time=script_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            results=export_results,
        )

    ## ------- CLEANUP ---------
    logger.debug("---- SCRIPT FINISHED ----")
    return 0


if __name__ == "__main__":
    sys.exit(main())
