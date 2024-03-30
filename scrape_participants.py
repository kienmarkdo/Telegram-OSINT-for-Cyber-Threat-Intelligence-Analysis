import ijson
import json
import logging
import os
import re
import time
from datetime import datetime
from string import ascii_lowercase
from helper.es import index_json_file_to_es
from telethon import TelegramClient
from telethon.sync import helpers
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.users import GetFullUserRequest, GetUsersRequest
from telethon.types import *

from helper.helper import (
    EntityName,
    JSONEncoder,
    get_entity_info,
    get_entity_type_name,
    rotate_proxy,
)

from helper import helper
from helper.logger import OUTPUT_DIR

COLLECTION_NAME: str = "participants"


def _collect_all_under_10k(
    client: TelegramClient, entity: Channel | Chat | User
) -> bool:
    """
    Collects all participants in a given entity via its API and stores the data in-memory.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group).

    Collection can only be done on public groups, private groups, and direct messages,
    not broadcast channels, as subscribers are hidden from non-admin users at the API
    level and cannot be bypassed.

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    # NOTE: Cannot get channel participants / subscribers unless have admin privilege
    # https://stackoverflow.com/questions/69651904/telethon-get-channel-participants-without-admin-privilages

    # NOTE: There is a an unknown limit on participants collection
    # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.chats.ChatMethods.iter_participants
    # See documentation for the deprecated "aggressive" argument...
    # > There have been several changes to Telegram’s API that limits the amount of members that can be retrieved,
    #   and this was a hack that no longer works.
    logging.info(f"[+] Participants collection in progress...")

    # Check that entity type is not a broadcast channel
    if get_entity_type_name(entity) == EntityName.BROADCAST_CHANNEL.value:
        logging.info(
            f"Cannot collect participants in {EntityName.BROADCAST_CHANNEL.value}. Skipping participants collection..."
        )
        return True

    all_participants: helpers.TotalList = None
    all_participants = client.get_participants(entity, limit=None)

    if all_participants is None or len(all_participants) == 0:
        logging.info(f"No public participants were collected. Skipping...")
        return True
    else:
        # Evaluate percentage of participants successfully collected
        collected_amount: int = len(all_participants)
        total_amount: int = entity.participants_count
        logging.info(
            f"{collected_amount} participants collected out of {total_amount} total participants"
        )
        logging.info(
            f"Successfully collected {'{:.2f}'.format(collected_amount/total_amount * 100)}% of participants"
        )

    # Convert the Participants object to JSON
    participants_list: list[dict] = []
    for participant in all_participants:
        participant_dict: dict = participant.to_dict()
        participants_list.append(participant_dict)

    output_path: str = _download(participants_list, "participants", entity)

    # # Index data into Elasticsearch
    # if helper.export_to_es:
    #     index_name: str = "users_index"

    #     if index_json_file_to_es(output_path, index_name):
    #         logging.info(f"[+] Indexed {COLLECTION_NAME} to Elasticsearch as: {index_name}")


def _collect_all_over_10k(client, entity: Channel | Chat | User):
    """
    Collects all participants in a given entity via its API and stores the data in-memory.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group).

    Collection can only be done on public groups, private groups, and direct messages,
    not broadcast channels, as subscribers are hidden from non-admin users at the API
    level and cannot be bypassed.

    NOTE: Not implemented with the core Telethon API that collects an entity's participants,
    as it can only collect up to 10,000 participants in one call. Instead, this method uses
    custom tradecraft to achieve as close to 100% participants collection as possible.

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    # Collect participants https://github.com/LonamiWebs/Telethon/issues/580#issuecomment-362802359
    logging.warning(
        f"Not capable of collecting 100% users in an entity with over 10,000 users yet"
    )
    logging.info(f"[+] Participants collection in progress...")
    queryKey = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
    ]
    all_participants = []
    proxy_counter: int = 0

    for key in queryKey:
        offset = 0
        limit = 100
        while True:
            proxy_counter += 1
            if proxy_counter % 3 == 0:
                rotate_proxy(client)

            participants = client(
                GetParticipantsRequest(
                    entity.id, ChannelParticipantsSearch(key), offset, limit, hash=0
                )
            )
            if not participants.users:
                logging.info(
                    f"Done searching for first names whose first English character is '{key}'"
                )
                break
            for user in participants.users:
                try:
                    if re.findall(r"\b[a-zA-Z]", user.first_name)[0].lower() == key:
                        all_participants.append(user)

                except:
                    pass

            offset += len(participants.users)

    # After collection

    if all_participants is None or len(all_participants) == 0:
        logging.info(f"There are no participants to collect. Skipping...")
        return True
    else:
        # Evaluate percentage of participants successfully collected
        collected_amount: int = len(all_participants)
        total_amount: int = entity.participants_count
        logging.info(
            f"{collected_amount} participants collected out of {total_amount} total participants"
        )
        logging.info(
            f"Successfully collected {'{:.2f}'.format(collected_amount/total_amount * 100)}% of participants"
        )
    # Convert the Participants object to JSON
    participants_list: list[dict] = []
    for participant in all_participants:
        participant_dict: dict = participant.to_dict()
        participants_list.append(participant_dict)

    output_path: str = _download(participants_list, "participants", entity)

    # # Index data into Elasticsearch
    # if helper.export_to_es:
    #     index_name: str = "users_index"

    #     if index_json_file_to_es(output_path, index_name):
    #         logging.info(f"[+] Indexed {COLLECTION_NAME} to Elasticsearch as: {index_name}")


