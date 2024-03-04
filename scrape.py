import json
import logging
import os
import time

from telethon.sync import helpers
from telethon.types import *

import scrape_entities
import scrape_messages
import scrape_participants
from credentials import PHONE_NUMBER
from db import start_database
from helper.helper import (
    EntityName,
    JSONEncoder,
    TelegramClientContext,
    _get_entity_info,
    _get_entity_type_name,
    _rotate_proxy,
)
from helper.logger import configure_logging, OUTPUT_DIR


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

        # Setup logging configurations
        configure_logging()  # TODO: Ask user for debug mode or normal mode

        return True
    except:
        raise


if __name__ == "__main__":

    # Setup operations
    start_time = time.time()  # Start of program execution to measure elapsed time
    if setup() is not True:
        raise "[-] Failed to setup the environment. Cannot begin collection."

    try:
        with TelegramClientContext() as client:

            # Connect to Telegram
            client.start(PHONE_NUMBER)

            # print(client.get_me().stringify())
            # print()
            # logging.info(client.get_me().stringify())
            # exit(-1)

            # Channel, Chat, User types explained: https://stackoverflow.com/questions/76683847/telethon-same-entity-type-for-a-group-and-channel-in-telethon
            #                                      https://docs.telethon.dev/en/stable/concepts/chats-vs-channels.html
            # Channel (Broadcast or Public Group): channel.broadcast == True/False
            # Chat    (Private group)            : No chat.username attribute
            # User    (User/DM)                  : No user.title attribute

            # Example of Group/Channel name change/migration
            # action=MessageActionChatMigrateTo(channel_id=2016527483)
            # action=MessageActionChannelMigrateFrom(title='Harry Testing', chat_id=4199887938)

            # Iterate through all inboxes aka dialogs (DMs, public groups, private groups, broadcast channels)
            # https://docs.telethon.dev/en/stable/quick-references/client-reference.html#dialogs
            # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.dialogs.DialogMethods.iter_dialogs
            # scrape_entities.scrape(client)
            for dialog in client.iter_dialogs():

                entity: Channel | Chat | User = dialog.entity
                # if entity.id != 1647639783 and entity.id != 1012147388:
                #     continue
                # if entity.id != 1012147388:  # whalepool
                #     continue
                # if entity.id != 1503790351:  # sri lanka
                #     continue
                if entity.id != 2016527483:  # my server
                    continue

                # Retrieve entity by its ID and display logs
                # entity: Channel | User | Chat = client.get_entity(id)
                # logging.info(f"------------------------------------------------------")
                logging.info(
                    f"=========================================================================="
                )
                logging.info(f"[+] Collection in progress: {_get_entity_info(entity)}")
                print()

                # scrape_entities.scrape(client)
                # scrape_entities.download_entity(entity)
                # scrape_messages.scrape(client, entity)
                print()
                scrape_participants.scrape(client, entity)
                # collect_participants(entity)
                # collect_participants_test(entity)
                # collect_participants_new(entity)
                # print("------------------------------------------------------")
                # if entity.id == 1647639783:  # russian
                #     break
                # if entity.id == 1012147388:
                #     break
                # if entity.id == 1503790351:  # sri lanka 26k members
                #     break
                if entity.id == 2016527483:
                    break
        logging.info(get_elapsed_time_message(start_time))

    except Exception as e:
        logging.exception(
            msg=e,
            stack_info=True,
            exc_info=True,
        )
