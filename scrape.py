import argparse
import logging
import os
import time

from telethon.types import *

import scrape_entities
import scrape_messages
import scrape_participants
from configs import PHONE_NUMBER
from db import start_database
from helper.helper import (
    TelegramClientContext,
    get_entity_info,
    update_argument_variables,
)
from helper import helper
from helper.logger import configure_logging, OUTPUT_DIR

###########################################################################################
# Create the ArgumentParser object to parse command line arguments
parser = argparse.ArgumentParser(
    description=f"Scrapes Telegram entities (broadcast channels, public/private groups, direct message) "
    f"for messages, users, and entity metadata."
)

# Setup argparse for parsing command-line arguments
# Add arguments
# NOTE: Arguments can be referenced in the code i.e. --get-messages is args.get_messages
parser.add_argument(
    "--get-messages", action="store_true", help="Collect all messages in an entity"
)
parser.add_argument(
    "--get-participants",
    action="store_true",
    help="Collect all participants in an entity",
)
parser.add_argument(
    "--get-entities", action="store_true", help="Collect all entities' metadata"
)
parser.add_argument(
    "--max-messages",
    type=int,
    default=helper.max_messages,
    help=f"Maximum number of messages to collect (default {helper.max_messages}) (must be a multiple of 500)",
)
parser.add_argument(
    "--max-entities",
    type=int,
    default=None,
    help="Number of entities to collect from (most recent first)",
)
parser.add_argument(
    "--throttle-time",
    nargs=2,
    type=int,
    default=[helper.min_throttle, helper.max_throttle],
    metavar=("MIN_SECONDS", "MAX_SECONDS"),
    help=f"Throttle time (in seconds) between API calls (default min: {helper.min_throttle}, default max: {helper.max_throttle})",
)
parser.add_argument(
    "--export-to-es",
    action="store_true",
    default=helper.export_to_es,
    help=f"Export results to Elasticsearch (default {helper.export_to_es})",
)
parser.add_argument(
    "--debug",
    action="store_true",
    default=False,
    help="Enable debug mode (default False)",
)

# Parse command-line arguments
args = parser.parse_args()

## Exit conditions
# Check if at least one of the required options is provided
if not (args.get_messages or args.get_participants or args.get_entities):
    parser.error(
        "Please specify at least one of the following options: --get-messages, --get-participants, --get-entities"
    )

# Check if throttle time is specified and contains both min and max seconds
if args.throttle_time and (
    args.throttle_time[0] is None or args.throttle_time[1] is None
):
    parser.error(
        "Error: Both minimum and maximum seconds must be specified for throttle time."
    )

# Check if max messages is specified without get messages
if args.max_messages is not None and not args.get_messages:
    parser.error("Error: --max-messages can only be specified with --get-messages.")

# If --get-messages is specified, but --max-messages is not, set it to None
if args.get_messages and args.max_messages is None:
    args.max_messages = None

if args.max_messages and args.max_messages % 500 != 0:
    parser.error(f"Error: The --max-messages argument must be a multiple of 500.")

# Set variables
update_argument_variables(
    args.max_messages, args.throttle_time[0], args.throttle_time[1], args.export_to_es
)


###########################################################################################


def get_elapsed_time_message(start_time: float) -> str:
    """
    Calculates the program's elapsed time since it was executed to when this
    function is called and returns a message for logging purposes.

    Args:
        start_time: UNIX time of when the program was initially executed

    Returns:
        A log message of the program's elapsed time in seconds.
    """
    end_time = time.time()  # End of program execution to measure elapsed time
    elapsed_time_seconds = "{:.6f}".format(
        end_time - start_time
    )  # Save elapsed time (up to 6 decimal digits)
    return f"Total elapsed time: {elapsed_time_seconds} seconds"


def setup() -> bool:
    """
    Sets up the environment prior to starting a collection

    Return:
        True if the setup was successful
    """
    try:
        # Start a new database or connect to an existing one
        start_database()
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        # Setup logging configurations (do not run logging.* before this)
        configure_logging(args.debug)
        logging.info(f"Debug mode set to {args.debug}")
        logging.debug(f"Set arguments: {vars(args)}")

        # Set and log CLI configs
        logging.info(
            f"Running collection of: Messages '{args.get_messages}', Participants '{args.get_participants}', Entities '{args.get_entities}'"
        )
        logging.info(f"Set maximum entities to collect  : {args.max_entities}")
        logging.info(f"Set export data to Elasticsearch : {helper.export_to_es}")
        logging.info(f"Set minimum API throttle time    : {helper.min_throttle}")
        logging.info(f"Set maxmimum API throttle time   : {helper.max_throttle}")

        return True
    except:
        raise


if __name__ == "__main__":

    # Setup operations
    start_time = time.time()  # Start of program execution to measure elapsed time
    if setup() is not True:
        raise "[-] Failed to setup the environment. Cannot begin collection."

    try:
        entities_collected: int = 0
        with TelegramClientContext() as client:

            # Connect to Telegram
            client.start(PHONE_NUMBER)

            # Channel, Chat, User types explained: https://stackoverflow.com/questions/76683847/telethon-same-entity-type-for-a-group-and-channel-in-telethon
            #                                      https://docs.telethon.dev/en/stable/concepts/chats-vs-channels.html
            # Channel (Broadcast or Public Group): channel.broadcast == True/False
            # Chat    (Private group)            : No chat.username attribute
            # User    (User/DM)                  : No user.title attribute

            # Iterate through all inboxes aka dialogs (DMs, public groups, private groups, broadcast channels)
            # https://docs.telethon.dev/en/stable/quick-references/client-reference.html#dialogs
            # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.dialogs.DialogMethods.iter_dialogs

            if args.get_entities:
                logging.info(
                    f"=========================================================================="
                )
                logging.info(f"[+] Collecting metadata on all entities")
                scrape_entities.scrape(client)

            for dialog in client.iter_dialogs():
                if args.max_entities and entities_collected > args.max_entities:
                    break
                entities_collected += 1

                entity: Channel | Chat | User = dialog.entity
                # if entity.id != 1647639783 and entity.id != 1012147388:
                #     continue
                # if entity.id != 1012147388:  # whalepool
                #     continue
                # if entity.id != 1503790351:  # sri lanka
                #     continue
                if entity.id != 1721768523:  # real test
                    continue
                logging.info(
                    f"=========================================================================="
                )
                logging.info(f"[+] Collection in progress: {get_entity_info(entity)}")

                if args.get_messages:
                    scrape_messages.scrape(client, entity)
                if args.get_participants:
                    scrape_participants.scrape(client, entity)

                # scrape_entities.download_entity(entity)
                # print("------------------------------------------------------")
                # if entity.id == 1647639783:  # russian
                #     break
                # if entity.id == 1012147388:
                #     break
                # if entity.id == 1503790351:  # sri lanka 26k members
                #     break
                if entity.id == 1721768523:
                    break
        logging.info(f"Entities collected: {entities_collected}")
        logging.info(get_elapsed_time_message(start_time))

    except Exception as e:
        logging.exception(
            msg=e,
            stack_info=True,
            exc_info=True,
        )
