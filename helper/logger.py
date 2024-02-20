import logging
import datetime

DATETIME_CODE_EXECUTED: str = str(
    datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
)
OUTPUT_DIR: str = f"output/{DATETIME_CODE_EXECUTED}"


def configure_logging():
    """
    Setup logging configurations such as output path and output formatting.

    To setup logging configs in a new file, do the following
    ```
    from helper import configure_logging
    import logging

    configure_logging("filename.py")
    logging.info("This is a log")
    ```

    Args:
        filename: name of the file that is being logged
    """
    logging_filename = f"{OUTPUT_DIR}/logging.log"

    # Set UTC time
    logging.Formatter.converter = lambda *args: datetime.datetime.now(
        datetime.timezone.utc
    ).timetuple()

    # Set basic configurations for logging formatting
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt=f"%Y-%m-%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(logging_filename),  # output to file
            logging.StreamHandler(),  # output to terminal
        ],
    )
    logging.info(f"Logging to '{logging_filename}' in UTC timezone")