def _download(data: list[dict], data_type: str, entity: Channel | Chat | User) -> str:
    """
    Downloads collected participants into JSON files on the disk

    Args:
        data: list of collected objects (messages, participants...)
        data_type: string description of the type of data collected ("messages", "participants"...)
        entity: channel (public group or broadcast channel), chat (private group), user (direct message)

    Return:
        The path of the downloaded JSON file
    """
    try:
        # Define the JSON file name
        json_file_name = f"{OUTPUT_DIR}/{get_entity_type_name(entity)}_{entity.id}/{data_type}_{entity.id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Write data from JSON object to JSON file
        with open(json_file_name, "w") as json_file:
            json.dump(data, json_file, cls=JSONEncoder, indent=2)

        logging.info(f"{len(data)} {data_type} successfully exported to {json_file_name}")

        return json_file_name
    except:
        logging.critical("[-] Failed to download the collected data into JSON files")
        raise


def scrape_participants_from_messages(
    client: TelegramClient, entity: Channel | Chat | User
) -> bool:
    """
    Scrapes participants from group chat's sent messages.

    A group may not display the users who are in that group due to the configurations
    set by that group's admin(s). As such, we can only collect participant information
    of those who have sent messages, because those users have made themselves known by
    sending messages in the chat.

    Participants collection must be done by getting the information of the individual
    users who have sent messages. We do this by iterating through each message in the
    current collection run, and calling the GetUserInfoRequest API on each new user.

    For instance, if 2500 messages were scraped from the current collection run, then
    only the users who have sent those 2500 messages are collected.

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if scrape was successful
    """
    logging.info(
        "--------------------------------------------------------------------------"
    )
    logging.info(
        f"[+] Collecting participants from sent messages because --get-messages and --get-participants are set to True"
    )
    logging.info(
        f"[+] Get user information of those who have sent messages, rather than from the GetParticipants API"
    )
    logging.info(
        f"[+] Begin {COLLECTION_NAME} scraping process from messages collected"
    )

    # Extract user IDs from the messages_<entity_id>.json obtained from messages collection
    collected_user_ids: list[int] = []  # List of extracted unique user IDs
    messages_json_filename = f"{OUTPUT_DIR}/{get_entity_type_name(entity)}_{entity.id}/messages_{entity.id}.json"

    # Reduce RAM usage by storing chunks of JSON in memory, rather than the entire file
    # https://pythonspeed.com/articles/json-memory-streaming/
    with open(messages_json_filename, "r") as messages_file:
        message_objs = ijson.items(messages_file, "item")  # Use ijson to stream JSON
        for message_obj in message_objs:  # Process each message object
            curr_user_id: int = (message_obj.get("from_id") or {}).get("user_id")
            if curr_user_id and curr_user_id not in collected_user_ids:
                collected_user_ids.append(curr_user_id)

    # Call API to get each collected user's information
    collected_participants: list = []

    logging.info(
        f"Number of participants found in messages: {len(collected_user_ids)}"
    )
    # Use the GetFullUserRequest API to get one user's info
    # collected_participants = client(GetUsersRequest(collected_user_ids))
    # Chunk size for each API request
    chunk_size: int = 200

    # Iterate over the list of collected user IDs in chunks
    for i in range(0, len(collected_user_ids), chunk_size):
        # Get the chunk of user IDs
        chunk = collected_user_ids[i:i+chunk_size]
        logging.info(f"Getting information on {len(chunk)} users...")

        # Use the GetUsersRequest API to get user info for the chunk
        collected_participants.extend(client(GetUsersRequest(chunk)))

    # Convert the Participants object to JSON
    participants_list: list[dict] = []
    for participant in collected_participants:
        participant_dict: dict = participant.to_dict()
        participants_list.append(participant_dict)

    # Log collection metadata / statistics
    if collected_participants is None or len(collected_participants) == 0:
        logging.info(f"No new participants were collected")
        return True
    else:
        collected_amount: int = len(collected_participants)
        logging.info(f"Successfully collected {collected_amount} participants from messages")

    # Download the collected data to JSON, or append to existing JSON
    participants_json_filename: str = (
        f"{OUTPUT_DIR}/{get_entity_type_name(entity)}_{entity.id}/participants_{entity.id}.json"
    )

    if os.path.exists(participants_json_filename):
        # Participants JSON file exists; Append unique participants info to it
        with open(participants_json_filename, "r") as file:
            existing_participants_json = json.load(file)

        existing_ids: set[int] = {user["id"] for user in existing_participants_json}
        unique_users: list[dict] = [user for user in participants_list if user["id"] not in existing_ids]
        updated_participants_json = existing_participants_json + unique_users

        with open(participants_json_filename, "w") as file:
            json.dump(updated_participants_json, file, indent=2)
    else:
        # Participants JSON does not exist; Download new Participants JSON file as usual
        _download(participants_list, "participants", entity)

    return True


