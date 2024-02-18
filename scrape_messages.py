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
    DATETIME_CODE_EXECUTED,
    OUTPUT_DIR,
)


def collect(client: TelegramClient, entity: Channel | Chat | User) -> bool:
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
        print("[+] Messages collection in progress...")

        # Collect messages from entity
        # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.get_messages
        # Or check client.iter_messages() documentation to see how client.get_messages() works
        # Due to limitations with the API retrieving more than 3000 messages will take longer than usual
        counter: int = 0  # Track number of API calls made
        counter_max: int = 3  # Max API calls to make in this collection
        chunk_size: int = 1000  # Number of messages to retrieve per iteration
        start_offset_id: int = messages_get_offset_id(entity.id)
        offset_id_value: int = start_offset_id
        collection_start_time: int = int(time.time())
        collection_end_time: int = collection_start_time
        messages_collected: helpers.TotalList = None

        # Proxy configurations
        counter_rotate_proxy: int = 2  # Number of iterations until proxy rotation

        # Main collection logic
        while True:
            # # Proxy rotation...
            # counter += 1
            # if counter == counter_rotate_proxy:
            #     print(f"Rotating proxy...")
            #     _rotate_proxy(client)
            #     counter = 0
            #     break

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

                print(f"Collecting {len(chunk)} messages...")
            else:  # No messages returned... All messages have been collected
                print(f"No Messages left to collect")
                break

            # Next collection will begin with this "latest message collected" offset id
            offset_id_value = chunk[-1].to_dict()["id"]

            counter += 1
            if counter == counter_max:
                break

        if messages_collected is None or len(messages_collected) == 0:
            print(f"There are no messages to collect. Skipping...")
            return True

        # Convert the Message object to JSON
        messages_list: list[dict] = []
        for message in messages_collected:
            # Known message types: Message, MessageService
            message_dict: dict = message.to_dict()
            messages_list.append(message_dict)

        download(messages_list, "messages", entity)

        print(f"Messages collection and download completed")
        print(f"Updating latest offset id for next collection as: {offset_id_value}")
        collection_end_time = int(time.time())

        # Insert collection details into DB for tracking purposes
        messages_insert_offset_id(
            entity.id,
            start_offset_id,
            offset_id_value,
            collection_start_time,
            collection_end_time,
        )
        return True
    except:
        print(f"Collection failed")
        raise


def download(data: list[dict], data_type: str, entity: Channel | Chat | User) -> bool:
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
    collect(client, entity)
