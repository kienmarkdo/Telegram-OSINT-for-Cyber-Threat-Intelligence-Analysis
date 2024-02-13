from telethon import TelegramClient
from telethon.sync import helpers
from telethon.types import *
from db import messages_get_offset_id, messages_insert_offset_id

import json
import os
import logging  # 2 TODO: Convert print statements to proper logging to a file
import time

from helper.helper import (
    JSONEncoder,
    _get_entity_type_name,
    _rotate_proxy,
)

OUTPUT_DIR: str = "output"
DATETIME_CODE_EXECUTED: str = str(datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ"))


def collect(client: TelegramClient, entity: Channel | Chat | User) -> bool:
    """


    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    entities: helpers.TotalList
    for dialog in client.iter_dialogs():
        entity: Channel | Chat | User = dialog.entity
        entities.append()


def download_messages(
    data: list[dict], data_type: str, entity: Channel | Chat | User
) -> bool:
    """
    Downloads collected messages into JSON files on the disk

    Args:
        data: list of collected objects (messages, participants...)
        data_type: string description of the type of data collected ("messages", "participants"...)
        entity: channel (public group or broadcast channel), chat (private group), user (direct message)

    Return:
        True if the download was successful
    """
    try:
        # Define the JSON file name
        json_file_name = f"{OUTPUT_DIR}/{DATETIME_CODE_EXECUTED}/{_get_entity_type_name(entity)}_{entity.id}/{data_type}_{entity.id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Write data from JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, cls=JSONEncoder, indent=2)

        print(f"{len(data)} {data_type} exported to {json_file_name}")

        return True
    except:
        print("[-] Failed to download the collected data into JSON files")
        raise


def scrape(client: TelegramClient) -> bool:
    """
    Scrapes a particular entity's metadata.

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
    collect(client)
