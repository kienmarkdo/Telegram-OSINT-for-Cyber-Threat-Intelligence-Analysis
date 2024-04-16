"""
Module for scraping messages in a given entity.
"""

import json
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor

from telethon import TelegramClient
from telethon.sync import helpers
from telethon.types import *

from helper import helper
from helper.db import (
    iocs_batch_insert,
    messages_collection_get_offset_id,
    messages_collection_insert_offset_id,
)
from helper.es import index_json_file_to_es
from helper.helper import JSONEncoder, get_entity_type_name, rotate_proxy, throttle
from helper.ioc import find_iocs
from helper.logger import OUTPUT_DIR
from helper.translate import translate

COLLECTION_NAME: str = "messages"


def _translate_message(message: dict):
    """
    Translate a message. Function to be executed in parallel.

    Args:
        message: a message object
    """
    original_message = message.get("message")
    if original_message:
        translated_message = translate(original_message)
        return translated_message
    return None


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
    # Pre-define minimal variable(s) for emergency data recovery in exception handling
    messages_collected: helpers.TotalList = None
    try:
        logging.info(f"[+] Collecting {COLLECTION_NAME} from Telethon API")

        # Collect messages from entity
        # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.get_messages
        # Or check client.iter_messages() documentation to see how client.get_messages() works
        # Due to limitations with the API retrieving more than 3000 messages will take longer than usual

        # Collection configs
        counter: int = -1  # Track number of API calls made
        # counter_max: int = 5  # Max API calls to make in this collection
        chunk_size: int = 500  # Number of messages to retrieve per iteration
        # max_messages: int = counter_max * chunk_size

        # Proxy configs
        counter_rotate_proxy: int = 2  # Number of API calls until proxy rotation

        # Tracking offset
        start_offset_id: int = messages_collection_get_offset_id(entity.id)
        offset_id_value: int = start_offset_id
        collection_start_time: int = int(time.time())
        collection_end_time: int = collection_start_time

        # Store collected messages
        messages_collected: helpers.TotalList = None

        # Begin collection
        logging.debug(f"Starting collection at offset value {offset_id_value}")
        logging.info(f"Max number of messages to be collected: {helper.max_messages}")
        if helper.max_messages is None:
            logging.info(f"Collect all messages in this entity's entire history")

        # Main collection logic
        while True:
            # Proxy rotation...
            counter += 1
            if counter % counter_rotate_proxy == 0:
                rotate_proxy(client)

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

            if (
                helper.max_messages is not None
                and len(messages_collected) >= helper.max_messages
            ):
                logging.info(f"Reached max number of messages to be collected")
                break

            # Delay code execution/API calls to prevent bot detection by Telegram
            throttle()

        # Post-collection logic
        if messages_collected is None or len(messages_collected) == 0:
            logging.info(f"There are no {COLLECTION_NAME} to collect. Skipping...")
            return True
        logging.info(f"Number of API calls made: {counter}")

        # Convert the Message object to JSON and extract IOCs
        all_iocs: list[dict] = []  # extracted IOCs
        messages_list: list[dict] = []

        # Collecting messages for translation
        messages_to_translate = [
            message.to_dict()
            for message in messages_collected
            if message.to_dict().get("message")
        ]

        # Performing the translation in parallel
        logging.info(f"Translating messages into English (this may take some time)...")
        with ProcessPoolExecutor() as executor:
            translated_messages = list(
                executor.map(_translate_message, messages_to_translate)
            )

        # Updating messages with translated texts
        for message_dict, translated in zip(messages_to_translate, translated_messages):
            if translated:
                message_dict["message_translated"] = translated

            extracted_iocs = _extract_iocs(message_dict)
            all_iocs.extend(extracted_iocs)
            # message_dict["iocs"] = extracted_iocs  # NOTE: Uncomment to insert IOCs directly into the Messages JSON file
            messages_list.append(message_dict)

        # # Perform a batch database insert of all collected IOCs
        # if len(all_iocs) > 0:
        #     iocs_batch_insert(all_iocs)

        # Download data to JSON
        iocs_output_path: str = _download(all_iocs, entity, "iocs")
        output_path: str = _download(messages_list, entity)

        # Index data into Elasticsearch
        if helper.export_to_es:
            index_name: str = "messages_index"
            iocs_index: str = "iocs_index"

            logging.info(f"[+] Exporting data to Elasticsearch")
            if index_json_file_to_es(output_path, index_name):
                logging.info(
                    f"[+] Indexed {COLLECTION_NAME} to Elasticsearch as: {index_name}"
                )
            if index_json_file_to_es(iocs_output_path, iocs_index):
                logging.info(f"[+] Indexed IOCs to Elasticsearch as: {iocs_index}")

        logging.info(
            f"[+] Completed the collection, downloading, and exporting of {COLLECTION_NAME}"
        )
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
        logging.info(
            f"Attempting to recover any partially collected messages stored in memory and downloading them to disk..."
        )
        logging.info(f"This data will be re-collected in the next collection run")
        # -- Download data to JSON
        # Convert the collected object to JSON
        messages_list: list[dict] = []
        for message in messages_collected:
            message_dict: dict = message.to_dict()
            messages_list.append(message_dict)
        _download(messages_list, entity)
        logging.info(f"Download complete")
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
    iocs = find_iocs(message_obj["message"])

    for ioc_type, ioc_value in iocs:
        iocs_list.append(
            {
                "message_id": message_obj["id"],
                "entity_id": message_obj.get("peer_id", {}).get("channel_id")
                or message_obj.get("peer_id", {}).get("chat_id")
                or message_obj.get("peer_id", {}).get("user_id"),
                "user_id": (message_obj.get("from_id") or {}).get("user_id"),
                "ioc_type": ioc_type,
                "ioc_value": ioc_value,
                "original_message": message_obj.get("message"),
                "translated_message": message_obj.get("message_translated", None),
            }
        )
    return iocs_list


def _download(
    data: list[dict], entity: Channel | Chat | User, data_type: str = COLLECTION_NAME
) -> str:
    """
    Downloads collected messages into JSON files on the disk

    Args:
        data: list of collected objects (messages, participants...)
        entity: channel (public group or broadcast channel), chat (private group), user (direct message)
        data_type: type of data that is being collected ("messages", "iocs")

    Return:
        The path of the downloaded JSON file
    """
    logging.info(f"[+] Downloading {data_type} into JSON: {entity.id}")
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

        return json_file_name
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
        "--------------------------------------------------------------------------"
    )
    logging.info(f"[+] Begin {COLLECTION_NAME} scraping process")
    _collect(client, entity)
    logging.info(
        f"[+] Successfully scraped {COLLECTION_NAME} {get_entity_type_name(entity)}"
    )

    return True