def scrape(
    client: TelegramClient, entity: Channel | Chat | User, collected_message: bool
) -> bool:
    """
    Scrapes participants in a particular entity.

    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group).

    Scraping has the following phases:
    - Collection: fetches participants from the provider API and stores the data in-memory
    - Download: downloads the collected participants from memory into disk (JSON file)

    Collection can only be done on public groups, private groups, and direct messages,
    not broadcast channels, as subscribers are hidden from non-admin users at the API
    level and cannot be bypassed.

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if scrape was successful
    """
    logging.info(
        "--------------------------------------------------------------------------"
    )
    logging.info(f"[+] Begin {COLLECTION_NAME} scraping process")

    # Check that entity type is not a broadcast channel
    if get_entity_type_name(entity) == EntityName.BROADCAST_CHANNEL.value:
        logging.info(
            f"Cannot collect participants in {EntityName.BROADCAST_CHANNEL.value}. Skipping participants collection..."
        )
        return None

    if entity.participants_count <= 10000:
        _collect_all_under_10k(client, entity)
    else:
        logging.info(
            f"There are {entity.participants_count} users in this {get_entity_info(entity)}"
        )
        logging.info(f"Please be patient while the collection runs...")
        _collect_all_over_10k(client, entity)

    # Collect participants who sent messages
    if collected_message:
        scrape_participants_from_messages(client, entity)

    # Index data into Elasticsearch
    output_path: str = (
        f"{OUTPUT_DIR}/{get_entity_type_name(entity)}_{entity.id}/participants_{entity.id}.json"
    )
    if helper.export_to_es:
        index_name: str = "users_index"

        if index_json_file_to_es(output_path, index_name):
            logging.info(f"[+] Indexed {COLLECTION_NAME} to Elasticsearch as: {index_name}")
    return True
