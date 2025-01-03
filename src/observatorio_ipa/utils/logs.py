import logging

# TODO: Replace hardcoded logger name with a project wide variable

logger = logging.getLogger("observatorio_ipa." + __name__)

DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(name)s %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "./observatorio_ipa.log",
            "encoding": "utf-8",
            "formatter": "standard",
        },
    },
    "loggers": {"observatorio_ipa": {"handlers": ["file"], "level": "INFO"}},
}


def get_log_level(log_level: str | None = "INFO") -> int:
    """
    Returns the numerical value of the log level based on the input string.
    Args:
        log_level (str): The desired logging level as a string.
                        Acceptable values are "DEBUG", "INFO", "WARNING", and "ERROR".
                        Defaults to "INFO".
    Returns:
        int: The numerical value of the log level or None if the input is invalid.
    """
    if not log_level:
        log_level = "INFO"

    log_level = log_level.upper()
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        log_level = "INFO"

    ## Get numerical value of log level.
    num_log_level = getattr(logging, log_level)
    # if not isinstance(num_log_level, int):
    #     raise ValueError(f'Invalid log level: {log_level}')
    return num_log_level


def update_logs_config(config: dict | None = None) -> dict:
    """
    Update the default logging configuration with a provided configuration.
    Args:
        config (dict): A dictionary containing the configuration values.
    Returns:
        dict: A dictionary containing the updated logging configuration.
    """
    config = config.copy() if config else {}
    default_config = DEFAULT_LOGGING_CONFIG.copy()

    config_options = {
        "log_level": None,
        "log_file": None,
    }

    if config:
        # set log level to Info if config["log_level"] is not valid
        if "log_level" in config:
            if config["log_level"] not in ("DEBUG", "INFO", "WARNING", "ERROR"):
                config["log_level"] = "INFO"

        for key in config_options:
            if key in config:
                config_options[key] = config[key]

    if config_options["log_level"]:
        default_config["loggers"]["observatorio_ipa"]["level"] = config_options[
            "log_level"
        ]

    if config_options["log_file"]:
        default_config["handlers"]["file"]["filename"] = config_options["log_file"]

    return default_config


def print_and_log(message: str, log_level: str = "INFO") -> None:
    """
    Print a message to console and to log file
    If no log file is set, logging will also print to console

    Args:
        message: Message to log
        log_level: log level to use when logging the message. Valid options are DEBUG, INFO, WARNING, ERROR.

    Returns:
        None
    """
    print(message)
    match log_level.upper():
        case "DEBUG":
            logger.debug(message)
        case "INFO":
            logger.info(message)
        case "WARNING":
            logger.warning(message)
        case "ERROR":
            logger.error(message)
