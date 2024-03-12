"""
Module for scraping messages in a given entity.
"""

import json
import logging
import os
import time

from telethon import TelegramClient
from telethon.sync import helpers
from telethon.types import *

from db import (
    messages_collection_get_offset_id,
    messages_collection_insert_offset_id,
    iocs_batch_insert,
)
from helper.helper import (
    JSONEncoder,
    get_entity_type_name,
    rotate_proxy,
)
from helper.logger import OUTPUT_DIR
from helper.translate import translate
from helper.ioc import find_iocs

COLLECTION_NAME: str = "messages"


def _collect(client: TelegramClient, entity: Channel | Chat | User) -> bool:
    """
    Collects all messages in a given entity via its API and stores the data in-memory.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group).

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    try:
        logging.info(f"[+] Collecting {COLLECTION_NAME} from Telethon API")

        # Collect messages from entity
        # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.get_messages
        # Or check client.iter_messages() documentation to see how client.get_messages() works
        # Due to limitations with the API retrieving more than 3000 messages will take longer than usual

        # Collection configs
        counter: int = -1  # Track number of API calls made
        counter_max: int = 5  # Max API calls to make in this collection
        chunk_size: int = 500  # Number of messages to retrieve per iteration
        max_messages: int = counter_max * chunk_size

        # Proxy configs
        counter_rotate_proxy: int = 2  # Number of iterations until proxy rotation

        # Tracking offset
        start_offset_id: int = messages_collection_get_offset_id(entity.id)
        offset_id_value: int = start_offset_id
        collection_start_time: int = int(time.time())
        collection_end_time: int = collection_start_time

        # Store collected messages
        messages_collected: helpers.TotalList = None

        # Main collection logic
        logging.debug(f"Starting collection at offset value {offset_id_value}")
        logging.info(f"Max number of messages to be collected: {max_messages}")

        while True:
            # Proxy rotation...
            counter += 1
            if counter >= counter_rotate_proxy:
                logging.info(f"Rotating proxy...")
                rotate_proxy(client)
                counter = 0
                break

            # Collect messages (reverse=True means oldest to newest)
            # Start at message with id offset_id, collect the next 'limit' messages
            chunk: helpers.TotalList = client.get_messages(
                entity, limit=chunk_size, reverse=True, offset_id=offset_id_value
            )

            if len(chunk) > 0:  # Messages were returned
                # Append collected messages to list of all messages collected
                if messages_collected is None:
                    messages_collected = chunk  # First chunk
                else:
                    messages_collected.extend(chunk)

                logging.info(f"Collected {len(chunk)} {COLLECTION_NAME}...")
            else:  # No messages returned... All messages have been collected
                logging.info(f"No new {COLLECTION_NAME} to collect")
                break

            # Next collection will begin with this "latest message collected" offset id
            offset_id_value = chunk[-1].to_dict()["id"]

            if counter >= counter_max:
                logging.info(f"Reached max number of messages to be collected")
                break

        # Post-collection logic
        if messages_collected is None or len(messages_collected) == 0:
            logging.info(f"There are no {COLLECTION_NAME} to collect. Skipping...")
            return True

        # Convert the Message object to JSON and extract IOCs
        all_iocs: list[dict] = []  # extracted IOCs
        messages_list: list[dict] = []
        for message in messages_collected:
            # Known message types: Message, MessageService
            message_dict: dict = message.to_dict()

            # Translate message to English, if it is not already in English
            original_message: str | None = message_dict.get("message")
            if original_message is not None:
                translated_message: str = translate(original_message)
                if translated_message is not None:
                    message_dict["message_translated"] = translated_message

            # Append to download list
            messages_list.append(message_dict)

            # Extract any IOCs present in the message
            if type(message) is Message:
                extracted_iocs = _extract_iocs(message_dict)
                all_iocs.extend(extracted_iocs)

        # Perform a batch database insert of all collected IOCs
        if len(all_iocs) > 0:
            iocs_batch_insert(all_iocs)

        _download(messages_list, COLLECTION_NAME, entity)

        logging.info(f"Completed collection and downloading of {COLLECTION_NAME}")
        logging.info(
            f"Updating latest offset id for next collection as: {offset_id_value}"
        )
        collection_end_time = int(time.time())

        # Insert collection details into DB for tracking purposes
        messages_collection_insert_offset_id(
            entity.id,
            start_offset_id,
            offset_id_value,
            collection_start_time,
            collection_end_time,
        )
        return True
    except:
        logging.critical(
            "[-] Failed to collect data from Telegram API for unknown reasons"
        )
        raise


def _extract_iocs(message_obj: dict) -> list[dict]:
    """
    Extracts IOCs and prepares them for batch insertion.

    Analyzes an original (non-translated) message object and extracts present IOCs
    into a list. The Message object must have been converted into a Python dictionary.

    IOCs could be URLs, domains, CVEs, IPs (IPv4, IPv6), hashes (SHA256, SHA1, MD5)...

    Example use cases:
    - As company Y, I know what my IPs are. I will search in the database for my IP 2.3.4.5
    to see if my IP is present. I discover that it is, I can investigate further. "Is my IP
    leaked? How was it leaked? Why are people talking about my IP?"
    - "Give me a list of all hashes that are being discussed, so that I can run it against
    my company's antivirus software or VirusTotal to see if I can detect it or not.

    Args:
        message_obj: Message object in a dictionary object

    Returns:
        Returns the list of IOCs present in the message
    """
    iocs_list: list[dict] = []
    # print(f"checking ioc...")
    iocs = find_iocs(message_obj["message"])

    for ioc_type, ioc_value in iocs:
        iocs_list.append(
            {
                "message_id": message_obj["id"],
                "channel_id": (message_obj.get("peer_id") or {}).get("channel_id"),
                "user_id": (message_obj.get("from_id") or {}).get("user_id"),
                "ioc_type": ioc_type,
                "ioc_value": ioc_value,
                "original_message": message_obj.get("message"),
                "translated_message": message_obj.get("message_translated", None),
            }
        )
    return iocs_list


def _download(data: list[dict], data_type: str, entity: Channel | Chat | User) -> bool:
    """
    Downloads collected messages into JSON files on the disk

    Args:
        data: list of collected objects (messages, participants...)
        data_type: string description of the type of data collected ("messages", "participants"...)
        entity: channel (public group or broadcast channel), chat (private group), user (direct message)

    Return:
        True if the download was successful
    """
    logging.info(f"[+] Downloading {COLLECTION_NAME} into JSON: {entity.id}")
    try:
        # Define the JSON file name
        json_file_name = f"{OUTPUT_DIR}/{get_entity_type_name(entity)}_{entity.id}/{data_type}_{entity.id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Write data from JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, cls=JSONEncoder, indent=2)

        logging.info(
            f"{len(data)} {data_type} successfully exported to {json_file_name}"
        )

        return True
    except:
        logging.error("[-] Failed to download the collected data into JSON files")
        raise


def scrape(client: TelegramClient, entity: Channel | Chat | User) -> bool:
    """
    Scrapes messages in a particular entity.

    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group).

    Scraping has the following phases:
    - Collection: fetches messages from the provider API and stores the data in-memory
    - Download: downloads the messages from memory into disk (JSON file)

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if scrape was successful
    """
    logging.info(
        "=========================================================================="
    )
    logging.info(f"[+] Begin {COLLECTION_NAME} scraping process")
    _collect(client, entity)
    logging.info(
        f"[+] Successfully scraped {COLLECTION_NAME} {get_entity_type_name(entity)}"
    )

    return True
