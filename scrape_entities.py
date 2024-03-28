import json
import logging
import os

from telethon import TelegramClient
from telethon.types import *

from helper import helper
from helper.es import index_json_file_to_es
from helper.helper import JSONEncoder, get_entity_type_name
from helper.logger import OUTPUT_DIR

COLLECTION_NAME: str = "entities"


def _collect(client: TelegramClient) -> list[dict]:
    """
    Collects information on all entities the current user is in

    Return:
        True if collection was successful
    """
    logging.info(f"[+] Collecting {COLLECTION_NAME} from Telethon API...")
    try:
        # Collect data via API
        entities_collected: list[Channel | Chat | User] = []
        for dialog in client.iter_dialogs():
            entity: Channel | Chat | User = dialog.entity
            entities_collected.append(entity)

        # Convert objects to JSON
        entities_list: list[dict] = []
        for entity in entities_collected:
            entity_dict: dict = entity.to_dict()
            entities_list.append(entity_dict)

        return entities_list
    except:
        logging.critical(
            "[-] Failed to collect data from Telegram API for unknown reasons"
        )
        raise


def _download(data: list[dict], data_type: str) -> str:
    """
    Downloads collected entities into JSON files on the disk

    Args:
        data: list of collected objects (messages, participants...)
        data_type: string description of the type of data collected ("messages", "participants"...)

    Return:
        The path of the downloaded JSON file
    """
    logging.info(f"[+] Downloading {COLLECTION_NAME} into JSON")
    try:
        # Define the JSON file name
        json_file_name = f"{OUTPUT_DIR}/{data_type}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Write data from JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, cls=JSONEncoder, indent=2)

        logging.info(f"{len(data)} {data_type} exported to {json_file_name}")

        return json_file_name
    except:
        logging.critical("[-] Failed to download the collected data into JSON files")
        raise


def download_entity(entity: Channel | Chat | User) -> bool:
    """
    Downloads a single collected entity into a JSON file on the disk

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if the download was successful
    """
    logging.info(f"[+] Downloading entity into JSON: {entity.id}")
    try:
        # Define the JSON file name
        data: dict = entity.to_dict()
        data_type: str = "entity_info"
        json_file_name = f"{OUTPUT_DIR}/{get_entity_type_name(entity)}_{entity.id}/{data_type}_{entity.id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Write data from JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, cls=JSONEncoder, indent=2)

        logging.info(f"{data_type} sucessfully exported to {json_file_name}")

        return True
    except:
        logging.critical("[-] Failed to download the collected data into JSON files")
        raise


def scrape(client: TelegramClient) -> bool:
    """
    Scrapes information on all entities the current user is in.

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
    # logging.info("==========================================================================")
    logging.info(
        "--------------------------------------------------------------------------"
    )
    logging.info(f"[+] Begin full {COLLECTION_NAME} scraping process")

    collected_result: list[dict] = _collect(client)
    if collected_result is None or len(collected_result) == 0:
        raise

    output_path: str = _download(collected_result, "all_entities")

    if helper.export_to_es:
        index_name: str = "entities_index"
        logging.info(f"[+] Exporting data to Elasticsearch")

        if index_json_file_to_es(output_path, index_name):
            logging.info(f"Indexed {COLLECTION_NAME} to Elasticsearch as: {index_name}")

    logging.info(f"[+] Successfully scraped {COLLECTION_NAME}")

    return True
