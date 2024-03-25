import logging
import datetime

DATETIME_CODE_EXECUTED: str = str(
    datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
)
OUTPUT_DIR: str = f"output/{DATETIME_CODE_EXECUTED}"
OUTPUT_NDJSON: str = f"output_ndjson/{DATETIME_CODE_EXECUTED}"  # newline-delimited JSON for Elasticsearch


def configure_logging(debug_mode: bool = False):
    """
    Setup logging configurations such as output path and output formatting.

    To setup logging configs in a new file, simply call this function
    ```
    # Import required libraries
    from helper import configure_logging
    import logging

    # Execute logging configuration setup function
    configure_logging()

    # Start logging
    logging.info("This is a log")
    logging.info("Привет")
    ```
    Args:
        debug_mode (optional): set debug mode to True or False. Default False.
    """
    logging_filename = f"{OUTPUT_DIR}/logging.log"

    # Set UTC time
    logging.Formatter.converter = lambda *args: datetime.datetime.now(
        datetime.timezone.utc
    ).timetuple()

    # Set basic configurations for logging formatting
    if debug_mode == False:
        logging.basicConfig(
            level=logging.INFO,
            encoding="utf-8",
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt=f"%Y-%m-%dT%H:%M:%S",
            handlers=[
                logging.FileHandler(logging_filename, encoding="utf-8"),  # output to file
                logging.StreamHandler(),  # output to terminal
            ],
        )
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            encoding="utf-8",
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt=f"%Y-%m-%dT%H:%M:%S",
            handlers=[
                logging.FileHandler(logging_filename, encoding="utf-8"),  # output to file
                logging.StreamHandler(),  # output to terminal
            ],
        )
    logging.info(f"Logging to '{logging_filename}' in UTC timezone")
